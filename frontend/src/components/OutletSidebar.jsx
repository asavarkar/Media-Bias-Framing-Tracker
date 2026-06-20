import { useState, useEffect } from 'react'
import { getOutlets, getOutletArticles } from '../api'
import { formatOutletName } from '../utils'

function sentimentLabel(score) {
  if (score == null) return ''
  if (score >  0.15) return '↑'
  if (score < -0.15) return '↓'
  return '·'
}

function sentimentColor(score) {
  if (score == null) return '#94a3b8'
  if (score >  0.15) return '#22c55e'
  if (score < -0.15) return '#ef4444'
  return '#94a3b8'
}

function ArticlePanel({ outletName, onClose }) {
  const [articles, setArticles] = useState(null)

  useEffect(() => {
    getOutletArticles(outletName)
      .then(setArticles)
      .catch(console.error)
  }, [outletName])

  return (
    <div className="article-panel">
      <div className="article-panel-header">
        <span>{formatOutletName(outletName)} — Recent Articles</span>
        <button className="article-panel-close" onClick={onClose}>✕</button>
      </div>

      {articles === null && (
        <div className="loading" style={{ padding: '10px 0' }}>Loading...</div>
      )}

      {articles && articles.length === 0 && (
        <div className="empty" style={{ padding: '10px 0', textAlign: 'left' }}>
          No articles found for this outlet yet.
        </div>
      )}

      {articles && articles.length > 0 && (
        <ul className="article-list">
          {articles.map((a, i) => (
            <li key={i} className="article-list-item">
              <a href={a.url} target="_blank" rel="noopener noreferrer">
                {a.title}
              </a>
              {a.sentiment_score != null && (
                <span
                  className="article-sentiment"
                  style={{ color: sentimentColor(a.sentiment_score) }}
                  title={`Sentiment score: ${a.sentiment_score > 0 ? '+' : ''}${a.sentiment_score.toFixed(2)}`}
                >
                  {sentimentLabel(a.sentiment_score)} {Math.abs(a.sentiment_score).toFixed(2)}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function OutletSidebar() {
  const [outlets, setOutlets] = useState([])
  const [selectedOutlet, setSelectedOutlet] = useState(null)

  useEffect(() => {
    getOutlets().then(setOutlets).catch(console.error)
  }, [])

  function handleOutletClick(outletKey) {
    setSelectedOutlet(prev => prev === outletKey ? null : outletKey)
  }

  return (
    <div className="sidebar">
      <h2
        className="section-title-tooltip"
        data-tooltip="Click any outlet to see the individual articles used — and verify the sentiment scores yourself."
      >
        Outlets
      </h2>

      {!outlets.length && <div className="loading">Loading...</div>}

      {outlets.map(o => (
        <div key={o.outlet}>
          <div
            className={`outlet-item ${selectedOutlet === o.outlet ? 'outlet-item--active' : ''}`}
            onClick={() => handleOutletClick(o.outlet)}
            title="Click to see articles from this outlet"
          >
            <div>
              <div className="outlet-name">{formatOutletName(o.outlet)}</div>
              <div className="outlet-count">{o.article_count} articles</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className={`lean-badge ${o.lean_label}`}>{o.lean_label}</span>
              <span className="outlet-chevron">
                {selectedOutlet === o.outlet ? '▲' : '▼'}
              </span>
            </div>
          </div>

          {selectedOutlet === o.outlet && (
            <ArticlePanel
              outletName={o.outlet}
              onClose={() => setSelectedOutlet(null)}
            />
          )}
        </div>
      ))}
    </div>
  )
}
