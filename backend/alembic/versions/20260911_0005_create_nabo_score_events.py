"""Add bounded, auditable NaboScore events, ratings, and damage disputes."""

import sqlalchemy as sa
from alembic import op

revision = "20260911_0005"
down_revision = "20260909_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_users_nabo_score", "users", "nabo_score BETWEEN 0 AND 100"
    )
    op.create_table(
        "nabo_score_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rental_id", sa.Uuid(), sa.ForeignKey("rental_requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "rental_id", "reason", name="uq_score_event_once"),
        sa.CheckConstraint("reason IN ('ON_TIME_RETURN','POSITIVE_RATING','LATE_RETURN','DAMAGED_ITEM_DISPUTE','CANCELLED_ACCEPTED_BOOKING')", name="ck_score_events_reason"),
    )
    op.create_index("ix_nabo_score_events_user_id", "nabo_score_events", ["user_id"])
    op.create_index("ix_nabo_score_events_rental_id", "nabo_score_events", ["rental_id"])
    op.create_table(
        "rental_ratings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("rental_id", sa.Uuid(), sa.ForeignKey("rental_requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rater_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rated_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("rental_id", "rater_id", name="uq_rental_rating_rater"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_rental_ratings_value"),
        sa.CheckConstraint("rater_id <> rated_user_id", name="ck_rental_ratings_not_self"),
    )
    op.create_index("ix_rental_ratings_rental_id", "rental_ratings", ["rental_id"])
    op.create_index("ix_rental_ratings_rater_id", "rental_ratings", ["rater_id"])
    op.create_index("ix_rental_ratings_rated_user_id", "rental_ratings", ["rated_user_id"])
    op.create_table(
        "damage_disputes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("rental_id", sa.Uuid(), sa.ForeignKey("rental_requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reported_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reported_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("rental_id", name="uq_damage_dispute_rental"),
        sa.CheckConstraint("reported_by_id <> reported_user_id", name="ck_damage_disputes_not_self"),
    )
    op.create_index("ix_damage_disputes_rental_id", "damage_disputes", ["rental_id"])
    op.create_index("ix_damage_disputes_reported_by_id", "damage_disputes", ["reported_by_id"])
    op.create_index("ix_damage_disputes_reported_user_id", "damage_disputes", ["reported_user_id"])


def downgrade() -> None:
    op.drop_table("damage_disputes")
    op.drop_table("rental_ratings")
    op.drop_table("nabo_score_events")
    op.drop_constraint("ck_users_nabo_score", "users", type_="check")
