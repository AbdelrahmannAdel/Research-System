import { useState, useEffect } from 'react'
import axios from 'axios'
import Navbar from '../components/Navbar.jsx'

function ProfilePage({ userName, darkMode, setDarkMode, onLogout, token }) {
  const [expandedId, setExpandedId] = useState(null)
  const [savedPapers, setSavedPapers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPapers = async () => {
      try {
        const response = await axios.get('http://localhost:8000/papers/profile', {
          headers: { Authorization: `Bearer ${token}` }
        })
        setSavedPapers(response.data)
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to load saved papers.')
      } finally {
        setLoading(false)
      }
    }
    fetchPapers()
  }, [token])

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-uob-dark">
      <Navbar userName={userName} darkMode={darkMode} setDarkMode={setDarkMode} onLogout={onLogout} />

      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-2xl font-bold text-uob-dark dark:text-white mb-8">My Library</h1>

        {loading ? ( 
          <div className="text-center py-20 text-gray-400">Loading...</div> 
        ) : savedPapers.length === 0 ? (
          // Empty state
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <p className="text-4xl mb-4">📂</p>
            <p className="text-lg font-medium">No saved papers yet</p>
            <p className="text-sm mt-1">Upload and save a paper from the Home page to see it here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {savedPapers.map((paper) => (
              <div key={paper.id} className="bg-white dark:bg-white/5 rounded-xl shadow overflow-hidden">

                {/* Card header — always visible, click to expand */}
                <button
                  onClick={() => toggleExpand(paper.id)}
                  className="w-full text-left px-6 py-5 flex items-start justify-between gap-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                >
                  <div>
                    <p className="font-semibold text-uob-dark dark:text-white">{paper.title}</p>
                    <p className="text-sm text-uob-primary dark:text-blue-300 mt-0.5">
                      {paper.main_category} › {paper.subcategory}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Saved on {paper.saved_at}</p>
                  </div>
                  <span className="text-gray-400 dark:text-gray-500 text-lg mt-1 shrink-0">
                    {expandedId === paper.id ? '▲' : '▼'}
                  </span>
                </button>

                {/* Expanded full analysis */}
                {expandedId === paper.id && (
                  <div className="px-6 pb-6 space-y-5 border-t border-gray-100 dark:border-white/10 pt-4">

                    <div>
                      <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">Summary</h3>
                      <p className="text-gray-700 dark:text-gray-200 text-sm leading-relaxed">{paper.summary}</p>
                    </div>

                    <div>
                      <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">Keywords</h3>
                      <div className="flex flex-wrap gap-2">
                        {paper.keywords.map((kw) => (
                          <span key={kw} className="rounded-full bg-uob-primary/10 dark:bg-uob-primary/20 text-uob-primary dark:text-blue-300 px-3 py-1 text-xs font-medium">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>

                    {paper.recommendations.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">Recommendations</h3>
                        <div className="space-y-2">
                          {paper.recommendations.map((rec, i) => (
                            <div key={i} className="flex items-center justify-between gap-4 rounded-lg bg-gray-50 dark:bg-white/5 px-4 py-3">
                              <div>
                                <a href={rec.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-uob-primary dark:text-blue-300 hover:underline">
                                  {rec.title}
                                </a>
                                <p className="text-xs text-gray-400">{rec.authors}</p>
                              </div>
                              <span className="shrink-0 rounded-full bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 px-2.5 py-1 text-xs font-bold">
                                {rec.similarity}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default ProfilePage
