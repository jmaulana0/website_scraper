# Web Scraping Instruction Document: NSW Wholesale Trade Companies from D&B Directory

## Objective

This document describes the step-by-step process to scrape data from the Dun & Bradstreet (D&B) public business directory page listing wholesale trade companies in New South Wales, Australia. The goal is to extract structured information such as company name, industry, location, and profile URL, and store it in CSV format.

## Target URL

Primary index page:
https://www.dnb.com/business-directory/company-information.wholesale_trade.au.new_south_wales.html

Pagination follows the pattern:
https://www.dnb.com/business-directory/company-information.wholesale_trade.au.new_south_wales.html?page=2
etc.
where 'page=2' can be replaced with the incremental next page.

## Tools and Libraries

The scraping workflow should be implemented in Python using the following libraries:
- `requests` for sending HTTP requests
- `BeautifulSoup` from `bs4` for HTML parsing
- `pandas` for storing and exporting structured data
- `time` for inserting delays between requests

## Scraping Workflow

1. Start at the main directory URL and extract the contents of the first page.
2. Loop through subsequent pages by dynamically constructing the URL with the incremented page number.
3. For each page:
   - Send a `GET` request to the page using `requests`, including appropriate headers to mimic a browser user-agent.
   - Parse the HTML response using `BeautifulSoup`.
   - Locate all HTML elements representing company listings. These are typically contained in identifiable card-style containers or table rows.
4. From each company listing, extract the following fields:
   - Company Name
   - Industry (if shown)
   - Location
   - Sales Revenue ($M)

Optional fields, if available directly in the listing or reachable via the profile URL, may include:
   - Contact email or phone
   - Company size (employee count)
   - Industry classification

5. Stop the loop when one of the following occurs:
   - The response status code is 404 or non-200.
   - The parsed page contains no company listings.
   - A pre-set maximum number of pages (e.g., 100) has been reached.

6. Add a delay between page requests using `time.sleep(1.5)` to avoid rate limiting or IP bans.

## Output Format

The extracted data should be stored in a CSV file named `dnb_wholesale_nsw.csv`.  
The CSV should contain the following columns:

