import { Link } from 'react-router-dom'

function Navbar({ userName, darkMode, setDarkMode, onLogout }) {
  return (
    <nav className="bg-uob-primary dark:bg-uob-dark border-b border-white/10 px-6 py-3 flex items-center justify-between">
      <Link to="/home" className="text-white font-bold text-lg tracking-tight">
        Research Paper AI
      </Link>
      {/* Link is like <a> without reload - token in memory is preserved*/}
      
      <div className="flex items-center gap-4">
        {userName && (
          <span className="text-sm text-white/80 hidden sm:block">
            Welcome, {userName}
          </span>
        )}

        {/* Dark/light mode toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold shadow transition-all bg-white text-uob-primary dark:bg-white/10 dark:text-white hover:opacity-90"
        >
          <span>{darkMode ? '☀️' : '🌙'}</span>
          {darkMode ? 'Light' : 'Dark'}
        </button>

        <Link to="/profile" className="text-sm font-semibold text-white/80 hover:text-white transition-colors">
          My Library
        </Link>

        <button
          onClick={onLogout}
          className="text-sm font-semibold text-white/80 hover:text-white transition-colors"
        >
          Logout
        </button>
      </div>
    </nav>
  )
}

export default Navbar
