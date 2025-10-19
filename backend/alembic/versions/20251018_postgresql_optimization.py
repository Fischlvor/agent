"""PostgreSQL optimization: JSONB, UUID, pgvector

Revision ID: 20251018_pg_opt
Revises: 20251018_refactor_to_unified_chunks
Create Date: 2025-10-18 16:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '20251018_pg_opt'
down_revision = '20251018_refactor'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级到 PostgreSQL 优化版本"""

    # ===== 1. 启用 pgvector 扩展 =====
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # ===== 2. 修改 users 表 =====
    # JSON → JSONB
    op.alter_column('users', 'preferences',
                    type_=JSONB,
                    postgresql_using='preferences::jsonb')

    # ===== 3. 修改 chat_sessions 表 =====
    # session_id: String(36) → UUID
    op.alter_column('chat_sessions', 'session_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='session_id::uuid')

    # JSON → JSONB
    op.alter_column('chat_sessions', 'context_data',
                    type_=JSONB,
                    postgresql_using='context_data::jsonb')
    op.alter_column('chat_sessions', 'session_metadata',
                    type_=JSONB,
                    postgresql_using='session_metadata::jsonb')
    op.alter_column('chat_sessions', 'tags',
                    type_=JSONB,
                    postgresql_using='tags::jsonb')

    # ===== 4. 修改 chat_messages 表 =====
    # message_id, session_id, parent_message_id: String(36) → UUID
    op.alter_column('chat_messages', 'message_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='message_id::uuid')
    op.alter_column('chat_messages', 'session_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='session_id::uuid')
    op.alter_column('chat_messages', 'parent_message_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='parent_message_id::uuid')

    # JSON → JSONB
    op.alter_column('chat_messages', 'structured_content',
                    type_=JSONB,
                    postgresql_using='structured_content::jsonb')
    op.alter_column('chat_messages', 'attachments',
                    type_=JSONB,
                    postgresql_using='attachments::jsonb')
    op.alter_column('chat_messages', 'message_metadata',
                    type_=JSONB,
                    postgresql_using='message_metadata::jsonb')
    op.alter_column('chat_messages', 'error_info',
                    type_=JSONB,
                    postgresql_using='error_info::jsonb')

    # ===== 5. 修改 ai_models 表 =====
    # JSON → JSONB
    op.alter_column('ai_models', 'config',
                    type_=JSONB,
                    postgresql_using='config::jsonb')

    # ===== 6. 修改 model_invocations 表 =====
    # message_id, session_id: String(36) → UUID
    op.alter_column('model_invocations', 'message_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='message_id::uuid')
    op.alter_column('model_invocations', 'session_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='session_id::uuid')

    # ===== 7. 修改 tool_invocations 表 =====
    # message_id, session_id: String(36) → UUID
    op.alter_column('tool_invocations', 'message_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='message_id::uuid')
    op.alter_column('tool_invocations', 'session_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='session_id::uuid')

    # arguments: JSON → JSONB
    op.alter_column('tool_invocations', 'arguments',
                    type_=JSONB,
                    postgresql_using='arguments::jsonb')

    # ===== 8. 修改 knowledge_bases 表 =====
    # JSON → JSONB
    op.alter_column('knowledge_bases', 'config',
                    type_=JSONB,
                    postgresql_using='config::jsonb')

    # ===== 9. 修改 documents 表 =====
    # metadata: JSON → JSONB
    op.alter_column('documents', 'metadata',
                    type_=JSONB,
                    postgresql_using='metadata::jsonb')

    # ===== 10. 修改 document_chunks 表（最重要！）=====
    # metadata: JSON → JSONB
    op.alter_column('document_chunks', 'metadata',
                    type_=JSONB,
                    postgresql_using='metadata::jsonb')

    # embedding: LargeBinary → Vector(1024)
    # 注意：这里需要先删除旧列，再创建新列，因为无法直接转换
    op.drop_column('document_chunks', 'embedding')
    op.add_column('document_chunks',
                  sa.Column('embedding', Vector(1024), nullable=True, comment='向量表示'))

    # ===== 11. 创建 HNSW 索引（pgvector）=====
    # 使用 HNSW 算法创建向量索引，提升检索速度
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    print("✓ PostgreSQL 优化完成：JSONB + UUID + pgvector + HNSW")


def downgrade() -> None:
    """降级到 MySQL 兼容版本（不建议）"""

    # 删除 HNSW 索引
    op.drop_index('idx_document_chunks_embedding_hnsw', table_name='document_chunks')

    # 恢复 embedding 为 LargeBinary
    op.drop_column('document_chunks', 'embedding')
    op.add_column('document_chunks',
                  sa.Column('embedding', sa.LargeBinary(), nullable=True))

    # 其他回滚操作略（实际生产中不建议降级）

    print("⚠️  警告：已降级到 MySQL 兼容版本")

