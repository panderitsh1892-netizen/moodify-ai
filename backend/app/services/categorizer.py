"""
app/services/categorizer.py
────────────────────────────
Mood categorization engine.

NOTE: Spotify's /audio-features endpoint requires Premium.
We use deterministic mock audio features based on track ID hash
so categorization works without Premium. The mood logic is identical
to what real audio features would use — swap get_mock_audio_features
for spotify_service.get_audio_features when Premium is available.
"""

import hashlib
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.track import Track
from app.models.user import User
from app.services.spotify import spotify_service


class Mood:
    ENERGETIC = "Energetic"
    ANGRY = "Angry"
    HAPPY = "Happy"
    ROMANTIC = "Romantic"
    MELANCHOLIC = "Melancholic"
    CHILL = "Chill"

    ALL = [ENERGETIC, ANGRY, HAPPY, ROMANTIC, MELANCHOLIC, CHILL]


@dataclass
class AudioFeatures:
    """Typed wrapper around audio feature values."""
    track_id: str
    valence: float
    energy: float
    danceability: float
    tempo: float
    speechiness: float
    key: int

    @classmethod
    def from_spotify(cls, data: dict) -> "AudioFeatures":
        return cls(
            track_id=data.get("id", ""),
            valence=data.get("valence", 0.5),
            energy=data.get("energy", 0.5),
            danceability=data.get("danceability", 0.5),
            tempo=data.get("tempo", 120.0),
            speechiness=data.get("speechiness", 0.0),
            key=data.get("key", 0),
        )

    @classmethod
    def from_mock(cls, track_id: str) -> "AudioFeatures":
        """
        Generate deterministic mock audio features from a track ID.

        Uses MD5 hash of the track ID to generate consistent values —
        the same track always gets the same features, so moods don't
        change between runs. This gives a realistic spread across all
        6 mood categories.

        Replace this with from_spotify() when Spotify Premium is available.
        """
        # Hash the track ID to get a stable seed
        hash_bytes = hashlib.md5(track_id.encode()).digest()

        # Convert different bytes to different feature values (0.0 - 1.0)
        valence = hash_bytes[0] / 255.0
        energy = hash_bytes[1] / 255.0
        danceability = hash_bytes[2] / 255.0
        speechiness = hash_bytes[3] / 512.0  # Keep low (most tracks aren't speech)
        tempo = 60.0 + (hash_bytes[4] / 255.0) * 140.0  # 60-200 BPM
        key = hash_bytes[5] % 12  # 0-11

        return cls(
            track_id=track_id,
            valence=round(valence, 3),
            energy=round(energy, 3),
            danceability=round(danceability, 3),
            tempo=round(tempo, 1),
            speechiness=round(speechiness, 3),
            key=key,
        )


class MoodCategorizer:
    """Categorizes tracks into mood buckets based on audio features."""

    def classify(self, features: AudioFeatures) -> str:
        """
        Apply mood rules to a single track's audio features.
        Rules checked in priority order — first match wins.
        """
        v = features.valence
        e = features.energy
        d = features.danceability

        # Energetic: high energy + high danceability
        if e >= 0.80 and d >= 0.70:
            return Mood.ENERGETIC

        # Angry: low positivity + high energy
        if v <= 0.35 and e >= 0.70:
            return Mood.ANGRY

        # Happy: high positivity + high energy
        if v >= 0.70 and e >= 0.60:
            return Mood.HAPPY

        # Romantic: high positivity + low-medium energy
        if v >= 0.50 and e <= 0.60:
            return Mood.ROMANTIC

        # Melancholic: low positivity + low energy
        if v <= 0.35 and e <= 0.50:
            return Mood.MELANCHOLIC

        # Chill: everything else
        return Mood.CHILL

    async def categorize_user_tracks(
        self,
        user: User,
        db: AsyncSession,
        only_uncategorized: bool = True,
    ) -> dict:
        """
        Assign moods to a user's tracks using mock audio features.

        Flow:
        1. Load tracks needing categorization
        2. Generate mock audio features per track
        3. Apply mood rules
        4. Bulk update DB with mood + audio features

        When Spotify Premium is available, replace step 2 with:
            raw = await spotify_service.get_audio_features(token, ids)
            features = AudioFeatures.from_spotify(f) for f in raw
        """
        # Step 1: Load tracks
        query = select(Track).where(Track.user_id == user.id)
        if only_uncategorized:
            query = query.where(Track.mood_category.is_(None))

        result = await db.execute(query)
        tracks = result.scalars().all()

        if not tracks:
            return {
                "message": "No tracks to categorize",
                "total_processed": 0,
                "categorized": 0,
                "by_mood": {},
            }

        # Refresh token in case it expired (good practice even with mock)
        await spotify_service.get_valid_access_token(user)
        await db.flush()

        # Step 2 & 3: Generate mock features and classify
        mood_counts: dict[str, int] = {}
        categorized = 0

        for track in tracks:
            # Generate deterministic mock features from track ID
            features = AudioFeatures.from_mock(track.spotify_track_id)
            mood = self.classify(features)

            # Step 4: Update track in DB
            await db.execute(
                update(Track)
                .where(Track.id == track.id)
                .values(
                    mood_category=mood,
                    valence=features.valence,
                    energy=features.energy,
                    tempo=features.tempo,
                    danceability=features.danceability,
                    speechiness=features.speechiness,
                    track_key=features.key,
                )
            )

            mood_counts[mood] = mood_counts.get(mood, 0) + 1
            categorized += 1

        return {
            "message": f"Categorization complete. {categorized} tracks categorized.",
            "total_processed": len(tracks),
            "categorized": categorized,
            "by_mood": mood_counts,
            "note": "Using mock audio features. Connect Spotify Premium for real features.",
        }


mood_categorizer = MoodCategorizer()
