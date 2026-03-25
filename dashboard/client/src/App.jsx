import React, { useState, useEffect, useRef } from 'react'

const COLORS = {
  claude: '#D97706', codex: '#059669', gemini: '#2563EB', rp: '#7C3AED',
  SHIP: '#10B981', NEEDS_WORK: '#F59E0B', MAJOR_RETHINK: '#EF4444',
  PASS: '#10B981', UNKNOWN: '#6B7280',
}

const ENGINE_LABELS = { claude: 'Claude', codex: 'Codex', gemini: 'Gemini', rp: 'RP Builder' }

function useWebSocket() {
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`
    let ws
    function connect() {
      ws = new WebSocket(wsUrl)
      ws.onopen = () => setConnected(true)
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data)
          if (data.type === 'new_event') {
            setEvents(prev => [...prev.slice(-200), data.event])
          }
        } catch {}
      }
    }
    connect()

    // Load history
    fetch('/api/events?limit=200')
      .then(r => r.json())
      .then(d => setEvents(d.events?.map(e => ({ ...e, ...(e.data ? JSON.parse(e.data) : {}) })) || []))
      .catch(() => {})

    return () => ws?.close()
  }, [])

  return { events, connected }
}

function Badge({ children, color }) {
  return <span style={{
    display: 'inline-block', padding: '2px 8px', borderRadius: 12,
    fontSize: 11, fontWeight: 600, color: '#fff',
    background: color || '#6B7280',
  }}>{children}</span>
}

function PipelineView({ events }) {
  const stages = ['router_decision', 'pipeline_stage', 'engine_start', 'engine_complete',
                   'debate_round', 'debate_vote', 'pua_round', 'failure_switch',
                   'learn_update', 'worktree_event']
  const stageEvents = {}
  events.forEach(e => {
    const type = e.event_type || e.type
    if (!stageEvents[type]) stageEvents[type] = []
    stageEvents[type].push(e)
  })

  return (
    <div style={{ display: 'flex', gap: 8, overflowX: 'auto', padding: '12px 0' }}>
      {stages.map(stage => {
        const count = (stageEvents[stage] || []).length
        const active = count > 0
        return (
          <div key={stage} style={{
            padding: '8px 14px', borderRadius: 8, minWidth: 120, textAlign: 'center',
            background: active ? '#1E293B' : '#0F172A',
            border: active ? '1px solid #334155' : '1px solid #1E293B',
            opacity: active ? 1 : 0.4,
          }}>
            <div style={{ fontSize: 11, color: '#94A3B8' }}>{stage.replace(/_/g, ' ')}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: active ? '#E2E8F0' : '#475569' }}>{count}</div>
          </div>
        )
      })}
    </div>
  )
}

function EnginePanel({ events }) {
  const engines = {}
  events.forEach(e => {
    const eng = e.engine || (e.data && JSON.parse(e.data || '{}').engine)
    if (eng && ENGINE_LABELS[eng]) {
      if (!engines[eng]) engines[eng] = { starts: 0, completes: 0, verdicts: [], issues: 0 }
      if ((e.event_type || e.type) === 'engine_start') engines[eng].starts++
      if ((e.event_type || e.type) === 'engine_complete') {
        engines[eng].completes++
        const d = typeof e.data === 'string' ? JSON.parse(e.data || '{}') : (e.data || {})
        if (d.verdict) engines[eng].verdicts.push(d.verdict)
        engines[eng].issues += d.issues || 0
      }
    }
  })

  return (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
      {Object.entries(ENGINE_LABELS).map(([key, label]) => {
        const data = engines[key] || { starts: 0, completes: 0, verdicts: [], issues: 0 }
        const lastVerdict = data.verdicts[data.verdicts.length - 1]
        return (
          <div key={key} style={{
            flex: '1 1 200px', padding: 16, borderRadius: 12,
            background: '#1E293B', border: `2px solid ${COLORS[key]}40`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, color: COLORS[key] }}>{label}</span>
              {lastVerdict && <Badge color={COLORS[lastVerdict]}>{lastVerdict}</Badge>}
            </div>
            <div style={{ marginTop: 8, fontSize: 13, color: '#94A3B8' }}>
              {data.starts} calls · {data.issues} issues
            </div>
          </div>
        )
      })}
    </div>
  )
}

function DebateTimeline({ events }) {
  const debates = events.filter(e => ['debate_round', 'debate_vote', 'pua_round'].includes(e.event_type || e.type))
  if (!debates.length) return <div style={{ color: '#475569', padding: 16 }}>No debate events yet</div>

  return (
    <div style={{ maxHeight: 300, overflowY: 'auto' }}>
      {debates.map((e, i) => {
        const d = typeof e.data === 'string' ? JSON.parse(e.data || '{}') : (e.data || {})
        const type = e.event_type || e.type
        return (
          <div key={i} style={{
            padding: '8px 12px', margin: '4px 0', borderRadius: 8,
            background: type === 'pua_round' ? '#312E81' : '#1E293B',
            borderLeft: `3px solid ${type === 'debate_vote' ? COLORS[d.verdict] || '#6B7280' : '#334155'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#E2E8F0' }}>
                {type === 'debate_round' && `Round ${d.round}`}
                {type === 'debate_vote' && `Verdict: ${d.verdict}`}
                {type === 'pua_round' && `PUA Round ${d.round}: ${d.author} proposed`}
              </span>
              {d.verdict && <Badge color={COLORS[d.verdict]}>{d.verdict}</Badge>}
            </div>
            {d.verdicts && (
              <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 4 }}>
                {Object.entries(d.verdicts).map(([e, v]) => `${e}: ${v}`).join(' · ')}
              </div>
            )}
            {d.reason && <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 2 }}>{d.reason}</div>}
          </div>
        )
      })}
    </div>
  )
}

function EventLog({ events }) {
  const ref = useRef(null)
  useEffect(() => { ref.current?.scrollTo(0, ref.current.scrollHeight) }, [events])

  return (
    <div ref={ref} style={{ maxHeight: 400, overflowY: 'auto', fontSize: 12 }}>
      {events.slice(-50).map((e, i) => {
        const type = e.event_type || e.type || '?'
        const d = typeof e.data === 'string' ? (() => { try { return JSON.parse(e.data) } catch { return {} } })() : (e.data || {})
        return (
          <div key={i} style={{
            padding: '4px 8px', borderBottom: '1px solid #1E293B',
            color: '#CBD5E1',
          }}>
            <span style={{ color: '#475569', marginRight: 8 }}>{e.timestamp || ''}</span>
            <Badge color={
              type.includes('engine') ? COLORS[e.engine] || '#6B7280' :
              type.includes('debate') ? '#7C3AED' :
              type.includes('pua') ? '#DB2777' :
              type.includes('pipeline') ? '#0891B2' :
              type.includes('failure') ? '#EF4444' :
              '#6B7280'
            }>{type.replace(/_/g, ' ')}</Badge>
            {e.engine && <span style={{ marginLeft: 6, color: COLORS[e.engine] }}>{e.engine}</span>}
            {d.verdict && <span style={{ marginLeft: 6 }}><Badge color={COLORS[d.verdict]}>{d.verdict}</Badge></span>}
            {d.query && <span style={{ marginLeft: 6, color: '#64748B' }}>"{d.query?.slice(0, 40)}"</span>}
            {d.chain && <span style={{ marginLeft: 6, color: '#22D3EE' }}>→ {d.chain}</span>}
            {d.methodology && <span style={{ marginLeft: 6, color: '#F97316' }}>⚡ {d.methodology}</span>}
          </div>
        )
      })}
    </div>
  )
}

export default function App() {
  const { events, connected } = useWebSocket()
  const [tab, setTab] = useState('pipeline')

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      background: '#0F172A', color: '#E2E8F0', minHeight: '100vh', padding: 20,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>⚡ cc-code Dashboard</h1>
          <span style={{ fontSize: 13, color: '#64748B' }}>3-Engine Workflow Visualization</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: '#64748B' }}>{events.length} events</span>
          <Badge color={connected ? '#10B981' : '#EF4444'}>{connected ? 'LIVE' : 'OFFLINE'}</Badge>
        </div>
      </div>

      {/* Engine Status */}
      <EnginePanel events={events} />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, margin: '16px 0', borderBottom: '1px solid #1E293B' }}>
        {['pipeline', 'debate', 'events'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '8px 16px', border: 'none', borderRadius: '8px 8px 0 0', cursor: 'pointer',
            background: tab === t ? '#1E293B' : 'transparent',
            color: tab === t ? '#E2E8F0' : '#64748B',
            fontWeight: tab === t ? 600 : 400, fontSize: 13,
          }}>
            {t === 'pipeline' ? '🔄 Pipeline' : t === 'debate' ? '⚔️ Debate' : '📋 Events'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ background: '#0F172A', borderRadius: 12, padding: 16 }}>
        {tab === 'pipeline' && <PipelineView events={events} />}
        {tab === 'debate' && <DebateTimeline events={events} />}
        {tab === 'events' && <EventLog events={events} />}
      </div>
    </div>
  )
}
