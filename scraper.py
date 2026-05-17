"""Tech Economy Data Flow: Alphabet Acquisitions Scraper by Rizwan Syedalavi Kaleelu"""

"""This project is a data extraction and processing pipeline built to track the flow of money in the tech economy. It uses Python and the Scrapling library 
(leveraging stealth, anti-bot browser capabilities) to scrape the comprehensive list of Alphabet's (Google's) mergers and acquisitions from Wikipedia.
The script cleans messy financial data, stores it persistently in a local MongoDB database, and performs data aggregation to generate business intelligence metrics.

Github link :https://github.com/Rizwan-SK/alphabet-etl-pipeline

Check the README.md file for detailed instructions on setting up the environment, running the scraper, and understanding the output metrics."""

import re
from scrapling.fetchers import Fetcher
from pymongo import MongoClient

def clean_value(value_str):
    """Cleans Wikipedia currency strings into integers."""
    if not value_str: 
        return 0
    
    if "undisclosed" in value_str.lower() or "—" in value_str or "-" in value_str:
        return 0
    
    # Remove citations [1], dollar signs, commas, and ALL hidden spaces
    cleaned = re.sub(r'\[.*?\]', '', value_str)
    cleaned = cleaned.replace('$', '').replace(',', '').replace(' ', '').replace('\xa0', '').strip()
    
    multiplier = 1
    if 'billion' in cleaned.lower():
        multiplier = 1_000_000_000
        cleaned = cleaned.lower().replace('billion', '')
    elif 'million' in cleaned.lower():
        multiplier = 1_000_000
        cleaned = cleaned.lower().replace('million', '')
        
    match = re.search(r'[\d\.]+', cleaned)
    if match:
        try:
            return int(float(match.group()) * multiplier)
        except ValueError:
            return 0
    return 0

def run_scraper():
    print("Fetching data from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_mergers_and_acquisitions_by_Alphabet"
    page = Fetcher.get(url)
    
    # ==========================================
    # 1. BULLETPROOF TABLE SELECTION
    # ==========================================
    tables = page.css('table.wikitable')
    target_table = None
    
    for tbl in tables:
        # Checking raw HTML is safer than .text due to hidden Wikipedia sorting tags
        html_str = tbl.get().lower() if hasattr(tbl, 'get') else str(tbl).lower()
        if 'acquisition date' in html_str and 'company' in html_str:
            target_table = tbl
            break
            
    if not target_table:
        print("Error: Could not find the main acquisitions table!")
        return

    table_rows = target_table.css('tr')
    
    # ==========================================
    # 2. THE 2D GRID PARSER
    # ==========================================
    grid = {}
    
    for r_idx, row in enumerate(table_rows):
        cells = row.xpath('./th | ./td')
        c_idx = 0
        
        for cell in cells:
            # Skip occupied columns
            while grid.get((r_idx, c_idx)) is not None:
                c_idx += 1
                
            # DEEP TEXT EXTRACTION: Get all nested text (ignores <a> and <span> tags)
            try:
                texts = cell.xpath('.//text()').getall()
                text = "".join(texts).replace('\xa0', ' ').strip()
            except Exception:
                text = cell.text.replace('\xa0', ' ').strip() if hasattr(cell, 'text') and cell.text else ""
            
            # SAFE ATTRIBUTE EXTRACTION
            try:
                rowspan_str = cell.xpath('@rowspan').get()
            except Exception:
                rowspan_str = None
                
            try:
                colspan_str = cell.xpath('@colspan').get()
            except Exception:
                colspan_str = None
            
            rowspan = int(rowspan_str) if rowspan_str and rowspan_str.isdigit() else 1
            colspan = int(colspan_str) if colspan_str and colspan_str.isdigit() else 1
            
            # Fill the grid dimensions
            for r in range(rowspan):
                for c in range(colspan):
                    grid[(r_idx + r, c_idx + c)] = text
                    
            c_idx += colspan

    # ==========================================
    # 3. DATA EXTRACTION & CLEANING FILTER
    # ==========================================
    data_to_insert = []
    max_row = max([k[0] for k in grid.keys()]) if grid else 0
    
    for r_idx in range(1, max_row + 1):
        date = grid.get((r_idx, 1), "").strip()
        company = grid.get((r_idx, 2), "").strip()
        business = grid.get((r_idx, 3), "").strip()
        country = grid.get((r_idx, 4), "").strip()
        price_str = grid.get((r_idx, 5), "")
        
        # STRICT FILTER: Skip headers and null data
        if not company or not date or company == date:
            continue
            
        record = {
            "date": date,
            "company": company,
            "business": business if business else "Unknown",
            "country": country if country else "Unknown",
            "value": clean_value(price_str)
        }
        data_to_insert.append(record)

    # ==========================================
    # 4. MONGODB CONNECTION & DATA INSERTION
    # ==========================================
    print("Connecting to MongoDB...")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['tech_economy_db']
    collection = db['acquisitions']
    
    collection.delete_many({})
    
    if data_to_insert:
        collection.insert_many(data_to_insert)
        print(f"Successfully cleaned and inserted {len(data_to_insert)} valid records.\n")
    else:
        print("No records found to insert.")
        return

    # ==========================================
    # 5. GOLD LAYER BUSINESS OUTCOMES
    # ==========================================
    print("--- BUSINESS OUTCOMES (GOLD LAYER) ---")

    # 1. Total money spent (Sum of all known values)
    total_spent = list(collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]))
    total_val = total_spent[0]['total'] if total_spent else 0
    print(f"1. Total Money Spent: ${total_val:,}")

    # 2. Top 3 most expensive buys (Excluding $0/undisclosed)
    top_3 = collection.find({"value": {"$gt": 0}}).sort("value", -1).limit(3)
    print("\n2. Top 3 Most Expensive Buys:")
    for i, corp in enumerate(top_3, 1):
        print(f"   {i}. {corp['company']} (${corp['value']:,})")

    # 3. Count of acquisitions grouped by business sector
    by_sector = collection.aggregate([
        {"$match": {"business": {"$nin": ["", "Unknown"]}}}, 
        {"$group": {"_id": "$business", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ])
    print("\n3. Top 5 Business Sectors by Acquisition Count:")
    for sector in by_sector:
        print(f"   - {sector['_id']}: {sector['count']}")

    # 4. Average cost of a disclosed acquisition
    avg_disclosed = list(collection.aggregate([
        {"$match": {"value": {"$gt": 0}}},
        {"$group": {"_id": None, "avg": {"$avg": "$value"}}}
    ]))
    if avg_disclosed:
        print(f"\n4. Average Disclosed Acquisition Cost: ${avg_disclosed[0]['avg']:,.2f}")
    else:
        print("\n4. Average Disclosed Acquisition Cost: $0")

    # 5. Count of acquisitions grouped by country
    by_country = collection.aggregate([
        {"$match": {"country": {"$nin": ["", "Unknown"]}}},
        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ])
    print("\n5. Top 5 Acquisitions by Country:")
    for country in by_country:
        print(f"   - {country['_id']}: {country['count']}")

if __name__ == "__main__":
    run_scraper()