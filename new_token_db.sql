-- ==============================
-- EXTENSIONS
-- ==============================
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- ==============================
-- SUPER ADMINS
-- ==============================
CREATE TABLE super_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- PLANS TABLE
-- ==============================
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,              -- Free, Starter, Pro, Enterprise
    description TEXT,

    monthly_token_limit BIGINT NOT NULL,    -- e.g. 100k, 1M, 10M
    price_monthly NUMERIC(10,2) NOT NULL,   -- billing amount

    max_agents INT DEFAULT 1,
    human_handover BOOLEAN DEFAULT FALSE,
    knowledge_base BOOLEAN DEFAULT TRUE,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- COMPANIES (TENANTS)
-- ==============================
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT,
    status TEXT CHECK (status IN ('active','inactive')) DEFAULT 'inactive',

    -- Billing
    total_tokens_used BIGINT DEFAULT 0,
    plan_id UUID REFERENCES plans(id) ON DELETE RESTRICT NOT NULL,
	
    created_at TIMESTAMP DEFAULT now()
);


-- ==============================
-- COMPANY API KEYS (CHAT WIDGET)
-- ==============================
CREATE TABLE company_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- COMPANY USERS (ADMINS / AGENTS)
-- ==============================
CREATE TABLE company_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK (role IN ('admin','agent')) NOT NULL,
    is_online BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(company_id, email)
);

-- ==============================
-- END USERS (WEBSITE VISITORS)
-- ==============================
CREATE TABLE end_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- CONVERSATIONS
-- ==============================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) NOT NULL,
    end_user_id UUID REFERENCES end_users(id),
    status TEXT CHECK (status IN ('bot','human')) DEFAULT 'bot',
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- MESSAGES
-- ==============================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
    sender TEXT CHECK (sender IN ('user','bot','agent')) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- KNOWLEDGE BASE (VECTOR SEARCH)
-- ==============================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding vector(384),
    created_by TEXT CHECK (created_by IN ('agent','admin','bot')),
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- HUMAN HANDOVER LOGS
-- ==============================
CREATE TABLE human_handover_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
    agent_id UUID REFERENCES company_users(id) NOT NULL,
    started_at TIMESTAMP DEFAULT now(),
    ended_at TIMESTAMP
);

-- ==============================
-- TOKEN USAGE LOGS (BILLING LEDGER)
-- ==============================
CREATE TABLE token_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),
    model TEXT NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens INT GENERATED ALWAYS AS
        (prompt_tokens + completion_tokens) STORED,
    created_at TIMESTAMP DEFAULT now()
);

-- ==============================
-- INDEXES (VERY IMPORTANT)
-- ==============================
CREATE INDEX idx_company_users_company ON company_users(company_id);
CREATE INDEX idx_end_users_company ON end_users(company_id);
CREATE INDEX idx_conversations_company ON conversations(company_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_kb_company ON knowledge_base(company_id);
CREATE INDEX idx_token_company ON token_usage_logs(company_id);
CREATE INDEX idx_token_created ON token_usage_logs(created_at);

-- Vector index (after inserting some data)
CREATE INDEX idx_kb_embedding
ON knowledge_base
USING ivfflat (embedding vector_cosine_ops);

DROP Table company_api_keys CASCADE;


-- ==============================
-- DROP TABLES (DEPENDENCY SAFE)
-- ==============================

DROP TABLE IF EXISTS
    token_usage_logs,
    human_handover_logs,
    knowledge_base,
    messages,
    conversations,
    end_users,
    company_users,
    company_api_keys,
    companies,
    plans,
    super_admins
CASCADE;

