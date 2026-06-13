import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import HomePage from './pages/HomePage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'

// Redirects to /login if the user is not authenticated
function ProtectedRoute({ token, children }) {
  if (!token) return <Navigate to="/login" replace />
  return children
}

function App() {
  // Holding shared data in App.jsx is better than separate pages.
  const [token, setToken] = useState(() => localStorage.getItem('token') || null)
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || '')
  const [darkMode, setDarkMode] = useState(true)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  const handleLogin = (accessToken, name) => {
    setToken(accessToken)
    setUserName(name)
    localStorage.setItem('token', accessToken)
    localStorage.setItem('userName', name)
  }

  const handleLogout = () => {
    setToken(null)
    setUserName('')
    localStorage.removeItem('token')
    localStorage.removeItem('userName')
  }

  // Shared props passed to every protected page
  const pageProps = { userName, darkMode, setDarkMode, onLogout: handleLogout, token }

  // Single Page Application, no route upon URL change => React swaps component instantly
  return (
    <div className={darkMode ? 'dark' : ''}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} darkMode={darkMode} setDarkMode={setDarkMode} />} />
          <Route path="/register" element={<RegisterPage darkMode={darkMode} setDarkMode={setDarkMode} />} />

          <Route path="/home" element={
            <ProtectedRoute token={token}>
              <HomePage {...pageProps} />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute token={token}>
              <ProfilePage {...pageProps} />
            </ProtectedRoute>
          } />

          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}

export default App
