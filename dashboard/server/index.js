/**
 * cc-code Dashboard Server
 *
 * Express + WebSocket server that:
 * 1. Receives events from cc-flow hooks (POST /api/events)
 * 2. Stores in SQLite
 * 3. Broadcasts to dashboard via WebSocket
 * 4. Serves static React client
 */

const express = require('express');
const { WebSocketServer } = require('ws');
const http = require('http');
const path = require('path');
const Database = require('better-sqlite3');
const cors = require('cors');

const PORT = process.env.CC_DASHBOARD_PORT || 3777;
const DB_PATH = process.env.CC_DASHBOARD_DB || path.join(__dirname, 'dashboard.db');

// ── Database ──
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.exec(`
  CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    session_id TEXT,
    event_type TEXT NOT NULL,
    phase TEXT,
    engine TEXT,
    data TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
  CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
`);

const insertEvent = db.prepare(`
  INSERT INTO events (session_id, event_type, phase, engine, data)
  VALUES (?, ?, ?, ?, ?)
`);

// ── Express ──
const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' }));

// Serve static client
app.use(express.static(path.join(__dirname, '../client/dist')));

// POST /api/events — receive events from cc-flow
app.post('/api/events', (req, res) => {
  const { session_id, event_type, phase, engine, data } = req.body;
  try {
    insertEvent.run(
      session_id || 'default',
      event_type || 'unknown',
      phase || null,
      engine || null,
      typeof data === 'string' ? data : JSON.stringify(data || {})
    );
    broadcast({ type: 'new_event', event: req.body });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/events — fetch event history
app.get('/api/events', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  const session = req.query.session || null;
  let rows;
  if (session) {
    rows = db.prepare('SELECT * FROM events WHERE session_id = ? ORDER BY id DESC LIMIT ?').all(session, limit);
  } else {
    rows = db.prepare('SELECT * FROM events ORDER BY id DESC LIMIT ?').all(limit);
  }
  res.json({ events: rows.reverse() });
});

// GET /api/sessions — list sessions
app.get('/api/sessions', (req, res) => {
  const rows = db.prepare(`
    SELECT session_id, COUNT(*) as event_count,
           MIN(timestamp) as started, MAX(timestamp) as last_event
    FROM events GROUP BY session_id ORDER BY last_event DESC LIMIT 20
  `).all();
  res.json({ sessions: rows });
});

// GET /api/stats — dashboard stats
app.get('/api/stats', (req, res) => {
  const total = db.prepare('SELECT COUNT(*) as count FROM events').get();
  const byType = db.prepare('SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type ORDER BY count DESC').all();
  const byEngine = db.prepare("SELECT engine, COUNT(*) as count FROM events WHERE engine IS NOT NULL GROUP BY engine ORDER BY count DESC").all();
  res.json({ total: total.count, by_type: byType, by_engine: byEngine });
});

// Fallback to client
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/dist/index.html'));
});

// ── HTTP + WebSocket ──
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });

let clients = new Set();
wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('close', () => clients.delete(ws));
  ws.on('error', () => clients.delete(ws));
});

function broadcast(data) {
  const msg = JSON.stringify(data);
  clients.forEach(ws => {
    if (ws.readyState === 1) ws.send(msg);
  });
}

server.listen(PORT, () => {
  console.log(`cc-code Dashboard: http://localhost:${PORT}`);
  console.log(`WebSocket: ws://localhost:${PORT}/ws`);
  console.log(`Events API: POST http://localhost:${PORT}/api/events`);
});
