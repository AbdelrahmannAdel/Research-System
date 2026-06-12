// ProfilePage.jsx
// Restyled in the Ivory palette to match HomePage.jsx.
// Same props, same axios endpoint, same expand/collapse behavior.

import { useState, useEffect } from 'react'
import axios from 'axios'
import Navbar from '../components/Navbar.jsx'
import API_URL from '../api.js'

function ProfilePage({ userName, darkMode, setDarkMode, onLogout, token }) {
  const [expandedId, setExpandedId] = useState(null)
  const [savedPapers, setSavedPapers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', !!darkMode)
  }, [darkMode])

  useEffect(() => {
    const fetchPapers = async () => {
      try {
        const response = await axios.get(`${API_URL}/papers/profile`, {
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
    <div className="min-h-screen relative" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="iv-bg-fx" aria-hidden="true" />

      <Navbar userName={userName} darkMode={darkMode} setDarkMode={setDarkMode} onLogout={onLogout} />

      <main className="max-w-5xl mx-auto px-6 pt-12 pb-24 relative z-10">

        {/* Page header */}
        <header className="mb-10">
          <span className="iv-eyebrow"><span className="dot" /> 02 — Library</span>
          <h1
            className="mt-4 mb-3 leading-[1.04] tracking-[-0.03em] font-medium"
            style={{ fontSize: 'clamp(34px, 4.4vw, 50px)' }}
          >
            Your saved papers.{' '}
            <span className="iv-serif" style={{ color: 'var(--accent)' }}>
              All in one place.
            </span>
          </h1>
          <p className="text-base leading-relaxed max-w-[56ch]" style={{ color: 'var(--text-mute)' }}>
            Every paper you've analyzed and saved, with its classification, summary, keywords, and
            recommendations preserved exactly as they were.
          </p>
        </header>

        {/* Counter strip */}
        {!loading && savedPapers.length > 0 && (
          <div
            className="flex items-center justify-between pb-3 mb-5"
            style={{ borderBottom: '1px solid var(--line)' }}
          >
            <h2 className="text-[22px] font-medium tracking-[-0.01em]">
              Library{' '}
              <span className="iv-serif font-normal" style={{ color: 'var(--text-mute)' }}>
                — {savedPapers.length} {savedPapers.length === 1 ? 'paper' : 'papers'}
              </span>
            </h2>
            <span
              className="iv-mono text-[11.5px]"
              style={{ color: 'var(--text-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}
            >
              Click a row to expand
            </span>
          </div>
        )}

        {/* States */}
        {loading ? (
          <LoadingState />
        ) : savedPapers.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="flex flex-col gap-2.5">
            {savedPapers.map((paper, i) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                index={i + 1}
                expanded={expandedId === paper.id}
                onToggle={() => toggleExpand(paper.id)}
              />
            ))}
          </div>
        )}

        {/* Footer */}
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

/* Sub-components */

function LoadingState() {
  return (
    <div className="iv-panel p-12 flex flex-col items-center justify-center gap-4">
      <span
        className="animate-spin inline-block rounded-full"
        style={{
          width: '28px', height: '28px',
          border: '2px solid var(--line-2)',
          borderTopColor: 'var(--accent)',
        }}
      />
      <span
        className="iv-mono text-[11.5px]"
        style={{ color: 'var(--text-mute)', letterSpacing: '0.16em', textTransform: 'uppercase' }}
      >
        Loading library…
      </span>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="iv-panel p-12 flex flex-col items-center text-center gap-3">
      {/* Empty file glyph */}
      <div
        className="w-12 h-16 relative rounded mb-2"
        style={{
          border: '1.5px dashed var(--line-2)',
        }}
      >
        <span
          className="absolute top-0 right-0 w-3.5 h-3.5"
          style={{
            background: 'var(--bg)',
            borderBottom: '1.5px dashed var(--line-2)',
            borderLeft: '1.5px dashed var(--line-2)',
          }}
        />
      </div>
      <h3
        className="font-medium"
        style={{ fontSize: '18px', letterSpacing: '-0.01em', color: 'var(--text)' }}
      >
        No saved papers yet
      </h3>
      <p className="text-[14px] max-w-[44ch]" style={{ color: 'var(--text-mute)' }}>
        Upload and analyze a paper from the home page, then click{' '}
        <span className="iv-serif" style={{ color: 'var(--accent)' }}>Save to library</span>{' '}
        to see it here.
      </p>
    </div>
  )
}

function PaperCard({ paper, index, expanded, onToggle }) {
  return (
    <div
      className="iv-panel transition-shadow"
      style={{ overflow: 'hidden' }}
    >
      {/* Header (always visible, click to expand) */}
      <button
        onClick={onToggle}
        className="w-full text-left p-5 grid items-start gap-4"
        style={{
          gridTemplateColumns: '36px minmax(0, 1fr) auto',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        {/* Index */}
        <div
          className="iv-mono pt-1"
          style={{ fontSize: '11.5px', color: 'var(--text-dim)', letterSpacing: '0.1em' }}
        >
          [{String(index).padStart(2, '0')}]
        </div>

        {/* Title block */}
        <div className="min-w-0">
          <div
            className="font-medium leading-[1.3]"
            style={{ fontSize: '16px', color: 'var(--text)', letterSpacing: '-0.01em' }}
          >
            {paper.title}
          </div>
          <div className="flex items-center gap-1.5 flex-wrap mt-2">
            <span className="iv-pill iv-pill-accent">{paper.main_category}</span>
            {paper.subcategory && paper.subcategory !== 'Unclassified' && (
              <>
                <span style={{ color: 'var(--text-dim)', fontFamily: 'Geist Mono, monospace' }}>›</span>
                <span className="iv-pill iv-pill-accent">{paper.subcategory}</span>
              </>
            )}
          </div>
          {paper.saved_at && (
            <div
              className="iv-mono mt-2"
              style={{ fontSize: '10.5px', color: 'var(--text-dim)', letterSpacing: '0.12em', textTransform: 'uppercase' }}
            >
              Saved · {paper.saved_at}
            </div>
          )}
        </div>

        {/* Chevron */}
        <div
          className="iv-mono self-center"
          style={{
            fontSize: '14px',
            color: expanded ? 'var(--accent)' : 'var(--text-dim)',
            transition: 'transform 0.25s ease, color 0.18s ease',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        >
          ▾
        </div>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div
          className="px-5 pb-5"
          style={{ borderTop: '1px dashed var(--line)' }}
        >
          <div className="pt-5 grid gap-3.5 md:grid-cols-2">
            {/* Summary, full width */}
            <div className="iv-panel-2 p-5 md:col-span-2">
              <h4
                className="iv-mono mb-3 flex items-center gap-2 font-medium"
                style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
              >
                Summary
              </h4>
              <p
                className="leading-[1.6]"
                style={{ fontSize: '14.5px', color: 'var(--text)' }}
              >
                {paper.summary}
              </p>
            </div>

            {/* Keywords, full width */}
            {paper.keywords && paper.keywords.length > 0 && (
              <div className="iv-panel-2 p-5 md:col-span-2">
                <h4
                  className="iv-mono mb-3 flex items-center gap-2 font-medium"
                  style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
                >
                  Keywords
                  <span
                    className="iv-serif"
                    style={{ fontSize: '13px', color: 'var(--text-dim)', letterSpacing: 0, textTransform: 'none' }}
                  >
                    — top {paper.keywords.length}
                  </span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {paper.keywords.map((kw) => (
                    <span key={kw} className="iv-pill">{kw}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Recommendations */}
          {paper.recommendations && paper.recommendations.length > 0 && (
            <div className="mt-5">
              <h4
                className="iv-mono mb-3 flex items-center gap-2 font-medium"
                style={{ fontSize: '11px', color: 'var(--text-mute)', letterSpacing: '0.18em', textTransform: 'uppercase' }}
              >
                Recommendations
                <span
                  className="iv-serif"
                  style={{ fontSize: '13px', color: 'var(--text-dim)', letterSpacing: 0, textTransform: 'none' }}
                >
                  — {paper.recommendations.length} similar papers
                </span>
              </h4>
              <div className="flex flex-col gap-2">
                {paper.recommendations.map((rec, i) => (
                  <RecRow key={i} rec={rec} index={i + 1} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RecRow({ rec, index }) {
  const sim = typeof rec.similarity === 'number' ? rec.similarity : parseFloat(rec.similarity)
  const simPct = sim > 1 ? sim : sim * 100

  return (
    <a
      href={rec.url}
      target="_blank"
      rel="noreferrer"
      className="iv-panel-2 p-4 grid gap-3 transition-transform hover:-translate-y-px"
      style={{
        gridTemplateColumns: '32px minmax(0, 1fr) 90px',
        textDecoration: 'none',
      }}
    >
      <div
        className="iv-mono pt-0.5"
        style={{ fontSize: '11px', color: 'var(--text-dim)', letterSpacing: '0.1em' }}
      >
        [{String(index).padStart(2, '0')}]
      </div>
      <div className="min-w-0">
        <div
          className="font-medium leading-[1.35] hover:underline"
          style={{ fontSize: '14px', color: 'var(--text)', letterSpacing: '-0.005em' }}
        >
          {rec.title}
        </div>
        {rec.authors && (
          <div
            className="iv-serif mt-0.5"
            style={{ fontSize: '13px', color: 'var(--text-mute)' }}
          >
            {rec.authors}
          </div>
        )}
      </div>
      <div className="flex flex-col items-end gap-1">
        <span
          className="iv-mono font-medium"
          style={{ fontSize: '14px', color: 'var(--accent)' }}
        >
          {(simPct / 100).toFixed(2)}
        </span>
        <div className="iv-bar" style={{ width: '60px', height: '3px' }}>
          <span style={{ width: `${Math.min(simPct, 100)}%` }} />
        </div>
      </div>
    </a>
  )
}

export default ProfilePage
