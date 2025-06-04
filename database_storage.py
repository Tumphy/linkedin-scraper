#!/usr/bin/env python3
"""
LinkedIn Profile Database Storage Module

Handles storage of extracted LinkedIn profiles to PostgreSQL database
Integrates with existing microservices architecture and maintains data consistency
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
import pandas as pd
from dataclasses import asdict
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager
from dotenv import load_dotenv

from working_linkedin_extractor import LinkedInProfile

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LinkedInDatabaseStorage:
    """Database storage handler for LinkedIn profiles"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'linkedin_scraper'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        # Parse DATABASE_URL if provided (for cloud deployments)
        if os.getenv('DATABASE_URL'):
            self._parse_database_url()
        
        # Ensure database and tables exist
        self.init_database()
    
    def _parse_database_url(self):
        """Parse DATABASE_URL environment variable"""
        import urllib.parse as urlparse
        
        url = urlparse.urlparse(os.getenv('DATABASE_URL'))
        self.db_config = {
            'host': url.hostname,
            'port': url.port,
            'database': url.path[1:],  # Remove leading slash
            'user': url.username,
            'password': url.password
        }
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            # First, try to connect to the specified database
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Create profiles table if it doesn't exist
                    self.create_profiles_table(cursor)
                    # Create contact_info table if it doesn't exist
                    self.create_contact_info_table(cursor)
                    # Create extraction_logs table
                    self.create_extraction_logs_table(cursor)
                conn.commit()
                logger.info("✅ Database tables initialized successfully")
        
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                # Database doesn't exist, create it
                self.create_database()
                # Now initialize tables
                self.init_database()
            else:
                logger.error(f"Database connection error: {e}")
                raise
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect to postgres database to create our database
            temp_config = self.db_config.copy()
            temp_config['database'] = 'postgres'
            
            conn = psycopg2.connect(**temp_config)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {self.db_config['database']}")
                logger.info(f"✅ Created database: {self.db_config['database']}")
            
            conn.close()
            
        except psycopg2.errors.DuplicateDatabase:
            logger.info(f"Database {self.db_config['database']} already exists")
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def create_profiles_table(self, cursor):
        """Create the main profiles table"""
        create_table_sql = \"\"\"
        CREATE TABLE IF NOT EXISTS linkedin_profiles (
            id SERIAL PRIMARY KEY,
            
            -- Core identifiers
            full_name VARCHAR(255) NOT NULL,
            linkedin_url VARCHAR(500) UNIQUE NOT NULL,
            
            -- Profile information
            role VARCHAR(255),
            company VARCHAR(255),
            company_linkedin_url VARCHAR(500),
            geography VARCHAR(255),
            location VARCHAR(255),
            headline TEXT,
            about TEXT,
            
            -- Sales Navigator specific
            date_added VARCHAR(100),
            
            -- Network metrics
            connections_count INTEGER,
            
            -- Profile metadata
            profile_type VARCHAR(50) DEFAULT 'unknown',
            extraction_success BOOLEAN DEFAULT FALSE,
            extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Data enrichment fields
            emails_count INTEGER DEFAULT 0,
            phones_count INTEGER DEFAULT 0,
            websites_count INTEGER DEFAULT 0,
            social_links_count INTEGER DEFAULT 0,
            
            -- Audit fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_name ON linkedin_profiles(full_name);
        CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_company ON linkedin_profiles(company);
        CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_type ON linkedin_profiles(profile_type);
        CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_extraction_time ON linkedin_profiles(extraction_timestamp);
        \"\"\"
        
        cursor.execute(create_table_sql)
        logger.debug("✅ Profiles table created/verified")
    
    def create_contact_info_table(self, cursor):
        """Create contact information table"""
        create_table_sql = \"\"\"
        CREATE TABLE IF NOT EXISTS linkedin_contact_info (
            id SERIAL PRIMARY KEY,
            profile_id INTEGER REFERENCES linkedin_profiles(id) ON DELETE CASCADE,
            
            -- Contact details
            contact_type VARCHAR(50) NOT NULL, -- 'email', 'phone', 'website', 'social', 'address'
            contact_value VARCHAR(500) NOT NULL,
            contact_platform VARCHAR(100), -- For social links: 'twitter', 'facebook', etc.
            
            -- Verification status
            is_verified BOOLEAN DEFAULT FALSE,
            verification_date TIMESTAMP,
            
            -- Audit fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(profile_id, contact_type, contact_value)
        );
        
        CREATE INDEX IF NOT EXISTS idx_contact_info_profile ON linkedin_contact_info(profile_id);
        CREATE INDEX IF NOT EXISTS idx_contact_info_type ON linkedin_contact_info(contact_type);
        \"\"\"
        
        cursor.execute(create_table_sql)
        logger.debug("✅ Contact info table created/verified")
    
    def create_extraction_logs_table(self, cursor):
        """Create extraction logs table for monitoring"""
        create_table_sql = \"\"\"
        CREATE TABLE IF NOT EXISTS extraction_logs (
            id SERIAL PRIMARY KEY,
            
            -- Extraction details
            extraction_type VARCHAR(50) NOT NULL, -- 'profile', 'search_results', 'bulk'
            source_url VARCHAR(500),
            profiles_extracted INTEGER DEFAULT 0,
            profiles_successful INTEGER DEFAULT 0,
            profiles_failed INTEGER DEFAULT 0,
            
            -- Timing
            extraction_start TIMESTAMP,
            extraction_end TIMESTAMP,
            duration_seconds INTEGER,
            
            -- Error tracking
            error_message TEXT,
            
            -- Audit
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_extraction_logs_type ON extraction_logs(extraction_type);
        CREATE INDEX IF NOT EXISTS idx_extraction_logs_date ON extraction_logs(created_at);
        \"\"\"
        
        cursor.execute(create_table_sql)
        logger.debug("✅ Extraction logs table created/verified")
    
    def save_profile(self, profile: LinkedInProfile) -> int:
        \"\"\"Save a single LinkedIn profile to database\"\"\"
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if profile already exists
                    cursor.execute(
                        "SELECT id FROM linkedin_profiles WHERE linkedin_url = %s",
                        (profile.linkedin_url,)
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        profile_id = existing[0]
                        # Update existing profile
                        self._update_profile(cursor, profile_id, profile)
                        logger.info(f"✅ Updated existing profile: {profile.full_name}")
                    else:
                        # Insert new profile
                        profile_id = self._insert_profile(cursor, profile)
                        logger.info(f"✅ Saved new profile: {profile.full_name}")
                    
                    # Save contact information
                    self._save_contact_info(cursor, profile_id, profile)
                    
                conn.commit()
                return profile_id
                
        except Exception as e:
            logger.error(f"❌ Error saving profile {profile.full_name}: {e}")
            raise
    
    def _insert_profile(self, cursor, profile: LinkedInProfile) -> int:
        \"\"\"Insert a new profile record\"\"\"
        insert_sql = \"\"\"
        INSERT INTO linkedin_profiles (
            full_name, linkedin_url, role, company, company_linkedin_url,
            geography, location, headline, about, date_added, connections_count,
            profile_type, extraction_success, extraction_timestamp,
            emails_count, phones_count, websites_count, social_links_count
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        \"\"\"
        
        cursor.execute(insert_sql, (
            profile.full_name, profile.linkedin_url, profile.role, profile.company,
            profile.company_linkedin_url, profile.geography, profile.location,
            profile.headline, profile.about, profile.date_added, profile.connections_count,
            profile.profile_type, profile.extraction_success, profile.extraction_timestamp,
            len(profile.emails), len(profile.phones), len(profile.websites), len(profile.social_links)
        ))
        
        return cursor.fetchone()[0]
    
    def _update_profile(self, cursor, profile_id: int, profile: LinkedInProfile):
        \"\"\"Update existing profile record\"\"\"
        update_sql = \"\"\"
        UPDATE linkedin_profiles SET
            full_name = %s, role = %s, company = %s, company_linkedin_url = %s,
            geography = %s, location = %s, headline = %s, about = %s, date_added = %s,
            connections_count = %s, profile_type = %s, extraction_success = %s,
            extraction_timestamp = %s, emails_count = %s, phones_count = %s,
            websites_count = %s, social_links_count = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        \"\"\"
        
        cursor.execute(update_sql, (
            profile.full_name, profile.role, profile.company, profile.company_linkedin_url,
            profile.geography, profile.location, profile.headline, profile.about,
            profile.date_added, profile.connections_count, profile.profile_type,
            profile.extraction_success, profile.extraction_timestamp,
            len(profile.emails), len(profile.phones), len(profile.websites),
            len(profile.social_links), profile_id
        ))
    
    def _save_contact_info(self, cursor, profile_id: int, profile: LinkedInProfile):
        \"\"\"Save contact information for a profile\"\"\"
        # Delete existing contact info for this profile
        cursor.execute("DELETE FROM linkedin_contact_info WHERE profile_id = %s", (profile_id,))
        
        # Prepare contact data
        contact_data = []
        
        # Add emails
        for email in profile.emails:
            contact_data.append((profile_id, 'email', email, None))
        
        # Add phones
        for phone in profile.phones:
            contact_data.append((profile_id, 'phone', phone, None))
        
        # Add websites
        for website in profile.websites:
            contact_data.append((profile_id, 'website', website, None))
        
        # Add social links
        for social in profile.social_links:
            platform = None
            if 'twitter.com' in social:
                platform = 'twitter'
            elif 'facebook.com' in social:
                platform = 'facebook'
            elif 'instagram.com' in social:
                platform = 'instagram'
            elif 'github.com' in social:
                platform = 'github'
            
            contact_data.append((profile_id, 'social', social, platform))
        
        # Add addresses
        for address in profile.addresses:
            contact_data.append((profile_id, 'address', address, None))
        
        # Insert contact data
        if contact_data:
            execute_values(
                cursor,
                \"\"\"INSERT INTO linkedin_contact_info 
                   (profile_id, contact_type, contact_value, contact_platform) 
                   VALUES %s ON CONFLICT DO NOTHING\"\"\",
                contact_data
            )
    
    def save_profiles_bulk(self, profiles: List[LinkedInProfile]) -> Dict[str, int]:
        \"\"\"Save multiple profiles in bulk\"\"\"
        results = {'saved': 0, 'updated': 0, 'failed': 0}
        
        for profile in profiles:
            try:
                profile_id = self.save_profile(profile)
                if profile_id:
                    # Check if this was an update or new save
                    with self.get_db_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(
                                "SELECT created_at, updated_at FROM linkedin_profiles WHERE id = %s",
                                (profile_id,)
                            )
                            created, updated = cursor.fetchone()
                            if created == updated:
                                results['saved'] += 1
                            else:
                                results['updated'] += 1
            except Exception as e:
                logger.error(f"❌ Failed to save profile: {e}")
                results['failed'] += 1
        
        logger.info(f"📊 Bulk save results: {results}")
        return results
    
    def get_profile_by_url(self, linkedin_url: str) -> Optional[Dict]:
        \"\"\"Get profile by LinkedIn URL\"\"\"
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM linkedin_profiles WHERE linkedin_url = %s",
                        (linkedin_url,)
                    )
                    return dict(cursor.fetchone()) if cursor.fetchone() else None
        except Exception as e:
            logger.error(f"❌ Error fetching profile: {e}")
            return None
    
    def search_profiles(self, **filters) -> List[Dict]:
        \"\"\"Search profiles with various filters\"\"\"
        try:
            conditions = []
            params = []
            
            # Build WHERE clause based on filters
            if filters.get('company'):
                conditions.append("company ILIKE %s")
                params.append(f"%{filters['company']}%")
            
            if filters.get('role'):
                conditions.append("role ILIKE %s")
                params.append(f"%{filters['role']}%")
            
            if filters.get('location'):
                conditions.append("(geography ILIKE %s OR location ILIKE %s)")
                params.extend([f"%{filters['location']}%", f"%{filters['location']}%"])
            
            if filters.get('profile_type'):
                conditions.append("profile_type = %s")
                params.append(filters['profile_type'])
            
            if filters.get('has_contact_info'):
                conditions.append("(emails_count > 0 OR phones_count > 0)")
            
            # Limit results
            limit = filters.get('limit', 100)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f\"\"\"
            SELECT * FROM linkedin_profiles 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT {limit}
            \"\"\"
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            logger.error(f"❌ Error searching profiles: {e}")
            return []
    
    def get_extraction_stats(self) -> Dict:
        \"\"\"Get extraction statistics\"\"\"
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    
                    # Total profiles
                    cursor.execute("SELECT COUNT(*) FROM linkedin_profiles")
                    stats['total_profiles'] = cursor.fetchone()[0]
                    
                    # Successful extractions
                    cursor.execute("SELECT COUNT(*) FROM linkedin_profiles WHERE extraction_success = TRUE")
                    stats['successful_profiles'] = cursor.fetchone()[0]
                    
                    # Profiles with contact info
                    cursor.execute("SELECT COUNT(*) FROM linkedin_profiles WHERE emails_count > 0 OR phones_count > 0")
                    stats['profiles_with_contacts'] = cursor.fetchone()[0]
                    
                    # Total contact info records
                    cursor.execute("SELECT COUNT(*) FROM linkedin_contact_info")
                    stats['total_contact_records'] = cursor.fetchone()[0]
                    
                    # Recent extractions (last 24 hours)
                    cursor.execute(
                        "SELECT COUNT(*) FROM linkedin_profiles WHERE created_at > NOW() - INTERVAL '24 hours'"
                    )
                    stats['recent_extractions'] = cursor.fetchone()[0]
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}
    
    def export_to_csv(self, output_file: str = None, **filters) -> str:
        \"\"\"Export profiles to CSV with contact information\"\"\"
        try:
            # Generate filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"linkedin_export_{timestamp}.csv"
            
            # Get profiles with filters
            profiles = self.search_profiles(**filters)
            
            if not profiles:
                logger.warning("No profiles found for export")
                return ""
            
            # Convert to DataFrame
            df = pd.DataFrame(profiles)
            
            # Add contact information
            contact_info = []
            for profile in profiles:
                profile_contacts = self._get_profile_contacts(profile['id'])
                contact_info.append(profile_contacts)
            
            # Add contact columns
            df['emails'] = [', '.join(c.get('emails', [])) for c in contact_info]
            df['phones'] = [', '.join(c.get('phones', [])) for c in contact_info]
            df['websites'] = [', '.join(c.get('websites', [])) for c in contact_info]
            df['social_links'] = [', '.join(c.get('social_links', [])) for c in contact_info]
            
            # Export to CSV
            df.to_csv(output_file, index=False)
            logger.info(f"✅ Exported {len(profiles)} profiles to {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")
            return ""
    
    def _get_profile_contacts(self, profile_id: int) -> Dict[str, List[str]]:
        \"\"\"Get contact information for a profile\"\"\"
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT contact_type, contact_value FROM linkedin_contact_info WHERE profile_id = %s",
                        (profile_id,)
                    )
                    
                    contacts = {'emails': [], 'phones': [], 'websites': [], 'social_links': [], 'addresses': []}
                    
                    for contact_type, contact_value in cursor.fetchall():
                        if contact_type in contacts:
                            contacts[contact_type].append(contact_value)
                        elif contact_type == 'social':
                            contacts['social_links'].append(contact_value)
                    
                    return contacts
                    
        except Exception as e:
            logger.error(f"❌ Error getting contacts for profile {profile_id}: {e}")
            return {'emails': [], 'phones': [], 'websites': [], 'social_links': [], 'addresses': []}
    
    def log_extraction(self, extraction_type: str, source_url: str, 
                      profiles_extracted: int, profiles_successful: int, 
                      duration_seconds: int, error_message: str = None):
        \"\"\"Log extraction activity\"\"\"
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(\"\"\"
                        INSERT INTO extraction_logs 
                        (extraction_type, source_url, profiles_extracted, profiles_successful, 
                         profiles_failed, duration_seconds, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    \"\"\", (
                        extraction_type, source_url, profiles_extracted, profiles_successful,
                        profiles_extracted - profiles_successful, duration_seconds, error_message
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error logging extraction: {e}")

    def test_connection(self) -> bool:
        \"\"\"Test database connection\"\"\"
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    logger.info("✅ Database connection successful")
                    return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

# Convenience functions for backwards compatibility
def save_linkedin_profile(profile: LinkedInProfile) -> int:
    \"\"\"Save a single LinkedIn profile\"\"\"
    storage = LinkedInDatabaseStorage()
    return storage.save_profile(profile)

def save_linkedin_profiles(profiles: List[LinkedInProfile]) -> Dict[str, int]:
    \"\"\"Save multiple LinkedIn profiles\"\"\"
    storage = LinkedInDatabaseStorage()
    return storage.save_profiles_bulk(profiles)

def export_profiles_to_csv(output_file: str = None, **filters) -> str:
    \"\"\"Export profiles to CSV\"\"\"
    storage = LinkedInDatabaseStorage()
    return storage.export_to_csv(output_file, **filters)