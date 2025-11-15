-- =============================================================================
-- PostgreSQL Database Initialization Script
-- =============================================================================
--
-- Purpose: Initialize database schema for pharmaceutical test generation system
-- Execution: Runs ONCE on first container startup (when volume is empty)
-- Mount Point: /docker-entrypoint-initdb.d/01-init.sql (Postgres convention)
--
-- Tables Created:
-- 1. jobs           - Job tracking table (matches main/api/models.py::JobRecord)
-- 2. rag_documents  - RAG vector store (for pgvector adapter)
--
-- GAMP-5 Category 5: Development environment (mocks Aurora Data API)
-- ALCOA+ Principles: Development schema (enforced in production only)
--
-- Parity Note:
-- - Aurora Data API uses HTTP/JSON protocol (~50-100ms latency)
-- - Local Postgres uses binary protocol (~1-5ms latency)
-- - Schema identical, performance characteristics differ
--
-- =============================================================================

-- Print initialization banner
DO $$
BEGIN
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Pharmaceutical Test Generation - Database Init';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Database: testgen';
    RAISE NOTICE 'Environment: Development';
    RAISE NOTICE 'GAMP-5 Category: 5 (Custom Software)';
    RAISE NOTICE '';
END $$;

-- =============================================================================
-- Extension: pgvector for RAG vector similarity search
-- =============================================================================
-- Enable pgvector extension for vector embeddings (1536-dimensional)
-- Required for PostgreSQLAdapter in main/src/adapters/vector_store.py
-- Compatible with OpenAI text-embedding-3-small (1536 dims)

DO $$
BEGIN
    RAISE NOTICE '[1/3] Creating pgvector extension...';
END $$;

CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE '   ✓ pgvector extension ready';
    ELSE
        RAISE EXCEPTION '   ✗ Failed to create pgvector extension';
    END IF;
END $$;

-- =============================================================================
-- Table: jobs
-- =============================================================================
-- Tracks pharmaceutical test generation job lifecycle
-- Maps to: main/api/models.py::JobRecord
-- ALCOA+ Compliance:
-- - Attributable: user_id (Clerk user ID)
-- - Contemporaneous: created_at, started_at, completed_at (timestamptz)
-- - Original: urs_hash (SHA-256 of source URS file)
-- - Accurate: CHECK constraints enforce data integrity

DO $$
BEGIN
    RAISE NOTICE '[2/3] Creating jobs table...';
END $$;

CREATE TABLE IF NOT EXISTS jobs (
    -- Primary Key
    job_id UUID PRIMARY KEY,

    -- Job Status Lifecycle
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- ALCOA+ Timestamps (Contemporaneous)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- URS File Metadata (Original, Accurate)
    urs_filename VARCHAR(255) NOT NULL,
    urs_storage_key TEXT NOT NULL,  -- Storage adapter key (local path or S3 key)
    urs_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash for data integrity
    urs_size_bytes INTEGER NOT NULL CHECK (urs_size_bytes > 0),

    -- ALCOA+ Attribution
    user_id VARCHAR(255) NOT NULL,  -- Clerk user ID (sub claim from JWT)

    -- Job Results
    result_uri TEXT,  -- Storage key for generated test suite YAML

    -- GAMP-5 Categorization Result
    gamp_category VARCHAR(1)
        CHECK (gamp_category IN ('1', '3', '4', '5')),

    -- Error Tracking (explicit failure reporting - NO FALLBACKS)
    error_message TEXT,
    error_type VARCHAR(100),

    -- Retry Logic (SQS DLQ integration)
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0)
);

-- Performance Indexes
-- Index 1: User job queries (GET /jobs endpoint filtered by user_id)
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);

-- Index 2: Status queries (worker polls for 'pending' jobs)
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Index 3: Chronological queries (most recent jobs first)
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

DO $$
BEGIN
    RAISE NOTICE '   ✓ jobs table created with 3 indexes';
END $$;

-- =============================================================================
-- Table: rag_documents
-- =============================================================================
-- Vector store for pharmaceutical documentation embeddings
-- Used by: main/src/adapters/vector_store.py::PostgreSQLAdapter
-- Supports: RAG (Retrieval-Augmented Generation) for context injection

DO $$
BEGIN
    RAISE NOTICE '[3/3] Creating rag_documents table...';
END $$;

CREATE TABLE IF NOT EXISTS rag_documents (
    -- Primary Key (auto-generated UUID)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Document Content
    content TEXT NOT NULL,

    -- Vector Embedding (1536 dimensions)
    -- Matches EMBEDDING_DIMENSIONS=1536 in config
    -- Compatible with text-embedding-3-small model
    embedding vector(1536),

    -- Metadata (JSONB for flexible schema)
    -- Example: {"source": "GAMP-5.pdf", "page": 42, "section": "3.2"}
    metadata JSONB,

    -- ALCOA+ Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Vector Similarity Index (IVFFlat for approximate nearest neighbor search)
-- Index Type: ivfflat (Inverted File with Flat Quantizer)
-- Distance Metric: vector_cosine_ops (cosine similarity)
-- Lists Parameter: 100 (number of inverted lists - tuned for ~10k documents)
--
-- Performance:
-- - Query latency: ~5-20ms (vs ~100-200ms without index)
-- - Trade-off: Approximate results (99% recall @ 10 neighbors)
-- - Build time: ~1s per 1000 documents

CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding
    ON rag_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

DO $$
BEGIN
    RAISE NOTICE '   ✓ rag_documents table created with vector index';
END $$;

-- =============================================================================
-- Permissions
-- =============================================================================
-- Grant all privileges to postgres user (development environment)
-- Production: Use fine-grained IAM roles with least privilege

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- =============================================================================
-- Initialization Summary
-- =============================================================================
DO $$
DECLARE
    jobs_count INTEGER;
    rag_count INTEGER;
BEGIN
    -- Count initial rows (should be 0 on first run)
    SELECT COUNT(*) INTO jobs_count FROM jobs;
    SELECT COUNT(*) INTO rag_count FROM rag_documents;

    RAISE NOTICE '';
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Database Initialization Complete!';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created:';
    RAISE NOTICE '  ✓ jobs (% rows)', jobs_count;
    RAISE NOTICE '  ✓ rag_documents (% rows)', rag_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Extensions:';
    RAISE NOTICE '  ✓ pgvector (vector similarity search)';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes:';
    RAISE NOTICE '  ✓ idx_jobs_user_id (B-tree)';
    RAISE NOTICE '  ✓ idx_jobs_status (B-tree)';
    RAISE NOTICE '  ✓ idx_jobs_created_at (B-tree DESC)';
    RAISE NOTICE '  ✓ idx_rag_documents_embedding (IVFFlat cosine)';
    RAISE NOTICE '';
    RAISE NOTICE 'API/Worker containers can now connect!';
    RAISE NOTICE '  Connection: postgresql://postgres:devpassword@postgres:5432/testgen';
    RAISE NOTICE '';
    RAISE NOTICE '==================================================';
END $$;
