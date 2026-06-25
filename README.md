# 🎵 Moodify AI

> Automatically creates and updates Spotify playlists based on your listening history and mood.

## How It Works

1. Connect your Spotify account
2. Listen to music normally
3. Moodify AI detects moods from your listening history
4. Playlists like "Romantic Vibes" or "Energetic Boost" appear in Spotify automatically

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 |
| Background Jobs | Celery + Celery Beat |
| Frontend | React 18 + TypeScript + Vite |
| Infrastructure | Docker + Docker Compose |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- A [Spotify Developer account](https://developer.spotify.com/dashboard)

## Getting Started

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd moodify-ai
cp .env.example .env
```

Edit `.env` and fill in your Spotify credentials:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

### 2. Register your Spotify app

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Add redirect URI: `http://localhost:8000/api/auth/callback`
4. Copy the Client ID and Secret into `.env`

### 3. Start all services

```bash
docker compose up --build
```

### 4. Open the apps

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |

## Development

```bash
# Start all services
docker compose up

# View logs for a specific service
docker compose logs -f backend
docker compose logs -f celery

# Run database migrations
docker compose exec backend alembic upgrade head

# Open a PostgreSQL shell
docker compose exec postgres psql -U moodify -d moodify

# Stop all services (keeps data)
docker compose down

# Stop all services and wipe data
docker compose down -v
```

## Project Structure

```
moodify-ai/
├── backend/
│   ├── app/
│   │   ├── api/        # FastAPI routers
│   │   ├── core/       # Config, database, security
│   │   ├── models/     # SQLAlchemy ORM models
│   │   ├── schemas/    # Pydantic request/response schemas
│   │   ├── services/   # Business logic (Spotify client, categorizer)
│   │   ├── tasks/      # Celery background jobs
│   │   └── main.py     # FastAPI app entry point
│   ├── alembic/        # Database migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── services/   # API client
├── docker-compose.yml
└── .env.example
```

## MVP Roadmap

- [x] Phase 1: Planning & Architecture
- [x] Phase 2: Project Setup
- [ ] Phase 3: Spotify Authentication
- [ ] Phase 4: Listening History Import
- [ ] Phase 5: Playlist Categorization
- [ ] Phase 6: Spotify Playlist Creation
- [ ] Phase 7: Automatic Sync Jobs
- [ ] Phase 8: Frontend Dashboard
- [ ] Phase 9: Testing
- [ ] Phase 10: Deployment
