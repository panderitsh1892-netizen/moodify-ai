"""create tracks table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:01:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the tracks table."""
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spotify_track_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("artist", sa.String(500), nullable=False),
        sa.Column("album", sa.String(500), nullable=True),
        sa.Column("album_art_url", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        # Audio features (filled in Phase 5)
        sa.Column("valence", sa.Float(), nullable=True),
        sa.Column("energy", sa.Float(), nullable=True),
        sa.Column("tempo", sa.Float(), nullable=True),
        sa.Column("danceability", sa.Float(), nullable=True),
        sa.Column("speechiness", sa.Float(), nullable=True),
        sa.Column("track_key", sa.Integer(), nullable=True),
        # Mood (filled in Phase 5)
        sa.Column("mood_category", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Foreign key to users table
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        # Unique constraint for deduplication
        sa.UniqueConstraint(
            "user_id",
            "spotify_track_id",
            "played_at",
            name="uq_user_track_played_at",
        ),
    )

    # Indexes for fast lookups
    op.create_index("ix_tracks_id", "tracks", ["id"])
    op.create_index("ix_tracks_user_id", "tracks", ["user_id"])
    op.create_index("ix_tracks_spotify_track_id", "tracks", ["spotify_track_id"])
    op.create_index("ix_tracks_played_at", "tracks", ["played_at"])
    op.create_index("ix_tracks_mood_category", "tracks", ["mood_category"])


def downgrade() -> None:
    """Drop the tracks table."""
    op.drop_index("ix_tracks_mood_category", table_name="tracks")
    op.drop_index("ix_tracks_played_at", table_name="tracks")
    op.drop_index("ix_tracks_spotify_track_id", table_name="tracks")
    op.drop_index("ix_tracks_user_id", table_name="tracks")
    op.drop_index("ix_tracks_id", table_name="tracks")
    op.drop_table("tracks")
