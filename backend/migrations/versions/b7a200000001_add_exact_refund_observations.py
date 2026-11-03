"""Add immutable authoritative refund observations without historical backfill.

Revision ID: b7a200000001
Revises: 8c6072dabc59
"""
from alembic import op
import sqlalchemy as sa

revision = 'b7a200000001'
down_revision = '8c6072dabc59'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contributions',sa.Column('refund_total_cents',sa.BigInteger(),nullable=True))
    op.create_check_constraint('ck_contribution_refund_total','contributions',
        'refund_total_cents IS NULL OR (refund_total_cents >= 0 AND refund_total_cents <= amount_cents)')
    op.create_table('paypal_refunds',
        sa.Column('id',sa.String(64),primary_key=True),
        sa.Column('contribution_id',sa.String(36),sa.ForeignKey('contributions.id'),nullable=False),
        sa.Column('capture_id',sa.String(64),nullable=False),
        sa.Column('event_id',sa.String(128),sa.ForeignKey('paypal_events.id'),nullable=False),
        sa.Column('amount_cents',sa.BigInteger(),nullable=False),
        sa.Column('currency',sa.String(3),nullable=False),
        sa.Column('provider_total_cents',sa.BigInteger(),nullable=True),
        sa.Column('observed_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.CheckConstraint('amount_cents > 0',name='ck_refund_amount'),
        sa.CheckConstraint('provider_total_cents IS NULL OR provider_total_cents >= amount_cents',name='ck_refund_provider_total'))
    op.create_index('ix_paypal_refunds_contribution_id','paypal_refunds',['contribution_id'])
    op.execute('''CREATE FUNCTION protect_paypal_refund() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE c contributions%ROWTYPE; recorded numeric;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'Refund observations are append-only'; END IF;
      SELECT * INTO c FROM contributions WHERE id=NEW.contribution_id FOR UPDATE;
      IF NOT FOUND OR c.capture_id IS DISTINCT FROM NEW.capture_id OR c.currency <> NEW.currency
         OR c.status NOT IN ('refunded','reversed') THEN
        RAISE EXCEPTION 'Refund capture binding mismatch';
      END IF;
      SELECT coalesce(sum(amount_cents),0)+NEW.amount_cents INTO recorded
        FROM paypal_refunds WHERE contribution_id=NEW.contribution_id;
      IF recorded > c.amount_cents OR NEW.provider_total_cents > c.amount_cents THEN
        RAISE EXCEPTION 'Refund total exceeds capture';
      END IF;
      IF c.refund_total_cents IS NOT NULL OR NEW.provider_total_cents IS NOT NULL THEN
        UPDATE contributions SET refund_total_cents=greatest(coalesce(c.refund_total_cents,0),
          coalesce(NEW.provider_total_cents,0),recorded) WHERE id=c.id;
      END IF;
      RETURN NEW;
    END $$''')
    op.execute('CREATE TRIGGER paypal_refund_guard BEFORE INSERT OR UPDATE OR DELETE ON paypal_refunds FOR EACH ROW EXECUTE FUNCTION protect_paypal_refund()')
    op.execute('''CREATE FUNCTION protect_refunded_contribution() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.refund_total_cents IS NOT NULL AND (NEW.refund_total_cents IS NULL OR NEW.refund_total_cents < OLD.refund_total_cents) THEN
        RAISE EXCEPTION 'Refund totals cannot decrease';
      END IF;
      IF EXISTS (SELECT 1 FROM paypal_refunds WHERE contribution_id=OLD.id) AND
        (NEW.capture_id IS DISTINCT FROM OLD.capture_id OR NEW.currency <> OLD.currency OR NEW.amount_cents <> OLD.amount_cents
         OR NEW.status NOT IN ('refunded','reversed')) THEN
        RAISE EXCEPTION 'Refund capture binding is immutable';
      END IF;
      RETURN NEW;
    END $$''')
    op.execute('CREATE TRIGGER refunded_contribution_guard BEFORE UPDATE ON contributions FOR EACH ROW EXECUTE FUNCTION protect_refunded_contribution()')


def downgrade():
    raise RuntimeError('Refund audit data is irreversible; recover using an approved backup/forward fix, not a destructive downgrade')
