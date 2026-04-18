import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Activity } from 'lucide-react';

// ═══════════════════════════════════════════════════════════
//  CẤU HÌNH — TỌA ĐỘ PIXEL (1000×500) + TỌA ĐỘ THỰC (ROS)
// ═══════════════════════════════════════════════════════════
const ROOM_PIXELS = {
  Phong_1:  [70,  165], Phong_2:  [130,  80], Phong_3:  [205,  50], Phong_4:  [275,  50],
  Phong_5:  [420,  70], Phong_6:  [365, 120], Phong_7:  [680,  70], Phong_8:  [605, 120],
  Phong_9:  [880, 200], Phong_10: [710, 220], Phong_11: [710, 280], Phong_12: [578, 220],
  Phong_13: [578, 280], Phong_14: [430, 230], Phong_15: [430, 280], Phong_16: [ 70, 339],
  Phong_17: [130, 421], Phong_18: [205, 450], Phong_19: [275, 450], Phong_20: [420, 430],
  Phong_21: [365, 385], Phong_22: [680, 430], Phong_23: [605, 385], Phong_24: [880, 430],
};

const ROOM_REAL = {
  Phong_1:  [-7.05,  4.57], Phong_2:  [-3.69,  7.84], Phong_3:  [ 0.23, 10.08], Phong_4:  [ 5.32,  9.98],
  Phong_5:  [14.14,  8.38], Phong_6:  [10.55,  7.17], Phong_7:  [28.66,  8.23], Phong_8:  [24.55,  7.21],
  Phong_9:  [38.84,  1.96], Phong_10: [28.89,  2.11], Phong_11: [28.23, -2.60], Phong_12: [22.26,  1.46],
  Phong_13: [22.21, -1.85], Phong_14: [14.05,  1.28], Phong_15: [14.14, -1.29], Phong_16: [-7.25, -4.58],
  Phong_17: [-3.80, -8.04], Phong_18: [ 0.92,-10.20], Phong_19: [ 4.75,-10.34], Phong_20: [14.18, -8.81],
  Phong_21: [10.54, -7.17], Phong_22: [28.28, -8.49], Phong_23: [24.54, -7.27], Phong_24: [37.24, -9.66],
};

const ROOM_COLORS = {
  Phong_1: '#ef4444', Phong_2: '#f97316', Phong_3: '#eab308', Phong_4: '#22c55e',
  Phong_5: '#06b6d4', Phong_6: '#3b82f6', Phong_7: '#8b5cf6', Phong_8: '#ec4899',
  Phong_9: '#14b8a6', Phong_10: '#f43f5e', Phong_11: '#a855f7', Phong_12: '#0ea5e9',
  Phong_13: '#84cc16', Phong_14: '#f59e0b', Phong_15: '#10b981', Phong_16: '#6366f1',
  Phong_17: '#e11d48', Phong_18: '#7c3aed', Phong_19: '#0891b2', Phong_20: '#16a34a',
  Phong_21: '#d946ef', Phong_22: '#ca8a04', Phong_23: '#0284c7', Phong_24: '#4f46e5',
};

const ROOMS = Object.keys(ROOM_PIXELS);

// ═══════════════════════════════════════════════════════════
//  MÀU SẮC THỐNG NHẤT
// ═══════════════════════════════════════════════════════════
const C = {
  bg:        '#080b14',
  panel:     '#0d1220',
  border:    '#1e2d4a',
  cyan:      '#00d4ff',
  cyanGlow:  '#00d4ff22',
  amber:     '#f59e0b',
  red:       '#f43f5e',
  green:     '#10b981',
  textDim:   '#475569',
};

// ═══════════════════════════════════════════════════════════
//  WEBSOCKET
// ═══════════════════════════════════════════════════════════
let socketInstance = null;
let pendingResolve = null;

function createSocket() {
  const ws = new WebSocket('ws://127.0.0.1:8080');
  ws.onmessage = (e) => {
    if (pendingResolve) { const r = pendingResolve; pendingResolve = null; r(e.data); }
  };
  return ws;
}

function getSocket() {
  if (!socketInstance || socketInstance.readyState === WebSocket.CLOSED) {
    socketInstance = createSocket();
  }
  return socketInstance;
}

function sendMessage(msg) {
  return new Promise((resolve) => {
    const ws = getSocket();
    if (ws.readyState === WebSocket.OPEN) { ws.send(JSON.stringify(msg)); pendingResolve = resolve; }
    else resolve(null);
  });
}

// ═══════════════════════════════════════════════════════════
//  NÚT PHÒNG — HIỂN THỊ TÊN + TỌA ĐỘ TRÊN MAP
// ═══════════════════════════════════════════════════════════
function RoomButton({ room, selected, visited, onClick }) {
  const label = room.replace('Phong_', '');
  const color = ROOM_COLORS[room] || C.cyan;
  const [px, py] = ROOM_PIXELS[room];
  const [rx, ry] = ROOM_REAL[room];

  // Nền trong suốt để nhìn xuyên map
  const bg = selected ? color : visited ? `${color}99` : `${color}33`;
  const textColor = selected ? '#000000' : color;
  const borderColor = selected ? color : `${color}88`;
  const shadow = selected
    ? `0 0 14px ${color}, 0 0 28px ${color}55`
    : `0 0 8px ${color}44`;

  return (
    <button
      onClick={onClick}
      title={`${room}  X:${rx.toFixed(2)}  Y:${ry.toFixed(2)}m`}
      style={{
        position: 'absolute',
        left: px,
        top: py,
        transform: 'translate(-50%, -50%)',
        zIndex: selected ? 20 : 10,
        padding: '3px 8px',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
        fontWeight: 700,
        color: textColor,
        background: bg,
        border: `1.5px solid ${borderColor}`,
        borderRadius: 6,
        cursor: 'pointer',
        boxShadow: shadow,
        whiteSpace: 'nowrap',
        transition: 'all 0.2s',
        scale: selected ? '1.25' : '1',
      }}
      onMouseEnter={e => {
        if (!selected) {
          e.currentTarget.style.background = `${color}55`;
          e.currentTarget.style.zIndex = 15;
        }
      }}
      onMouseLeave={e => {
        if (!selected) {
          e.currentTarget.style.background = `${color}33`;
          e.currentTarget.style.zIndex = 10;
        }
      }}
    >
      {label}
    </button>
  );
}

// ═══════════════════════════════════════════════════════════
//  NÚT ĐIỀU KHIỂN
// ═══════════════════════════════════════════════════════════
function CtrlBtn({ children, onClick, variant = 'primary', disabled, loading, icon }) {
  const styles = {
    primary:   { bg: `linear-gradient(135deg, ${C.cyan}, #0099cc)`, color: '#000' },
    danger:    { bg: `linear-gradient(135deg, ${C.red}, #cc1133)`, color: '#fff' },
    success:   { bg: `linear-gradient(135deg, ${C.green}, #059669)`, color: '#000' },
    secondary: { bg: 'linear-gradient(135deg, #1e293b, #0f172a)', color: '#e2e8f0', border: `1px solid ${C.border}` },
  };
  const s = styles[variant];
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        width: '100%',
        padding: '11px 16px',
        borderRadius: 10,
        border: s.border || 'none',
        background: s.bg,
        color: s.color,
        fontFamily: "'DM Sans', sans-serif",
        fontWeight: 700,
        fontSize: 13,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        transition: 'filter 0.2s',
      }}
      onMouseEnter={e => { if (!disabled) e.currentTarget.style.filter = 'brightness(1.15)'; }}
      onMouseLeave={e => { e.currentTarget.style.filter = 'none'; }}
    >
      {loading ? '⟳' : icon ? icon : null}
      {children}
    </button>
  );
}

// ═══════════════════════════════════════════════════════════
//  THẺ TRẠNG THÁI
// ═══════════════════════════════════════════════════════════
function StatCard({ label, value, color, icon }) {
  return (
    <div style={{
      background: '#0a0f1e',
      border: `1px solid ${C.border}`,
      borderRadius: 10,
      padding: '12px 14px',
      display: 'flex',
      alignItems: 'center',
      gap: 12,
    }}>
      <div style={{
        width: 36, height: 36,
        borderRadius: 8,
        background: `${color}22`,
        border: `1px solid ${color}44`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, flexShrink: 0,
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 10, color: C.textDim, fontFamily: "'DM Sans', sans-serif", letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          {label}
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color, fontFamily: "'JetBrains Mono', monospace", marginTop: 2 }}>
          {value}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
//  LOG BOX
// ═══════════════════════════════════════════════════════════
function LogBox({ logs }) {
  const ref = useRef(null);
  useEffect(() => { ref.current?.scrollTo(0, ref.current.scrollHeight); }, [logs]);
  return (
    <div ref={ref} style={{
      background: '#03070f',
      border: `1px solid ${C.border}`,
      borderRadius: 8,
      padding: '10px 12px',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 11,
      color: '#4ade80',
      height: 140,
      overflowY: 'auto',
      lineHeight: 1.7,
    }}>
      {logs.map((l, i) => <div key={i}>{l}</div>)}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
//  APP
// ═══════════════════════════════════════════════════════════
export default function App() {
  const [selectedRooms, setSelectedRooms]   = useState([]);
  const [visitedRooms,  setVisitedRooms]    = useState([]);
  const [modeIndex,     setModeIndex]       = useState(0);
  const [previewRoute,  setPreviewRoute]    = useState(null);
  const [distance,      setDistance]        = useState(null);
  const [logs,          setLogs]            = useState([
    '> Hệ thống FMS khởi động.',
    '> Kết nối WebSocket...',
    '> Chọn phòng trên bản đồ.',
  ]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [robotStatus,   setRobotStatus]     = useState('offline');

  const addLog = useCallback((text) => setLogs(prev => [...prev.slice(-199), text]), []);

  useEffect(() => {
    const ws = getSocket();
    ws.onopen    = () => { addLog('> [✓] WebSocket kết nối.');     setRobotStatus('active'); };
    ws.onerror   = () => { addLog('> [✗] Lỗi WebSocket!');       setRobotStatus('offline'); };
    ws.onclose   = () => { addLog('> [✗] WebSocket đã đóng.');  setRobotStatus('offline'); };
  }, []);

  const toggleRoom = useCallback((room) => {
    setSelectedRooms(prev => prev.includes(room) ? prev.filter(r => r !== room) : [...prev, room]);
    setPreviewRoute(null);
    setDistance(null);
  }, []);

  const clearAll = useCallback(() => {
    setSelectedRooms([]);
    setVisitedRooms([]);
    setPreviewRoute(null);
    setDistance(null);
    addLog('> [✖] Đã xóa lựa chọn.');
  }, [addLog]);

  const handlePreview = useCallback(async () => {
    if (selectedRooms.length === 0) { addLog('> [!] Chọn ít nhất 1 phòng!'); return; }
    const mode = modeIndex === 0 ? 'ga' : 'sequential';
    addLog(`> [...] Tính lộ trình (${mode === 'ga' ? 'GA' : 'thứ tự'})...`);
    setPreviewLoading(true);
    try {
      const resp = await sendMessage({ type: 'preview', rooms: selectedRooms, mode });
      setPreviewLoading(false);
      if (resp) {
        const data = JSON.parse(resp);
        setPreviewRoute(data.route || selectedRooms);
        setDistance(data.distance || 0);
        const clean = (data.route || []).map(r => r.replace('Phong_', '')).join(' → ');
        addLog(`> [✓] Lộ trình: ${clean}`);
        addLog(`> [✓] Khoảng cách: ${(data.distance || 0).toFixed(2)} m`);
      }
    } catch (e) { setPreviewLoading(false); addLog(`> [✗] Lỗi: ${e.message}`); }
  }, [selectedRooms, modeIndex, addLog]);

  const handleExecute = useCallback(async () => {
    if (selectedRooms.length === 0) { addLog('> [!] Chưa có phòng nào!'); return; }
    const mode = modeIndex === 0 ? 'ga' : 'sequential';
    addLog('');
    addLog('══════════════════════════════════');
    addLog(`> [►] THỰC THI (${mode.toUpperCase()}) — ${selectedRooms.length} phòng`);
    addLog('══════════════════════════════════');
    setExecuteLoading(true);
    try {
      await sendMessage({ type: 'execute', rooms: selectedRooms, mode });
      setExecuteLoading(false);
      addLog('> [✓] Lệnh đã gửi đến robot.');
      setVisitedRooms([]);
    } catch (e) { setExecuteLoading(false); addLog(`> [✗] Lỗi: ${e.message}`); }
  }, [selectedRooms, modeIndex, addLog]);

  const routeColor = modeIndex === 0 ? C.cyan : C.amber;

  return (
    <div style={{
      width: '100vw', height: '100vh',
      background: C.bg,
      display: 'flex',
      overflow: 'hidden',
    }}>

      {/* ── KHU VỰC MAP ── */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: '20px 16px 20px 20px',
        gap: 16,
        overflow: 'auto',
        minWidth: 0,
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 4, height: 28, background: C.cyan, borderRadius: 2, boxShadow: `0 0 10px ${C.cyan}` }} />
          <span style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0', letterSpacing: '0.05em' }}>FLOOR MAP</span>
          <span style={{ fontSize: 11, color: C.textDim, fontFamily: "'JetBrains Mono', monospace" }}>Tầng 1 — Bệnh viện</span>
        </div>

        {/* Map + scroll ngang nếu cần */}
        <div style={{ display: 'flex', justifyContent: 'center', overflowX: 'auto' }}>
          <div style={{
            position: 'relative',
            width: 1000,
            height: 500,
            flexShrink: 0,
            borderRadius: 12,
            overflow: 'hidden',
            border: `1px solid ${C.border}`,
            boxShadow: `0 0 40px rgba(0,212,255,0.06), inset 0 0 60px rgba(0,0,0,0.5)`,
            background: '#1a1a2e',
          }}>
            {/* Ảnh map */}
            <img
              src="/map_hospital.jpg"
              alt="Hospital Map"
              style={{ position: 'absolute', top: 0, left: 0, width: 1000, height: 500, display: 'block', opacity: 0.95 }}
            />

            {/* 24 nút phòng — TÊN + TỌA ĐỘ HIỂN THỊ LUÔN */}
            {ROOMS.map(room => (
              <RoomButton
                key={room}
                room={room}
                selected={selectedRooms.includes(room)}
                visited={visitedRooms.includes(room)}
                onClick={() => toggleRoom(room)}
              />
            ))}

            {/* Viền góc trang trí */}
            <div style={{ position: 'absolute', top: 8, left: 8, width: 20, height: 20, borderTop: `2px solid ${C.cyan}55`, borderLeft: `2px solid ${C.cyan}55` }} />
            <div style={{ position: 'absolute', top: 8, right: 8, width: 20, height: 20, borderTop: `2px solid ${C.cyan}55`, borderRight: `2px solid ${C.cyan}55` }} />
            <div style={{ position: 'absolute', bottom: 8, left: 8, width: 20, height: 20, borderBottom: `2px solid ${C.cyan}55`, borderLeft: `2px solid ${C.cyan}55` }} />
            <div style={{ position: 'absolute', bottom: 8, right: 8, width: 20, height: 20, borderBottom: `2px solid ${C.cyan}55`, borderRight: `2px solid ${C.cyan}55` }} />
          </div>
        </div>

        {/* Log */}
        <LogBox logs={logs} />
      </div>

      {/* ── BẢNG ĐIỀU KHIỂN ── */}
      <div style={{
        width: 340,
        background: C.panel,
        borderLeft: `1px solid ${C.border}`,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{ padding: '20px 20px 16px', borderBottom: `1px solid ${C.border}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <Activity size={18} color={C.cyan} />
            <span style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0', letterSpacing: '0.06em' }}>FMS</span>
          </div>
          <div style={{ fontSize: 11, color: C.textDim, fontFamily: "'JetBrains Mono', monospace", marginLeft: 28 }}>
            Hospital Robot Navigation
          </div>
        </div>

        {/* Nội dung scrollable */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* Robot status */}
          <div style={{ background: '#0a0f1e', border: `1px solid ${C.border}`, borderRadius: 10, padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: robotStatus === 'active' ? C.green : C.red,
              boxShadow: robotStatus === 'active' ? `0 0 8px ${C.green}` : `0 0 8px ${C.red}`,
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>
              {robotStatus === 'active' ? 'Robot: ACTIVE' : 'Robot: OFFLINE'}
            </span>
            <span style={{ marginLeft: 'auto', fontSize: 11, color: C.textDim, fontFamily: "'JetBrains Mono', monospace" }}>FMS v2.0</span>
          </div>

          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <StatCard label="Phòng chọn" value={selectedRooms.length} color={C.cyan} icon="📍" />
            <StatCard label="Khoảng cách" value={distance !== null ? `${distance.toFixed(1)}m` : '—'} color={C.amber} icon="📏" />
          </div>

          {/* Danh sách phòng đã chọn */}
          {selectedRooms.length > 0 && (
            <div style={{ background: '#0a0f1e', border: `1px solid ${C.border}`, borderRadius: 10, padding: '10px 12px' }}>
              <div style={{ fontSize: 10, color: C.textDim, fontFamily: "'DM Sans', sans-serif", letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
                Thứ tự ghé thăm
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {selectedRooms.map((r, i) => (
                  <span key={r} style={{
                    fontSize: 11, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                    background: `${ROOM_COLORS[r] || C.cyan}22`,
                    border: `1px solid ${ROOM_COLORS[r] || C.cyan}66`,
                    color: ROOM_COLORS[r] || C.cyan,
                    borderRadius: 6, padding: '3px 8px',
                  }}>
                    {i + 1}. {r.replace('Phong_', '')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Chế độ */}
          <div>
            <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, marginBottom: 8, letterSpacing: '0.04em' }}>
              CHẾ ĐỘ DI CHUYỂN
            </div>
            {[
              { idx: 0, label: '⚡ Tối ưu lộ trình (GA)', desc: 'Thuật toán di truyền tìm đường ngắn nhất' },
              { idx: 1, label: '▶ Chạy theo thứ tự chọn', desc: 'Ghé thăm theo thứ tự bạn bấm' },
            ].map(m => (
              <div key={m.idx} onClick={() => setModeIndex(m.idx)} style={{
                background: modeIndex === m.idx ? `${C.cyan}11` : '#0a0f1e',
                border: `1px solid ${modeIndex === m.idx ? C.cyan : C.border}`,
                borderRadius: 8,
                padding: '10px 12px',
                cursor: 'pointer',
                marginBottom: 6,
                transition: 'all 0.2s',
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: modeIndex === m.idx ? C.cyan : '#94a3b8', fontFamily: "'DM Sans', sans-serif" }}>
                  {m.label}
                </div>
                <div style={{ fontSize: 10, color: C.textDim, marginTop: 3, fontFamily: "'DM Sans', sans-serif" }}>
                  {m.desc}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Nút dưới cùng */}
        <div style={{ padding: '12px 20px 16px', borderTop: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <CtrlBtn onClick={clearAll} variant="secondary" icon="✖">Xóa chọn</CtrlBtn>
            <CtrlBtn onClick={handlePreview} variant="secondary" disabled={selectedRooms.length === 0} loading={previewLoading} icon="👁">
              Xem trước
            </CtrlBtn>
          </div>
          <CtrlBtn onClick={handleExecute} variant="success" disabled={selectedRooms.length === 0} loading={executeLoading} icon="🚀">
            THỰC THI ROBOT
          </CtrlBtn>
        </div>
      </div>
    </div>
  );
}
