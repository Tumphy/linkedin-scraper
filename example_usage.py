#!/usr/bin/env python3
"""
LinkedIn Scraper - Example Usage Scripts

This file contains practical examples of how to use the LinkedIn scraper
for various common use cases.
"""

import os
import sys
from typing import List

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from working_linkedin_extractor import WorkingLinkedInExtractor, LinkedInProfile
from database_storage import LinkedInDatabaseStorage, export_profiles_to_csv
from stealth_browser import create_enhanced_browser

def example_1_single_profile():
    """Example 1: Extract a single LinkedIn profile"""
    print("📝 Example 1: Single Profile Extraction")
    print("=" * 50)
    
    # Initialize browser and extractor
    driver = create_enhanced_browser(use_stealth=True)
    extractor = WorkingLinkedInExtractor(driver)
    storage = LinkedInDatabaseStorage()
    
    try:
        # Extract profile
        profile_url = "https://www.linkedin.com/in/williamhgates/"
        profile = extractor.extract_profile(profile_url)
        
        if profile and profile.extraction_success:
            print(f"✅ Successfully extracted: {profile.full_name}")
            print(f"   Role: {profile.role}")
            print(f"   Company: {profile.company}")
            print(f"   Location: {profile.location or profile.geography}")
            print(f"   Emails: {profile.emails}")
            print(f"   Phones: {profile.phones}")
            
            # Save to database
            profile_id = storage.save_profile(profile)
            print(f"   💾 Saved to database with ID: {profile_id}")
        else:
            print("❌ Failed to extract profile")
            
    finally:
        driver.quit()

def example_2_bulk_extraction():
    """Example 2: Bulk profile extraction from a list"""
    print("\n📝 Example 2: Bulk Profile Extraction")
    print("=" * 50)
    
    profile_urls = [
        "https://www.linkedin.com/in/williamhgates/",
        "https://www.linkedin.com/in/jeffweiner08/",
        "https://www.linkedin.com/in/satyanadella/"
    ]
    
    driver = create_enhanced_browser(use_stealth=True)
    extractor = WorkingLinkedInExtractor(driver)
    storage = LinkedInDatabaseStorage()
    
    try:
        extracted_profiles = []
        
        for i, url in enumerate(profile_urls, 1):
            print(f"\n[{i}/{len(profile_urls)}] Processing: {url}")
            
            profile = extractor.extract_profile(url)
            
            if profile and profile.extraction_success:
                # Save to database
                profile_id = storage.save_profile(profile)
                extracted_profiles.append(profile)
                print(f"✅ Extracted: {profile.full_name} (ID: {profile_id})")
            else:
                print(f"❌ Failed to extract: {url}")
            
            # Respectful delay between requests
            if i < len(profile_urls):
                print("⏳ Waiting 3 seconds...")
                import time
                time.sleep(3)
        
        print(f"\n📊 Bulk extraction summary:")
        print(f"   Successfully extracted: {len(extracted_profiles)}/{len(profile_urls)}")
        print(f"   Success rate: {len(extracted_profiles)/len(profile_urls)*100:.1f}%")
        
    finally:
        driver.quit()

def example_3_contact_extraction():
    """Example 3: Focus on contact information extraction"""
    print("\n📝 Example 3: Contact Information Extraction")
    print("=" * 50)
    
    driver = create_enhanced_browser(use_stealth=True)
    extractor = WorkingLinkedInExtractor(driver)
    
    try:
        # Example with a profile that might have contact information
        profile_url = "https://www.linkedin.com/in/williamhgates/"
        profile = extractor.extract_profile(profile_url)
        
        if profile and profile.extraction_success:
            print(f"👤 Profile: {profile.full_name}")
            print(f"📞 Contact Information Found:")
            
            if profile.emails:
                print(f"   📧 Email addresses ({len(profile.emails)}):")
                for email in profile.emails:
                    print(f"      • {email}")
            else:
                print("   📧 No email addresses found")
            
            if profile.phones:
                print(f"   📱 Phone numbers ({len(profile.phones)}):")
                for phone in profile.phones:
                    print(f"      • {phone}")
            else:
                print("   📱 No phone numbers found")
            
            if profile.websites:
                print(f"   🌐 Websites ({len(profile.websites)}):")
                for website in profile.websites:
                    print(f"      • {website}")
            else:
                print("   🌐 No websites found")
            
            # Calculate contact quality score
            contact_points = len(profile.emails) + len(profile.phones) + len(profile.websites)
            quality_score = min(contact_points * 2, 10)  # Simple scoring
            
            print(f"\n📊 Contact Quality Score: {quality_score}/10")
            print(f"   Contact points found: {contact_points}")
            print(f"   Profile type: {profile.profile_type}")
            
        else:
            print("❌ Failed to extract profile")
            
    finally:
        driver.quit()

def example_4_database_operations():
    """Example 4: Database operations and exports"""
    print("\n📝 Example 4: Database Operations")
    print("=" * 50)
    
    storage = LinkedInDatabaseStorage()
    
    # Get statistics
    stats = storage.get_extraction_stats()
    print("📊 Current Database Statistics:")
    print(f"   Total profiles: {stats.get('total_profiles', 0)}")
    print(f"   Successful extractions: {stats.get('successful_profiles', 0)}")
    print(f"   Profiles with contacts: {stats.get('profiles_with_contacts', 0)}")
    print(f"   Recent extractions (24h): {stats.get('recent_extractions', 0)}")
    
    # Search for profiles
    print("\n🔍 Searching for Technology profiles:")
    tech_profiles = storage.search_profiles(company="Microsoft", limit=5)
    
    if tech_profiles:
        for profile in tech_profiles:
            print(f"   • {profile['full_name']} - {profile['company']}")
    else:
        print("   No profiles found")
    
    # Export to CSV
    print("\n💾 Exporting profiles to CSV:")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_file = f"example_export_{timestamp}.csv"
    
    exported_file = export_profiles_to_csv(export_file, limit=10)
    if exported_file:
        print(f"   ✅ Exported to: {exported_file}")
    else:
        print("   ❌ Export failed")

def example_5_sales_navigator():
    """Example 5: Sales Navigator extraction (requires Sales Navigator access)"""
    print("\n📝 Example 5: Sales Navigator Extraction")
    print("=" * 50)
    print("⚠️  This example requires LinkedIn Sales Navigator subscription")
    
    # This would be used with actual Sales Navigator URLs
    sales_navigator_examples = [
        "https://www.linkedin.com/sales/search/people?keywords=CEO",
        "https://www.linkedin.com/sales/lead/12345678"  # Example lead URL
    ]
    
    print("🔍 Example Sales Navigator URLs:")
    for url in sales_navigator_examples:
        print(f"   • {url}")
    
    print("\n💡 To use Sales Navigator extraction:")
    print("   1. Ensure you have Sales Navigator subscription")
    print("   2. Login to LinkedIn normally")
    print("   3. Navigate to Sales Navigator search or lead pages")
    print("   4. Use the extractor on those URLs")
    print("   5. Contact information will be extracted from accessible modals")

def example_6_advanced_filtering():
    """Example 6: Advanced database filtering and reporting"""
    print("\n📝 Example 6: Advanced Database Filtering")
    print("=" * 50)
    
    storage = LinkedInDatabaseStorage()
    
    # Various search examples
    search_examples = [
        ("Technology Companies", {"company": "Google"}),
        ("Profiles with Contact Info", {"has_contact_info": True}),
        ("Sales Navigator Profiles", {"profile_type": "sales_navigator"}),
        ("Bay Area Profiles", {"location": "San Francisco"})
    ]
    
    for description, filters in search_examples:
        print(f"\n🔍 {description}:")
        profiles = storage.search_profiles(**filters, limit=3)
        
        if profiles:
            for profile in profiles:
                emails_count = profile.get('emails_count', 0)
                phones_count = profile.get('phones_count', 0)
                print(f"   • {profile['full_name']} - {profile['company']}")
                print(f"     📧 {emails_count} emails, 📱 {phones_count} phones")
        else:
            print("   No profiles found")

def run_all_examples():
    """Run all examples in sequence"""
    print("🎉 LinkedIn Scraper - Example Usage")
    print("=" * 70)
    print("This will demonstrate various ways to use the LinkedIn scraper")
    print("\n⚠️  Note: Some examples require actual LinkedIn login and profiles")
    
    try:
        # Database operations (no browser needed)
        example_4_database_operations()
        example_6_advanced_filtering()
        
        # Sales Navigator info (no browser needed)
        example_5_sales_navigator()
        
        print("\n✅ Examples completed!")
        print("\n💡 To run browser-based examples:")
        print("   1. Ensure your .env file has LinkedIn credentials")
        print("   2. Run individual example functions")
        print("   3. Or use the main.py script for production usage")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    # Run examples that don't require browser by default
    run_all_examples()
    
    # Uncomment to run browser-based examples:
    # example_1_single_profile()
    # example_2_bulk_extraction() 
    # example_3_contact_extraction()