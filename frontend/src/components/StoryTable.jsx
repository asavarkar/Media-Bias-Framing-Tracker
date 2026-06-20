import { useState, useEffect } from 'react'
import { getStories, getOutlets } from '../api'
import { formatOutletName } from '../utils'

function DivergenceBar({ score }) {
  const pct = Math.min((score / 10) * 100, 100)
  const color =
    score >= 7 ? '#ef4444' :
    score >= 5 ? '#f59e0b' :
                 '#6366f1'

  const label =
    score >= 7 ? 'High' :
    score >= 5 ? 'Medium' :
                 'Low'

  return (
    <div style={{ minWidth: 160, paddingRight: 12 }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        marginBottom: 6,
      }}>
        <span style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Divergence
        </span>
        <span style={{ fontSize: '0.82rem', fontWeight: 700, color }}>
          {label} — {score?.toFixed(1)} / 10
        </span>
      </div>
      <div style={{
        width: '100%',
        height: 6,
        background: 'var(--border)',
        borderRadius: 999,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: color,
          borderRadius: 999,
          transition: 'width 0.4s ease',
        }} />
      </div>
    </div>
  )
}

export default function StoryTable() {
  const [stories, setStories] = useState([])
  const [outletLeans, setOutletLeans] = useState({})

  useEffect(() => {
    getStories(5.0).then(setStories).catch(console.error)
    getOutlets().then(outlets => {
      const leans = {}
      outlets.forEach(o => { leans[o.outlet] = o.lean_label })
      setOutletLeans(leans)
    }).catch(console.error)
  }, [])

  if (!stories.length) return (
    <div className="empty">
      No high-divergence stories found yet. Run the pipeline to populate data.
    </div>
  )

  return (
    <div>
      {stories.map(story => (
        <div key={story.cluster_id} className="story-row">
          <div>
            <div className="story-headline">{story.headline || story.label}</div>
            <div className="story-meta">
              {story.outlet_tags.slice(0, 6).map(tag => (
                <span key={tag} className={`outlet-tag ${outletLeans[tag] || 'neutral'}`}>
                  {formatOutletName(tag)}
                </span>
              ))}
            </div>
          </div>
          <DivergenceBar score={story.divergence_score ?? 0} />
        </div>
      ))}
    </div>
  )
}
