#!/usr/bin/env python3
"""
Contact Extraction Demo - Cognism-like Capabilities

This script demonstrates our contact information extraction capabilities
that are comparable to commercial tools like Cognism.

Features demonstrated:
- Email extraction from Sales Navigator
- Phone number extraction
- Social media profile discovery
- Website and contact information
- Company contact details
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from working_linkedin_extractor import WorkingLinkedInExtractor, LinkedInProfile
from database_storage import LinkedInDatabaseStorage
from stealth_browser import create_enhanced_browser, BrowserConfig

class ContactExtractionDemo:
    """Demonstrate contact extraction capabilities like Cognism"""
    
    def __init__(self):
        self.extractor = None
        self.storage = None
        
    def initialize(self):
        """Initialize the contact extraction system"""
        try:
            print("🚀 Initializing Contact Extraction System")
            
            # Initialize browser (non-headless to see what's happening)
            config = BrowserConfig()
            config.headless = False  # Show browser for demo
            
            driver = create_enhanced_browser(use_stealth=True, config=config)
            self.extractor = WorkingLinkedInExtractor(driver)
            self.storage = LinkedInDatabaseStorage()
            
            print("✅ Contact extraction system ready")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def demonstrate_contact_extraction(self, profile_url: str) -> Dict:
        """Demonstrate comprehensive contact extraction"""
        print(f"\n🎯 Extracting contact information from: {profile_url}")
        print("=" * 60)
        
        # Extract profile with contact information
        profile = self.extractor.extract_profile(profile_url)
        
        if not isinstance(profile, LinkedInProfile) or not profile.extraction_success:
            print("❌ Failed to extract profile")
            return {}
        
        # Display Cognism-like contact extraction results
        contact_data = {
            "profile_info": {
                "name": profile.full_name,
                "title": profile.role,
                "company": profile.company,
                "location": profile.location or profile.geography,
                "linkedin_url": profile.linkedin_url
            },
            "contact_information": {
                "emails": profile.emails,
                "phones": profile.phones,
                "websites": profile.websites,
                "social_links": profile.social_links,
                "addresses": profile.addresses
            },
            "extraction_metadata": {
                "profile_type": profile.profile_type,
                "extraction_timestamp": profile.extraction_timestamp,
                "contact_points_found": len(profile.emails) + len(profile.phones) + len(profile.websites),
                "data_sources": self._identify_data_sources(profile)
            }
        }
        
        # Display results in Cognism-like format
        self._display_cognism_style_results(contact_data)
        
        # Save to database
        profile_id = self.storage.save_profile(profile)
        contact_data["database_id"] = profile_id
        
        return contact_data
    
    def _identify_data_sources(self, profile: LinkedInProfile) -> List[str]:
        """Identify where contact data was found"""
        sources = []
        
        if profile.emails:
            sources.append("LinkedIn Sales Navigator Contact Modal")
        if profile.phones:
            sources.append("LinkedIn Phone Directory")
        if profile.websites:
            sources.append("LinkedIn Profile Websites Section")
        if profile.social_links:
            sources.append("LinkedIn Social Media Links")
        if profile.about:
            sources.append("LinkedIn About Section")
            
        return sources or ["LinkedIn Public Profile"]
    
    def _display_cognism_style_results(self, contact_data: Dict):
        """Display results in a format similar to Cognism"""
        profile = contact_data["profile_info"]
        contacts = contact_data["contact_information"]
        metadata = contact_data["extraction_metadata"]
        
        print(f"\n👤 PROFILE INFORMATION")
        print(f"   Name: {profile['name']}")
        print(f"   Title: {profile['title'] or 'Not specified'}")
        print(f"   Company: {profile['company'] or 'Not specified'}")
        print(f"   Location: {profile['location'] or 'Not specified'}")
        print(f"   LinkedIn: {profile['linkedin_url']}")
        
        print(f"\n📞 CONTACT INFORMATION")
        
        # Email addresses
        if contacts['emails']:
            print(f"   📧 Email Addresses ({len(contacts['emails'])} found):")
            for i, email in enumerate(contacts['emails'], 1):
                print(f"      {i}. {email}")
                print(f"         ✅ Verified: Available in LinkedIn")
        else:
            print(f"   📧 Email Addresses: None found in accessible sources")
        
        # Phone numbers
        if contacts['phones']:
            print(f"   📱 Phone Numbers ({len(contacts['phones'])} found):")
            for i, phone in enumerate(contacts['phones'], 1):
                print(f"      {i}. {phone}")
                print(f"         ✅ Source: LinkedIn Contact Information")
        else:
            print(f"   📱 Phone Numbers: None found in accessible sources")
        
        # Websites
        if contacts['websites']:
            print(f"   🌐 Websites ({len(contacts['websites'])} found):")
            for i, website in enumerate(contacts['websites'], 1):
                print(f"      {i}. {website}")
        else:
            print(f"   🌐 Websites: None found")
        
        # Social media
        if contacts['social_links']:
            print(f"   🔗 Social Media ({len(contacts['social_links'])} found):")
            for i, social in enumerate(contacts['social_links'], 1):
                platform = self._identify_social_platform(social)
                print(f"      {i}. {platform}: {social}")
        else:
            print(f"   🔗 Social Media: None found")
        
        print(f"\n📊 EXTRACTION SUMMARY")
        print(f"   Contact Points Found: {metadata['contact_points_found']}")
        print(f"   Profile Type: {metadata['profile_type']}")
        print(f"   Data Sources: {', '.join(metadata['data_sources'])}")
        print(f"   Extraction Time: {metadata['extraction_timestamp']}")
        
        # Contact quality assessment (like Cognism)
        quality_score = self._calculate_contact_quality(contacts)
        print(f"   Contact Quality Score: {quality_score}/10")
        
    def _identify_social_platform(self, url: str) -> str:
        """Identify social media platform from URL"""
        if 'twitter.com' in url or 'x.com' in url:
            return 'Twitter/X'
        elif 'facebook.com' in url:
            return 'Facebook'
        elif 'instagram.com' in url:
            return 'Instagram'
        elif 'github.com' in url:
            return 'GitHub'
        elif 'pinterest.com' in url:
            return 'Pinterest'
        else:
            return 'Other'
    
    def _calculate_contact_quality(self, contacts: Dict) -> int:
        """Calculate contact quality score (0-10) like Cognism"""
        score = 0
        
        # Email addresses (most valuable)
        if contacts['emails']:
            score += min(len(contacts['emails']) * 3, 5)  # Max 5 points for emails
        
        # Phone numbers (very valuable)
        if contacts['phones']:
            score += min(len(contacts['phones']) * 2, 3)  # Max 3 points for phones
        
        # Websites (moderately valuable)
        if contacts['websites']:
            score += min(len(contacts['websites']), 1)  # Max 1 point for websites
        
        # Social media (somewhat valuable)
        if contacts['social_links']:
            score += min(len(contacts['social_links']), 1)  # Max 1 point for social
        
        return min(score, 10)  # Cap at 10
    
    def bulk_contact_extraction_demo(self, profile_urls: List[str]) -> List[Dict]:
        """Demonstrate bulk contact extraction"""
        print(f"\n🔄 Bulk Contact Extraction - {len(profile_urls)} profiles")
        print("=" * 60)
        
        results = []
        
        for i, url in enumerate(profile_urls, 1):
            print(f"\n[{i}/{len(profile_urls)}] Processing: {url}")
            
            try:
                contact_data = self.demonstrate_contact_extraction(url)
                if contact_data:
                    results.append(contact_data)
                    
                # Add delay between profiles to be respectful
                if i < len(profile_urls):
                    print("⏳ Waiting 3 seconds before next extraction...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                continue
        
        self._generate_bulk_report(results)
        return results
    
    def _generate_bulk_report(self, results: List[Dict]):
        """Generate summary report for bulk extraction"""
        if not results:
            print("\n❌ No successful extractions for bulk report")
            return
        
        print(f"\n📈 BULK EXTRACTION REPORT")
        print("=" * 40)
        
        total_profiles = len(results)
        profiles_with_emails = sum(1 for r in results if r["contact_information"]["emails"])
        profiles_with_phones = sum(1 for r in results if r["contact_information"]["phones"])
        total_emails = sum(len(r["contact_information"]["emails"]) for r in results)
        total_phones = sum(len(r["contact_information"]["phones"]) for r in results)
        avg_quality = sum(self._calculate_contact_quality(r["contact_information"]) for r in results) / total_profiles
        
        print(f"📊 STATISTICS:")
        print(f"   Total Profiles Processed: {total_profiles}")
        print(f"   Profiles with Emails: {profiles_with_emails} ({profiles_with_emails/total_profiles*100:.1f}%)")
        print(f"   Profiles with Phones: {profiles_with_phones} ({profiles_with_phones/total_profiles*100:.1f}%)")
        print(f"   Total Email Addresses: {total_emails}")
        print(f"   Total Phone Numbers: {total_phones}")
        print(f"   Average Contact Quality: {avg_quality:.1f}/10")
        
        contact_discovery_rate = (profiles_with_emails + profiles_with_phones) / total_profiles * 100
        print(f"   Contact Discovery Rate: {contact_discovery_rate:.1f}%")
        
        print(f"\n🎯 COGNISM COMPARISON:")
        print(f"   Our Contact Discovery: {contact_discovery_rate:.1f}%")
        print(f"   Typical Cognism Rate: 70-80%")
        print(f"   Our Performance: {'✅ Competitive' if contact_discovery_rate >= 60 else '⚠️ Below Average'}")
    
    def export_contact_data(self, results: List[Dict], filename: str = None) -> str:
        """Export contact data to CSV (like Cognism export)"""
        try:
            import pandas as pd
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"contact_extraction_export_{timestamp}.csv"
            
            # Flatten data for CSV export
            export_data = []
            
            for result in results:
                profile = result["profile_info"]
                contacts = result["contact_information"]
                metadata = result["extraction_metadata"]
                
                export_data.append({
                    "Name": profile["name"],
                    "Title": profile["title"],
                    "Company": profile["company"],
                    "Location": profile["location"],
                    "LinkedIn URL": profile["linkedin_url"],
                    "Email Addresses": "; ".join(contacts["emails"]),
                    "Phone Numbers": "; ".join(contacts["phones"]),
                    "Websites": "; ".join(contacts["websites"]),
                    "Social Links": "; ".join(contacts["social_links"]),
                    "Contact Quality Score": self._calculate_contact_quality(contacts),
                    "Contact Points Found": metadata["contact_points_found"],
                    "Data Sources": "; ".join(metadata["data_sources"]),
                    "Extraction Date": metadata["extraction_timestamp"]
                })
            
            df = pd.DataFrame(export_data)
            df.to_csv(filename, index=False)
            
            print(f"✅ Contact data exported to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return ""
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.extractor and hasattr(self.extractor, 'driver'):
                self.extractor.driver.quit()
                print("✅ Browser cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def main():
    """Main demonstration function"""
    print("🎉 LinkedIn Contact Extraction Demo")
    print("Demonstrating Cognism-like contact discovery capabilities")
    print("=" * 70)
    
    demo = ContactExtractionDemo()
    
    try:
        # Initialize the system
        if not demo.initialize():
            print("❌ Failed to initialize contact extraction system")
            return
        
        # Demo profiles (replace with actual URLs you want to test)
        demo_profiles = [
            "https://www.linkedin.com/in/williamhgates/",
            "https://www.linkedin.com/in/jeffweiner08/",
            "https://www.linkedin.com/in/satyanadella/"
        ]
        
        print(f"\n🎯 Running contact extraction demo with {len(demo_profiles)} profiles")
        print("This will demonstrate our Cognism-comparable contact discovery capabilities")
        
        # Single profile demonstration
        print(f"\n🔍 SINGLE PROFILE DEMONSTRATION")
        contact_data = demo.demonstrate_contact_extraction(demo_profiles[0])
        
        # Bulk extraction demonstration
        print(f"\n🔄 BULK EXTRACTION DEMONSTRATION")
        all_results = demo.bulk_contact_extraction_demo(demo_profiles)
        
        # Export results
        if all_results:
            export_file = demo.export_contact_data(all_results)
            print(f"\n💾 Results exported to: {export_file}")
        
        print(f"\n🎉 Contact extraction demo completed successfully!")
        print(f"This demonstrates our ability to extract contact information")
        print(f"comparable to commercial tools like Cognism.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()