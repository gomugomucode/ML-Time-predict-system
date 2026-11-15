import React, { useState } from 'react';
import StudentKiosk from './components/StudentKiosk';
import TellerScreen from './components/TellerScreen';
import { User, MonitorCheck } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('kiosk');

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
      {/* Navigation Header */}
      <nav style={navStyle}>
        <div style={navBrandStyle}>
          🏫 <span>College Queue AI</span>
        </div>
        <div style={tabGroupStyle}>
          <button
            onClick={() => setActiveTab('kiosk')}
            style={{
              ...tabBtnStyle,
              background: activeTab === 'kiosk' ? '#2563eb' : 'transparent',
              color: activeTab === 'kiosk' ? '#ffffff' : '#64748b',
            }}
          >
            <User size={16} /> Student Kiosk
          </button>
          <button
            onClick={() => setActiveTab('teller')}
            style={{
              ...tabBtnStyle,
              background: activeTab === 'teller' ? '#16a34a' : 'transparent',
              color: activeTab === 'teller' ? '#ffffff' : '#64748b',
            }}
          >
            <MonitorCheck size={16} /> Teller Desk
          </button>
        </div>
      </nav>

      {/* Main View Area */}
      <main>
        {activeTab === 'kiosk' ? <StudentKiosk /> : <TellerScreen />}
      </main>
    </div>
  );
}

const navStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '16px 28px',
  background: '#ffffff',
  borderBottom: '1px solid #e2e8f0',
};

const navBrandStyle = {
  fontSize: '18px',
  fontWeight: '800',
  color: '#0f172a',
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
};

const tabGroupStyle = {
  display: 'flex',
  gap: '8px',
  background: '#f1f5f9',
  padding: '4px',
  borderRadius: '10px',
};

const tabBtnStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '8px 16px',
  fontSize: '14px',
  fontWeight: '600',
  border: 'none',
  borderRadius: '8px',
  cursor: 'pointer',
  transition: 'all 0.15s ease',
};
