-- Comprehensive Supabase Database Schema for Negotiation Agent
-- Run these commands in your Supabase SQL Editor

-- ==================== MAIN TABLES ====================

-- Table for storing negotiation sessions
CREATE TABLE IF NOT EXISTS negotiation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Brand Details (JSON)
    brand_details JSONB NOT NULL,
    
    -- Influencer Profile (JSON)
    influencer_profile JSONB NOT NULL,
    
    -- Session Status and Metadata
    status VARCHAR(50) NOT NULL DEFAULT 'initiated' CHECK (status IN ('initiated', 'in_progress', 'counter_offer', 'agreed', 'rejected', 'cancelled', 'contract_generated', 'archived')),
    negotiation_round INTEGER NOT NULL DEFAULT 1,
    
    -- Current Offer (JSON)
    current_offer JSONB,
    
    -- Counter Offers (JSON Array)
    counter_offers JSONB DEFAULT '[]'::jsonb,
    
    -- Agreed Terms (JSON)
    agreed_terms JSONB,
    
    -- Conversation History (JSON Array)
    conversation_history JSONB DEFAULT '[]'::jsonb,
    
    -- Deliverables (JSON Array)
    deliverables JSONB DEFAULT '[]'::jsonb,
    
    -- Payment Terms (JSON)
    payment_terms JSONB,
    
    -- Contract Terms (JSON)
    contract_terms JSONB,
    contract_id VARCHAR(255),
    
    -- Timestamps and Status
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Table for detailed operation logging
CREATE TABLE IF NOT EXISTS negotiation_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL CHECK (operation_type IN ('start', 'continue', 'deliverable_update', 'budget_change', 'contract_generation', 'archive', 'delete')),
    
    -- Operation details
    user_input TEXT,
    agent_response TEXT,
    
    -- Related data (JSON)
    brand_details JSONB,
    influencer_profile JSONB,
    deliverables JSONB,
    budget_info JSONB,
    
    -- Contract and status
    contract_id VARCHAR(255),
    status VARCHAR(50),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Foreign key
    FOREIGN KEY (session_id) REFERENCES negotiation_sessions(session_id) ON DELETE CASCADE
);

-- Table for individual conversation messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'agent')),
    content TEXT NOT NULL,
    
    -- Message metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Foreign key
    FOREIGN KEY (session_id) REFERENCES negotiation_sessions(session_id) ON DELETE CASCADE
);

-- Table for contracts
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    
    -- Contract data
    contract_data JSONB NOT NULL,
    
    -- Contract status
    status VARCHAR(50) NOT NULL DEFAULT 'pending_signatures' CHECK (status IN ('pending_signatures', 'brand_signed', 'influencer_signed', 'fully_executed', 'cancelled')),
    
    -- File storage
    pdf_url TEXT,
    html_content TEXT,
    
    -- Signatures
    brand_signature JSONB,
    influencer_signature JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    signed_at TIMESTAMPTZ,
    
    -- Foreign key
    FOREIGN KEY (session_id) REFERENCES negotiation_sessions(session_id) ON DELETE CASCADE
);

-- ==================== INDEXES FOR PERFORMANCE ====================

-- Indexes on negotiation_sessions
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_session_id ON negotiation_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_user_id ON negotiation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_status ON negotiation_sessions(status);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_is_active ON negotiation_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_created_at ON negotiation_sessions(created_at);

-- Indexes on negotiation_operations
CREATE INDEX IF NOT EXISTS idx_negotiation_operations_session_id ON negotiation_operations(session_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_operations_operation_type ON negotiation_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_negotiation_operations_timestamp ON negotiation_operations(timestamp);
CREATE INDEX IF NOT EXISTS idx_negotiation_operations_status ON negotiation_operations(status);

-- Indexes on conversation_messages
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_id ON conversation_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_message_type ON conversation_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);

-- Indexes on contracts
CREATE INDEX IF NOT EXISTS idx_contracts_contract_id ON contracts(contract_id);
CREATE INDEX IF NOT EXISTS idx_contracts_session_id ON contracts(session_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_created_at ON contracts(created_at);

-- ==================== TRIGGERS FOR AUTOMATIC UPDATES ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_negotiation_sessions_updated_at BEFORE UPDATE ON negotiation_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== ROW LEVEL SECURITY (RLS) ====================

-- Enable RLS on all tables
ALTER TABLE negotiation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE negotiation_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;

-- Policies for negotiation_sessions
CREATE POLICY "Users can view their own negotiation sessions" ON negotiation_sessions
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own negotiation sessions" ON negotiation_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can update their own negotiation sessions" ON negotiation_sessions
    FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete their own negotiation sessions" ON negotiation_sessions
    FOR DELETE USING (auth.uid() = user_id OR user_id IS NULL);

-- Policies for negotiation_operations (inherit from sessions)
CREATE POLICY "Users can view operations for their sessions" ON negotiation_operations
    FOR SELECT USING (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

CREATE POLICY "Users can insert operations for their sessions" ON negotiation_operations
    FOR INSERT WITH CHECK (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

-- Policies for conversation_messages (inherit from sessions)
CREATE POLICY "Users can view messages for their sessions" ON conversation_messages
    FOR SELECT USING (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

CREATE POLICY "Users can insert messages for their sessions" ON conversation_messages
    FOR INSERT WITH CHECK (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

-- Policies for contracts (inherit from sessions)
CREATE POLICY "Users can view contracts for their sessions" ON contracts
    FOR SELECT USING (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

CREATE POLICY "Users can insert contracts for their sessions" ON contracts
    FOR INSERT WITH CHECK (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

CREATE POLICY "Users can update contracts for their sessions" ON contracts
    FOR UPDATE USING (
        session_id IN (
            SELECT session_id FROM negotiation_sessions 
            WHERE auth.uid() = user_id OR user_id IS NULL
        )
    );

-- ==================== STORAGE BUCKETS ====================

-- Create storage bucket for contracts (run this separately in Supabase Storage)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('contracts', 'contracts', false);

-- Storage policies for contracts bucket
-- CREATE POLICY "Users can upload their own contract files" ON storage.objects
--     FOR INSERT WITH CHECK (bucket_id = 'contracts' AND auth.role() = 'authenticated');

-- CREATE POLICY "Users can view their own contract files" ON storage.objects
--     FOR SELECT USING (bucket_id = 'contracts' AND auth.role() = 'authenticated');

-- ==================== UTILITY VIEWS ====================

-- View for session analytics
CREATE OR REPLACE VIEW session_analytics AS
SELECT 
    ns.session_id,
    ns.status,
    ns.created_at,
    ns.updated_at,
    ns.negotiation_round,
    ns.is_active,
    ns.brand_details->>'name' AS brand_name,
    ns.influencer_profile->>'name' AS influencer_name,
    COUNT(DISTINCT no.id) AS total_operations,
    COUNT(DISTINCT cm.id) AS total_messages,
    COUNT(DISTINCT CASE WHEN cm.message_type = 'user' THEN cm.id END) AS user_messages,
    COUNT(DISTINCT CASE WHEN cm.message_type = 'agent' THEN cm.id END) AS agent_messages,
    COUNT(DISTINCT c.id) AS contract_count,
    EXTRACT(EPOCH FROM (ns.updated_at - ns.created_at)) / 3600 AS duration_hours
FROM negotiation_sessions ns
LEFT JOIN negotiation_operations no ON ns.session_id = no.session_id
LEFT JOIN conversation_messages cm ON ns.session_id = cm.session_id
LEFT JOIN contracts c ON ns.session_id = c.session_id
GROUP BY ns.session_id, ns.status, ns.created_at, ns.updated_at, ns.negotiation_round, ns.is_active, ns.brand_details, ns.influencer_profile;

-- View for operation analytics
CREATE OR REPLACE VIEW operation_analytics AS
WITH operation_intervals AS (
    SELECT 
        operation_type,
        session_id,
        timestamp,
        EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY session_id ORDER BY timestamp))) / 60 AS time_diff_minutes
    FROM negotiation_operations
)
SELECT 
    operation_type,
    COUNT(*) AS total_count,
    COUNT(DISTINCT session_id) AS unique_sessions,
    AVG(time_diff_minutes) AS avg_time_between_operations_minutes,
    MIN(time_diff_minutes) AS min_time_between_operations_minutes,
    MAX(time_diff_minutes) AS max_time_between_operations_minutes
FROM operation_intervals
WHERE time_diff_minutes IS NOT NULL
GROUP BY operation_type;

-- ==================== SAMPLE DATA (OPTIONAL) ====================

-- Uncomment to insert sample data for testing
/*
-- Sample negotiation session
INSERT INTO negotiation_sessions (
    session_id,
    brand_details,
    influencer_profile,
    status,
    metadata
) VALUES (
    'sample-session-001',
    '{
        "name": "TechCorp",
        "budget": 5000,
        "budget_currency": "USD",
        "goals": ["brand awareness", "product launch"],
        "target_platforms": ["instagram", "youtube"]
    }',
    '{
        "name": "Influencer Jane",
        "followers": 100000,
        "engagement_rate": 0.045,
        "location": "US",
        "platforms": ["instagram", "youtube"],
        "niches": ["technology", "lifestyle"]
    }',
    'in_progress',
    '{"test": true}'
);

-- Sample operation
INSERT INTO negotiation_operations (
    session_id,
    operation,
    operation_type,
    status,
    metadata
) VALUES (
    'sample-session-001',
    'session_created',
    'start',
    'success',
    '{"test": true}'
);
*/

-- ==================== COMPLETION MESSAGE ====================

DO $$
BEGIN
    RAISE NOTICE 'Negotiation Agent database schema created successfully!';
    RAISE NOTICE 'Tables created: negotiation_sessions, negotiation_operations, conversation_messages, contracts';
    RAISE NOTICE 'Indexes created for optimal performance';
    RAISE NOTICE 'Row Level Security (RLS) enabled with user-based policies';
    RAISE NOTICE 'Utility views created: session_analytics, operation_analytics';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Create storage bucket for contracts in Supabase Storage UI';
    RAISE NOTICE '2. Test the API endpoints with the provided curl scripts';
    RAISE NOTICE '3. Monitor performance with the analytics views';
END $$;
