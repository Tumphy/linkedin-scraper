#!/usr/bin/env python3
"""
Stealth Browser Engine - Enhanced LinkedIn Scraping with Anti-Detection

This module provides enhanced browser capabilities with anti-detection features
while maintaining full backward compatibility with the original Selenium setup.

Key Features:
- Undetected Chrome browser with stealth mode
- Fake user agent rotation  
- Proxy support (future enhancement)
- Fallback to original Selenium if enhanced libraries unavailable
- Zero breaking changes to existing code
"""

import os
import logging
import time
import random
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Enhanced imports (with fallback handling)
try:
    import undetected_chromedriver as uc
    STEALTH_AVAILABLE = True
    print("✅ Stealth browser capabilities available")
except ImportError:
    STEALTH_AVAILABLE = False
    print("⚠️  Stealth browser not available, using standard Selenium")

try:
    from fake_useragent import UserAgent
    FAKE_UA_AVAILABLE = True
except ImportError:
    FAKE_UA_AVAILABLE = False

# Configuration
logger = logging.getLogger(__name__)

class BrowserConfig:
    """Configuration class for browser settings"""
    
    def __init__(self):
        # Original settings (preserved from existing system)
        self.headless = os.getenv("HEADLESS_BROWSER", "false").lower() == "true"
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", "30"))
        
        # Enhanced settings (optional)
        self.stealth_mode = os.getenv("STEALTH_MODE", "true").lower() == "true"
        self.rotate_user_agent = os.getenv("ROTATE_USER_AGENT", "true").lower() == "true"
        self.window_size = os.getenv("WINDOW_SIZE", "1920,1080")
        
        # Anti-detection settings
        self.disable_blink_features = True
        self.disable_extensions = True
        self.disable_plugins = True
        self.disable_images = os.getenv("DISABLE_IMAGES", "false").lower() == "true"


def get_random_user_agent() -> str:
    """Get a random user agent string"""
    if FAKE_UA_AVAILABLE:
        try:
            ua = UserAgent()
            return ua.random
        except Exception as e:
            logger.warning(f"Failed to get random user agent: {e}")
    
    # Fallback user agents
    fallback_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return random.choice(fallback_agents)


def get_stealth_chrome_options(config: BrowserConfig) -> ChromeOptions:
    """Get Chrome options optimized for stealth mode"""
    options = ChromeOptions()
    
    # Basic settings
    if config.headless:
        options.add_argument("--headless=new")
    
    # Window size
    width, height = config.window_size.split(',')
    options.add_argument(f"--window-size={width},{height}")
    
    # Anti-detection arguments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Experimental options for stealth
    try:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    except Exception as e:
        logger.warning(f"Could not set experimental options: {e}")
    
    # Additional stealth options
    if config.disable_images:
        try:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        except Exception as e:
            logger.warning(f"Could not disable images: {e}")
    
    # User agent rotation
    if config.rotate_user_agent:
        user_agent = get_random_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        logger.info(f"Using user agent: {user_agent[:50]}...")
    
    return options


def get_original_selenium_driver(config: BrowserConfig) -> webdriver.Chrome:
    """Get original Selenium Chrome driver (backward compatibility)"""
    options = ChromeOptions()
    
    if config.headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Window size
    width, height = config.window_size.split(',')
    options.add_argument(f"--window-size={width},{height}")
    
    # Use webdriver manager for automatic driver management
    try:
        driver_path = ChromeDriverManager().install()
        service = ChromeService(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
    except Exception as e:
        logger.warning(f"WebDriver Manager failed: {e}")
        # Fallback: try to find system chromedriver
        try:
            import subprocess
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            if result.returncode == 0:
                driver_path = result.stdout.strip()
                logger.info(f"Using system chromedriver: {driver_path}")
                service = ChromeService(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                raise Exception("No chromedriver found in system PATH")
        except Exception as e2:
            logger.error(f"All chromedriver methods failed: {e2}")
            raise Exception(f"Could not create Chrome driver: {e}, {e2}")
    
    # Set timeouts
    driver.implicitly_wait(config.timeout)
    driver.set_page_load_timeout(config.timeout)
    
    return driver


def get_undetected_chrome_driver(config: BrowserConfig) -> webdriver.Chrome:
    """Get undetected Chrome driver for stealth mode"""
    if not STEALTH_AVAILABLE:
        raise ImportError("undetected-chromedriver not available")
    
    try:
        # Configure undetected Chrome options
        options = uc.ChromeOptions()
        
        # Add stealth arguments
        if config.headless:
            options.add_argument("--headless=new")
        
        # Window size
        width, height = config.window_size.split(',')
        options.add_argument(f"--window-size={width},{height}")
        
        # Additional stealth options
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--password-store=basic")
        
        # User agent
        if config.rotate_user_agent:
            user_agent = get_random_user_agent()
            options.add_argument(f"--user-agent={user_agent}")
        
        # Create undetected Chrome driver
        driver = uc.Chrome(options=options, version_main=None)
        
        # Set timeouts
        driver.implicitly_wait(config.timeout)
        driver.set_page_load_timeout(config.timeout)
        
        # Additional stealth enhancements
        enhance_browser_stealth(driver)
        
        logger.info("✅ Created undetected Chrome driver")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to create undetected Chrome driver: {e}")
        raise


def create_enhanced_browser(use_stealth: bool = None, config: BrowserConfig = None) -> webdriver.Chrome:
    """
    Create enhanced browser with stealth capabilities
    
    Args:
        use_stealth: Force stealth mode on/off. If None, auto-detect based on availability
        config: Browser configuration. If None, use default config
    
    Returns:
        webdriver.Chrome: Enhanced Chrome driver instance
    """
    if config is None:
        config = BrowserConfig()
    
    # Determine whether to use stealth mode
    if use_stealth is None:
        use_stealth = STEALTH_AVAILABLE and config.stealth_mode
    elif use_stealth and not STEALTH_AVAILABLE:
        logger.warning("Stealth mode requested but not available, falling back to standard Selenium")
        use_stealth = False
    
    try:
        if use_stealth:
            logger.info("🥷 Creating stealth browser...")
            driver = get_undetected_chrome_driver(config)
        else:
            logger.info("🌐 Creating standard browser...")
            driver = get_original_selenium_driver(config)
        
        # Add random startup delay to appear more human
        add_random_delay(1, 3)
        
        logger.info(f"✅ Browser created successfully (stealth: {use_stealth})")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to create enhanced browser: {e}")
        
        # Final fallback: try basic Chrome driver
        if use_stealth:
            logger.info("🔄 Falling back to standard browser...")
            return create_enhanced_browser(use_stealth=False, config=config)
        else:
            raise


def enhance_browser_stealth(driver: webdriver.Chrome) -> None:
    """Apply additional stealth enhancements to existing driver"""
    try:
        # Execute stealth scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override chrome object
        driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        # Override languages
        driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        logger.debug("✅ Applied additional stealth enhancements")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not apply some stealth enhancements: {e}")


def add_random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Add random delay to simulate human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def simulate_human_behavior(driver: webdriver.Chrome) -> None:
    """Simulate human-like behavior"""
    try:
        # Random mouse movements (simplified)
        driver.execute_script("""
            var event = new MouseEvent('mousemove', {
                'view': window,
                'bubbles': true,
                'cancelable': true,
                'clientX': Math.random() * window.innerWidth,
                'clientY': Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)
        
        # Random scroll
        scroll_amount = random.randint(100, 500)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
        # Random delay
        add_random_delay(0.5, 2.0)
        
    except Exception as e:
        logger.debug(f"Could not simulate human behavior: {e}")


# Backward compatibility functions
def create_driver(headless: bool = False) -> webdriver.Chrome:
    """Backward compatibility function"""
    config = BrowserConfig()
    config.headless = headless
    return create_enhanced_browser(config=config)


class StealthBrowser:
    """Context manager for stealth browser"""
    
    def __init__(self, use_stealth: bool = None, config: BrowserConfig = None):
        self.use_stealth = use_stealth
        self.config = config
        self.driver = None
    
    def __enter__(self) -> webdriver.Chrome:
        self.driver = create_enhanced_browser(self.use_stealth, self.config)
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")


# Usage examples and testing
if __name__ == "__main__":
    # Test stealth browser creation
    logging.basicConfig(level=logging.INFO)
    
    print("Testing stealth browser creation...")
    
    try:
        with StealthBrowser(use_stealth=True) as driver:
            driver.get("https://www.linkedin.com")
            print(f"✅ Successfully navigated to LinkedIn")
            print(f"📊 User agent: {driver.execute_script('return navigator.userAgent')}")
            time.sleep(2)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("Test completed.")