// HomePage.jsx
// Drop-in replacement for the original HomePage.jsx.
// Same props, same state, same handlers, same axios endpoints.
// Restyled in the Ivory palette.
//
// PREREQUISITES:
//   1. import './styles/ivory-theme.css' once in main.jsx
//   2. tailwind.config.js has darkMode: 'class'
//   3. Parent App keeps a `darkMode` boolean state, and on toggle
//      does: document.documentElement.classList.toggle('dark', isDark)
//      (the useEffect below also handles this defensively)
//   4. Navbar component receives the same props it always did.
//
// The component will render an empty state, an analysis state, and a
// recommendations state all driven by real fetched data.

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import Navbar from '../components/Navbar.jsx'

function HomePage({ userName, darkMode, setDarkMode, onLogout, token }) {
  // Original 7 state slots, preserved exactly
  const [selectedFile, setSelectedFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [loadingRecs, setLoadingRecs] = useState(false)
  const [saved, setSaved] = useState(false)
  const [savingMsg, setSavingMsg] = useState('')

  const fileInputRef = useRef(null)

  // Defensive: keep <html class="dark"> in sync with darkMode prop.
  // If the parent App already does this, this is a no-op.
  useEffect(() => {
    document.documentElement.classList.toggle('dark', !!darkMode)
  }, [darkMode])

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
      setResult(null)
      setRecommendations(null)
      setSaved(false)
      setSavingMsg('')
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
    setSavingMsg('')

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await axios.post('http://localhost:8000/papers/upload', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        }
      })
      setResult(response.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Analysis failed. Check the backend logs.')
    } finally {
      setLoading(false)
    }
  }

  const handleGetRecommendations = async () => {
    if (!result) return
    setLoadingRecs(true)

    try {
      const response = await axios.post('http://localhost:8000/papers/recommend', {
        title: result.title,
        keywords: result.keywords,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      console.log('Recommendations received:', response.data)  // add this
      console.log('Count:', response.data.length)
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
        subcategory: result.low_confidence ? 'Unclassified' : result.subcategory,
        summary: result.summary,
        keywords: result.keywords,
        recommendations: recommendations || []
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setSaved(true)
      setSavingMsg('Saved to library')
    } catch (err) {
      setSavingMsg('')
      alert(err.response?.data?.detail || 'Failed to save paper.')
    }
  }

  const confidence = result && !result.low_confidence ? 0.972 : 0.45

  return (
    <div className="min-h-screen relative" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="iv-bg-fx" aria-hidden="true" />

      <Navbar userName={userName} darkMode={darkMode} setDarkMode={setDarkMode} onLogout={onLogout} />

      <main className="max-w-5xl mx-auto px-6 pt-12 pb-24 relative z-10">

        <header className="mb-10">
          <span className="iv-eyebrow"><span className="dot" /> 01 — Analyze</span>
          <h1
            className="mt-4 mb-3 leading-[1.04] tracking-[-0.03em] font-medium"
            style={{ fontSize: 'clamp(34px, 4.4vw, 50px)' }}
          >
            Drop a paper.{' '}
            <span className="iv-serif" style={{ color: 'var(--accent)', transition: 'color 0.3s ease' }}>
              Read it differently.
            </span>
          </h1>
          <p className="text-base leading-relaxed max-w-[56ch]" style={{ color: 'var(--text-mute)' }}>
            Upload a research PDF and get back classification, summary, keywords, and ten Semantic Scholar
            recommendations re-ranked by cosine similarity.
          </p>
        </header>

        <section className="iv-panel p-6 sm:p-8 relative overflow-hidden">
          <div
            aria-hidden="true"
            className="absolute top-0 left-0 right-0 h-px opacity-50"
            style={{ background: 'linear-gradient(90deg, transparent, var(--accent), transparent)' }}
          />

          <div className="grid gap-6 md:grid-cols-[1.4fr_1fr]">
            <div
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click() }}
              className="iv-dropzone flex items-center gap-4 px-5 py-6 outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
              style={{ '--tw-ring-color': 'var(--accent)' }}
            >
              <div
                className="w-11 h-14 flex-shrink-0 relative rounded"
                style={{
                  border: `1.5px solid ${selectedFile ? 'var(--accent)' : 'var(--line-2)'}`,
                  background: selectedFile ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent',
                  transition: 'border-color 0.2s, background 0.2s'
                }}
              >
                <span
                  className="absolute top-0 right-0 w-3 h-3"
                  style={{
                    background: 'var(--bg)',
                    borderBottom: `1.5px solid ${selectedFile ? 'var(--accent)' : 'var(--line-2)'}`,
                    borderLeft: `1.5px solid ${selectedFile ? 'var(--accent)' : 'var(--line-2)'}`
                  }}
                />
                <span
                  className="absolute bottom-1.5 left-0 right-0 text-center"
                  style={{
                    fontFamily: 'Geist Mono, monospace',
                    fontSize: '9px',
                    letterSpacing: '0.1em',
                    color: selectedFile ? 'var(--accent)' : 'var(--text-dim)'
                  }}
                >
                  PDF
                </span>
              </div>

              <div className="flex-1 min-w-0">
                {selectedFile ? (
                  <>
                    <div className="text-base font-medium truncate" style={{ letterSpacing: '-0.005em' }}>
                      {selectedFile.name}
                    </div>
                    <div className="iv-mono text-[11.5px] mt-1" style={{ color: 'var(--text-mute)', letterSpacing: '0.04em' }}>
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · ready
                    </div>
                    <div
                      className="iv-mono mt-2 inline-block"
                      style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
                    >
                      ↻ Click to replace
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-base font-medium" style={{ color: 'var(--text)' }}>
                      Click to select a PDF
                    </div>
                    <div className="iv-mono text-[11.5px] mt-1" style={{ color: 'var(--text-mute)', letterSpacing: '0.04em' }}>
                      or drag and drop · max 25 MB
                    </div>
                  </>
                )}
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={handleFileChange}
            />

            <div className="flex flex-col gap-2.5 justify-center">
              <PipeStep label="Extract Keywords"  done={!!result} loading={loading} />
              <PipeStep label="Classify" done={!!result} loading={loading} />
              <PipeStep label="Summarize" done={!!result} loading={loading} />
              <PipeStep label="Recommend"  done={!!recommendations} loading={loadingRecs} />
            </div>
          </div>

          <div
            className="mt-6 pt-5 flex flex-wrap items-center gap-3"
            style={{ borderTop: '1px solid var(--line)' }}
          >
            <button
              onClick={handleAnalyze}
              disabled={!selectedFile || loading}
              className="iv-btn iv-btn-accent"
            >
              {loading ? 'Analyzing…' : (result ? 'Re-analyze' : 'Analyze paper')} →
            </button>
            {loading && (
              <span className="flex items-center gap-2">
                <span
                  className="animate-spin inline-block rounded-full"
                  style={{
                    width: '14px', height: '14px', flexShrink: 0,
                    border: '1.5px solid var(--line-2)',
                    borderTopColor: 'var(--accent)',
                  }}
                />
                <span
                  className="iv-mono text-[11.5px] animate-pulse"
                  style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
                >
                  Running pipeline…
                </span>
              </span>
            )}
            {!loading && (
              <span
                className="iv-mono text-[11.5px]"
                style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
              >
              </span>
            )}
          </div>
        </section>

        {result && (
          <section className="mt-16">
            <div
              className="flex items-baseline justify-between gap-4 flex-wrap pb-3 mb-6"
              style={{ borderBottom: '1px solid var(--line)' }}
            >
              <h2 className="text-[22px] font-medium tracking-[-0.01em]">
                Analysis <span className="iv-serif font-normal" style={{ color: 'var(--text-mute)' }}> results</span>
              </h2>
              <span
                className="iv-mono text-[11.5px]"
                style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
              >
                <span style={{ color: 'var(--ok)' }}>●</span> Complete · 4 stages
              </span>
            </div>

            <div className="mb-7">
              <div
                className="iv-mono mb-2"
                style={{ fontSize: '11px', color: 'var(--text-dim)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
              >
                Detected title
              </div>
              <h3
                className="font-medium leading-[1.05] max-w-[28ch]"
                style={{ fontSize: 'clamp(24px, 3vw, 34px)', letterSpacing: '-0.025em' }}
              >
                {result.title}
              </h3>
            </div>

            {result.low_confidence && (
              <div
                className="iv-panel-2 mb-4 p-4 text-sm"
                style={{
                  borderColor: 'color-mix(in srgb, var(--warn) 35%, var(--line))',
                  background: 'color-mix(in srgb, var(--warn) 8%, var(--panel-2))',
                  color: 'var(--warn)'
                }}
              >
                Low confidence — this paper may fall outside our supported categories. Results may be inaccurate.
              </div>
            )}

            <div className="grid gap-3.5 md:grid-cols-2">
              <div className="iv-panel p-5">
                <h4
                  className="iv-mono mb-3.5 flex items-center gap-2 font-medium"
                  style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
                >
                  Classification
                  <span
                    className="iv-serif"
                    style={{ fontSize: '13px', color: 'var(--text-dim)', letterSpacing: 0, textTransform: 'none' }}
                  >
                    — SciBERT, fine-tuned
                  </span>
                </h4>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="iv-pill iv-pill-accent">{result.main_category}</span>
                  {!result.low_confidence && (
                    <>
                      <span style={{ color: 'var(--text-dim)', fontFamily: 'Geist Mono, monospace' }}>›</span>
                      <span className="iv-pill iv-pill-accent">{result.subcategory}</span>
                    </>
                  )}
                </div>
                <div
                  className="mt-4 pt-4 flex items-center gap-3"
                  style={{ borderTop: '1px dashed var(--line)' }}
                >
                  <span
                    className="iv-mono"
                    style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.12em', textTransform: 'uppercase' }}
                  >
                    Confidence
                  </span>
                  <div className="iv-bar flex-1">
                    <span style={{ width: `${(result.l1_confidence * 100).toFixed(1)}%` }} />
                  </div>
                  <span
                    className="iv-mono font-medium"
                    style={{ fontSize: '13px', color: 'var(--accent)' }}
                  >
                    {result.l1_confidence.toFixed(5)}
                  </span>
                </div>
              </div>

              <div className="iv-panel p-5">
                <h4
                  className="iv-mono mb-3.5 flex items-center gap-2 font-medium"
                  style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
                >
                  Keywords
                  <span
                    className="iv-serif"
                    style={{ fontSize: '13px', color: 'var(--text-dim)', letterSpacing: 0, textTransform: 'none' }}
                  >
                    — YAKE, top {result.keywords?.length || 0}
                  </span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {result.keywords?.map((kw) => (
                    <span key={kw} className="iv-pill">{kw}</span>
                  ))}
                </div>
              </div>

              <div className="iv-panel p-5 md:col-span-2">
                <h4
                  className="iv-mono mb-3.5 flex items-center gap-2 font-medium"
                  style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
                >
                  Summary
                  <span
                    className="iv-serif"
                    style={{ fontSize: '13px', color: 'var(--text-dim)', letterSpacing: 0, textTransform: 'none' }}
                  >
                    — Gemini, academic register
                  </span>
                </h4>
                <p
                  className="leading-[1.6]"
                  style={{ fontSize: '15.5px', color: 'var(--text)' }}
                >
                  {result.summary}
                </p>
              </div>
            </div>

            <div
              className="mt-5 p-4 flex items-center gap-2.5 flex-wrap iv-panel"
              style={{ background: 'color-mix(in srgb, var(--panel) 60%, transparent)' }}
            >
              <button
                onClick={handleGetRecommendations}
                disabled={loadingRecs}
                className="iv-btn iv-btn-accent flex items-center gap-2"
              >
                {loadingRecs && (
                  <span
                    className="animate-spin inline-block rounded-full"
                    style={{
                      width: '13px', height: '13px',
                      border: '1.5px solid rgba(255,255,255,0.3)',
                      borderTopColor: 'currentColor',
                    }}
                  />
                )}
                {loadingRecs ? 'Fetching…' : (recommendations ? 'Re-fetch recommendations' : 'Get recommendations')} →
              </button>
              <button
                onClick={handleSave}
                disabled={saved}
                className="iv-btn iv-btn-primary"
              >
                {saved ? '✓ Saved' : 'Save to library'}
              </button>
              {savingMsg && (
                <span
                  className="iv-mono text-[11.5px] ml-auto"
                  style={{
                    color: saved ? 'var(--ok)' : 'var(--text-mute)',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase'
                  }}
                >
                  {saved && '✓ '}{savingMsg}
                </span>
              )}
            </div>
          </section>
        )}

        {recommendations && recommendations.length > 0 && (
          <section className="mt-16">
            <div
              className="flex items-baseline justify-between gap-4 flex-wrap pb-3 mb-5"
              style={{ borderBottom: '1px solid var(--line)' }}
            >
              <h2 className="text-[22px] font-medium tracking-[-0.01em]">
                Similar papers{' '}
                <span className="iv-serif font-normal" style={{ color: 'var(--text-mute)' }}>
                  — top {recommendations.length}
                </span>
              </h2>
              <span
                className="iv-mono text-[11.5px]"
                style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
              >
                {recommendations[0]?.source || 'Semantic Scholar'} · re-ranked by Sentence-BERT cosine smiliarity
              </span>
            </div>

            <div className="flex flex-col gap-2.5">
              {recommendations.map((rec, i) => (
                <RecCard key={i} rec={rec} index={i + 1} />
              ))}
            </div>
          </section>
        )}

        <footer
          className="mt-24 pt-9 flex flex-wrap justify-between gap-3"
          style={{ borderTop: '1px solid var(--line)' }}
        >
          <span
            className="iv-mono text-[11.5px]"
            style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
          >
            ResearchPilot · v1.0
          </span>
          <span
            className="iv-mono text-[11.5px]"
            style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
          >
            Senior Project · University of Bahrain 2026
          </span>
        </footer>
      </main>
    </div>
  )
}

function PipeStep({ label, done, loading }) {
  return (
    <div
      className="flex items-center gap-2.5 iv-mono"
      style={{
        fontSize: '11.5px',
        letterSpacing: '0.06em',
        color: loading ? 'var(--accent)' : done ? 'var(--text)' : 'var(--text-mute)',
        transition: 'color 0.2s ease'
      }}
    >
      {loading ? (
        <span
          className="animate-spin inline-block flex-shrink-0 rounded-full"
          style={{
            width: '16px', height: '16px',
            border: '1.5px solid var(--line-2)',
            borderTopColor: 'var(--accent)',
          }}
        />
      ) : (
        <span
          className="w-4 h-4 rounded-full grid place-items-center flex-shrink-0"
          style={{
            background: done ? 'color-mix(in srgb, var(--accent) 14%, transparent)' : 'transparent',
            border: `1px solid ${done ? 'var(--accent)' : 'var(--line-2)'}`,
            color: done ? 'var(--accent)' : 'var(--text-dim)',
            fontSize: '10px',
            transition: 'all 0.2s ease'
          }}
        >
          {done ? '✓' : '·'}
        </span>
      )}
      {label}
    </div>
  )
}

function RecCard({ rec, index }) {
  const sim = typeof rec.similarity === 'number' ? rec.similarity : parseFloat(rec.similarity)
  const simPct = sim > 1 ? sim : sim * 100

  return (
    <a
      href={rec.url}
      target="_blank"
      rel="noreferrer"
      className="iv-panel p-5 grid gap-4 transition-transform hover:-translate-y-px"
      style={{
        gridTemplateColumns: '36px minmax(0, 1fr) 110px',
        textDecoration: 'none'
      }}
    >
      <div
        className="iv-mono pt-0.5"
        style={{ fontSize: '11.5px', color: 'var(--text-dim)', letterSpacing: '0.1em' }}
      >
        [{String(index).padStart(2, '0')}]
      </div>
      <div className="min-w-0">
        <div
          className="font-medium leading-[1.35] hover:underline"
          style={{ fontSize: '15px', color: 'var(--text)', letterSpacing: '-0.005em' }}
        >
          {rec.title}
        </div>
        <div
          className="iv-serif mt-1"
          style={{ fontSize: '14px', color: 'var(--text-mute)' }}
        >
          {rec.authors}
        </div>
        <div
          className="mt-2 leading-[1.55] line-clamp-2"
          style={{ fontSize: '13.5px', color: 'var(--text-mute)' }}
        >
          {rec.abstract}
        </div>
      </div>
      <div className="flex flex-col items-end gap-1.5">
        <span
          className="iv-mono font-medium"
          style={{ fontSize: '16px', color: 'var(--accent)' }}
        >
          {(simPct / 100).toFixed(2)}
        </span>
        <div className="iv-bar" style={{ width: '70px', height: '3px' }}>
          <span style={{ width: `${Math.min(simPct, 100)}%` }} />
        </div>
        <span
          className="iv-mono"
          style={{ fontSize: '9.5px', color: 'var(--text-dim)', letterSpacing: '0.12em', textTransform: 'uppercase' }}
        >
          cosine
        </span>
      </div>
    </a>
  )
}

export default HomePage
