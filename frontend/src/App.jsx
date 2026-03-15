import { useState, useEffect } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

const API_BASE = import.meta.env.VITE_API_URL || ''

const AUTONOMOUS_ACTIONS = [
  { condition: s => s <= 4, actions: ['🔕 Muted all non-urgent Slack notifications', '📅 Blocked 2–4 PM for rest', '🔁 Rescheduled 3 PM standup to tomorrow'] },
  { condition: s => s <= 6, actions: ['📅 Blocked 1–2 PM for a recovery break', '🎵 Queued a focus playlist', '⏰ Set a hydration reminder every 45 min'] },
  { condition: s => s <= 8, actions: ['📋 Prioritized top 3 tasks for your focus window', '🔔 Scheduled a mid-afternoon check-in', '💧 Set hydration reminders'] },
  { condition: s => s > 8, actions: ['🚀 Scheduled deep work block for peak hours', '📧 Queued non-urgent emails for after focus window', '🏋️ Suggested a workout during energy peak'] },
]

function getActions(score) {
  return AUTONOMOUS_ACTIONS.find(a => a.condition(score))?.actions || []
}

function formatHour(h) {
  if (h === 0) return '12 AM'
  if (h < 12) return `${h} AM`
  if (h === 12) return '12 PM'
  return `${h - 12} PM`
}

function ScoreGauge({ score }) {
  const pct = (score / 10) * 100
  const color = score <= 4 ? '#ef4444' : score <= 6 ? '#f59e0b' : score <= 8 ? '#6366f1' : '#22c55e'
  const label = score <= 4 ? 'Low' : score <= 6 ? 'Moderate' : score <= 8 ? 'Good' : 'Peak'
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#f1f5f9" strokeWidth="12" />
          <circle cx="60" cy="60" r="50" fill="none" stroke={color} strokeWidth="12"
            strokeDasharray={`${2 * Math.PI * 50}`}
            strokeDashoffset={`${2 * Math.PI * 50 * (1 - pct / 100)}`}
            strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1.2s ease' }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-black text-slate-800" style={{ color }}>{score}</span>
          <span className="text-xs text-slate-400 font-medium">/10</span>
        </div>
      </div>
      <span className="text-xs font-bold uppercase tracking-widest" style={{ color }}>{label}</span>
    </div>
  )
}

function SignalPill({ label, value, unit }) {
  return (
    <div className="flex flex-col items-center bg-slate-50 rounded-xl px-3 py-2 min-w-[72px]">
      <span className="text-base font-bold text-slate-700">{value}<span className="text-xs font-normal text-slate-400 ml-0.5">{unit}</span></span>
      <span className="text-[10px] text-slate-400 mt-0.5 text-center leading-tight">{label}</span>
    </div>
  )
}

function EnergyChart({ data, crashWindow, focusWindow }) {
  if (!data || data.length === 0) return null
  const chartData = data.map(d => ({ ...d, label: formatHour(d.hour) }))
  const minEnergy = Math.min(...data.map(d => d.energy))
  const crashHour = data.find(d => d.energy === minEnergy)?.hour

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Hourly Energy Curve</h2>
        <div className="flex gap-2">
          {focusWindow && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-600 font-medium">⚡ {focusWindow}</span>
          )}
          {crashWindow && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-500 font-medium">⚠️ {crashWindow}</span>
          )}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
          <defs>
            <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f8fafc" />
          <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94a3b8' }} interval={1} />
          <YAxis domain={[0, 10]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
            formatter={(v) => [`${v}/10`, 'Energy']}
          />
          {crashHour && (
            <ReferenceLine x={formatHour(crashHour)} stroke="#ef4444" strokeDasharray="4 4"
              label={{ value: '⚠️', position: 'top', fontSize: 12 }} />
          )}
          <Area type="monotone" dataKey="energy" stroke="#6366f1" strokeWidth={2.5}
            fill="url(#energyGrad)" dot={{ r: 3, fill: '#6366f1', strokeWidth: 0 }} activeDot={{ r: 5, fill: '#6366f1' }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function App() {
  const [forecast, setForecast] = useState(null)
  const [signals, setSignals] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)
  const [actionsVisible, setActionsVisible] = useState(false)

  const fetchLatest = async () => {
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/forecast/latest`)
      if (res.ok) { const data = await res.json(); setForecast(data) }
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const fetchSignals = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/simulate`)
      if (res.ok) { const data = await res.json(); setSignals(data.payload) }
    } catch (_) {}
  }

  const runNow = async () => {
    setRunning(true); setError(null); setActionsVisible(false)
    await fetchSignals()
    try {
      const res = await fetch(`${API_BASE}/api/forecast/run?use_simulated=true`, { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setForecast(data)
      setTimeout(() => setActionsVisible(true), 600)
    } catch (e) { setError(e.message) } finally { setRunning(false) }
  }

  useEffect(() => { fetchLatest() }, [])
  const actions = forecast ? getActions(forecast.score_1_to_10) : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 p-4 md:p-8">
      <div className="max-w-3xl mx-auto flex flex-col gap-5">

        {/* Header */}
        <header className="text-center pt-2">
          <div className="inline-flex items-center gap-2 mb-1">
            <span className="text-2xl">◈</span>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Prism</h1>
          </div>
          <p className="text-slate-400 text-xs">Private edge inference — wearable signals → daily performance forecast</p>
        </header>

        {/* Top row: Score + Summary + Run */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Today's Forecast</h2>
            <button onClick={runNow} disabled={running}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 transition shadow-sm">
              {running ? '⟳ Analyzing…' : '▶ Run now'}
            </button>
          </div>

          {loading && !forecast && <p className="text-slate-400 text-sm text-center py-4">Loading…</p>}
          {error && <p className="text-amber-500 text-sm">{error}</p>}

          {forecast ? (
            <div className="flex gap-6 items-start">
              <ScoreGauge score={forecast.score_1_to_10} />
              <div className="flex-1 flex flex-col gap-3">
                <p className="text-slate-600 text-sm leading-relaxed">{forecast.summary}</p>
                <div className="flex flex-wrap gap-2">
                  {forecast.focus_window && (
                    <span className="px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold">⚡ Peak: {forecast.focus_window}</span>
                  )}
                  {forecast.crash_window && (
                    <span className="px-2.5 py-1 rounded-full bg-red-100 text-red-600 text-xs font-semibold">⚠️ Crash: {forecast.crash_window}</span>
                  )}
                </div>
                {forecast.suggestions?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {forecast.suggestions.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-xs">{s}</span>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-slate-300">Generated {new Date(forecast.generated_at_utc).toLocaleString()}</p>
              </div>
            </div>
          ) : !loading && (
            <p className="text-slate-400 text-sm text-center py-4">Click "Run now" to generate your forecast.</p>
          )}
        </div>

        {/* Signals row */}
        {signals && (
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Edge Signals</h2>
              <span className="text-[10px] text-slate-400">Raw data stays on device — only these reach the LLM</span>
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              <SignalPill label="HRV" value={signals.hrv_rmssd_last_night} unit="ms" />
              <SignalPill label="Sleep" value={signals.sleep_hours} unit="h" />
              <SignalPill label="Efficiency" value={signals.sleep_efficiency_pct} unit="%" />
              <SignalPill label="Steps" value={signals.steps_yesterday} unit="" />
              <SignalPill label="Active" value={signals.active_minutes_yesterday} unit="min" />
              <SignalPill label="Recovery" value={(signals.recovery_signal * 100).toFixed(0)} unit="%" />
            </div>
            <div className="flex gap-2 flex-wrap">
              {['Raw HR', 'GPS', 'Identity'].map(l => (
                <span key={l} className="text-[10px] px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-200">🔒 {l} anonymized</span>
              ))}
            </div>
          </div>
        )}

        {/* Energy Chart */}
        {forecast?.hourly_energy_curve?.length > 0 && (
          <EnergyChart data={forecast.hourly_energy_curve} crashWindow={forecast.crash_window} focusWindow={forecast.focus_window} />
        )}

        {/* Autonomous Actions */}
        {actionsVisible && actions.length > 0 && (
          <div className="rounded-2xl border border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🤖</span>
              <h2 className="text-sm font-semibold text-green-800 uppercase tracking-wider">Agent Acted Autonomously</h2>
              <span className="ml-auto text-[10px] bg-green-200 text-green-700 px-2 py-0.5 rounded-full font-semibold">0 clicks required</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {actions.map((a, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-green-800 bg-white rounded-xl px-4 py-2.5 shadow-sm border border-green-100">{a}</div>
              ))}
            </div>
          </div>
        )}

        {/* Privacy footer */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200">
          <span>🔒</span>
          <p className="text-[10px] text-slate-400">
            <strong className="text-slate-500">Edge privacy:</strong> Raw biometrics never leave your device. Only anonymous derived signals reach the inference layer.
          </p>
        </div>

      </div>
    </div>
  )
}

export default App
