#!/usr/bin/env python3
"""
Universal Web Scraper with Proxy Support and Anti-Bot Protection

A production-ready web scraper that can be adapted for various websites.
Features:
- Proxy rotation and testing
- Advanced stealth browser configuration  
- Robust error handling and retry logic
- CSV data export
- Configurable for different target sites
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os
import random
import re
import requests
from typing import List, Dict, Optional
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UniversalWebScraper:
    """Universal web scraper with proxy support and anti-bot protection"""
    
    def __init__(self, config_file: str = 'config/settings.yaml'):
        """Initialize scraper with configuration"""
        self.config = self.load_config(config_file)
        self.driver = None
        self.scraped_data = []
        self.proxy_list = []
        self.current_proxy_index = 0
        self.session_count = 0
        
        # Enhanced user agents for better stealth
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except Exception as e:
            logger.warning(f"Could not load config file {config_file}: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            'target': {
                'base_url': 'https://example.com',
                'max_pages': 10,
                'delay_range': [3, 8],
                'page_load_timeout': 15
            },
            'scraping': {
                'selectors': {
                    'container': 'div.item',
                    'title': 'h2, h3',
                    'description': 'p, .description',
                    'link': 'a'
                },
                'pagination': {
                    'url_pattern': '{base_url}?page={page_num}',
                    'start_page': 1
                }
            },
            'proxy': {
                'enabled': True,
                'max_failures': 3,
                'rotation_frequency': 5
            },
            'output': {
                'filename': 'scraped_data.csv',
                'directory': 'data'
            }
        }
    
    def fetch_proxy_list(self) -> List[Dict]:
        """Fetch working proxies from multiple sources"""
        logger.info("Fetching proxy list...")
        proxies = []
        
        # Free proxy APIs
        proxy_sources = [
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10, verify=False)
                if response.status_code == 200:
                    content = response.text.strip()
                    proxy_lines = content.split('\n')
                    
                    for line in proxy_lines[:20]:  # Limit per source
                        line = line.strip()
                        if ':' in line and len(line.split(':')) == 2:
                            ip, port = line.split(':')
                            if self.is_valid_ip(ip) and port.isdigit():
                                proxies.append({'ip': ip, 'port': port})
                                
                    logger.info(f"Fetched proxies from {source}")
            except Exception as e:
                logger.warning(f"Failed to fetch from {source}: {e}")
        
        logger.info(f"Total proxies collected: {len(proxies)}")
        return proxies
    
    def is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def test_proxy(self, proxy: Dict) -> bool:
        """Test if a proxy is working"""
        try:
            proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
            test_proxies = {'http': proxy_url, 'https': proxy_url}
            
            response = requests.get(
                "http://httpbin.org/ip",
                proxies=test_proxies,
                timeout=10,
                headers={'User-Agent': random.choice(self.user_agents)}
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Proxy {proxy['ip']}:{proxy['port']} is working")
                return True
                
        except Exception as e:
            logger.debug(f"Proxy {proxy['ip']}:{proxy['port']} failed: {e}")
        
        return False
    
    def get_working_proxies(self) -> List[Dict]:
        """Get list of working proxies"""
        if not self.config['proxy']['enabled']:
            return []
        
        all_proxies = self.fetch_proxy_list()
        working_proxies = []
        
        logger.info("Testing proxies...")
        for proxy in all_proxies:
            if len(working_proxies) >= 10:  # Limit working proxies
                break
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        logger.info(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    def setup_driver(self, proxy: Optional[Dict] = None) -> bool:
        """Setup Chrome driver with stealth configuration"""
        try:
            chrome_options = Options()
            
            # Basic stealth options
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Anti-detection options
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            
            # Random user agent
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Add proxy if provided
            if proxy:
                proxy_string = f"{proxy['ip']}:{proxy['port']}"
                chrome_options.add_argument(f"--proxy-server=http://{proxy_string}")
                logger.info(f"Using proxy: {proxy_string}")
            
            # Initialize driver
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception:
                # Fallback to system chromedriver
                service = Service("/usr/local/bin/chromedriver")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute stealth scripts
            stealth_scripts = [
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
            ]
            
            for script in stealth_scripts:
                try:
                    self.driver.execute_script(script)
                except:
                    pass
            
            logger.info("Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def get_page_content(self, url: str, retry_count: int = 0) -> Optional[BeautifulSoup]:
        """Get page content with retry logic"""
        max_retries = 3
        
        try:
            logger.info(f"Loading: {url}")
            
            # Random delay
            delay_range = self.config['target']['delay_range']
            delay = random.uniform(delay_range[0], delay_range[1])
            logger.info(f"Waiting {delay:.1f} seconds...")
            time.sleep(delay)
            
            self.driver.get(url)
            
            # Wait for page load
            timeout = self.config['target']['page_load_timeout']
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(2, 4))
            
            # Check for blocking patterns
            page_text = self.driver.page_source.lower()
            block_indicators = [
                'access denied', 'blocked', 'captcha', 'unusual traffic',
                'bot detected', 'security check'
            ]
            
            if any(indicator in page_text for indicator in block_indicators):
                logger.warning("Page appears to be blocked")
                if retry_count < max_retries and self.proxy_list:
                    logger.info("Rotating proxy and retrying...")
                    self.rotate_proxy()
                    time.sleep(random.uniform(5, 10))
                    return self.get_page_content(url, retry_count + 1)
                return None
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            self.session_count += 1
            
            logger.info("Page loaded successfully")
            return soup
            
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            if retry_count < max_retries and self.proxy_list:
                self.rotate_proxy()
                time.sleep(random.uniform(5, 10))
                return self.get_page_content(url, retry_count + 1)
            return None
    
    def rotate_proxy(self):
        """Rotate to next working proxy"""
        if not self.proxy_list:
            return
        
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        current_proxy = self.proxy_list[self.current_proxy_index]
        
        logger.info(f"Rotating to proxy: {current_proxy['ip']}:{current_proxy['port']}")
        self.setup_driver(current_proxy)
        self.session_count = 0
    
    def extract_data_from_page(self, soup: BeautifulSoup, page_num: int) -> List[Dict]:
        """Extract data from page using configured selectors"""
        extracted_items = []
        
        try:
            selectors = self.config['scraping']['selectors']
            container_selector = selectors.get('container', 'div')
            
            # Find all container elements
            containers = soup.select(container_selector)
            logger.info(f"Found {len(containers)} items on page {page_num}")
            
            for idx, container in enumerate(containers):
                item = {'page_number': page_num, 'item_index': idx + 1}
                
                # Extract title
                title_selector = selectors.get('title', 'h1, h2, h3')
                title_elem = container.select_one(title_selector)
                if title_elem:
                    item['title'] = title_elem.get_text(strip=True)
                
                # Extract description
                desc_selector = selectors.get('description', 'p')
                desc_elem = container.select_one(desc_selector)
                if desc_elem:
                    item['description'] = desc_elem.get_text(strip=True)
                
                # Extract link
                link_selector = selectors.get('link', 'a')
                link_elem = container.select_one(link_selector)
                if link_elem and link_elem.get('href'):
                    item['link'] = link_elem.get('href')
                
                # Only add items with at least a title
                if item.get('title'):
                    extracted_items.append(item)
            
            logger.info(f"Extracted {len(extracted_items)} valid items from page {page_num}")
            
        except Exception as e:
            logger.error(f"Error extracting data from page {page_num}: {e}")
        
        return extracted_items
    
    def save_to_csv(self):
        """Save scraped data to CSV file"""
        if not self.scraped_data:
            logger.warning("No data to save")
            return
        
        output_dir = self.config['output']['directory']
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.join(output_dir, self.config['output']['filename'])
        
        try:
            df = pd.DataFrame(self.scraped_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Saved {len(self.scraped_data)} items to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def run(self) -> bool:
        """Run the scraper"""
        logger.info("Starting web scraper...")
        
        try:
            # Get working proxies
            if self.config['proxy']['enabled']:
                self.proxy_list = self.get_working_proxies()
            
            # Setup initial driver
            initial_proxy = self.proxy_list[0] if self.proxy_list else None
            if not self.setup_driver(initial_proxy):
                logger.error("Failed to setup driver")
                return False
            
            # Scrape pages
            base_url = self.config['target']['base_url']
            max_pages = self.config['target']['max_pages']
            url_pattern = self.config['scraping']['pagination']['url_pattern']
            start_page = self.config['scraping']['pagination']['start_page']
            
            for page_num in range(start_page, start_page + max_pages):
                logger.info(f"Processing page {page_num}/{start_page + max_pages - 1}")
                
                # Construct URL
                if page_num == 1:
                    url = base_url
                else:
                    url = url_pattern.format(base_url=base_url, page_num=page_num)
                
                soup = self.get_page_content(url)
                if soup is None:
                    logger.warning(f"Could not load page {page_num}, stopping")
                    break
                
                items = self.extract_data_from_page(soup, page_num)
                if not items:
                    logger.warning(f"No items found on page {page_num}")
                    continue
                
                self.scraped_data.extend(items)
                logger.info(f"Total items collected: {len(self.scraped_data)}")
                
                # Check if we need to rotate proxy
                rotation_freq = self.config['proxy']['rotation_frequency']
                if (self.proxy_list and 
                    self.session_count >= rotation_freq):
                    self.rotate_proxy()
                
                # Delay between pages
                delay = random.uniform(5, 12)
                logger.info(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
            
            # Save results
            if self.scraped_data:
                self.save_to_csv()
                logger.info(f"Scraping completed! Total items: {len(self.scraped_data)}")
                return True
            else:
                logger.warning("No data was scraped")
                return False
                
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            if self.scraped_data:
                self.save_to_csv()
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if self.scraped_data:
                self.save_to_csv()
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")


def main():
    """Main function"""
    scraper = UniversalWebScraper()
    
    try:
        success = scraper.run()
        if success:
            logger.info("Scraping completed successfully!")
        else:
            logger.error("Scraping failed")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()
