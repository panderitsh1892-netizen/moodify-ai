/**
 * Landing page — shown to unauthenticated users
 */

interface Props {
  onLogin: () => void
}

export default function Landing({ onLogin }: Props) {
  return (
    <div className="landing">
      <div className="landing-content">
        {/* Logo */}
        <div className="landing-logo">🎵</div>

        {/* Headline */}
        <h1 className="landing-title">Moodify AI</h1>
        <p className="landing-subtitle">
          Your music, automatically organized by mood.
        </p>

        {/* How it works */}
        <div className="landing-steps">
          <div className="landing-step">
            <div className="step-icon">🎧</div>
            <div className="step-text">
              <strong>Listen</strong> to music on Spotify
            </div>
          </div>
          <div className="landing-arrow">→</div>
          <div className="landing-step">
            <div className="step-icon">🧠</div>
            <div className="step-text">
              <strong>Moodify</strong> detects the mood
            </div>
          </div>
          <div className="landing-arrow">→</div>
          <div className="landing-step">
            <div className="step-icon">🎶</div>
            <div className="step-text">
              <strong>Playlists</strong> appear automatically
            </div>
          </div>
        </div>

        {/* Example moods */}
        <div className="landing-moods">
          {[
            { emoji: '🌹', label: 'Romantic Vibes' },
            { emoji: '⚡', label: 'Energetic Boost' },
            { emoji: '😌', label: 'Chill Zone' },
            { emoji: '⭐', label: 'Happy Vibes' },
            { emoji: '🌧️', label: 'Melancholic Feels' },
            { emoji: '🔥', label: 'Angry Mode' },
          ].map(({ emoji, label }) => (
            <span key={label} className="landing-mood-pill">
              {emoji} {label}
            </span>
          ))}
        </div>

        {/* CTA */}
        <button onClick={onLogin} className="btn-spotify">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
          </svg>
          Connect Spotify
        </button>

        <p className="landing-note">
          Your listening data stays private. Playlists are created in your Spotify account.
        </p>
      </div>
    </div>
  )
}
