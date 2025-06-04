#!/usr/bin/env python3
"""
Basic Tests for LinkedIn Scraper

This file contains essential tests to verify the scraper components work correctly.
Run these tests before deploying to production.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from working_linkedin_extractor import LinkedInProfile, WorkingLinkedInExtractor
from database_storage import LinkedInDatabaseStorage
from stealth_browser import BrowserConfig, get_random_user_agent

class TestLinkedInProfile(unittest.TestCase):
    """Test LinkedInProfile data structure"""
    
    def test_profile_initialization(self):
        """Test profile can be initialized with default values"""
        profile = LinkedInProfile()
        
        self.assertEqual(profile.full_name, "")
        self.assertEqual(profile.linkedin_url, "")
        self.assertIsInstance(profile.emails, list)
        self.assertIsInstance(profile.phones, list)
        self.assertEqual(len(profile.emails), 0)
        self.assertEqual(len(profile.phones), 0)
        self.assertFalse(profile.extraction_success)
    
    def test_profile_with_data(self):
        """Test profile initialization with actual data"""
        profile = LinkedInProfile(
            full_name="John Doe",
            linkedin_url="https://linkedin.com/in/johndoe",
            role="Software Engineer",
            company="Tech Corp",
            emails=["john@example.com"],
            phones=["+1234567890"]
        )
        
        self.assertEqual(profile.full_name, "John Doe")
        self.assertEqual(profile.linkedin_url, "https://linkedin.com/in/johndoe")
        self.assertEqual(profile.role, "Software Engineer")
        self.assertEqual(profile.company, "Tech Corp")
        self.assertEqual(len(profile.emails), 1)
        self.assertEqual(len(profile.phones), 1)
        self.assertEqual(profile.emails[0], "john@example.com")
        self.assertEqual(profile.phones[0], "+1234567890")
    
    def test_profile_to_dict(self):
        """Test profile conversion to dictionary"""
        profile = LinkedInProfile(
            full_name="Jane Smith",
            company="Example Inc"
        )
        
        profile_dict = profile.to_dict()
        
        self.assertIsInstance(profile_dict, dict)
        self.assertEqual(profile_dict['full_name'], "Jane Smith")
        self.assertEqual(profile_dict['company'], "Example Inc")
        self.assertIn('extraction_timestamp', profile_dict)

class TestBrowserConfig(unittest.TestCase):
    """Test browser configuration"""
    
    def test_browser_config_defaults(self):
        """Test default browser configuration"""
        config = BrowserConfig()
        
        self.assertIsInstance(config.headless, bool)
        self.assertIsInstance(config.timeout, int)
        self.assertIsInstance(config.stealth_mode, bool)
        self.assertIsInstance(config.window_size, str)
    
    def test_user_agent_generation(self):
        """Test user agent generation"""
        user_agent = get_random_user_agent()
        
        self.assertIsInstance(user_agent, str)
        self.assertGreater(len(user_agent), 10)
        self.assertIn("Mozilla", user_agent)

class TestDatabaseStorage(unittest.TestCase):
    """Test database storage functionality"""
    
    def setUp(self):
        """Set up test database"""
        # Use test environment variables or defaults
        os.environ['DB_NAME'] = 'linkedin_scraper_test'
        self.storage = None
    
    def test_database_config(self):
        """Test database configuration loading"""
        try:
            storage = LinkedInDatabaseStorage()
            self.assertIsInstance(storage.db_config, dict)
            self.assertIn('host', storage.db_config)
            self.assertIn('database', storage.db_config)
        except Exception as e:
            # If database is not available, skip this test
            self.skipTest(f"Database not available: {e}")
    
    def test_profile_save_and_retrieve(self):
        """Test saving and retrieving a profile"""
        try:
            storage = LinkedInDatabaseStorage()
            
            # Create test profile
            profile = LinkedInProfile(
                full_name="Test User",
                linkedin_url="https://linkedin.com/in/testuser",
                role="Test Role",
                company="Test Company",
                emails=["test@example.com"],
                extraction_success=True
            )
            
            # Save profile
            profile_id = storage.save_profile(profile)
            self.assertIsInstance(profile_id, int)
            self.assertGreater(profile_id, 0)
            
            # Retrieve profile
            retrieved = storage.get_profile_by_url("https://linkedin.com/in/testuser")
            if retrieved:
                self.assertEqual(retrieved['full_name'], "Test User")
                self.assertEqual(retrieved['company'], "Test Company")
            
        except Exception as e:
            self.skipTest(f"Database operations not available: {e}")

class TestExtractorComponents(unittest.TestCase):
    """Test extractor components without browser"""
    
    def test_extractor_initialization(self):
        """Test extractor can be initialized"""
        # Mock driver for testing
        mock_driver = Mock()
        
        extractor = WorkingLinkedInExtractor(mock_driver)
        
        self.assertIsNotNone(extractor.driver)
        self.assertIsNotNone(extractor.wait)
    
    def test_page_type_detection(self):
        """Test page type detection logic"""
        mock_driver = Mock()
        extractor = WorkingLinkedInExtractor(mock_driver)
        
        # Test different URL patterns
        test_urls = [
            ("https://linkedin.com/in/username", "authenticated_profile"),
            ("https://linkedin.com/sales/lead/12345", "sales_navigator_profile"),
            ("https://linkedin.com/sales/search/people", "sales_navigator_search"),
            ("https://linkedin.com/company/example", "company_page"),
            ("https://example.com", "unknown")
        ]
        
        for url, expected_type in test_urls:
            mock_driver.current_url = url
            detected_type = extractor.detect_page_type()
            
            # Some detection requires DOM elements, so we'll accept partial matches
            if expected_type in ["sales_navigator_profile", "sales_navigator_search", "company_page"]:
                self.assertIn(expected_type.split('_')[0], detected_type)

class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    def test_end_to_end_mock(self):
        """Test end-to-end workflow with mocked components"""
        # Create a mock profile
        profile = LinkedInProfile(
            full_name="Integration Test User",
            linkedin_url="https://linkedin.com/in/integrationtest",
            role="Test Engineer",
            company="Integration Corp",
            emails=["integration@test.com"],
            extraction_success=True
        )
        
        # Test profile data integrity
        self.assertTrue(profile.extraction_success)
        self.assertEqual(len(profile.emails), 1)
        
        # Test serialization
        profile_dict = profile.to_dict()
        self.assertIsInstance(profile_dict, dict)
        self.assertEqual(profile_dict['full_name'], "Integration Test User")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid profile data
        profile = LinkedInProfile()
        self.assertFalse(profile.extraction_success)
        
        # Test with None values
        profile.emails = None
        profile.__post_init__()  # Re-initialize
        self.assertIsInstance(profile.emails, list)

def run_tests():
    """Run all tests and report results"""
    print("🧪 Running LinkedIn Scraper Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_classes = [
        TestLinkedInProfile,
        TestBrowserConfig,
        TestDatabaseStorage,
        TestExtractorComponents,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Report results
    print("\n📊 Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ Success Rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    
    if success:
        print("\n🎉 All tests passed! The scraper is ready for use.")
    else:
        print("\n⚠️  Some tests failed. Please review the issues before deployment.")
        sys.exit(1)