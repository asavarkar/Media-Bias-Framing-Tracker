import { useState, useEffect } from 'react'
import { getSummary } from '../api'

export default function MetricCards() {
  const [data, setData] = useState(null)

  useEffect(() => {
    getSummary().then(setData).catch(console.error)
  }, [])

  if (!data) return <div className="loading">Loading metrics...</div>

  return (
    <div className="metric-cards">
      <div className="card">
        <div
          className="label section-title-tooltip"
          data-tooltip="Total articles fetched from all outlets in the last 28 hours."
        >
          Articles Today
        </div>
        <div className="value accent">{data.total_articles.toLocaleString()}</div>
        <div className="sublabel">across all outlets</div>
      </div>

      <div className="card">
        <div
          className="label section-title-tooltip"
          data-tooltip="Average sentiment magnitude across all articles — higher means more emotionally charged coverage overall."
        >
          Avg Emotional Intensity
        </div>
        <div className="value">
          {data.avg_emotional_intensity}
          <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/10</span>
        </div>
        <div className="sublabel">sentiment magnitude</div>
      </div>

      <div className="card">
        <div
          className="label section-title-tooltip"
          data-tooltip="Number of story clusters where outlets disagreed significantly — scored 5.0 or higher on the 0–10 divergence scale."
        >
          High-Divergence Stories
        </div>
        <div className={`value ${data.high_divergence_count > 10 ? 'red' : ''}`}>
          {data.high_divergence_count}
        </div>
        <div className="sublabel">score ≥ 5.0 / 10</div>
      </div>

      <div className="card">
        <div
          className="label section-title-tooltip"
          data-tooltip="Number of distinct story groups found by the ML clustering algorithm from today's articles."
        >
          Topics Clustered
        </div>
        <div className="value accent">{data.topic_count}</div>
        <div className="sublabel">distinct story groups</div>
      </div>
    </div>
  )
}
