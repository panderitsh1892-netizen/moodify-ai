# ── Frontend Dockerfile ─────────────────────────────────────────────────────────
#
# Development setup: Vite dev server with hot module replacement (HMR).
# The source code is mounted as a volume so changes appear instantly
# without rebuilding the container.
#
# For production we'd add a second stage: `npm run build` → serve via nginx.
# We'll do that in Phase 10 (Deployment).

FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files first (for Docker layer caching).
# npm install only re-runs when package.json or package-lock.json changes.
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the source
COPY . .

# Expose Vite's dev server port
EXPOSE 3000

# Start Vite dev server
# --host 0.0.0.0 is required inside Docker so the host machine can reach it
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
