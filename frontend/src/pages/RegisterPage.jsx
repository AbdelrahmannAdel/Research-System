// RegisterPage.jsx
// Restyled in the Ivory palette to match HomePage.jsx.
// Same props, same axios endpoints, same handlers.

import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'

function RegisterPage({ darkMode, setDarkMode }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', !!darkMode)
  }, [darkMode])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await axios.post('http://localhost:8000/auth/register', { name, email, password })
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="iv-bg-fx" aria-hidden="true" />

      {/* Top brand strip */}
      <header className="max-w-5xl mx-auto px-6 pt-7 pb-4 flex items-center justify-between relative z-10">
        <Link to="/login" className="flex items-center gap-2.5" style={{ textDecoration: 'none' }}>
          <span
            aria-hidden="true"
            className="rounded-full"
            style={{ width: '7px', height: '7px', background: 'var(--accent)', boxShadow: '0 0 12px var(--accent)' }}
          />
          <span
            className="iv-mono font-medium"
            style={{ fontSize: '13px', color: 'var(--text)', letterSpacing: '0.16em', textTransform: 'uppercase' }}
          >
            ResearchPilot
          </span>
        </Link>
        <button
          onClick={() => setDarkMode(!darkMode)}
          title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label="Toggle theme"
          className="iv-nav-icon-btn"
        >
          {darkMode ? '☀' : '☾'}
        </button>
      </header>

      <main className="max-w-md mx-auto px-6 pt-12 pb-20 relative z-10">

        {/* Eyebrow + heading */}
        <div className="mb-8">
          <span className="iv-eyebrow"><span className="dot" /> 00 — Register</span>
          <h1
            className="mt-4 mb-3 leading-[1.06] tracking-[-0.025em] font-medium"
            style={{ fontSize: 'clamp(28px, 4vw, 38px)' }}
          >
            Start reading.{' '}
            <span className="iv-serif" style={{ color: 'var(--accent)' }}>
              Differently.
            </span>
          </h1>
          <p className="text-[14.5px] leading-relaxed" style={{ color: 'var(--text-mute)' }}>
            Create an account to upload research papers and build your personal library.
          </p>
        </div>

        {/* Form panel */}
        <section className="iv-panel p-7 relative overflow-hidden">
          <div
            aria-hidden="true"
            className="absolute top-0 left-0 right-0 h-px opacity-50"
            style={{ background: 'linear-gradient(90deg, transparent, var(--accent), transparent)' }}
          />

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="name" className="iv-label">Full name</label>
              <input
                id="name"
                type="text"
                name="name"
                required
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="iv-input"
                placeholder="Mohamed Yaser"
              />
            </div>

            <div>
              <label htmlFor="email" className="iv-label">Email</label>
              <input
                id="email"
                type="email"
                name="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="iv-input"
                placeholder="you@university.edu"
              />
            </div>

            <div>
              <label htmlFor="password" className="iv-label">Password</label>
              <input
                id="password"
                type="password"
                name="password"
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="iv-input"
                placeholder="At least 8 characters"
              />
            </div>

            {error && (
              <div
                className="iv-mono text-[12px] px-3 py-2 rounded-md"
                style={{
                  background: 'color-mix(in srgb, var(--danger) 10%, transparent)',
                  color: 'var(--danger)',
                  border: '1px solid color-mix(in srgb, var(--danger) 30%, transparent)',
                  letterSpacing: '0.02em',
                }}
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="iv-btn iv-btn-accent w-full justify-center flex items-center gap-2"
              style={{ paddingTop: '12px', paddingBottom: '12px' }}
            >
              {loading && (
                <span
                  className="animate-spin inline-block rounded-full"
                  style={{
                    width: '13px', height: '13px',
                    border: '1.5px solid rgba(255,255,255,0.35)',
                    borderTopColor: 'currentColor',
                  }}
                />
              )}
              {loading ? 'Creating account…' : 'Create account →'}
            </button>
          </form>
        </section>

        {/* Footer link */}
        <p
          className="mt-7 text-center text-[14px]"
          style={{ color: 'var(--text-mute)' }}
        >
          Already have an account?{' '}
          <Link
            to="/login"
            className="iv-serif"
            style={{ color: 'var(--accent)', textDecoration: 'none', borderBottom: '1px solid currentColor', paddingBottom: '1px' }}
          >
            Sign in
          </Link>
        </p>

        {/* Footer */}
        <footer
          className="mt-20 pt-6 flex justify-between"
          style={{ borderTop: '1px solid var(--line)' }}
        >
          <span
            className="iv-mono text-[11px]"
            style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
          >
            ResearchPilot · v1.0
          </span>
          <span
            className="iv-mono text-[11px]"
            style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
          >
            Senior Project
          </span>
        </footer>
      </main>
    </div>
  )
}

export default RegisterPage
