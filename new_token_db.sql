CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE super_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT,
    status TEXT CHECK (status IN ('active','inactive')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE company_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    api_key TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE company_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK (role IN ('admin','agent')) NOT NULL,
    is_online BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(company_id, email)
);

CREATE TABLE end_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    end_user_id UUID REFERENCES end_users(id),
    status TEXT CHECK (status IN ('bot','human')) DEFAULT 'bot',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    sender TEXT CHECK (sender IN ('user','bot','agent')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding DOUBLE PRECISION[],  -- ✅ Temp
    created_by TEXT CHECK (created_by IN ('agent','admin','bot')),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE human_handover_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    agent_id UUID REFERENCES company_users(id),
    started_at TIMESTAMP DEFAULT now(),
    ended_at TIMESTAMP
);

-- Add--the--Total_token_used---
ALTER TABLE companies
ADD COLUMN total_tokens_used BIGINT DEFAULT 0;


ALTER TABLE companies
ADD COLUMN Token_Plan BIGINT DEFAULT 0;

------token_usage_logs----------

CREATE TABLE token_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),
    model TEXT NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens INT GENERATED ALWAYS AS 
        (prompt_tokens + completion_tokens) STORED,
    created_at TIMESTAMP DEFAULT now()
);


-- -AddING-VECTOR---------
ALTER TABLE knowledge_base
ADD COLUMN embedding vector(384),
DROP COLUMN embedding;


SELECT * FROM knowledge_base;
