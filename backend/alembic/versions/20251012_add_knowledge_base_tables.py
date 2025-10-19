"""add knowledge base tables

Revision ID: 20251012_kb_001
Revises: f9405fbfc7c1
Create Date: 2025-10-12 14:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20251012_kb_001'
down_revision = 'f9405fbfc7c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建知识库表
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='知识库名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='知识库描述'),
        sa.Column('config', sa.JSON(), nullable=True, comment='配置信息：分块参数、模型设置等'),
        sa.Column('doc_count', sa.Integer(), nullable=True, default=0, comment='文档数量'),
        sa.Column('chunk_count', sa.Integer(), nullable=True, default=0, comment='分块总数'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_kb_name', 'knowledge_bases', ['name'])

    # 创建文档表
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('kb_id', sa.Integer(), nullable=False, comment='所属知识库'),
        sa.Column('filename', sa.String(length=255), nullable=False, comment='文件名'),
        sa.Column('filepath', sa.String(length=500), nullable=False, comment='文件路径'),
        sa.Column('filesize', sa.BigInteger(), nullable=True, comment='文件大小（字节）'),
        sa.Column('filehash', sa.String(length=64), nullable=True, comment='文件SHA256哈希'),
        sa.Column('mimetype', sa.String(length=100), nullable=True, default='application/pdf', comment='文件类型'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='文档元数据：标题、作者、摘要等'),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='documentstatus'), nullable=False, comment='处理状态'),
        sa.Column('error_msg', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('page_count', sa.Integer(), nullable=True, comment='页数'),
        sa.Column('chunk_count', sa.Integer(), nullable=True, default=0, comment='分块数量'),
        sa.Column('parent_chunk_count', sa.Integer(), nullable=True, default=0, comment='父块数量'),
        sa.Column('char_count', sa.Integer(), nullable=True, comment='字符总数'),
        sa.Column('processed_at', sa.DateTime(), nullable=True, comment='处理完成时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['kb_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_doc_kb_id', 'documents', ['kb_id'])
    op.create_index('idx_doc_status', 'documents', ['status'])
    op.create_index('idx_doc_kb_hash', 'documents', ['kb_id', 'filehash'], unique=True)

    # 创建父块表
    op.create_table(
        'parent_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=False, comment='所属文档'),
        sa.Column('parent_text', sa.Text(), nullable=False, comment='父块文本（2048 tokens）'),
        sa.Column('parent_index', sa.Integer(), nullable=False, comment='父块序号'),
        sa.Column('page_number', sa.Integer(), nullable=True, comment='页码'),
        sa.Column('section_title', sa.String(length=500), nullable=True, comment='所在章节'),
        sa.Column('token_count', sa.Integer(), nullable=True, comment='Token 数量'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_parent_doc_id', 'parent_chunks', ['doc_id'])
    op.create_index('idx_parent_section', 'parent_chunks', ['section_title'])

    # 创建子块表
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=False, comment='所属文档'),
        sa.Column('parent_chunk_id', sa.Integer(), nullable=False, comment='所属父块'),
        sa.Column('chunk_text', sa.Text(), nullable=False, comment='子块文本（512 tokens）'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='子块序号（在父块内）'),
        sa.Column('token_count', sa.Integer(), nullable=True, comment='Token 数量'),
        sa.Column('embedding', sa.LargeBinary(), nullable=True, comment='向量表示（序列化）'),
        sa.Column('embedding_model', sa.String(length=100), nullable=True, default='BAAI/bge-m3', comment='Embedding 模型'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_chunk_id'], ['parent_chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_chunk_doc_id', 'document_chunks', ['doc_id'])
    op.create_index('idx_chunk_parent_id', 'document_chunks', ['parent_chunk_id'])
    op.create_index('idx_chunk_index', 'document_chunks', ['chunk_index'])


def downgrade() -> None:
    # 删除表（按依赖顺序反向删除）
    op.drop_table('document_chunks')
    op.drop_table('parent_chunks')
    op.drop_table('documents')
    op.drop_table('knowledge_bases')


