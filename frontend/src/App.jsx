import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'

// Redirects to /login if the user is not authenticated
function ProtectedRoute({ token, children }) {
  if (!token) return <Navigate to="/login" replace />
  return children
}

function App() {
  const [token, setToken] = useState(null)
  const [darkMode, setDarkMode] = useState(true)

  const handleLogin = (accessToken) => {
    setToken(accessToken)
  }

  return (
    // Applying 'dark' class here activates all dark: variants across the app
    <div className={darkMode ? 'dark' : ''}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} darkMode={darkMode} setDarkMode={setDarkMode} />} />
          <Route path="/register" element={<RegisterPage darkMode={darkMode} setDarkMode={setDarkMode} />} />

          {/* Protected routes — redirect to /login if no token */}
          <Route path="/home" element={
            <ProtectedRoute token={token}>
              <div className="text-white p-8">Home page — coming soon</div>
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute token={token}>
              <div className="text-white p-8">Profile page — coming soon</div>
            </ProtectedRoute>
          } />

          {/* Default: redirect root to /login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}

export default App
