-- Run this in your Supabase SQL editor to create the audits table
-- https://supabase.com/dashboard/project/_/sql

CREATE TABLE IF NOT EXISTS seo_audits (
    id                  BIGSERIAL PRIMARY KEY,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    url                 TEXT NOT NULL,
    email               TEXT NOT NULL,
    domain              TEXT,
    overall_score       INT,
    seo_score           INT,
    content_score       INT,
    ai_score            INT,
    opportunity_score   INT,
    overall_grade       TEXT,
    fetch_time_ms       INT,
    error               TEXT
);

-- Index for lead lookups by email
CREATE INDEX IF NOT EXISTS idx_seo_audits_email ON seo_audits (email);
CREATE INDEX IF NOT EXISTS idx_seo_audits_domain ON seo_audits (domain);
CREATE INDEX IF NOT EXISTS idx_seo_audits_created ON seo_audits (created_at DESC);

-- Enable Row Level Security (recommended)
ALTER TABLE seo_audits ENABLE ROW LEVEL SECURITY;

-- Allow insert from anon key (your app writes with the anon key)
CREATE POLICY "Allow insert" ON seo_audits
    FOR INSERT TO anon WITH CHECK (true);

-- Block public reads (admin only via service_role key)
CREATE POLICY "Block public select" ON seo_audits
    FOR SELECT TO anon USING (false);
