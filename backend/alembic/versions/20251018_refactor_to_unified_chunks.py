"""refactor to unified chunks table

Revision ID: 20251018_refactor
Revises: 20251012_add_knowledge_base_tables
Create Date: 2025-10-18 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20251018_refactor'
down_revision = '20251012_kb_001'
branch_labels = None
depends_on = None


def upgrade():
    """统一chunks表，支持父子分块"""

    # 创建新的document_chunks表
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键'),
        sa.Column('doc_id', sa.Integer(), nullable=False, comment='所属文档ID'),
        sa.Column('parent_id', sa.Integer(), nullable=True, comment='父块ID（NULL表示是parent chunk）'),
        sa.Column('content', sa.Text(), nullable=False, comment='块内容'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='块序号'),
        sa.Column('chunk_type', sa.Enum('PARENT', 'CHILD', name='chunktype'), nullable=False, comment='块类型'),

        # Embedding相关（只有child chunk有）
        sa.Column('embedding', sa.LargeBinary(), nullable=True, comment='向量表示（序列化）'),
        sa.Column('embedding_model', sa.String(100), nullable=True, comment='Embedding模型'),

        # 位置信息
        sa.Column('page_number', sa.Integer(), nullable=True, comment='页码（PDF特有）'),
        sa.Column('section_title', sa.String(500), nullable=True, comment='所在章节'),

        # 统计信息
        sa.Column('token_count', sa.Integer(), nullable=True, comment='Token数量'),
        sa.Column('char_count', sa.Integer(), nullable=True, comment='字符数量'),

        # 元数据
        sa.Column('metadata', sa.JSON(), nullable=True, comment='扩展元数据'),

        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['document_chunks.id'], ondelete='CASCADE'),

        # 索引
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 创建索引
    op.create_index('idx_document_chunks_doc_id', 'document_chunks', ['doc_id'])
    op.create_index('idx_document_chunks_parent_id', 'document_chunks', ['parent_id'])
    op.create_index('idx_document_chunks_type', 'document_chunks', ['chunk_type'])
    op.create_index('idx_document_chunks_page', 'document_chunks', ['page_number'])

    # 唯一性约束：防止重复插入
    op.create_index('idx_document_chunks_unique', 'document_chunks', ['doc_id', 'chunk_type', 'chunk_index'], unique=True)


def downgrade():
    """回滚：不支持，因为新旧表结构差异太大"""
    raise NotImplementedError("暂不支持降级，请手动恢复数据库")

