import React, { useState } from 'react';
import axios from 'axios';
import { 
  Ticket as TicketIcon, 
  Users, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles,
  Printer
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE = 'http://127.0.0.1:8000/api';

const SERVICES = [
  { code: 'ACC', name: 'Tuition & Semester Fee', icon: '💳', badge: 'Fast Track' },
  { code: 'ADM', name: 'Admissions & Clearance', icon: '📝', badge: 'Standard' },
  { code: 'EXM', name: 'Exam & Transcript Verification', icon: '🎓', badge: 'Standard' },
  { code: 'GEN', name: 'General Inquiries', icon: 'ℹ️', badge: 'Quick' },
];

export default function StudentKiosk() {
  const [selectedService, setSelectedService] = useState('ACC');
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleIssueTicket = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/tickets/issue/`, {
        service_code: selectedService,
      });

      setTicket(response.data);

      // Trigger celebration confetti on successful ticket issuance
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.8 },
      });
    } catch (err) {
      console.error('Error issuing ticket:', err);
      setError('Unable to reach the queue server. Ensure your Django backend is running at port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="kiosk-container">
      {/* Header */}
      <div className="kiosk-header">
        <div className="kiosk-badge">
          <Sparkles size={14} className="sparkle-icon" /> AI-Driven Real-Time Queue
        </div>
        <h1>College Account Section</h1>
        <p>Select your service counter and withdraw your queue token with dynamic wait-time forecasting.</p>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Selector vs Output Card */}
      <div className="kiosk-grid">
        {/* Left Column: Service Selection */}
        <div className="selection-panel">
          <h3>Select Required Service</h3>
          <div className="service-options">
            {SERVICES.map((s) => (
              <button
                key={s.code}
                type="button"
                onClick={() => setSelectedService(s.code)}
                className={`service-card ${selectedService === s.code ? 'active' : ''}`}
              >
                <div className="service-icon">{s.icon}</div>
                <div className="service-info">
                  <div className="service-title">{s.name}</div>
                  <div className="service-code-tag">Code: {s.code} • {s.badge}</div>
                </div>
              </button>
            ))}
          </div>

          <button
            onClick={handleIssueTicket}
            disabled={loading}
            className="issue-btn"
          >
            <TicketIcon size={20} />
            {loading ? 'Calculating Queue & Generating...' : 'Get Queue Token'}
          </button>
        </div>

        {/* Right Column: Issued Ticket Card */}
        <div className="display-panel">
          {ticket ? (
            <div className="ticket-card printable-ticket">
              <div className="ticket-card-header">
                <div>
                  <span className="live-pill">Live Active Token</span>
                  <h2>{ticket.ticket_number}</h2>
                </div>
                <CheckCircle2 size={32} className="success-icon" />
              </div>

              <div className="ticket-divider" />

              <div className="metric-row">
                <div className="metric-box">
                  <div className="metric-label">
                    <Users size={16} /> Ahead in Queue
                  </div>
                  <div className="metric-value">{ticket.people_ahead} <span className="unit">students</span></div>
                </div>

                <div className="metric-box highlight">
                  <div className="metric-label">
                    <Clock size={16} /> Est. Wait Time
                  </div>
                  <div className="metric-value">
                    ~{ticket.estimated_wait_minutes} <span className="unit">min</span>
                  </div>
                </div>
              </div>

              <div className="ticket-footer">
                <div>
                  <span className="timestamp-label">Issued Epoch:</span>
                  <span className="timestamp-val">{ticket.created_at}</span>
                </div>
                <button onClick={handlePrint} className="print-btn" title="Print slip">
                  <Printer size={16} /> Print Slip
                </button>
              </div>

              <div className="kiosk-note">
                Please take a seat. Your token will be announced on the counter display board.
              </div>
            </div>
          ) : (
            <div className="ticket-placeholder">
              <div className="placeholder-icon">
                <TicketIcon size={48} />
              </div>
              <h4>No Token Generated Yet</h4>
              <p>Choose your service on the left and tap "Get Queue Token" to receive your estimated waiting time.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
