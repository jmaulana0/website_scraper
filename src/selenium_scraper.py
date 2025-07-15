#!/usr/bin/env python3
"""
Selenium-based DNB scraper that can handle JavaScript-rendered content

This scraper uses a headless browser to access the D&B business directory
and extract company information following the specifications in INSTRUCTIONS.md
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os
import random
import re

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'selenium_scraper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SeleniumDNBScraper:
    """Selenium-based scraper for DNB business directory"""
    
    def __init__(self):
        self.base_url = "https://www.dnb.com/business-directory/company-information.wholesale_trade.au.new_south_wales.html"
        self.driver = None
        self.companies_data = []
        self.max_pages = 100  # As specified in INSTRUCTIONS.md
        
    def setup_driver(self):
        """Set up Chrome driver with enhanced stealth options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster performance
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Enhanced stealth options
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Add user agent
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Try to use system Chrome driver first
            try:
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
                
                # Try different common paths for Chrome driver
                possible_paths = [
                    "/usr/local/bin/chromedriver",
                    "/opt/homebrew/bin/chromedriver",
                    "/usr/bin/chromedriver"
                ]
                
                driver_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        driver_path = path
                        break
                
                if driver_path:
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    # Try without specifying path (assumes chromedriver is in PATH)
                    self.driver = webdriver.Chrome(options=chrome_options)
                
                # Execute script to remove webdriver property
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                logger.info("Chrome driver initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Could not initialize Chrome driver: {e}")
                logger.info("Please install ChromeDriver: brew install chromedriver")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def get_page_content(self, page_num: int = 1) -> BeautifulSoup:
        """Get page content using Selenium for a specific page number"""
        try:
            # Construct URL based on page number
            if page_num == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}?page={page_num}"
            
            logger.info(f"Loading page {page_num}: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for body element to be present
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(2, 4))
            
            # Handle cookie consent only on first page
            if page_num == 1:
                try:
                    # Look for common popup/cookie consent elements
                    popup_selectors = [
                        "button[class*='accept']",
                        "button[class*='cookie']",
                        "button[class*='consent']",
                        ".cookie-banner button",
                        "#cookie-consent button"
                    ]
                    
                    for selector in popup_selectors:
                        try:
                            popup_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if popup_button.is_displayed():
                                popup_button.click()
                                logger.info(f"Clicked popup with selector: {selector}")
                                time.sleep(1)
                                break
                        except NoSuchElementException:
                            continue
                            
                except Exception as e:
                    logger.debug(f"No popup handling needed: {e}")
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Log page info
            title = soup.find('title')
            if title:
                logger.info(f"Page title: {title.get_text()}")
            
            return soup
            
        except TimeoutException:
            logger.error(f"Timeout loading page {page_num}: {url}")
            return None
        except Exception as e:
            logger.error(f"Error loading page {page_num} ({url}): {e}")
            return None
    
    def analyze_page_structure(self, soup: BeautifulSoup):
        """Analyze the page structure to understand the layout"""
        logger.info("=== PAGE STRUCTURE ANALYSIS ===")
        
        # Check if the page has loaded properly
        page_text = soup.get_text()
        if "javascript" in page_text.lower() and "enable" in page_text.lower():
            logger.warning("Page still shows JavaScript requirement")
        
        # Look for company listings with various selectors
        selectors_to_try = [
            'a[href*="company-profiles"]',
            '.company-listing',
            '.business-listing',
            '.company-name',
            '.business-name',
            '[data-company]',
            '.result',
            '.search-result',
            'div[class*="company"]',
            'div[class*="business"]',
            'li[class*="company"]',
            'li[class*="business"]'
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                if len(elements) > 0:
                    sample_text = elements[0].get_text(strip=True)[:100]
                    logger.info(f"Sample element text: {sample_text}")
        
        # Look for pagination
        pagination_elements = soup.find_all(['a', 'button'], text=re.compile(r'Next|Page|[0-9]+'))
        logger.info(f"Found {len(pagination_elements)} potential pagination elements")
        
        # Look for any structured data
        scripts = soup.find_all('script', {'type': 'application/ld+json'})
        if scripts:
            logger.info(f"Found {len(scripts)} JSON-LD structured data scripts")
        
        # Count total links
        all_links = soup.find_all('a', href=True)
        company_related_links = [link for link in all_links 
                               if any(keyword in link.get('href', '').lower() 
                                     for keyword in ['company', 'business', 'profile'])]
        logger.info(f"Found {len(company_related_links)} company-related links out of {len(all_links)} total links")
        
        return len(company_related_links) > 0
    
    def extract_company_data_enhanced(self, soup: BeautifulSoup) -> list:
        """Extract company data with enhanced location and revenue extraction"""
        companies = []
        
        try:
            # Find all company profile links
            company_links = soup.find_all('a', href=re.compile(r'company-profiles'))
            logger.info(f"Found {len(company_links)} company profile links")
            
            for link in company_links:
                try:
                    company_name = link.get_text(strip=True)
                    if not company_name or len(company_name) < 3:
                        continue
                    
                    company_data = {
                        'Company Name': company_name,
                        'Industry': 'Wholesale Trade',  # We know this from the URL
                        'Location': '',
                        'Sales Revenue ($M)': ''
                    }
                    
                    # Look for location and revenue in surrounding elements
                    # Check multiple parent levels for comprehensive data extraction
                    search_elements = []
                    
                    # Add the link's parent containers
                    current_element = link
                    for _ in range(3):  # Check up to 3 parent levels
                        parent = current_element.find_parent() if current_element else None
                        if parent:
                            search_elements.append(parent)
                            current_element = parent
                    
                    # Also check siblings of the link
                    if link.parent:
                        for sibling in link.parent.find_next_siblings(limit=3):
                            search_elements.append(sibling)
                        for sibling in link.parent.find_previous_siblings(limit=3):
                            search_elements.append(sibling)
                    
                    # Extract all text from search elements
                    combined_text = ""
                    for element in search_elements:
                        if element:
                            combined_text += " " + element.get_text()
                    
                    # Enhanced location extraction patterns
                    location_patterns = [
                        r'Country:\s*([^,\n]+,\s*New South Wales)',
                        r'Location:\s*([^,\n]+,\s*New South Wales)',
                        r'([A-Z][a-z\s]+,\s*New South Wales)',
                        r'([A-Z][a-z\s]+,\s*NSW)',
                        r'([A-Z][a-z\s]+),\s*Australia',
                        r'Country:\s*([^,\n]+),\s*[^,\n]+Australia'
                    ]
                    
                    for pattern in location_patterns:
                        location_match = re.search(pattern, combined_text, re.IGNORECASE)
                        if location_match:
                            location = location_match.group(1).strip()
                            # Clean up location
                            if 'Country:' not in location and len(location) > 2:
                                company_data['Location'] = location
                                break
                    
                    # Enhanced revenue extraction patterns
                    revenue_patterns = [
                        r'Sales Revenue \(\$M\):\s*\$([0-9,]+\.?[0-9]*M?)',
                        r'Revenue.*?\$([0-9,]+\.?[0-9]*[MKB]?)',
                        r'\$([0-9,]+\.?[0-9]*[MKB]?)\s*(?:revenue|sales)',
                        r'Sales.*?\$([0-9,]+\.?[0-9]*[MKB]?)',
                        r'\$([0-9,]+\.?[0-9]*M)\b'
                    ]
                    
                    for pattern in revenue_patterns:
                        revenue_match = re.search(pattern, combined_text, re.IGNORECASE)
                        if revenue_match:
                            revenue = revenue_match.group(1).replace(',', '')
                            # Ensure proper format
                            if not revenue.endswith('M') and not revenue.endswith('B') and not revenue.endswith('K'):
                                if '.' in revenue or len(revenue) > 3:
                                    revenue += 'M'
                            company_data['Sales Revenue ($M)'] = revenue
                            break
                    
                    companies.append(company_data)
                    logger.debug(f"Extracted: {company_name} | Location: {company_data['Location']} | Revenue: {company_data['Sales Revenue ($M)']}")
                
                except Exception as e:
                    logger.error(f"Error processing company: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(companies)} companies from this page")
            return companies
            
        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
            return []
    
    def has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page available"""
        try:
            # Look for pagination indicators
            next_indicators = [
                soup.find('a', string=re.compile(r'Next', re.IGNORECASE)),
                soup.find('a', string=re.compile(r'>', re.IGNORECASE)),
                soup.find('button', string=re.compile(r'Next', re.IGNORECASE)),
                soup.find('a', {'aria-label': re.compile(r'next', re.IGNORECASE)}),
            ]
            
            for indicator in next_indicators:
                if indicator and (indicator.get('href') or indicator.get('onclick')):
                    return True
            
            # Also check for numbered pagination
            page_numbers = soup.find_all('a', href=re.compile(r'page=\d+'))
            if page_numbers:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking for next page: {e}")
            return False

    def scrape_all_pages(self):
        """Scrape all pages following INSTRUCTIONS.md specifications"""
        if not self.setup_driver():
            logger.error("Could not set up web driver")
            return
        
        try:
            page_num = 1
            
            while page_num <= self.max_pages:
                logger.info(f"Processing page {page_num}")
                
                # Get page content
                soup = self.get_page_content(page_num)
                
                # Check stopping condition: failed to load page
                if not soup:
                    logger.error(f"Failed to load page {page_num}, stopping")
                    break
                
                # Extract company data from this page
                page_companies = self.extract_company_data_enhanced(soup)
                
                # Check stopping condition: no companies found
                if not page_companies:
                    logger.info(f"No companies found on page {page_num}, stopping")
                    break
                
                # Add companies to our dataset
                self.companies_data.extend(page_companies)
                
                logger.info(f"Page {page_num} completed. Companies on this page: {len(page_companies)}")
                logger.info(f"Total companies collected so far: {len(self.companies_data)}")
                
                # Check stopping condition: no next page
                if not self.has_next_page(soup):
                    logger.info("No next page found, stopping")
                    break
                
                # Add delay between requests with longer wait for subsequent pages
                if page_num == 1:
                    delay = 1.5
                else:
                    delay = random.uniform(3.0, 5.0)  # Longer delay for subsequent pages
                
                logger.info(f"Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
                
                page_num += 1
            
            logger.info(f"Scraping completed. Total companies collected: {len(self.companies_data)}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def save_to_csv(self, filename: str = None):
        """Save scraped data to CSV as specified in INSTRUCTIONS.md"""
        if filename is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            filename = os.path.join(data_dir, 'dnb_wholesale_nsw.csv')  # As specified in INSTRUCTIONS.md
        
        try:
            if not self.companies_data:
                logger.warning("No data to save")
                return
            
            # Create DataFrame with exact columns as specified in INSTRUCTIONS.md
            df = pd.DataFrame(self.companies_data)
            
            # Ensure we have the required columns in the right order
            required_columns = ['Company Name', 'Industry', 'Location', 'Sales Revenue ($M)']
            
            # Make sure all columns exist
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Reorder columns to match INSTRUCTIONS.md specification
            df = df[required_columns]
            
            df.to_csv(filename, index=False)
            logger.info(f"Data saved to {filename}")
            logger.info(f"Total records: {len(df)}")
            
            # Show sample of what we collected
            logger.info("Sample of collected data:")
            for i, row in df.head(10).iterrows():
                logger.info(f"{i+1}. {row['Company Name']} | {row['Location']} | {row['Sales Revenue ($M)']}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")


def main():
    """Main function"""
    logger.info("Starting Selenium DNB scraper with pagination")
    
    scraper = SeleniumDNBScraper()
    scraper.scrape_all_pages()
    scraper.save_to_csv()
    
    logger.info("Selenium scraping completed")


if __name__ == "__main__":
    main()
