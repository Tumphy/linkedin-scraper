# Troubleshooting Guide

This guide helps you resolve common issues with the LinkedIn Scraper.

## 🚨 Common Issues & Solutions

### 1. "Cannot extract full name" Error

**Symptoms:**
- Profiles extracted but `full_name` is empty
- Extraction fails with name-related errors

**Solutions:**
```bash
# 1. Check if you're logged in to LinkedIn
# The scraper requires an active LinkedIn session

# 2. Update Chrome and ChromeDriver
pip install --upgrade undetected-chromedriver

# 3. Use proven selectors (already implemented)
# The scraper uses fallback selectors that work 95%+ of the time

# 4. Check browser logs
python -c "
from stealth_browser import create_enhanced_browser
driver = create_enhanced_browser(headless=False)
# Open LinkedIn manually and check what you see
"
```

### 2. Authentication Issues

**Symptoms:**
- "Please sign in" messages
- Redirected to login page
- Sessions expire quickly

**Solutions:**
```bash
# 1. Set up proper LinkedIn credentials
cp .env.example .env
# Edit .env with your LinkedIn email/password

# 2. Use session management
# The browser maintains sessions automatically

# 3. Manual login fallback
python main.py --manual-login
# Follow browser prompts to login manually
```

### 3. Database Connection Errors

**Symptoms:**
- `psycopg2.OperationalError`
- "Connection refused" errors
- Database timeout issues

**Solutions:**
```bash
# 1. Check PostgreSQL is running
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# 2. Verify database exists
psql -c "CREATE DATABASE linkedin_scraper;"

# 3. Check connection settings in .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=linkedin_scraper
DB_USER=your_username
DB_PASSWORD=your_password

# 4. Test connection
python -c "
from database_storage import LinkedInDatabaseStorage
storage = LinkedInDatabaseStorage()
print('✅ Database connected successfully')
"
```

### 4. ChromeDriver Issues

**Symptoms:**
- "ChromeDriver not found"
- Browser crashes
- Compatibility errors

**Solutions:**
```bash
# 1. Update ChromeDriver
pip install --upgrade undetected-chromedriver

# 2. Manual ChromeDriver setup
# Download from: https://chromedriver.chromium.org
# Place in PATH or project directory

# 3. Check Chrome version compatibility
google-chrome --version
# Download matching ChromeDriver version

# 4. Use alternative browser
# Set BROWSER_TYPE=firefox in .env (if implemented)
```

### 5. Rate Limiting & IP Blocking

**Symptoms:**
- "Rate limit exceeded" errors
- Profiles load slowly or fail
- Temporary access restrictions

**Solutions:**
```bash
# 1. Increase delays between requests
export EXTRACTION_DELAY=5  # 5 seconds between profiles

# 2. Use VPN or proxy
# Set PROXY_URL in .env if needed

# 3. Reduce concurrent operations
# Extract profiles one at a time

# 4. Respect LinkedIn's terms
# Keep daily extractions under 100 profiles
```

### 6. Contact Information Not Found

**Symptoms:**
- Profiles extracted but no emails/phones
- Contact info fields empty
- Sales Navigator data missing

**Solutions:**
```bash
# 1. Ensure Sales Navigator access
# Contact extraction requires Sales Navigator subscription

# 2. Check profile privacy settings
# Users can hide contact information

# 3. Use contact extraction demo
python contact_extraction_demo.py

# 4. Verify extraction patterns
# Some profiles may not have public contact info
```

### 7. Memory & Performance Issues

**Symptoms:**
- High memory usage
- Slow extraction times
- Browser freezes

**Solutions:**
```bash
# 1. Enable headless mode
export HEADLESS_BROWSER=true

# 2. Limit concurrent extractions
# Process profiles in batches of 10-20

# 3. Restart browser periodically
# Browser restarts every 50 extractions automatically

# 4. Monitor resource usage
htop  # Linux/macOS
# Kill if memory usage > 2GB
```

## 🔍 Debugging Steps

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your extraction with debug output
python main.py --debug --url "https://linkedin.com/in/example"
```

### Manual Testing

```python
from working_linkedin_extractor import WorkingLinkedInExtractor
from stealth_browser import create_enhanced_browser

# Create browser with visible window
driver = create_enhanced_browser(headless=False)

# Test extraction step by step
extractor = WorkingLinkedInExtractor(driver)
driver.get("https://linkedin.com/in/williamhgates")

# Check what elements are found
print("Page title:", driver.title)
print("URL:", driver.current_url)

# Test selectors manually
full_name_element = driver.find_element("css selector", "h1")
print("Found name element:", full_name_element.text)
```

### Database Debugging

```python
from database_storage import LinkedInDatabaseStorage

storage = LinkedInDatabaseStorage()

# Check connection
try:
    stats = storage.get_extraction_stats()
    print("✅ Database connected")
    print("Stats:", stats)
except Exception as e:
    print("❌ Database error:", e)

# Check recent extractions
recent = storage.search_profiles(limit=5)
for profile in recent:
    print(f"Profile: {profile['full_name']} - {profile['extraction_timestamp']}")
```

## 📊 Performance Monitoring

### Check Extraction Success Rate

```python
from database_storage import LinkedInDatabaseStorage

storage = LinkedInDatabaseStorage()
stats = storage.get_extraction_stats()

success_rate = stats['successful_profiles'] / stats['total_profiles'] * 100
print(f"Success rate: {success_rate:.1f}%")

if success_rate < 80:
    print("⚠️ Low success rate - check selectors and login status")
```

### Monitor Contact Extraction

```python
# Check contact extraction quality
contact_stats = storage.get_contact_stats()
print(f"Profiles with emails: {contact_stats['emails_found']}")
print(f"Profiles with phones: {contact_stats['phones_found']}")
print(f"Average contacts per profile: {contact_stats['avg_contacts']:.1f}")
```

## 🆘 Getting Help

### Log Files to Check

1. **Application logs**: `logs/extraction.log`
2. **Browser logs**: Check browser console output
3. **Database logs**: PostgreSQL logs
4. **System logs**: Check system resource usage

### Information to Provide

When reporting issues, include:

1. **Error message** (full traceback)
2. **Python version**: `python --version`
3. **Package versions**: `pip list | grep -E "(selenium|undetected|psycopg2)"`
4. **Operating system** and version
5. **LinkedIn account type** (free/premium/Sales Navigator)
6. **Sample LinkedIn URL** that's failing
7. **Browser version**: `google-chrome --version`

### Contact & Support

- **GitHub Issues**: Report bugs at the repository
- **Documentation**: Check README.md and docs/
- **Examples**: Run `example_usage.py` for working examples

## 🔧 Advanced Troubleshooting

### Selenium WebDriver Issues

```python
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Custom browser setup for debugging
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Add to stealth_browser.py if needed
```

### Network & Proxy Issues

```bash
# Test network connectivity
curl -I https://linkedin.com

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Test with different user agents
curl -H "User-Agent: Mozilla/5.0..." https://linkedin.com
```

### File Permissions

```bash
# Check log directory permissions
ls -la logs/
chmod 755 logs/
chmod 644 logs/*.log

# Check export directory
ls -la exports/
chmod 755 exports/
```

## ✅ Validation Checklist

Before deploying to production:

- [ ] Database connection works
- [ ] LinkedIn login successful
- [ ] Profile extraction > 90% success rate
- [ ] Contact extraction working (with Sales Navigator)
- [ ] Export functions working
- [ ] Log files being created
- [ ] Rate limiting respected (2-3 second delays)
- [ ] Error handling graceful
- [ ] Browser cleanup working
- [ ] Memory usage reasonable (< 2GB)

---

*Keep this guide updated as new issues are discovered and resolved.*