import React, { useState, useEffect } from 'react';
import { Ticket, Users, Clock, CheckCircle, Sparkles, AlertCircle, RefreshCw, Printer } from 'lucide-react';
import { api } from '../api';

const SERVICES = [
  { code: 'ACC', name: 'Accounting & Billing', desc: 'Tuition fees, billing statements, payment clearance', icon: '💳' },
  { code: 'REG', name: 'Registrar & Admissions', desc: 'Course enrollment, transcripts, graduation status', icon: '📚' },
  { code: 'FIN', name: 'Financial Aid', desc: 'Scholarships, student loans, emergency grants', icon: '💰' },
  { code: 'ADV', name: 'Academic Advising', desc: 'Degree planning, prerequisite waivers, graduation audits', icon: '🎓' },
];

export default function StudentKiosk({ onTicketIssued }) {
  const [selectedService, setSelectedService] = useState('ACC');
  const [loading, setLoading] = useState(false);
  const [issuedTicket, setIssuedTicket] = useState(null);
  const [queueInfo, setQueueInfo] = useState(null);
  const [error, setError] = useState(null);

  const fetchLiveStatus = async () => {
    try {
      const data = await api.getQueueStatus();
      setQueueInfo(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch queue info:', err);
      // Non-blocking error for kiosk display
    }
  };

  useEffect(() => {
    fetchLiveStatus();
    const interval = setInterval(fetchLiveStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleIssueTicket = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.issueTicket(selectedService);
      setIssuedTicket(result);
      if (onTicketIssued) onTicketIssued(result);
      fetchLiveStatus();
    } catch (err) {
      console.error('Ticket issue error:', err);
      setError(
        err.response?.data?.error ||
        'Could not connect to Django backend. Ensure python manage.py runserver is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setIssuedTicket(null);
    setError(null);
    fetchLiveStatus();
  };

  return (
    <div className="kiosk-container">
      {/* Header Banner */}
      <div className="kiosk-header">
        <div className="badge-kiosk">
          <Sparkles size={16} /> Campus Smart Kiosk
        </div>
        <h2>Select a Department Service</h2>
        <p className="subtitle">
          Touch your service category below to receive a queue token with real-time AI wait-time estimation.
        </p>
      </div>

      {error && (
        <div className="alert-error">
          <AlertCircle size={20} />
          <div>
            <strong>Service Communication Error:</strong> {error}
          </div>
        </div>
      )}

      {!issuedTicket ? (
        <div className="kiosk-selection-flow">
          {/* Service Cards Grid */}
          <div className="service-grid">
            {SERVICES.map((s) => {
              const isSelected = selectedService === s.code;
              return (
                <div
                  key={s.code}
                  className={`service-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedService(s.code)}
                >
                  <div className="service-icon">{s.icon}</div>
                  <div className="service-info">
                    <div className="service-header-row">
                      <span className="service-code">{s.code}</span>
                      {isSelected && <span className="selected-pill">Selected</span>}
                    </div>
                    <h3>{s.name}</h3>
                    <p>{s.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Queue Snapshot & Action Bar */}
          <div className="kiosk-action-box">
            <div className="live-snapshot">
              <div className="stat-pill">
                <Users size={18} />
                <span>
                  Currently in line: <strong>{queueInfo?.waiting_count ?? '...'} students</strong>
                </span>
              </div>
              <div className="stat-pill">
                <Clock size={18} />
                <span>
                  Open service desks: <strong>{queueInfo?.open_counters ?? 1}</strong>
                </span>
              </div>
            </div>

            <button
              className="btn-primary-kiosk"
              onClick={handleIssueTicket}
              disabled={loading}
            >
              {loading ? (
                <>
                  <RefreshCw className="spin" size={20} /> Generating ML Token...
                </>
              ) : (
                <>
                  <Ticket size={22} /> Get Queue Ticket ({selectedService})
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        /* Render Issued Ticket Token Card */
        <div className="ticket-result-view">
          <div className="ticket-pass-card">
            <div className="ticket-pass-top">
              <div className="ticket-badge-row">
                <span className="token-service-tag">{selectedService} DEPARTMENT</span>
                <span className="token-status-tag">CONFIRMED</span>
              </div>
              <p className="ticket-label">YOUR TOKEN NUMBER</p>
              <h1 className="ticket-token-number">{issuedTicket.ticket_number}</h1>
              <div className="ticket-barcode-mock">
                <span className="barcode-bars">||| | |||| | ||| |||| || | |||| ||</span>
              </div>
            </div>

            <div className="ticket-pass-divider">
              <div className="notch notch-left"></div>
              <div className="dashed-line"></div>
              <div className="notch notch-right"></div>
            </div>

            <div className="ticket-pass-body">
              <div className="ticket-metrics-grid">
                <div className="metric-box">
                  <div className="metric-icon"><Users size={20} /></div>
                  <div className="metric-data">
                    <span className="metric-label">Students Ahead</span>
                    <span className="metric-value">{issuedTicket.people_ahead}</span>
                  </div>
                </div>

                <div className="metric-box highlight">
                  <div className="metric-icon"><Clock size={20} /></div>
                  <div className="metric-data">
                    <span className="metric-label">Estimated Wait</span>
                    <span className="metric-value">{issuedTicket.estimated_wait_minutes} min</span>
                  </div>
                </div>
              </div>

              <div className="ticket-footnote">
                <Sparkles size={14} />
                <span>
                  Predicted by Random Forest Regressor using arrival depth & peak-hour factors.
                </span>
              </div>

              <div className="ticket-timestamp">
                Issued At: {issuedTicket.created_at}
              </div>

              <div className="ticket-actions">
                <button className="btn-print" onClick={() => window.print()}>
                  <Printer size={18} /> Print Ticket Slip
                </button>
                <button className="btn-secondary" onClick={handleReset}>
                  <CheckCircle size={18} /> Finish / Issue Another
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
