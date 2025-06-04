# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

This guide will get you extracting LinkedIn profiles and contact information in under 5 minutes.

---

## 📋 Prerequisites

- **Python 3.8+** installed
- **PostgreSQL** database (local or cloud)
- **LinkedIn account** (Sales Navigator recommended for contact extraction)
- **Chrome browser** installed

---

## ⚡ Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Tumphy/linkedin-scraper.git
cd linkedin-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required .env settings:**
```bash
LINKEDIN_USERNAME=your.email@domain.com
LINKEDIN_PASSWORD=your_password
DATABASE_URL=postgresql://username:password@localhost/linkedin_scraper
```

### 3. Database Setup

```bash
# Initialize database (creates tables automatically)
python -c "from database_storage import LinkedInDatabaseStorage; LinkedInDatabaseStorage()"
```

---

## 🎯 Basic Usage

### Single Profile Extraction

```python
from working_linkedin_extractor import WorkingLinkedInExtractor
from stealth_browser import create_enhanced_browser
from database_storage import save_linkedin_profile

# Create browser and extractor
driver = create_enhanced_browser(use_stealth=True)
extractor = WorkingLinkedInExtractor(driver)

# Extract profile
profile = extractor.extract_profile("https://www.linkedin.com/in/williamhgates/")

# Save to database
profile_id = save_linkedin_profile(profile)

print(f"✅ Extracted: {profile.full_name}")
print(f"📧 Emails: {profile.emails}")
print(f"📱 Phones: {profile.phones}")

# Cleanup
driver.quit()
```

### Contact Extraction Demo

```bash
# Run the contact extraction demo
python contact_extraction_demo.py
```

---

## 🔧 Sales Navigator Setup

### 1. Sales Navigator Access

1. Ensure you have LinkedIn Sales Navigator subscription
2. Login to Sales Navigator at https://linkedin.com/sales
3. Verify access to contact information features

### 2. Test Sales Navigator Extraction

```bash
# Test Sales Navigator capabilities
python tests/test_sales_navigator.py
```

---

## 📊 Quick Commands

### Export Data
```bash
# Export all profiles to CSV
python -c "from database_storage import export_profiles_to_csv; export_profiles_to_csv('my_export.csv')"
```

### Check Database
```bash
# View extraction statistics
python -c "from database_storage import LinkedInDatabaseStorage; print(LinkedInDatabaseStorage().get_extraction_stats())"
```

### Test Connection
```bash
# Test database connection
python -c "from database_storage import LinkedInDatabaseStorage; LinkedInDatabaseStorage().test_connection()"
```

---

## 🎉 You're Ready!

You now have a fully functional LinkedIn scraper with:
- ✅ Profile extraction capabilities
- ✅ Contact information discovery
- ✅ Database storage
- ✅ Export functionality

**Next Steps:**
- Read the [full documentation](README.md)
- Explore [Sales Navigator features](docs/SALES_NAVIGATOR_SETUP.md)
- Check the [production roadmap](docs/PRODUCTION_ROADMAP.md)

---

## 🆘 Troubleshooting

### Common Issues

**Browser/ChromeDriver Issues:**
```bash
pip install --upgrade selenium webdriver-manager
```

**Database Connection Failed:**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Ensure database exists

**LinkedIn Login Issues:**
- Check credentials in .env
- Verify 2FA is disabled or handled
- Clear browser cache/cookies

### Getting Help

- Check the [troubleshooting guide](README.md#support--troubleshooting)
- Review logs in the `logs/` directory
- Open an issue on GitHub

Happy scraping! 🎯