import React, { useState, useEffect } from 'react';
import {
  Volume2,
  Users,
  Clock,
  CheckCircle,
  AlertTriangle,
  Activity,
  RefreshCw,
  Hash,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { api } from '../api';

export default function TellerScreen({ onTicketCalled }) {
  const [counterId, setCounterId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [lastCalled, setLastCalled] = useState(null);
  const [queueStatus, setQueueStatus] = useState(null);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = async () => {
    try {
      const data = await api.getQueueStatus();
      setQueueStatus(data);
      setError(null);
    } catch (err) {
      console.error('Failed to refresh queue status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    if (!autoRefresh) return;
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleCallNext = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.callNextTicket(counterId);
      if (result.status === 'empty') {
        setError('No tickets currently waiting in line.');
        setLastCalled(null);
      } else {
        setLastCalled(result);
        if (onTicketCalled) onTicketCalled(result);
      }
      fetchStatus();
    } catch (err) {
      console.error('Call ticket error:', err);
      setError(
        err.response?.data?.message ||
        'Could not reach backend to call next student.'
      );
    } finally {
      setLoading(false);
    }
  };

  const getAccuracyBadge = (errorMin) => {
    if (errorMin === null || errorMin === undefined) {
      return { text: 'N/A', class: 'badge-muted', desc: 'No error data' };
    }
    if (errorMin <= 5.0) {
      return { text: `±${errorMin} min (High Accuracy)`, class: 'badge-success', desc: 'Model within 5-min threshold' };
    }
    if (errorMin <= 10.0) {
      return { text: `±${errorMin} min (Moderate)`, class: 'badge-warning', desc: 'Normal variance' };
    }
    return { text: `±${errorMin} min (Drift Alert)`, class: 'badge-danger', desc: 'Outlier service duration' };
  };

  const waitingCount = queueStatus?.waiting_count ?? 0;

  return (
    <div className="teller-container">
      {/* Top Console Bar */}
      <div className="teller-top-bar">
        <div className="teller-id-block">
          <h2>Service Desk Console</h2>
          <p className="subtitle">Staff Station & Live Queue Processing Terminal</p>
        </div>

        {/* Counter Selector */}
        <div className="counter-selector">
          <span className="selector-label">Desk Number:</span>
          <div className="counter-pills">
            {[1, 2, 3, 4].map((id) => (
              <button
                key={id}
                className={`counter-pill ${counterId === id ? 'active' : ''}`}
                onClick={() => setCounterId(id)}
              >
                Counter {id}
              </button>
            ))}
          </div>
        </div>

        <div className="refresh-controls">
          <button
            className={`btn-icon ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title="Toggle Live Auto-Refresh (3s)"
          >
            <RefreshCw className={autoRefresh ? 'spin' : ''} size={18} />
            <span>{autoRefresh ? 'Live Sync ON' : 'Paused'}</span>
          </button>
          <button className="btn-icon" onClick={fetchStatus} title="Refresh Now">
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-warning">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Grid Layout: Left Action Console / Right Live Queue & Drift */}
      <div className="teller-grid">
        {/* Left Column: Call Next Action & Current Ticket */}
        <div className="teller-left-panel">
          {/* Big CTA */}
          <div className="call-action-card">
            <div className="waiting-indicator">
              <Users size={22} />
              <span>
                <strong>{waitingCount}</strong> {waitingCount === 1 ? 'student' : 'students'} currently in queue
              </span>
            </div>

            <button
              className="btn-call-next"
              onClick={handleCallNext}
              disabled={loading || waitingCount === 0}
            >
              <Volume2 size={24} />
              <span>
                {loading
                  ? 'Calling Student...'
                  : waitingCount === 0
                  ? 'No Students Waiting'
                  : `📢 Call Next Student (Desk ${counterId})`}
              </span>
            </button>
          </div>

          {/* Active Serving Card */}
          <div className="current-ticket-card">
            <div className="card-header">
              <Activity size={18} />
              <h3>Currently Serving at Desk {counterId}</h3>
            </div>

            {lastCalled ? (
              <div className="serving-content">
                <div className="called-ticket-token">
                  <span className="label">ACTIVE TICKET</span>
                  <span className="number">{lastCalled.called_ticket}</span>
                </div>

                <div className="accuracy-audit-grid">
                  <div className="audit-tile">
                    <span className="tile-label">Actual Wait Duration</span>
                    <span className="tile-value highlight">
                      {lastCalled.actual_wait_minutes ?? '0.0'} min
                    </span>
                    <span className="tile-sub">Realized time in queue ($W_q$)</span>
                  </div>

                  <div className="audit-tile">
                    <span className="tile-label">ML Predicted Wait</span>
                    <span className="tile-value">
                      {lastCalled.predicted_wait_minutes ?? '0.0'} min
                    </span>
                    <span className="tile-sub">Estimated at arrival ($\hat{W}_q$)</span>
                  </div>

                  <div className="audit-tile full-width">
                    <div className="drift-row">
                      <span className="tile-label">Model Prediction Error</span>
                      <span className={`badge ${getAccuracyBadge(lastCalled.prediction_error_minutes).class}`}>
                        {getAccuracyBadge(lastCalled.prediction_error_minutes).text}
                      </span>
                    </div>
                    <p className="drift-desc">
                      {getAccuracyBadge(lastCalled.prediction_error_minutes).desc}.
                      Recorded into <code>PredictionLog</code> database table for MLOps tracking.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <Clock size={36} />
                <p>No student called at Desk {counterId} yet.</p>
                <small>Click "Call Next Student" above to summon the next ticket in line.</small>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Live Waiting Line & Accuracy Audit */}
        <div className="teller-right-panel">
          {/* Waiting Line Table */}
          <div className="panel-card">
            <div className="panel-card-header">
              <div className="header-left">
                <Users size={18} />
                <h4>Live Waiting Queue (FIFO Order)</h4>
              </div>
              <span className="badge badge-primary">{waitingCount} waiting</span>
            </div>

            <div className="table-wrapper">
              <table className="queue-table">
                <thead>
                  <tr>
                    <th>Token</th>
                    <th>Service</th>
                    <th>Est. Wait</th>
                    <th>Arrival</th>
                  </tr>
                </thead>
                <tbody>
                  {queueStatus?.waiting_list && queueStatus.waiting_list.length > 0 ? (
                    queueStatus.waiting_list.map((ticket, index) => (
                      <tr key={ticket.ticket_number} className={index === 0 ? 'next-in-line' : ''}>
                        <td>
                          <div className="token-cell">
                            {index === 0 && <span className="next-badge">NEXT</span>}
                            <strong>{ticket.ticket_number}</strong>
                          </div>
                        </td>
                        <td>
                          <span className="dept-tag">{ticket.service_code}</span>
                        </td>
                        <td>{ticket.predicted_wait_minutes} min</td>
                        <td>{ticket.created_at}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="text-center empty-cell">
                        Queue is currently clear.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Model Drift & Accuracy Real-Time Audit */}
          <div className="panel-card">
            <div className="panel-card-header">
              <div className="header-left">
                <TrendingUp size={18} />
                <h4>Live MLOps Drift & Error Audit</h4>
              </div>
              <span className="badge badge-success">Active Telemetry</span>
            </div>

            <div className="table-wrapper">
              <table className="queue-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Predicted</th>
                    <th>Realized</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {queueStatus?.recent_accuracy && queueStatus.recent_accuracy.length > 0 ? (
                    queueStatus.recent_accuracy.map((row) => {
                      const badge = getAccuracyBadge(row.error);
                      return (
                        <tr key={row.ticket_number}>
                          <td><strong>{row.ticket_number}</strong></td>
                          <td>{row.predicted}m</td>
                          <td>{row.actual}m</td>
                          <td>
                            <span className={`badge ${badge.class}`}>
                              ±{row.error}m
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={4} className="text-center empty-cell">
                        No resolved predictions logged today yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
