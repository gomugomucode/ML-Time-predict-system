import React, { useState, useEffect } from 'react';
import {
  Ticket,
  UserCheck,
  Tv,
  Cpu,
  ExternalLink,
  Zap,
  CheckCircle2,
  AlertCircle,
  Play,
} from 'lucide-react';
import StudentKiosk from './components/StudentKiosk';
import TellerScreen from './components/TellerScreen';
import PublicDisplay from './components/PublicDisplay';
import { api } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('kiosk');
  const [backendStatus, setBackendStatus] = useState({ online: false, checking: true });
  const [simulating, setSimulating] = useState(false);
  const [simMessage, setSimMessage] = useState(null);

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setBackendStatus({ online: true, checking: false, data });
    } catch {
      setBackendStatus({ online: false, checking: false });
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 6000);
    return () => clearInterval(interval);
  }, []);

  // Quick 1-click batch simulation for demonstration
  const handleQuickSimulate = async () => {
    setSimulating(true);
    setSimMessage('Simulating arrival of 2 students and 1 desk service call...');
    try {
      await api.issueTicket('ACC');
      await api.issueTicket('REG');
      await new Promise((r) => setTimeout(r, 1200));
      const called = await api.callNextTicket(1);
      setSimMessage(
        `Simulation Success: Issued 2 tickets and called ${called.called_ticket ?? 'ticket'} to Counter 1 (Wait: ${called.actual_wait_minutes ?? 0}m, Error: ±${called.prediction_error_minutes ?? 0}m)!`
      );
    } catch (err) {
      console.error(err);
      setSimMessage('Simulation error: Ensure Django backend is running at http://127.0.0.1:8000.');
    } finally {
      setSimulating(false);
      setTimeout(() => setSimMessage(null), 8000);
    }
  };

  return (
    <div className="app-shell">
      {/* Top Main Navigation Bar */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-icon">
            <Cpu size={24} />
          </div>
          <div className="brand-text">
            <h1>SmartQueue <span className="brand-accent">ML</span></h1>
            <span className="brand-sub">Real-Time Predictive Queue & Drift Intelligence</span>
          </div>
        </div>

        {/* View Navigation Switcher */}
        <nav className="nav-tabs">
          <button
            className={`tab-btn ${activeTab === 'kiosk' ? 'active' : ''}`}
            onClick={() => setActiveTab('kiosk')}
          >
            <Ticket size={18} />
            <span>Student Kiosk</span>
          </button>

          <button
            className={`tab-btn ${activeTab === 'teller' ? 'active' : ''}`}
            onClick={() => setActiveTab('teller')}
          >
            <UserCheck size={18} />
            <span>Teller Desk</span>
          </button>

          <button
            className={`tab-btn ${activeTab === 'display' ? 'active' : ''}`}
            onClick={() => setActiveTab('display')}
          >
            <Tv size={18} />
            <span>Public TV Board</span>
          </button>
        </nav>

        {/* System Health & Quick Actions */}
        <div className="nav-actions">
          <button
            className="btn-quick-sim"
            onClick={handleQuickSimulate}
            disabled={simulating || !backendStatus.online}
            title="Quickly issue 2 tickets and call 1 ticket to generate live data"
          >
            <Play size={14} />
            <span>{simulating ? 'Simulating...' : 'Quick Sim'}</span>
          </button>

          <a
            href="http://127.0.0.1:8000/admin/"
            target="_blank"
            rel="noreferrer"
            className="btn-admin-link"
            title="Open Django Admin Dashboard"
          >
            <span>Django Admin</span>
            <ExternalLink size={14} />
          </a>

          <div
            className={`health-badge ${
              backendStatus.checking
                ? 'checking'
                : backendStatus.online
                ? 'online'
                : 'offline'
            }`}
            title="Backend Connection Status"
          >
            {backendStatus.online ? (
              <>
                <CheckCircle2 size={14} />
                <span>API Online</span>
              </>
            ) : (
              <>
                <AlertCircle size={14} />
                <span>API Offline</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Global Simulation Alert Notification */}
      {simMessage && (
        <div className="simulation-banner">
          <Zap size={18} />
          <span>{simMessage}</span>
        </div>
      )}

      {/* Main Tab Content */}
      <main className="main-content">
        {activeTab === 'kiosk' && <StudentKiosk />}
        {activeTab === 'teller' && <TellerScreen />}
        {activeTab === 'display' && <PublicDisplay />}
      </main>

      {/* Footer Info */}
      <footer className="footer-bar">
        <div className="footer-left">
          <span>Engine: <strong>RandomForestRegressor v1.0 (83.6% MAE vs baseline)</strong></span>
          <span className="dot-sep">•</span>
          <span>Dual Fallback: <strong>Average Service Time (AST)</strong></span>
        </div>
        <div className="footer-right">
          <span>Telemetry: <strong>1-to-1 Ground Truth PredictionLog & MLOps Drift Tracking</strong></span>
        </div>
      </footer>
    </div>
  );
}
