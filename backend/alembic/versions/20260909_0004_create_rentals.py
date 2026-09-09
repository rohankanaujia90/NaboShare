"""Create rental requests with protected history and booking indexes."""

import sqlalchemy as sa
from alembic import op

revision = "20260909_0004"
down_revision = "20260909_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rental_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("borrower_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rental_amount", sa.Numeric(16, 2), nullable=False),
        sa.Column("platform_fee", sa.Numeric(16, 2), nullable=False),
        sa.Column("security_deposit", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(16), server_default="PENDING", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_date > start_date", name="ck_rentals_dates"),
        sa.CheckConstraint("borrower_id <> owner_id", name="ck_rentals_not_self"),
        sa.CheckConstraint("rental_amount >= 0 AND platform_fee >= 0 AND security_deposit >= 0", name="ck_rentals_amounts"),
        sa.CheckConstraint("status IN ('PENDING','ACCEPTED','REJECTED','ACTIVE','RETURNED','CANCELLED')", name="ck_rentals_status"),
    )
    op.create_index("ix_rental_requests_borrower_id", "rental_requests", ["borrower_id"])
    op.create_index("ix_rental_requests_owner_id", "rental_requests", ["owner_id"])
    op.create_index("ix_rentals_item_booking", "rental_requests", ["item_id", "status", "start_date", "end_date"])


def downgrade() -> None:
    op.drop_table("rental_requests")
