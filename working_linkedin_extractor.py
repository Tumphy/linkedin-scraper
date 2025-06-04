#!/usr/bin/env python3
"""
Working LinkedIn Profile & Sales Navigator Extractor
Combines proven selectors from the original repo with enhanced architecture

This extractor works with:
1. Regular LinkedIn profiles (linkedin.com/in/username)
2. LinkedIn Sales Navigator profiles (linkedin.com/sales/lead/xxxxx)
3. LinkedIn Sales Navigator search results

Uses battle-tested selectors from the original kingtroga/linkedin_scraper repo
"""

import re
import time
import logging
from typing import Dict, List, Optional, Any, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class LinkedInProfile:
    """Working LinkedIn profile data structure"""
    # Core fields (always extracted)
    full_name: str = ""
    linkedin_url: str = ""
    
    # Sales Navigator specific fields
    role: str = ""
    company: str = ""
    company_linkedin_url: str = ""
    geography: str = ""
    date_added: str = ""
    
    # Enhanced profile fields (when available)
    headline: str = ""
    about: str = ""
    location: str = ""
    connections_count: Optional[int] = None
    
    # Contact information
    emails: List[str] = None
    phones: List[str] = None
    websites: List[str] = None
    social_links: List[str] = None
    addresses: List[str] = None
    
    # Meta information
    profile_type: str = "unknown"  # 'public', 'authenticated', 'sales_navigator'
    extraction_timestamp: str = ""
    extraction_success: bool = False
    
    def __post_init__(self):
        """Initialize lists and timestamp"""
        if self.emails is None:
            self.emails = []
        if self.phones is None:
            self.phones = []
        if self.websites is None:
            self.websites = []
        if self.social_links is None:
            self.social_links = []
        if self.addresses is None:
            self.addresses = []
        if not self.extraction_timestamp:
            self.extraction_timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)

class WorkingLinkedInExtractor:
    """Working LinkedIn extractor using proven selectors"""
    
    def __init__(self, driver: webdriver.Chrome, wait_timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_timeout)
        
    def detect_page_type(self) -> str:
        """Detect the type of LinkedIn page we're on"""
        current_url = self.driver.current_url
        
        if "/sales/lead/" in current_url:
            return "sales_navigator_profile"
        elif "/sales/search/" in current_url or "/sales/lists/" in current_url:
            return "sales_navigator_search"
        elif "/in/" in current_url:
            # Check if we're logged in (authenticated profile vs public)
            try:
                self.driver.find_element(By.CSS_SELECTOR, ".pv-text-details__right-panel")
                return "authenticated_profile"
            except NoSuchElementException:
                return "public_profile"
        elif "/company/" in current_url:
            return "company_page"
        else:
            return "unknown"
    
    def extract_sales_navigator_profile(self) -> LinkedInProfile:
        """Extract from Sales Navigator profile page using proven selectors"""
        profile = LinkedInProfile()
        profile.profile_type = "sales_navigator"
        profile.linkedin_url = self.driver.current_url
        
        try:
            logger.info("🎯 Extracting Sales Navigator profile...")
            
            # Wait for page to load
            time.sleep(3)
            
            # Extract basic profile info using original selectors
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Name - try multiple selectors from original repo
            name_selectors = [
                ".profile-topcard-person-entity__name",
                ".artdeco-entity-lockup__title",
                ".profile-topcard__name",
                "h1"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = soup.select_one(selector)
                    if name_elem and name_elem.get_text(strip=True):
                        profile.full_name = name_elem.get_text(strip=True)
                        break
                except:
                    continue
            
            # Role/Title
            role_selectors = [
                ".profile-topcard-person-entity__title",
                ".artdeco-entity-lockup__subtitle",
                ".profile-topcard__occupation"
            ]
            
            for selector in role_selectors:
                try:
                    role_elem = soup.select_one(selector)
                    if role_elem and role_elem.get_text(strip=True):
                        profile.role = role_elem.get_text(strip=True)
                        break
                except:
                    continue
            
            # Company
            company_selectors = [
                ".profile-topcard-person-entity__company",
                ".profile-topcard__summary-company"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = soup.select_one(selector)
                    if company_elem and company_elem.get_text(strip=True):
                        profile.company = company_elem.get_text(strip=True)
                        break
                except:
                    continue
            
            # Location/Geography
            location_selectors = [
                ".profile-topcard-person-entity__location",
                ".profile-topcard__summary-location"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = soup.select_one(selector)
                    if location_elem and location_elem.get_text(strip=True):
                        profile.geography = location_elem.get_text(strip=True)
                        break
                except:
                    continue
            
            # Extract contact information (based on original contact_info.py)
            self._extract_sales_navigator_contact_info(profile)
            
            # Extract About section
            self._extract_about_section(profile)
            
            # Get actual LinkedIn profile URL (not Sales Navigator URL)
            self._extract_linkedin_profile_url(profile)
            
            profile.extraction_success = bool(profile.full_name)
            
            logger.info(f"✅ Extracted Sales Navigator profile: {profile.full_name}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting Sales Navigator profile: {e}")
            profile.extraction_success = False
        
        return profile
    
    def extract_regular_profile(self) -> LinkedInProfile:
        """Extract from regular LinkedIn profile using enhanced selectors"""
        profile = LinkedInProfile()
        profile.linkedin_url = self.driver.current_url
        
        try:
            logger.info("👤 Extracting regular LinkedIn profile...")
            
            # Determine if authenticated or public
            profile.profile_type = self.detect_page_type()
            
            # Wait for page to load
            time.sleep(3)
            
            # Name - multiple selectors for reliability
            name_selectors = [
                "h1.text-heading-xlarge",
                ".pv-text-details__left-panel h1",
                ".ph5.pb5 h1",
                "h1",
                ".pv-top-card--list h1"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if name_elem.text.strip():
                        profile.full_name = name_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Enhanced title/role extraction with better logic
            role_found = False
            role_selectors = [
                ".text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium", 
                ".ph5.pb5 .text-body-medium",
                ".pv-top-card--list .text-body-medium",
                "div[data-generated-suggestion-target]",
                ".pv-entity__summary-info"
            ]
            
            for selector in role_selectors:
                if role_found:
                    break
                try:
                    role_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in role_elems:
                        text = elem.text.strip()
                        if text and not any(skip in text.lower() for skip in ['contact info', 'message', 'connect', 'follow']):
                            if len(text) > 10 and len(text) < 200:  # Reasonable role length
                                profile.role = text
                                role_found = True
                                break
                except NoSuchElementException:
                    continue
            
            # Company extraction
            company_selectors = [
                ".pv-text-details__left-panel .text-body-medium:contains('at')",
                ".experience-item__title",
                ".pv-entity__summary-info-v2"
            ]
            
            for selector in company_selectors:
                try:
                    if "contains" in selector:
                        # Use BeautifulSoup for text content search
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        elems = soup.select(".pv-text-details__left-panel .text-body-medium")
                        for elem in elems:
                            text = elem.get_text(strip=True)
                            if " at " in text:
                                company_part = text.split(" at ")[-1]
                                if company_part and len(company_part) < 100:
                                    profile.company = company_part
                                    break
                    else:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if elem.text.strip():
                            profile.company = elem.text.strip()
                            break
                except:
                    continue
            
            # Location
            location_selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small",
                "[data-anonymize='location']"
            ]
            
            for selector in location_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    if text and len(text) < 100:  # Reasonable location length
                        profile.location = text
                        break
                except NoSuchElementException:
                    continue
            
            # About section
            self._extract_about_section(profile)
            
            # Extract contact information for authenticated profiles
            if profile.profile_type == "authenticated_profile":
                self._extract_contact_info(profile)
            
            profile.extraction_success = bool(profile.full_name)
            
            logger.info(f"✅ Extracted regular profile: {profile.full_name}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting regular profile: {e}")
            profile.extraction_success = False
        
        return profile
    
    def _extract_sales_navigator_contact_info(self, profile: LinkedInProfile):
        """Extract contact information from Sales Navigator profile"""
        try:
            logger.info("📞 Extracting Sales Navigator contact information...")
            
            # Wait for any contact modal or info to load
            time.sleep(2)
            
            # Try to click contact info button if available
            contact_selectors = [
                "button[data-control-name='contact_see_more']",
                ".contact-see-more-card",
                "[data-anonymize='phone']",
                "[data-anonymize='email']"
            ]
            
            page_source = self.driver.page_source
            
            # Extract emails using regex patterns
            email_patterns = [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
            ]
            
            for pattern in email_patterns:
                emails = re.findall(pattern, page_source, re.IGNORECASE)
                for email in emails:
                    if email not in profile.emails and '@' in email:
                        profile.emails.append(email.lower())
            
            # Extract phone numbers using regex
            phone_patterns = [
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
                r'\+[1-9]\d{1,14}',  # International format
                r'\([0-9]{3}\)\s?[0-9]{3}-[0-9]{4}'  # US format with parentheses
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, page_source)
                for phone in phones:
                    cleaned_phone = re.sub(r'[^\d+]', '', phone)
                    if len(cleaned_phone) >= 10 and cleaned_phone not in profile.phones:
                        profile.phones.append(phone)
            
            # Extract websites
            url_patterns = [
                r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
                r'www\.[\w.-]+\.[a-z]{2,}'
            ]
            
            for pattern in url_patterns:
                websites = re.findall(pattern, page_source, re.IGNORECASE)
                for website in websites:
                    if website not in profile.websites and 'linkedin.com' not in website:
                        profile.websites.append(website)
            
            # Try to extract from contact modals (if accessible)
            try:
                contact_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='contact'], .contact-info")
                for button in contact_buttons[:2]:  # Limit to first 2 to avoid spam
                    try:
                        button.click()
                        time.sleep(1)
                        
                        # Look for contact info in modal
                        modal_content = self.driver.page_source
                        
                        # Extract from modal
                        modal_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', modal_content)
                        for email in modal_emails:
                            if email not in profile.emails:
                                profile.emails.append(email.lower())
                        
                        # Close modal
                        try:
                            close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close'], .artdeco-modal__dismiss")
                            close_button.click()
                            time.sleep(0.5)
                        except:
                            pass
                            
                    except Exception as e:
                        logger.debug(f"Could not click contact button: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"No contact buttons found: {e}")
            
            logger.info(f"📞 Found {len(profile.emails)} emails, {len(profile.phones)} phones, {len(profile.websites)} websites")
            
        except Exception as e:
            logger.error(f"❌ Error extracting contact info: {e}")
    
    def _extract_contact_info(self, profile: LinkedInProfile):
        """Extract contact information from regular LinkedIn profile"""
        try:
            logger.info("📞 Extracting contact information...")
            
            # Try to find contact info section
            contact_sections = [
                ".pv-contact-info",
                ".contact-info",
                "[data-section='contactInfo']"
            ]
            
            # Look for contact info button and click it
            try:
                contact_button = self.driver.find_element(By.CSS_SELECTOR, "a[data-control-name='contact_see_more']")
                contact_button.click()
                time.sleep(2)
                
                # Extract from contact modal
                page_source = self.driver.page_source
                
                # Extract emails
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_source)
                profile.emails.extend([email.lower() for email in emails if email not in profile.emails])
                
                # Extract phones
                phones = re.findall(r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', page_source)
                profile.phones.extend([phone for phone in phones if phone not in profile.phones])
                
                # Extract websites
                websites = re.findall(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?', page_source)
                profile.websites.extend([site for site in websites if site not in profile.websites and 'linkedin.com' not in site])
                
                # Close modal
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Dismiss'], .artdeco-modal__dismiss")
                    close_button.click()
                    time.sleep(1)
                except:
                    pass
                    
            except NoSuchElementException:
                logger.debug("No contact info button found")
                
        except Exception as e:
            logger.error(f"❌ Error extracting contact info: {e}")
    
    def _extract_about_section(self, profile: LinkedInProfile):
        """Extract About/Summary section"""
        try:
            about_selectors = [
                ".pv-about__text",
                ".summary",
                "[data-section='summary']",
                ".pv-about-section .pv-about__text"
            ]
            
            for selector in about_selectors:
                try:
                    about_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    about_text = about_elem.text.strip()
                    if about_text and len(about_text) > 20:  # Meaningful about section
                        profile.about = about_text
                        break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            logger.debug(f"Could not extract about section: {e}")
    
    def _extract_linkedin_profile_url(self, profile: LinkedInProfile):
        """Extract the actual LinkedIn profile URL from Sales Navigator"""
        try:
            # Look for LinkedIn profile link in Sales Navigator
            profile_link_selectors = [
                "a[href*='/in/']",
                ".profile-topcard-person-entity__name a",
                "a[data-control-name='view_linkedin']"
            ]
            
            for selector in profile_link_selectors:
                try:
                    link_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    href = link_elem.get_attribute('href')
                    if href and '/in/' in href:
                        profile.linkedin_url = href
                        break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            logger.debug(f"Could not extract LinkedIn profile URL: {e}")
    
    def extract_sales_navigator_search_results(self) -> List[LinkedInProfile]:
        """Extract multiple profiles from Sales Navigator search results"""
        profiles = []
        
        try:
            logger.info("🔍 Extracting Sales Navigator search results...")
            
            # Wait for search results to load
            time.sleep(5)
            
            # Find all profile cards in search results
            profile_cards = self.driver.find_elements(By.CSS_SELECTOR, ".search-results__result-item")
            
            if not profile_cards:
                # Try alternative selector
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-anonymize='person']")
            
            logger.info(f"Found {len(profile_cards)} profile cards")
            
            for i, card in enumerate(profile_cards[:10]):  # Limit to first 10 for testing
                try:
                    profile = LinkedInProfile()
                    profile.profile_type = "sales_navigator_search"
                    
                    # Extract name
                    name_selectors = [".search-results__result-item__name", ".name", "h3", "h4"]
                    for selector in name_selectors:
                        try:
                            name_elem = card.find_element(By.CSS_SELECTOR, selector)
                            if name_elem.text.strip():
                                profile.full_name = name_elem.text.strip()
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Extract role
                    role_selectors = [".search-results__result-item__title", ".title", ".subtitle"]
                    for selector in role_selectors:
                        try:
                            role_elem = card.find_element(By.CSS_SELECTOR, selector)
                            if role_elem.text.strip():
                                profile.role = role_elem.text.strip()
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Extract company
                    company_selectors = [".search-results__result-item__company", ".company", ".organization"]
                    for selector in company_selectors:
                        try:
                            company_elem = card.find_element(By.CSS_SELECTOR, selector)
                            if company_elem.text.strip():
                                profile.company = company_elem.text.strip()
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Extract location
                    location_selectors = [".search-results__result-item__location", ".location", ".geography"]
                    for selector in location_selectors:
                        try:
                            location_elem = card.find_element(By.CSS_SELECTOR, selector)
                            if location_elem.text.strip():
                                profile.geography = location_elem.text.strip()
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Try to get profile URL
                    try:
                        profile_link = card.find_element(By.CSS_SELECTOR, "a")
                        href = profile_link.get_attribute('href')
                        if href:
                            profile.linkedin_url = href
                    except NoSuchElementException:
                        pass
                    
                    profile.extraction_success = bool(profile.full_name)
                    
                    if profile.extraction_success:
                        profiles.append(profile)
                        logger.info(f"✅ Extracted: {profile.full_name} - {profile.company}")
                    
                except Exception as e:
                    logger.error(f"❌ Error extracting profile {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Successfully extracted {len(profiles)} profiles from search results")
            
        except Exception as e:
            logger.error(f"❌ Error extracting search results: {e}")
        
        return profiles
    
    def extract_profile(self, url: str = None) -> Union[LinkedInProfile, List[LinkedInProfile]]:
        """Main extraction method - detects page type and extracts accordingly"""
        if url:
            self.driver.get(url)
            time.sleep(3)
        
        page_type = self.detect_page_type()
        
        if page_type == "sales_navigator_profile":
            return self.extract_sales_navigator_profile()
        elif page_type == "sales_navigator_search":
            return self.extract_sales_navigator_search_results()
        elif page_type in ["authenticated_profile", "public_profile"]:
            return self.extract_regular_profile()
        else:
            logger.error(f"Unsupported page type: {page_type}")
            return LinkedInProfile()

# Backwards compatibility function
def extract_linkedin_profile(driver: webdriver.Chrome, url: str = None) -> Union[LinkedInProfile, List[LinkedInProfile]]:
    """Backwards compatibility wrapper"""
    extractor = WorkingLinkedInExtractor(driver)
    return extractor.extract_profile(url)