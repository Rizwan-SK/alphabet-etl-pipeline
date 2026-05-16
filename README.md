# Tech Economy Data Flow: Alphabet Acquisitions Scraper

## Project Overview
This project is a data extraction and processing pipeline built to track the flow of money in the tech economy. It uses Python to scrape the comprehensive list of Alphabet's (Google's) mergers and acquisitions from Wikipedia. 

The script cleans messy financial data, stores it persistently in a local MongoDB database, and performs data aggregation to generate business intelligence metrics.

> **Note:** If you encounter any issues during setup or execution, please refer to the [Troubleshooting](#-troubleshooting) section at the bottom of this document.

## Business Outcomes (Gold Layer)
The script queries the cleaned database to produce 5 distinct analytical outcomes:
1. **Total Money Spent:** Overall disclosed acquisition spending.
2. **Top 3 Most Expensive Acquisitions:** Ranked by purchase price.
3. **Acquisitions by Business Sector:** Categorized count to identify investment trends.
4. **Average Cost:** The mean price per disclosed acquisition.
5. **Geographic Distribution:** Acquisitions grouped and counted by country.

---

## Prerequisites
To run this project, you will need:
* **Operating System:** Linux (Mint/Ubuntu) recommended, macOS/Windows supported.
* **Python:** Version 3.10 or higher.
* **Database:** MongoDB installed and running locally on the default port (`27017`).

---

## Bulletproof Setup Instructions

Follow these exact steps to set up the environment safely and ensure the stealth browser dependencies do not crash.

**1. Clone the repository and enter the directory:**
```bash
git clone [https://github.com/Rizwan-SK/alphabet-etl-pipeline](https://github.com/Rizwan-SK/alphabet-etl-pipeline)
cd alphabet-etl-pipeline
```

**2. Ensure MongoDB is running:**
Make sure your local MongoDB service is active. On Linux Mint/Ubuntu, you can start it with:
```bash
sudo systemctl start mongod
```

**3. Create and activate a Virtual Environment:**
This isolates the project dependencies from your system Python.
```bash
python3 -m venv venv
source venv/bin/activate
```
*(Note for Windows users: use `venv\Scripts\activate` instead)*

**4. Install Python Packages:**
Install the required libraries (`scrapling[all]` and `pymongo`):
```bash
pip install -r requirements.txt
```

**5. Install Stealth Browser Binaries:**
Initialize Scrapling's anti-bot browser dependencies:
```bash
scrapling install
```

**6. Install System-Level Dependencies (Linux/Mac only):**
If you are running this on a fresh Linux install, run this command to ensure the headless browser has the necessary OS-level libraries (like fonts and media packages) to launch successfully:
```bash
playwright install-deps
```

---

## How to Run the Project

Once your environment is set up and MongoDB is running, simply execute the main script:

```bash
python scraper.py
```

The script will:
1. Clear any old data to prevent duplicates.
2. Fetch the latest Wikipedia data.
3. Clean the financial strings into pure integers.
4. Insert the clean documents into MongoDB.
5. Output the 5 Gold Layer Business Outcomes directly to your terminal.

---

## Troubleshooting

* **Error: `pymongo.errors.ServerSelectionTimeoutError` (Connection Refused)**
  * **Cause:** Your Python script cannot find MongoDB.
  * **Fix:** Ensure MongoDB is installed and running. Run `sudo systemctl status mongod` to check its status, and `sudo systemctl start mongod` to boot it up.
* **Error: `ModuleNotFoundError: No module named 'scrapling'`**
  * **Cause:** The virtual environment isn't activated, or the packages weren't installed.
  * **Fix:** Ensure you see `(venv)` in your terminal prompt. If not, run `source venv/bin/activate` and try running the script again.
* **Browser crashes or Playwright OS Errors on execution**
  * **Cause:** Missing low-level Linux libraries required by the headless browser.
  * **Fix:** Run `playwright install-deps` in your terminal to automatically install the missing system packages.
