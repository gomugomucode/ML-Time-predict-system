import React, { useState } from 'react';
import axios from 'axios';
import { 
  Bell, 
  CheckCircle, 
  AlertTriangle, 
  UserCheck, 
  Clock, 
  Gauge, 
  ArrowRightCircle,
  Hash
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000/api';

export default function TellerScreen() {
  const [counterId, setCounterId] = useState(1);
  const [servingTicket, setServingTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [callHistory, setCallHistory] = useState([]);

  const handleCallNext = async () => {
    setLoading(true);
    setStatusMessage(null);

    try {
      const response = await axios.post(`${API_BASE}/tickets/call/${counterId}/`);
      const data = response.data;

      if (data.status === 'success') {
        setServingTicket(data);
        setStatusMessage({ type: 'success', text: `Called token ${data.called_ticket} to Counter ${counterId}` });
        
        // Add to local audit list of called tickets
        setCallHistory((prev) => [
          {
            ticket: data.called_ticket,
            actual: data.actual_wait_minutes,
            predicted: data.predicted_wait_minutes,
            error: data.prediction_error_minutes,
            calledAt: new Date().toLocaleTimeString(),
          },
          ...prev.slice(0, 4), // Keep last 5
        ]);
      } else if (data.status === 'empty') {
        setStatusMessage({ type: 'info', text: data.message || 'No students currently waiting in the queue.' });
      }
    } catch (err) {
      console.error('Call next failed:', err);
      setStatusMessage({ 
        type: 'error', 
        text: 'Failed to contact queue server. Ensure Django is running on port 8000.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="teller-container">
      {/* Top Bar: Counter Selection & Staff Status */}
      <div className="teller-topbar">
        <div>
          <h2>Teller Desk Station</h2>
          <p>Call waiting students and inspect real-time ML prediction accuracy.</p>
        </div>

        <div className="counter-selector">
          <label htmlFor="counter-select">Desk Station:</label>
          <select 
            id="counter-select"
            value={counterId} 
            onChange={(e) => setCounterId(Number(e.target.value))}
            className="counter-dropdown"
          >
            <option value={1}>Counter 1 (Accounts)</option>
            <option value={2}>Counter 2 (Tuition / Cash)</option>
            <option value={3}>Counter 3 (Clearance)</option>
          </select>
        </div>
      </div>

      {statusMessage && (
        <div className={`status-banner ${statusMessage.type}`}>
          {statusMessage.type === 'error' && <AlertTriangle size={18} />}
          {statusMessage.type === 'success' && <CheckCircle size={18} />}
          {statusMessage.type === 'info' && <Bell size={18} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Main Grid: Active Serving Card + Action Area */}
      <div className="teller-grid">
        {/* Left: Action & Active Ticket */}
        <div className="teller-main-card">
          <div className="action-row">
            <button 
              onClick={handleCallNext} 
              disabled={loading}
              className="call-btn"
            >
              <Bell size={22} className={loading ? 'bell-ring' : ''} />
              {loading ? 'Calling Next in Line...' : `Call Next Token (Counter ${counterId})`}
            </button>
          </div>

          <div className="active-serving-box">
            <span className="serving-pill">Currently Serving</span>
            {servingTicket ? (
              <div className="serving-display">
                <div className="serving-number">{servingTicket.called_ticket}</div>
                <div className="serving-counter-tag">Assigned to Counter {servingTicket.counter}</div>

                <div className="accuracy-audit-grid">
                  <div className="audit-card">
                    <div className="audit-label"><Clock size={14} /> Actual Wait Time (W<sub>q</sub>)</div>
                    <div className="audit-val">{servingTicket.actual_wait_minutes} <span className="unit">min</span></div>
                    <div className="audit-sub">From arrival to service call</div>
                  </div>

                  <div className="audit-card">
                    <div className="audit-label"><Gauge size={14} /> ML Prediction (Ŵ)</div>
                    <div className="audit-val">{servingTicket.predicted_wait_minutes} <span className="unit">min</span></div>
                    <div className="audit-sub">Random Forest estimate</div>
                  </div>

                  <div className={`audit-card ${servingTicket.prediction_error_minutes > 10 ? 'error-high' : 'error-good'}`}>
                    <div className="audit-label"><AlertTriangle size={14} /> Prediction Error (|W<sub>q</sub> - Ŵ|)</div>
                    <div className="audit-val">±{servingTicket.prediction_error_minutes} <span className="unit">min</span></div>
                    <div className="audit-sub">
                      {servingTicket.prediction_error_minutes <= 5 ? 'High Accuracy (< 5m)' : 'Acceptable Variance'}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="serving-empty">
                <UserCheck size={44} />
                <p>No student currently at the desk. Click <strong>"Call Next Token"</strong> to summon the next ticket.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: Desk Call Log */}
        <div className="teller-sidebar">
          <h3>Recent Counter Calls</h3>
          {callHistory.length > 0 ? (
            <div className="call-history-list">
              {callHistory.map((item, idx) => (
                <div key={idx} className="history-item">
                  <div className="history-top">
                    <span className="history-token"><Hash size={14} /> {item.ticket}</span>
                    <span className="history-time">{item.calledAt}</span>
                  </div>
                  <div className="history-details">
                    <span>Act: <strong>{item.actual}m</strong></span>
                    <span>Pred: <strong>{item.predicted}m</strong></span>
                    <span className={`err-badge ${item.error > 10 ? 'high' : 'ok'}`}>
                      Err: ±{item.error}m
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="history-empty">
              <ArrowRightCircle size={32} />
              <p>Tickets called during this active session will be logged here with their ground-truth error metrics.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
