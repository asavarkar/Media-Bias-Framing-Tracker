import { useState, useEffect } from 'react'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend,
} from 'chart.js'
import { getFraming, getTopics } from '../api'
import { formatOutletName } from '../utils'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function FramingDivergenceChart() {
  const [framing, setFraming] = useState([])
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState('')

  useEffect(() => {
    getTopics().then(setTopics).catch(console.error)
  }, [])

  useEffect(() => {
    getFraming(selectedTopic || null).then(setFraming).catch(console.error)
  }, [selectedTopic])

  const data = {
    labels: framing.map(f => formatOutletName(f.outlet)),
    datasets: [
      {
        label: 'Avg Sentiment',
        data: framing.map(f => f.avg_sentiment),
        backgroundColor: framing.map(f =>
          f.avg_sentiment > 0
            ? `rgba(34,197,94,${0.4 + Math.abs(f.avg_sentiment) * 0.5})`
            : `rgba(239,68,68,${0.4 + Math.abs(f.avg_sentiment) * 0.5})`
        ),
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const val = ctx.raw
            const abs = Math.abs(val).toFixed(2)
            if (val > 0.15)  return `Positive framing (+${abs}) — coverage skews favorable`
            if (val < -0.15) return `Negative framing (−${abs}) — coverage skews critical`
            return `Neutral framing (${val >= 0 ? '+' : ''}${val.toFixed(2)}) — coverage is balanced`
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#0F172A', font: { size: 11 } },
      },
      y: {
        min: -1,
        max: 1,
        grid: { color: 'rgba(15,23,42,0.06)' },
        ticks: {
          color: '#64748B',
          stepSize: 0.5,
          callback: v => {
            if (v > 0) return `+${v.toFixed(1)}`
            return v.toFixed(1)
          },
        },
      },
    },
  }

  return (
    <>
      <div className="topic-selector">
        <label>Topic:</label>
        <select value={selectedTopic} onChange={e => setSelectedTopic(e.target.value)}>
          <option value="">All Topics</option>
          {topics.map(t => (
            <option key={t.cluster_id} value={t.label}>{t.label}</option>
          ))}
        </select>
      </div>

      {!framing.length
        ? <div className="empty">No framing data for this topic yet — try another topic or wait for the next pipeline run.</div>
        : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: '0.72rem', color: '#ef4444' }}>← More negative / critical</span>
              {/* ⓘ badge — hover for y-axis explanation */}
              <span
                className="axis-info-badge section-title-tooltip"
                data-tooltip="Y-axis shows sentiment score: −1.0 = strongly negative/critical framing, 0 = neutral, +1.0 = strongly positive/favorable framing."
              >
                ⓘ What does the y-axis mean?
              </span>
              <span style={{ fontSize: '0.72rem', color: '#22c55e' }}>More positive / favorable →</span>
            </div>
            <div className="chart-inner"><Bar data={data} options={options} /></div>
          </>
        )
      }
    </>
  )
}
