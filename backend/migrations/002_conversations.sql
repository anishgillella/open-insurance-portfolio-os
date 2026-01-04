-- Open Insurance Phase 3: Conversations Migration
-- Run this directly in Supabase SQL Editor
-- Version: 002
-- Description: Creates conversations and messages tables for RAG chat functionality

-- ============================================================================
-- CONVERSATIONS
-- Chat conversations for RAG Q&A functionality.
-- ============================================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Optional organization scope (for future multi-tenancy)
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Conversation metadata
    title TEXT,

    -- Optional filters applied to this conversation
    property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,
    document_type TEXT,

    -- Stats
    message_count INTEGER DEFAULT 0,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_org ON conversations(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_property ON conversations(property_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_created ON conversations(created_at DESC) WHERE deleted_at IS NULL;

-- ============================================================================
-- MESSAGES
-- Individual messages within a conversation.
-- ============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Message content
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,

    -- For assistant messages: sources/citations
    sources JSONB DEFAULT '[]',

    -- For assistant messages: confidence and metrics
    confidence FLOAT,
    tokens_used INTEGER,
    latency_ms INTEGER,

    -- Model used for generation
    model TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(conversation_id, created_at);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update conversation message count on message insert
CREATE OR REPLACE FUNCTION update_conversation_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_message_count_on_insert
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_message_count();

-- Update conversations updated_at trigger
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "Service role has full access to conversations"
    ON conversations FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to messages"
    ON messages FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- DONE!
-- ============================================================================
-- Tables created:
-- 1. conversations - Chat conversation sessions
-- 2. messages - Individual messages within conversations
--
-- RLS enabled with service_role full access.
