-- Create negotiation_sessions table for storing chat sessions in Supabase
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS negotiation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Brand Details (JSON)
    brand_details JSONB NOT NULL,
    
    -- Influencer Profile (JSON)
    influencer_profile JSONB NOT NULL,
    
    -- Session Status and Metadata
    status VARCHAR(50) NOT NULL DEFAULT 'initiated' CHECK (status IN ('initiated', 'in_progress', 'counter_offer', 'agreed', 'rejected', 'cancelled')),
    negotiation_round INTEGER NOT NULL DEFAULT 1,
    
    -- Current Offer (JSON)
    current_offer JSONB,
    
    -- Counter Offers (JSON Array)
    counter_offers JSONB DEFAULT '[]'::jsonb,
    
    -- Agreed Terms (JSON)
    agreed_terms JSONB,
    
    -- Conversation History (JSON Array)
    conversation_history JSONB DEFAULT '[]'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_session_id ON negotiation_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_user_id ON negotiation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_status ON negotiation_sessions(status);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_created_at ON negotiation_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_last_activity ON negotiation_sessions(last_activity_at);

-- Create or replace the update trigger for updated_at
CREATE OR REPLACE FUNCTION update_negotiation_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.last_activity_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_negotiation_sessions_updated_at ON negotiation_sessions;
CREATE TRIGGER update_negotiation_sessions_updated_at
    BEFORE UPDATE ON negotiation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_negotiation_sessions_updated_at();

-- Enable RLS
ALTER TABLE negotiation_sessions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own sessions" ON negotiation_sessions;
DROP POLICY IF EXISTS "Users can update own sessions" ON negotiation_sessions;
DROP POLICY IF EXISTS "Users can insert own sessions" ON negotiation_sessions;
DROP POLICY IF EXISTS "Users can delete own sessions" ON negotiation_sessions;

-- Create RLS policies
-- Users can only view their own negotiation sessions
CREATE POLICY "Users can view own sessions" ON negotiation_sessions
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only update their own negotiation sessions
CREATE POLICY "Users can update own sessions" ON negotiation_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only insert their own negotiation sessions
CREATE POLICY "Users can insert own sessions" ON negotiation_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own negotiation sessions
CREATE POLICY "Users can delete own sessions" ON negotiation_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Grant necessary permissions
GRANT ALL ON negotiation_sessions TO postgres;
GRANT ALL ON negotiation_sessions TO service_role;
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON negotiation_sessions TO anon;

-- Create function to clean up old sessions (optional)
CREATE OR REPLACE FUNCTION cleanup_old_negotiation_sessions()
RETURNS void AS $$
BEGIN
    -- Delete sessions older than 30 days with no activity
    DELETE FROM negotiation_sessions 
    WHERE last_activity_at < NOW() - INTERVAL '30 days'
    AND status IN ('rejected', 'cancelled');
    
    -- Optionally archive completed sessions older than 90 days
    -- (You could move these to an archive table instead of deleting)
END;
$$ language 'plpgsql';

-- Create a view for session summaries (optional but useful)
CREATE OR REPLACE VIEW negotiation_session_summaries AS
SELECT 
    id,
    session_id,
    user_id,
    brand_details->>'name' as brand_name,
    influencer_profile->>'name' as influencer_name,
    status,
    negotiation_round,
    jsonb_array_length(conversation_history) as message_count,
    created_at,
    updated_at,
    last_activity_at
FROM negotiation_sessions;

-- Grant permissions on the view
GRANT SELECT ON negotiation_session_summaries TO anon;
GRANT SELECT ON negotiation_session_summaries TO postgres;
GRANT SELECT ON negotiation_session_summaries TO service_role;
