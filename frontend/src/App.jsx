import { useState, useEffect } from 'react'
import MetricCards from './components/MetricCards'
import TopicBarChart from './components/TopicBarChart'
import FramingDivergenceChart from './components/FramingDivergenceChart'
import StoryTable from './components/StoryTable'
import OutletSidebar from './components/OutletSidebar'

export default function App() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Media<span>Lens</span></h1>
          <div className="subtitle">News Framing Analyzer — ML-powered divergence scoring across outlets</div>
        </div>
        <div className="last-updated">
          Last checked: {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </header>

      <OutletSidebar />

      <main className="main-content">
        <MetricCards />

        <div className="chart-row">
          <div className="chart-card">
            <h3
              className="section-title-tooltip"
              data-tooltip="How many articles each story cluster received across all outlets today — larger bars mean more coverage."
            >
              Stories by Topic
            </h3>
            <TopicBarChart />
          </div>
          <div className="chart-card">
            <h3
              className="section-title-tooltip"
              data-tooltip="How positively or negatively each outlet framed the selected topic — bars left of center are critical, right of center are favorable."
            >
              Outlet Framing — Sentiment by Topic
            </h3>
            <FramingDivergenceChart />
          </div>
        </div>

        <div className="story-table-card">
          <h3
            className="section-title-tooltip"
            data-tooltip="Stories where outlets disagreed most sharply in their framing — a higher score means wider sentiment gap between outlets covering the same event."
          >
            High-Divergence Stories
          </h3>
          <StoryTable />
        </div>
      </main>
    </div>
  )
}
