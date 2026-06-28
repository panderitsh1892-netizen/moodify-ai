"""create playlists table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:02:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spotify_playlist_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mood_category", sa.String(100), nullable=False),
        sa.Column("spotify_url", sa.Text(), nullable=True),
        sa.Column("track_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("spotify_playlist_id"),
    )
    op.create_index("ix_playlists_id", "playlists", ["id"])
    op.create_index("ix_playlists_user_id", "playlists", ["user_id"])
    op.create_index("ix_playlists_mood_category", "playlists", ["mood_category"])
    op.create_index(
        "ix_playlists_spotify_playlist_id",
        "playlists",
        ["spotify_playlist_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_playlists_spotify_playlist_id", table_name="playlists")
    op.drop_index("ix_playlists_mood_category", table_name="playlists")
    op.drop_index("ix_playlists_user_id", table_name="playlists")
    op.drop_index("ix_playlists_id", table_name="playlists")
    op.drop_table("playlists")
