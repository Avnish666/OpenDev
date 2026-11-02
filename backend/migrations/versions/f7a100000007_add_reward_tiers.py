"""Add reward tiers; no payment or entitlement records.

Revision ID: f7a100000007
Revises: ec107b8b4763
"""
from alembic import op
import sqlalchemy as sa

revision = 'f7a100000007'
down_revision = 'ec107b8b4763'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reward_tiers',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('benefits', sa.JSON(), nullable=False),
        sa.Column('quantity_limit', sa.BigInteger(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('price_cents > 0', name='ck_reward_price'),
        sa.CheckConstraint('quantity_limit IS NULL OR quantity_limit > 0', name='ck_reward_quantity'),
        sa.CheckConstraint("currency = 'USD'", name='ck_reward_currency'))
    op.create_index('ix_reward_tiers_project_id', 'reward_tiers', ['project_id'])
    op.create_index('uq_reward_project_name', 'reward_tiers', ['project_id', sa.text('lower(trim(name))')], unique=True)


def downgrade():
    raise RuntimeError('Destructive rollback is prohibited; use a reviewed forward migration')
