# Website Scraper

A Selenium-based web scraper for extracting business directory data from DNB (Dun & Bradstreet).

## Target Website
https://www.dnb.com/business-directory/company-information.wholesale_trade.au.new_south_wales.html

## Project Structure
```
website_scraper/
├── src/
│   ├── selenium_scraper.py    # Main working scraper
│   └── README.md
├── data/
│   ├── dnb_wholesale_nsw_selenium.csv  # Scraped data (50 companies)
│   └── README.md
├── config/
│   ├── settings.yaml          # Configuration file
│   └── README.md
├── docs/                      # Documentation
├── logs/
│   ├── selenium_scraper.log   # Scraper logs
│   └── README.md
├── tests/                     # Test files
├── INSTRUCTIONS.md            # Detailed scraping instructions
├── requirements.txt           # Python dependencies
├── run.py                     # Simple runner script
└── README.md                  # This file
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install ChromeDriver:**
   ```bash
   brew install chromedriver
   ```

3. **Run the scraper:**
   ```bash
   python run.py
   ```

## Current Status

✅ **Working:** The Selenium-based scraper successfully:
- Accesses the DNB website (handles JavaScript content)
- Extracts company names and profile URLs
- Handles cookie consent popups
- Saves data to CSV format
- Successfully collected 50 companies from the first page

## Data Collected

The scraper has successfully extracted data for 50 wholesale trade companies in New South Wales, including:
- Company names (e.g., "WOOLWORTHS GROUP LIMITED", "BUNNINGS PROPERTIES PTY. LTD")
- Profile URLs for each company
- Ready for extension to extract location and revenue data

## Next Steps

See `INSTRUCTIONS.md` for detailed requirements and potential enhancements.
