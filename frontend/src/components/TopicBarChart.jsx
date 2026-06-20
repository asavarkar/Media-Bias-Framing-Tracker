import { useState, useEffect } from 'react'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  Tooltip, Legend,
} from 'chart.js'
import { getTopics } from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function TopicBarChart() {
  const [topics, setTopics] = useState([])

  useEffect(() => {
    getTopics().then(setTopics).catch(console.error)
  }, [])

  if (!topics.length) return <div className="loading">Loading topics...</div>

  const top = topics.slice(0, 12)

  const data = {
    labels: top.map(t => t.label),
    datasets: [
      {
        label: 'Articles',
        data: top.map(t => t.article_count),
        backgroundColor: top.map(t =>
          (t.divergence_score ?? 0) >= 6
            ? 'rgba(239,68,68,0.7)'
            : 'rgba(37,99,235,0.65)'
        ),
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  }

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: {
      callbacks: {
        afterLabel: (ctx) => {
          const t = top[ctx.dataIndex]
          return t.divergence_score != null
            ? `Divergence: ${t.divergence_score}/10`
            : ''
        },
      },
    }},
    scales: {
      x: { grid: { color: 'rgba(15,23,42,0.06)' }, ticks: { color: '#64748B' } },
      y: { grid: { display: false }, ticks: { color: '#0F172A', font: { size: 11 } } },
    },
  }

  return (
    <div className="chart-inner">
      <Bar data={data} options={options} />
    </div>
  )
}
