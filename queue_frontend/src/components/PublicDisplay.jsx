import React, { useState, useEffect } from 'react';
import { Tv, Users, Clock, ArrowRight, BellRing } from 'lucide-react';
import { api } from '../api';

export default function PublicDisplay() {
  const [queueStatus, setQueueStatus] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchStatus = async () => {
    try {
      const data = await api.getQueueStatus();
      setQueueStatus(data);
    } catch (err) {
      console.error('Display sync error:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const activeCalls = queueStatus?.currently_serving ?? [];
  const waitingList = queueStatus?.waiting_list ?? [];

  return (
    <div className="display-board-container">
      {/* Top TV Header Bar */}
      <div className="display-header">
        <div className="display-branding">
          <Tv size={26} />
          <div>
            <h1>CAMPUS SERVICE CENTER</h1>
            <p>Live Queue Status & Now Calling Board</p>
          </div>
        </div>
        <div className="display-clock-box">
          <div className="live-clock">{currentTime}</div>
          <div className="live-pulse">
            <span className="pulse-dot"></span> LIVE
          </div>
        </div>
      </div>

      {/* Main Split Display Screen */}
      <div className="display-main-grid">
        {/* Left: Now Serving Hero Section */}
        <div className="now-calling-column">
          <div className="column-title">
            <BellRing className="bell-shake" size={24} />
            <h2>NOW CALLING / IN SERVICE</h2>
          </div>

          <div className="now-calling-cards">
            {activeCalls.length > 0 ? (
              activeCalls.map((call, idx) => (
                <div key={call.ticket_number} className={`calling-card ${idx === 0 ? 'calling-hero' : ''}`}>
                  <div className="calling-token-section">
                    <span className="calling-tag">TICKET</span>
                    <span className="calling-token-num">{call.ticket_number}</span>
                  </div>
                  <div className="calling-arrow">
                    <ArrowRight size={36} />
                  </div>
                  <div className="calling-dest-section">
                    <span className="calling-dest-label">PLEASE PROCEED TO</span>
                    <span className="calling-dest-counter">DESK {call.counter ?? 1}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="no-calls-card">
                <Clock size={48} />
                <p>All service counters are currently ready for next students.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: Upcoming Tickets in Line */}
        <div className="upcoming-column">
          <div className="column-title">
            <Users size={24} />
            <h2>UPCOMING IN QUEUE ({queueStatus?.waiting_count ?? 0})</h2>
          </div>

          <div className="upcoming-cards-list">
            {waitingList.length > 0 ? (
              waitingList.slice(0, 7).map((ticket, idx) => (
                <div key={ticket.ticket_number} className="upcoming-card">
                  <div className="upcoming-rank">#{idx + 1}</div>
                  <div className="upcoming-token">
                    <strong>{ticket.ticket_number}</strong>
                    <span className="dept-tag">{ticket.service_code}</span>
                  </div>
                  <div className="upcoming-wait">
                    <Clock size={16} />
                    <span>~{ticket.predicted_wait_minutes} min wait</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="upcoming-empty">
                <p>No waiting tickets currently in queue.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
