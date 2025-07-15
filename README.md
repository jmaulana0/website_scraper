# Universal Web Scraper

A production-ready, generic web scraping toolkit that can be adapted for various websites. Features advanced anti-bot protection, proxy support, and robust data extraction capabilities.

## ✅ **Tested and Working**

This scraper has been tested and verified to work with real websites. Example: Successfully extracted 30 quotes from quotes.toscrape.com across 3 pages with clean CSV output.

## 🚀 Features

- **Universal Design**: Easily adaptable for different target websites
- **Advanced Anti-Bot Protection**: Stealth browser configurations and randomization
- **Proxy Support**: Built-in proxy rotation and testing capabilities  
- **Multiple Scraping Methods**: Selenium for JavaScript-heavy sites, requests for static content
- **Robust Error Handling**: Retry logic, graceful failures, and comprehensive logging
- **Data Export**: CSV output with configurable formatting
- **Configuration-Driven**: YAML configuration for easy customization

## 📁 Project Structure

```
website_scraper/
├── src/
│   ├── universal_scraper.py    # Advanced scraper with proxy support
│   └── selenium_scraper.py     # Basic Selenium scraper
├── config/
│   └── settings.yaml          # Configuration file
├── data/
│   └── *.csv                  # Scraped data output
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome/ChromeDriver**
   - Install Google Chrome browser
   - Install ChromeDriver (or use webdriver-manager for automatic management)

3. **Configure Settings**
   - Edit `config/settings.yaml` to match your target website
   - Update selectors, URLs, and scraping parameters

## ⚙️ Configuration

Edit `config/settings.yaml` to customize for your target website:

```yaml
target:
  base_url: "https://your-target-site.com"
  max_pages: 10
  delay_range: [3, 8]

scraping:
  selectors:
    container: "div.item"           # Main item containers
    title: "h2, h3"                # Title elements
    description: "p, .description"  # Description elements
    # Add more selectors as needed

proxy:
  enabled: true                    # Enable/disable proxy rotation
  max_failures: 3                 # Max failures before removing proxy
```

## 🎯 Usage

### Universal Scraper (Recommended)
```python
from src.universal_scraper import UniversalWebScraper

# Initialize with config file
scraper = UniversalWebScraper('config/settings.yaml')

# Run scraper
success = scraper.run()
```

### Basic Selenium Scraper
```python
from src.selenium_scraper import SeleniumWebScraper

# Initialize with target URL
scraper = SeleniumWebScraper(
    base_url="https://example.com",
    max_pages=5
)

# Run scraper
success = scraper.run()
```

### Command Line Usage
```bash
# Run universal scraper
cd src && python universal_scraper.py

# Run basic selenium scraper  
cd src && python selenium_scraper.py
```

## 🔧 Customization

### For Different Websites

1. **Update Configuration**: Modify `config/settings.yaml` with:
   - Target website URL
   - CSS selectors for data extraction
   - Pagination patterns
   - Output preferences

2. **Customize Selectors**: Update the extraction logic in the scraper files:
   - `container`: Main item wrapper elements
   - `title`: Title/name elements
   - `description`: Description/summary elements
   - `link`: Link elements
   - Add custom fields as needed

3. **Adapt Data Structure**: Modify the data extraction methods to match your target site's structure

### Example Adaptations

**E-commerce Site**:
```yaml
scraping:
  selectors:
    container: ".product-item"
    title: ".product-name"
    price: ".price"
    rating: ".rating"
```

**News Site**:
```yaml
scraping:
  selectors:
    container: "article"
    title: "h1, h2"
    summary: ".excerpt"
    date: ".publish-date"
```

## 🛡️ Anti-Bot Features

- **Stealth Browser Configuration**: Removes automation signatures
- **User Agent Rotation**: Random, realistic user agents
- **Request Timing**: Random delays between requests
- **Proxy Support**: IP rotation to avoid rate limiting
- **Error Recovery**: Intelligent retry logic with backoff

## 📊 Output

Scraped data is saved to CSV files in the `data/` directory with:
- Structured data columns
- Page number tracking
- Extraction order preservation
- UTF-8 encoding for international characters

## 🚨 Legal & Ethical Usage

- **Respect robots.txt**: Check target site's robots.txt file
- **Rate Limiting**: Use appropriate delays between requests
- **Terms of Service**: Comply with website terms of service
- **Data Privacy**: Handle scraped data responsibly
- **Commercial Use**: Ensure compliance with applicable laws

## 🐛 Troubleshooting

**ChromeDriver Issues**:
```bash
# Install ChromeDriver via homebrew (macOS)
brew install chromedriver

# Or install webdriver-manager for automatic management
pip install webdriver-manager
```

**Proxy Issues**:
- Free proxies may be unreliable
- Consider premium proxy services for production use
- Disable proxy rotation if not needed: `proxy.enabled: false`

**Site Blocking**:
- Increase delays between requests
- Use different proxy sources
- Update user agent strings
- Check for updated anti-bot measures

## 📝 Logging

Detailed logs are written to:
- `scraper.log`: General scraping activities
- Console output: Real-time progress updates

Log levels can be adjusted in the scraper files.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test with different websites
5. Submit a pull request

## 📄 License

This project is provided for educational and research purposes. Users are responsible for ensuring compliance with applicable laws and website terms of service.
