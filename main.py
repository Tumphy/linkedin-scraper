#!/usr/bin/env python3
"""
LinkedIn Scraper - Production Entry Point

Main script for running LinkedIn profile and contact extraction.
Supports both individual profiles and bulk processing with Sales Navigator.

Usage:
    python main.py --url "https://linkedin.com/in/username"
    python main.py --bulk urls.txt
    python main.py --sales-navigator "search_url"
    
Examples:
    # Single profile
    python main.py --url "https://linkedin.com/in/williamhgates"
    
    # Bulk processing from file
    python main.py --bulk profile_urls.txt
    
    # Sales Navigator search
    python main.py --sales-navigator "https://linkedin.com/sales/search/people"
    
    # Export results
    python main.py --export-csv results.csv
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from working_linkedin_extractor import WorkingLinkedInExtractor, LinkedInProfile
from database_storage import LinkedInDatabaseStorage, export_profiles_to_csv
from stealth_browser import create_enhanced_browser, BrowserConfig
from contact_extraction_demo import ContactExtractionDemo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'linkedin_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInScraperMain:
    """Main LinkedIn scraper application"""
    
    def __init__(self, headless: bool = True, use_stealth: bool = True):
        self.headless = headless
        self.use_stealth = use_stealth
        self.driver = None
        self.extractor = None
        self.storage = None
        
    def initialize(self) -> bool:
        """Initialize the scraper components"""
        try:
            logger.info("🚀 Initializing LinkedIn Scraper")
            
            # Create browser
            config = BrowserConfig()
            config.headless = self.headless
            
            self.driver = create_enhanced_browser(use_stealth=self.use_stealth, config=config)
            self.extractor = WorkingLinkedInExtractor(self.driver)
            self.storage = LinkedInDatabaseStorage()
            
            logger.info("✅ LinkedIn Scraper initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize scraper: {e}")
            return False
    
    def login_to_linkedin(self) -> bool:
        """Login to LinkedIn using credentials from environment"""
        try:
            username = os.getenv('LINKEDIN_USERNAME')
            password = os.getenv('LINKEDIN_PASSWORD')
            
            if not username or not password:
                logger.error("❌ LinkedIn credentials not found in environment")
                logger.info("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in .env file")
                return False
            
            logger.info("🔐 Logging into LinkedIn...")
            
            # Navigate to LinkedIn login
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for page load
            import time
            time.sleep(3)
            
            # Find and fill login form
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, 10)
            
            # Enter username
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click sign in
            signin_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            signin_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url:
                logger.info("✅ Successfully logged into LinkedIn")
                return True
            elif "challenge" in current_url:
                logger.warning("⚠️ LinkedIn requires additional verification (2FA/CAPTCHA)")
                logger.info("Please complete verification manually and then continue")
                input("Press Enter after completing verification...")
                return True
            else:
                logger.error("❌ LinkedIn login failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during LinkedIn login: {e}")
            return False
    
    def extract_single_profile(self, profile_url: str) -> Optional[LinkedInProfile]:
        """Extract a single LinkedIn profile"""
        try:
            logger.info(f"🎯 Extracting profile: {profile_url}")
            
            profile = self.extractor.extract_profile(profile_url)
            
            if isinstance(profile, LinkedInProfile) and profile.extraction_success:
                # Save to database
                profile_id = self.storage.save_profile(profile)
                
                logger.info(f"✅ Successfully extracted: {profile.full_name}")
                logger.info(f"   📧 Emails: {len(profile.emails)}")
                logger.info(f"   📱 Phones: {len(profile.phones)}")
                logger.info(f"   🌐 Websites: {len(profile.websites)}")
                logger.info(f"   💾 Saved to database with ID: {profile_id}")
                
                return profile
            else:
                logger.error(f"❌ Failed to extract profile: {profile_url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting profile {profile_url}: {e}")
            return None
    
    def extract_bulk_profiles(self, profile_urls: List[str]) -> List[LinkedInProfile]:
        """Extract multiple LinkedIn profiles"""
        logger.info(f"🔄 Starting bulk extraction of {len(profile_urls)} profiles")
        
        results = []
        
        for i, url in enumerate(profile_urls, 1):
            logger.info(f"\n[{i}/{len(profile_urls)}] Processing: {url}")
            
            profile = self.extract_single_profile(url)
            if profile:
                results.append(profile)
            
            # Add delay between requests to be respectful
            if i < len(profile_urls):
                import time
                delay = 3
                logger.info(f"⏳ Waiting {delay} seconds before next extraction...")
                time.sleep(delay)
        
        logger.info(f"\n✅ Bulk extraction completed")
        logger.info(f"   Successfully extracted: {len(results)}/{len(profile_urls)} profiles")
        logger.info(f"   Success rate: {len(results)/len(profile_urls)*100:.1f}%")
        
        return results
    
    def extract_sales_navigator_search(self, search_url: str) -> List[LinkedInProfile]:
        """Extract profiles from Sales Navigator search results"""
        try:
            logger.info(f"🔍 Extracting Sales Navigator search: {search_url}")
            
            profiles = self.extractor.extract_profile(search_url)
            
            if isinstance(profiles, list):
                # Save all profiles to database
                saved_count = 0
                for profile in profiles:
                    if profile.extraction_success:
                        self.storage.save_profile(profile)
                        saved_count += 1
                
                logger.info(f"✅ Sales Navigator extraction completed")
                logger.info(f"   Profiles found: {len(profiles)}")
                logger.info(f"   Successfully saved: {saved_count}")
                
                return profiles
            else:
                logger.error("❌ Failed to extract Sales Navigator search results")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error extracting Sales Navigator search: {e}")
            return []
    
    def export_results(self, filename: str, **filters) -> str:
        """Export extraction results to CSV"""
        try:
            logger.info(f"📊 Exporting results to: {filename}")
            
            exported_file = export_profiles_to_csv(filename, **filters)
            
            if exported_file:
                logger.info(f"✅ Results exported to: {exported_file}")
                return exported_file
            else:
                logger.error("❌ Export failed")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Error exporting results: {e}")
            return ""
    
    def get_statistics(self) -> Dict:
        """Get extraction statistics"""
        try:
            stats = self.storage.get_extraction_stats()
            
            logger.info("📊 Current Statistics:")
            logger.info(f"   Total profiles: {stats.get('total_profiles', 0)}")
            logger.info(f"   Successful extractions: {stats.get('successful_profiles', 0)}")
            logger.info(f"   Profiles with contacts: {stats.get('profiles_with_contacts', 0)}")
            logger.info(f"   Recent extractions (24h): {stats.get('recent_extractions', 0)}")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("✅ Browser cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

def load_urls_from_file(filename: str) -> List[str]:
    """Load URLs from a text file"""
    try:
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        logger.info(f"📂 Loaded {len(urls)} URLs from {filename}")
        return urls
    except Exception as e:
        logger.error(f"❌ Error loading URLs from {filename}: {e}")
        return []

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='LinkedIn Profile & Contact Scraper')
    
    # Input options
    parser.add_argument('--url', help='Single LinkedIn profile URL to extract')
    parser.add_argument('--bulk', help='File containing LinkedIn profile URLs (one per line)')
    parser.add_argument('--sales-navigator', help='Sales Navigator search URL')
    
    # Behavior options
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-stealth', action='store_true', help='Disable stealth mode')
    parser.add_argument('--no-login', action='store_true', help='Skip LinkedIn login')
    
    # Output options
    parser.add_argument('--export-csv', help='Export results to CSV file')
    parser.add_argument('--stats', action='store_true', help='Show extraction statistics')
    
    # Demo options
    parser.add_argument('--demo', action='store_true', help='Run contact extraction demo')
    
    args = parser.parse_args()
    
    if not any([args.url, args.bulk, args.sales_navigator, args.stats, args.demo]):
        parser.print_help()
        return
    
    # Initialize scraper
    scraper = LinkedInScraperMain(
        headless=args.headless,
        use_stealth=not args.no_stealth
    )
    
    try:
        # Initialize components
        if not scraper.initialize():
            logger.error("❌ Failed to initialize scraper")
            return
        
        # Handle demo mode
        if args.demo:
            logger.info("🎉 Running contact extraction demo")
            demo = ContactExtractionDemo()
            if demo.initialize():
                demo_profiles = [
                    "https://www.linkedin.com/in/williamhgates/",
                    "https://www.linkedin.com/in/jeffweiner08/"
                ]
                demo.bulk_contact_extraction_demo(demo_profiles)
                demo.cleanup()
            return
        
        # Handle statistics only
        if args.stats and not any([args.url, args.bulk, args.sales_navigator]):
            scraper.get_statistics()
            return
        
        # Login to LinkedIn if needed
        if not args.no_login:
            if not scraper.login_to_linkedin():
                logger.error("❌ LinkedIn login required for extraction")
                return
        
        # Process extraction requests
        results = []
        
        if args.url:
            profile = scraper.extract_single_profile(args.url)
            if profile:
                results.append(profile)
        
        if args.bulk:
            urls = load_urls_from_file(args.bulk)
            if urls:
                bulk_results = scraper.extract_bulk_profiles(urls)
                results.extend(bulk_results)
        
        if args.sales_navigator:
            sn_results = scraper.extract_sales_navigator_search(args.sales_navigator)
            results.extend(sn_results)
        
        # Export results if requested
        if args.export_csv and results:
            scraper.export_results(args.export_csv)
        
        # Show statistics
        if args.stats:
            scraper.get_statistics()
        
        logger.info(f"\n🎉 LinkedIn scraping session completed!")
        logger.info(f"Total profiles processed: {len(results)}")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()