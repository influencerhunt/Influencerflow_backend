-- Add brand_id and inf_id columns to negotiation_sessions table
-- Run this in your Supabase SQL Editor

-- Add brand_id and inf_id columns
ALTER TABLE negotiation_sessions 
ADD COLUMN IF NOT EXISTS brand_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS inf_id VARCHAR(255);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_brand_id ON negotiation_sessions(brand_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_inf_id ON negotiation_sessions(inf_id);

-- Add a composite index for brand_id and inf_id together
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_brand_inf ON negotiation_sessions(brand_id, inf_id);

-- Update existing records to extract brand_id and inf_id from JSON
UPDATE negotiation_sessions 
SET 
    brand_id = brand_details->>'brand_id',
    inf_id = influencer_profile->>'inf_id'
WHERE brand_id IS NULL OR inf_id IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN negotiation_sessions.brand_id IS 'Brand identifier for easier querying and relationships';
COMMENT ON COLUMN negotiation_sessions.inf_id IS 'Influencer identifier for easier querying and relationships';
