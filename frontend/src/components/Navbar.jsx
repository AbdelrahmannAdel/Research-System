// Navbar.jsx
// Translucent sticky top bar in the Ivory theme.
// - Accent dot logo + monospace wordmark
// - Active route gets an accent underline + glow
// - Compact icon-only theme toggle (sun / moon glyphs)
// - Logout sits to the right as a quiet ghost button

import { Link, useLocation } from 'react-router-dom'

function Navbar({ userName, darkMode, setDarkMode, onLogout }) {
  const { pathname } = useLocation()

  return (
    <nav className="iv-nav">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between gap-4">

        {/* Brand */}
        <Link to="/home" className="flex items-center gap-2.5 group" style={{ textDecoration: 'none' }}>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="24" height="24" style={{ borderRadius: '6px', flexShrink: 0 }}>
            <rect width="48" height="48" rx="10" fill="#2a5db0"/>
            <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" fontFamily="system-ui, -apple-system, sans-serif" fontWeight="700" fontSize="18" fill="#ffffff" letterSpacing="-0.5">RP</text>
          </svg>
          <span
            className="iv-mono font-medium"
            style={{
              fontSize: '13px',
              color: 'var(--text)',
              letterSpacing: '0.16em',
              textTransform: 'uppercase',
            }}
          >
            ResearchPilot
          </span>
        </Link>

        {/* Right side: nav + actions */}
        <div className="flex items-center gap-1.5">
          <NavLink to="/home"    label="Analyze" active={pathname === '/home'} />
          <NavLink to="/profile" label="Library" active={pathname === '/profile'} />

          {/* Divider */}
          <span
            aria-hidden="true"
            className="hidden sm:inline-block mx-2"
            style={{ width: '1px', height: '18px', background: 'var(--line-2)' }}
          />

          {/* User name (mono, dimmed) */}
          {userName && (
            <span
              className="iv-mono hidden md:inline-block"
              style={{
                fontSize: '11px',
                color: 'var(--text-dim)',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                marginRight: '4px',
              }}
            >
              {userName}
            </span>
          )}

          {/* Theme toggle, icon only */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle theme"
            className="iv-nav-icon-btn"
          >
            {darkMode ? '☀' : '☾'}
          </button>

          {/* Logout, quiet ghost button */}
          <button
            onClick={onLogout}
            className="iv-nav-link"
            style={{ marginLeft: '2px' }}
            title="Log out"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

function NavLink({ to, label, active }) {
  return (
    <Link to={to} className={`iv-nav-link ${active ? 'active' : ''}`}>
      {label}
    </Link>
  )
}

export default Navbar
