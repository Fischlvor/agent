-- 初始化数据库脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(255),
    bio TEXT,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_password_token VARCHAR(255),
    reset_password_expires TIMESTAMP,
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表字段注释
COMMENT ON TABLE users IS '用户信息表';
COMMENT ON COLUMN users.id IS '用户唯一标识符';
COMMENT ON COLUMN users.username IS '用户名，用于登录';
COMMENT ON COLUMN users.email IS '用户邮箱，用于登录和通知';
COMMENT ON COLUMN users.password_hash IS '密码哈希值';
COMMENT ON COLUMN users.full_name IS '用户全名';
COMMENT ON COLUMN users.avatar_url IS '用户头像URL';
COMMENT ON COLUMN users.bio IS '用户简介';
COMMENT ON COLUMN users.role IS '用户角色，如user、admin等';
COMMENT ON COLUMN users.is_active IS '用户是否激活';
COMMENT ON COLUMN users.is_verified IS '用户是否已验证邮箱';
COMMENT ON COLUMN users.verification_token IS '邮箱验证令牌';
COMMENT ON COLUMN users.reset_password_token IS '密码重置令牌';
COMMENT ON COLUMN users.reset_password_expires IS '密码重置令牌过期时间';
COMMENT ON COLUMN users.last_login_at IS '最后登录时间';
COMMENT ON COLUMN users.login_count IS '登录次数';
COMMENT ON COLUMN users.preferences IS '用户偏好设置，JSON格式';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.updated_at IS '更新时间';

-- 创建会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    description TEXT,
    status VARCHAR(20),
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    ai_model VARCHAR(50),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4000,
    context_data JSONB,
    system_prompt TEXT,
    metadata JSONB,
    tags JSONB
);

-- 会话表字段注释
COMMENT ON TABLE chat_sessions IS '聊天会话表';
COMMENT ON COLUMN chat_sessions.id IS '会话唯一标识符';
COMMENT ON COLUMN chat_sessions.session_id IS '会话外部ID，用于API引用';
COMMENT ON COLUMN chat_sessions.user_id IS '关联的用户ID';
COMMENT ON COLUMN chat_sessions.title IS '会话标题';
COMMENT ON COLUMN chat_sessions.description IS '会话描述';
COMMENT ON COLUMN chat_sessions.status IS '会话状态，如active、archived等';
COMMENT ON COLUMN chat_sessions.is_pinned IS '是否置顶';
COMMENT ON COLUMN chat_sessions.created_at IS '创建时间';
COMMENT ON COLUMN chat_sessions.updated_at IS '更新时间';
COMMENT ON COLUMN chat_sessions.last_activity_at IS '最后活动时间';
COMMENT ON COLUMN chat_sessions.message_count IS '消息数量';
COMMENT ON COLUMN chat_sessions.total_tokens IS '总令牌数';
COMMENT ON COLUMN chat_sessions.ai_model IS '使用的AI模型';
COMMENT ON COLUMN chat_sessions.temperature IS 'AI模型温度参数';
COMMENT ON COLUMN chat_sessions.max_tokens IS '最大令牌数限制';
COMMENT ON COLUMN chat_sessions.context_data IS '上下文数据，JSON格式';
COMMENT ON COLUMN chat_sessions.system_prompt IS '系统提示词';
COMMENT ON COLUMN chat_sessions.metadata IS '元数据，JSON格式';
COMMENT ON COLUMN chat_sessions.tags IS '标签，JSON格式';

-- 创建消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR UNIQUE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    parent_message_id VARCHAR,
    role VARCHAR(20),
    content TEXT,
    message_type VARCHAR(30),
    status VARCHAR(20),
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    model_name VARCHAR(50),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    generation_time FLOAT,
    structured_content JSONB,
    attachments JSONB,
    user_rating INTEGER,
    user_feedback TEXT,
    metadata JSONB,
    error_info JSONB
);

-- 消息表字段注释
COMMENT ON TABLE chat_messages IS '聊天消息表';
COMMENT ON COLUMN chat_messages.id IS '消息唯一标识符';
COMMENT ON COLUMN chat_messages.message_id IS '消息外部ID，用于API引用';
COMMENT ON COLUMN chat_messages.session_id IS '关联的会话ID';
COMMENT ON COLUMN chat_messages.parent_message_id IS '父消息ID，用于构建对话树';
COMMENT ON COLUMN chat_messages.role IS '消息角色，如user、assistant、system、tool';
COMMENT ON COLUMN chat_messages.content IS '消息内容';
COMMENT ON COLUMN chat_messages.message_type IS '消息类型，如text、image、file等';
COMMENT ON COLUMN chat_messages.status IS '消息状态，如pending、sent、delivered、read、failed等';
COMMENT ON COLUMN chat_messages.is_edited IS '是否已编辑';
COMMENT ON COLUMN chat_messages.is_deleted IS '是否已删除';
COMMENT ON COLUMN chat_messages.is_pinned IS '是否置顶';
COMMENT ON COLUMN chat_messages.created_at IS '创建时间';
COMMENT ON COLUMN chat_messages.updated_at IS '更新时间';
COMMENT ON COLUMN chat_messages.sent_at IS '发送时间';
COMMENT ON COLUMN chat_messages.delivered_at IS '送达时间';
COMMENT ON COLUMN chat_messages.read_at IS '已读时间';
COMMENT ON COLUMN chat_messages.model_name IS '使用的模型名称';
COMMENT ON COLUMN chat_messages.prompt_tokens IS '提示词令牌数';
COMMENT ON COLUMN chat_messages.completion_tokens IS '完成词令牌数';
COMMENT ON COLUMN chat_messages.total_tokens IS '总令牌数';
COMMENT ON COLUMN chat_messages.generation_time IS '生成时间（秒）';
COMMENT ON COLUMN chat_messages.structured_content IS '结构化内容，JSON格式';
COMMENT ON COLUMN chat_messages.attachments IS '附件信息，JSON格式';
COMMENT ON COLUMN chat_messages.user_rating IS '用户评分（1-5）';
COMMENT ON COLUMN chat_messages.user_feedback IS '用户反馈';
COMMENT ON COLUMN chat_messages.metadata IS '元数据，JSON格式';
COMMENT ON COLUMN chat_messages.error_info IS '错误信息，JSON格式';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_parent_message_id ON chat_messages(parent_message_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 添加更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为表添加更新时间触发器
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_messages_updated_at
    BEFORE UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 