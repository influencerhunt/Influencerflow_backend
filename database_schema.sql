-- Supabase SQL Schema for Influencers Table
-- Run this in your Supabase SQL Editor to create the influencers table

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

-- Create indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_influencers_platform ON influencers(platform);
CREATE INDEX IF NOT EXISTS idx_influencers_followers ON influencers(followers);
CREATE INDEX IF NOT EXISTS idx_influencers_location ON influencers(location);
CREATE INDEX IF NOT EXISTS idx_influencers_niche ON influencers(niche);
CREATE INDEX IF NOT EXISTS idx_influencers_price ON influencers(price_per_post);
CREATE INDEX IF NOT EXISTS idx_influencers_verified ON influencers(verified);

-- Create unique constraint for username + platform combination
CREATE UNIQUE INDEX IF NOT EXISTS idx_influencers_username_platform ON influencers(username, platform);

-- Enable Row Level Security (RLS)
ALTER TABLE influencers ENABLE ROW LEVEL SECURITY;

-- Create policies for RLS (adjust based on your auth requirements)
CREATE POLICY "Public read access on influencers" ON influencers
    FOR SELECT USING (true);

-- Optional: Insert some sample data
INSERT INTO influencers (name, username, platform, followers, engagement_rate, price_per_post, location, niche, bio, verified) VALUES
('Sarah Fashion', 'sarahfashion', 'instagram', 125000, 3.5, 850, 'New York, NY', 'fashion', 'Fashion blogger and style influencer based in NYC', true),
('TechGuru Mike', 'techgurumike', 'youtube', 250000, 4.2, 1500, 'San Francisco, CA', 'tech', 'Technology reviews and tutorials', true),
('FitLife Anna', 'fitlifeanna', 'instagram', 80000, 5.1, 600, 'Los Angeles, CA', 'fitness', 'Fitness coach and wellness advocate', false),
('FoodieExplorer', 'foodieexplorer', 'tiktok', 45000, 6.8, 300, 'Chicago, IL', 'food', 'Exploring the best food spots around the world', false),
('Travel With Tom', 'travelwithtom', 'youtube', 180000, 3.8, 1200, 'Denver, CO', 'travel', 'Adventure travel and outdoor experiences', true)
ON CONFLICT (username, platform) DO NOTHING;
