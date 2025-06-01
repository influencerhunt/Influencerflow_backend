#!/usr/bin/env python3
"""
Database setup script for InfluencerFlow Backend
This script creates the influencers table and inserts sample data
"""

import psycopg2
from decouple import config
import sys

def setup_database():
    """Set up the database schema and sample data"""
    
    # Get database URL from environment
    database_url = config("DATABASE_URL", default="")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    try:
        # Connect to PostgreSQL
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read and execute schema
        print("📝 Creating influencers table...")
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS influencers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                username VARCHAR(255) NOT NULL,
                platform VARCHAR(50) NOT NULL CHECK (platform IN ('instagram', 'youtube', 'tiktok', 'twitter', 'linkedin', 'facebook')),
                followers INTEGER NOT NULL DEFAULT 0,
                engagement_rate DECIMAL(5,2),
                price_per_post INTEGER,
                location VARCHAR(255),
                niche VARCHAR(255),
                bio TEXT,
                profile_link VARCHAR(500),
                avatar_url VARCHAR(500),
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create indexes
        print("📊 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_influencers_platform ON influencers(platform);",
            "CREATE INDEX IF NOT EXISTS idx_influencers_followers ON influencers(followers);",
            "CREATE INDEX IF NOT EXISTS idx_influencers_location ON influencers(location);",
            "CREATE INDEX IF NOT EXISTS idx_influencers_niche ON influencers(niche);",
            "CREATE INDEX IF NOT EXISTS idx_influencers_price ON influencers(price_per_post);",
            "CREATE INDEX IF NOT EXISTS idx_influencers_verified ON influencers(verified);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_influencers_username_platform ON influencers(username, platform);"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Enable RLS
        print("🔒 Enabling Row Level Security...")
        cursor.execute("ALTER TABLE influencers ENABLE ROW LEVEL SECURITY;")
        
        # Create RLS policy
        cursor.execute("""
            DROP POLICY IF EXISTS "Public read access on influencers" ON influencers;
            CREATE POLICY "Public read access on influencers" ON influencers
                FOR SELECT USING (true);
        """)
        
        # Insert sample data
        print("📊 Inserting sample data...")
        sample_data = [
            ('Sarah Fashion', 'sarahfashion', 'instagram', 125000, 3.5, 850, 'New York, NY', 'fashion', 'Fashion blogger and style influencer based in NYC', True),
            ('TechGuru Mike', 'techgurumike', 'youtube', 250000, 4.2, 1500, 'San Francisco, CA', 'tech', 'Technology reviews and tutorials', True),
            ('FitLife Anna', 'fitlifeanna', 'instagram', 80000, 5.1, 600, 'Los Angeles, CA', 'fitness', 'Fitness coach and wellness advocate', False),
            ('FoodieExplorer', 'foodieexplorer', 'tiktok', 45000, 6.8, 300, 'Chicago, IL', 'food', 'Exploring the best food spots around the world', False),
            ('Travel With Tom', 'travelwithtom', 'youtube', 180000, 3.8, 1200, 'Denver, CO', 'travel', 'Adventure travel and outdoor experiences', True),
            ('Beauty Guru Lisa', 'beautyguruuisa', 'instagram', 95000, 4.7, 750, 'Miami, FL', 'beauty', 'Makeup tutorials and beauty product reviews', True),
            ('Fitness Beast', 'fitnessbeast', 'tiktok', 67000, 7.2, 400, 'Austin, TX', 'fitness', 'High-intensity workouts and nutrition tips', False),
            ('Gaming Pro Alex', 'gamingproalex', 'youtube', 340000, 3.9, 2000, 'Seattle, WA', 'gaming', 'Gaming reviews, streams and esports content', True),
            ('Cooking Mama', 'cookingmama', 'instagram', 150000, 4.5, 900, 'Portland, OR', 'food', 'Home cooking recipes and kitchen tips', True),
            ('Style Icon', 'styleicon', 'tiktok', 89000, 6.1, 550, 'Los Angeles, CA', 'fashion', 'Street style and fashion trends', False)
        ]
        
        cursor.executemany("""
            INSERT INTO influencers (name, username, platform, followers, engagement_rate, price_per_post, location, niche, bio, verified) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username, platform) DO NOTHING;
        """, sample_data)
        
        # Commit changes
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM influencers;")
        count = cursor.fetchone()[0]
        
        print(f"✅ Database setup complete!")
        print(f"📊 Total influencers in database: {count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
