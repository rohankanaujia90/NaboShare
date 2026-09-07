"""Create communities and add user membership.

Revision ID: 20260907_0002
Revises: 20260903_0001
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0002"
down_revision: str | Sequence[str] | None = "20260903_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("invite_code", sa.String(length=12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type IN ('college', 'hostel', 'apartment_society', 'corporate_campus')",
            name="ck_communities_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communities_city"), "communities", ["city"])
    op.create_index(
        op.f("ix_communities_invite_code"),
        "communities",
        ["invite_code"],
        unique=True,
    )
    op.add_column("users", sa.Column("community_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_users_community_id"), "users", ["community_id"])
    op.create_foreign_key(
        op.f("fk_users_community_id_communities"),
        "users",
        "communities",
        ["community_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_users_community_id_communities"),
        "users",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_users_community_id"), table_name="users")
    op.drop_column("users", "community_id")
    op.drop_index(op.f("ix_communities_invite_code"), table_name="communities")
    op.drop_index(op.f("ix_communities_city"), table_name="communities")
    op.drop_table("communities")

