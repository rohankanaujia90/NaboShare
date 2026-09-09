"""Create community-scoped item listings."""

import sqlalchemy as sa
from alembic import op

revision = "20260909_0003"
down_revision = "20260907_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("community_id", sa.Uuid(), sa.ForeignKey("communities.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("rental_price_per_day", sa.Numeric(12, 2), nullable=False),
        sa.Column("security_deposit", sa.Numeric(12, 2), nullable=False),
        sa.Column("replacement_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("availability", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rental_price_per_day >= 0 AND security_deposit >= 0 AND replacement_value >= 0", name="ck_items_prices"),
        sa.CheckConstraint("category IN ('Electronics','Tools','Travel','Books','Sports','Events','Camping','Other')", name="ck_items_category"),
    )
    op.create_index("ix_items_owner_id", "items", ["owner_id"])
    op.create_index("ix_items_community_created", "items", ["community_id", "created_at"])


def downgrade() -> None:
    op.drop_table("items")
