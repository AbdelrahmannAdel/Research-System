import { useState, useRef } from 'react'
import axios from 'axios'
import Navbar from '../components/Navbar.jsx'

function HomePage({ userName, darkMode, setDarkMode, onLogout, token }) {
  // This page has 7 pieces of state
  const [selectedFile, setSelectedFile] = useState(null) // which file is chosen
  const [loading, setLoading] = useState(false) // analysis running?
  const [result, setResult] = useState(null) // analysis result
  const [recommendations, setRecommendations] = useState(null) // recommendation
  const [loadingRecs, setLoadingRecs] = useState(false) // recs loading?
  const [saved, setSaved] = useState(false) // paper saved?
  const [savingMsg, setSavingMsg] = useState('') // Saved to Library msg
  
  // hidden file input for UI/UX purposes - hide file input with nice looking div
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
      setResult(null)
      setRecommendations(null)
      setSaved(false)
    } else {
      alert('Please select a valid PDF file.')
    }
  }

const handleAnalyze = async () => {
    if (!selectedFile) return
    setLoading(true)
    setResult(null)
    setRecommendations(null)
    setSaved(false)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      const response = await axios.post('http://localhost:8000/papers/upload', formData, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setResult(response.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setLoading(false)
    }
}

const handleGetRecommendations = async () => {
    setLoadingRecs(true)

    try {
      const response = await axios.post('http://localhost:8000/papers/recommend', {
        title: result.title,
        keywords: result.keywords
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setRecommendations(response.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to fetch recommendations.')
    } finally {
      setLoadingRecs(false)
    }
  }

const handleSave = async () => {
    setSavingMsg('Saving...')

    try {
      await axios.post('http://localhost:8000/papers/save', {
        title: result.title,
        main_category: result.main_category,
        subcategory: result.subcategory,
        summary: result.summary,
        keywords: result.keywords,
        recommendations: recommendations || []
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setSaved(true)
      setSavingMsg('Saved to library!')
    } catch (err) {
      setSavingMsg('')
      alert(err.response?.data?.detail || 'Failed to save paper.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-uob-dark">
      <Navbar userName={userName} darkMode={darkMode} setDarkMode={setDarkMode} onLogout={onLogout} />

      <main className="max-w-3xl mx-auto px-6 py-12">

        {/* Upload section */}
        <div className="bg-white dark:bg-white/5 rounded-xl p-8 shadow text-center">
          <h1 className="text-2xl font-bold text-uob-dark dark:text-white mb-2">Upload a Research Paper</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">PDF files only. The system will classify, summarize, and extract keywords automatically.</p>

          <div
            onClick={() => fileInputRef.current.click()}
            className="border-2 border-dashed border-uob-primary/40 dark:border-white/20 rounded-lg px-6 py-10 cursor-pointer hover:border-uob-primary dark:hover:border-white/40 transition-colors"
          >
            <p className="text-uob-primary dark:text-white/70 font-medium">
              {selectedFile ? `📄 ${selectedFile.name}` : 'Click to select a PDF'}
            </p>
            <p className="text-xs text-gray-400 mt-1">or drag and drop here</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleFileChange}
          />

          <button
            onClick={handleAnalyze}
            disabled={!selectedFile || loading}
            className="mt-6 w-full rounded-md bg-uob-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Analyze Paper'}
          </button>

          {loading && (
            <p className="mt-3 text-sm text-gray-400 animate-pulse">Running AI pipeline — this may take a few seconds...</p>
          )}
        </div>

        {/* Results section */}
        {result && (
          <div className="mt-8 space-y-6">

            {/* Classification */}
            <div className="bg-white dark:bg-white/5 rounded-xl p-6 shadow">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Classification</h2>
              <p className="text-xl font-bold text-uob-dark dark:text-white">
                {result.main_category} <span className="text-uob-primary">›</span> {result.subcategory}
              </p>
            </div>

            {/* Summary */}
            <div className="bg-white dark:bg-white/5 rounded-xl p-6 shadow">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Summary</h2>
              <p className="text-gray-700 dark:text-gray-200 leading-relaxed">{result.summary}</p>
            </div>

            {/* Keywords */}
            <div className="bg-white dark:bg-white/5 rounded-xl p-6 shadow">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Keywords</h2>
              <div className="flex flex-wrap gap-2">
                {result.keywords.map((kw) => (
                  <span key={kw} className="rounded-full bg-uob-primary/10 dark:bg-uob-primary/20 text-uob-primary dark:text-blue-300 px-3 py-1 text-sm font-medium">
                    {kw}
                  </span>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleGetRecommendations}
                disabled={loadingRecs}
                className="flex-1 rounded-md border border-uob-primary text-uob-primary dark:text-blue-300 dark:border-blue-400 px-4 py-2 text-sm font-semibold hover:bg-uob-primary hover:text-white dark:hover:bg-uob-primary dark:hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loadingRecs ? 'Fetching...' : '🔍 Get Recommendations'}
              </button>
              <button
                onClick={handleSave}
                disabled={saved}
                className="flex-1 rounded-md bg-uob-primary text-white px-4 py-2 text-sm font-semibold hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {saved ? '✓ Saved' : '💾 Save to Library'}
              </button>
            </div>
            {savingMsg && <p className="text-sm text-green-500 dark:text-green-400 text-center">{savingMsg}</p>}
          </div>
        )}

        {/* Recommendations section */}
        {recommendations && (
          <div className="mt-8">
            <h2 className="text-lg font-bold text-uob-dark dark:text-white mb-4">Similar Papers</h2>
            <div className="space-y-4">
              {recommendations.map((rec, i) => (
                <div key={i} className="bg-white dark:bg-white/5 rounded-xl p-5 shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <a href={rec.url} target="_blank" rel="noreferrer" className="font-semibold text-uob-primary dark:text-blue-300 hover:underline">
                        {rec.title}
                      </a>
                      <p className="text-xs text-gray-400 mt-0.5">{rec.authors}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">{rec.abstract}</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 px-2.5 py-1 text-xs font-bold">
                      {rec.similarity}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>
    </div>
  )
}

export default HomePage
