import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Volume2, VolumeX, Users, Clock, MonitorPlay, Radio } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000/api';

export default function PublicDisplay() {
  const [queueData, setQueueData] = useState({ now_serving: [], upcoming: [], total_waiting: 0 });
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const lastAnnouncedTicket = useRef(null);

  // Synthesize voice announcement with audio chime
  const announceTicket = (ticketNumber, counterNumber) => {
    if (!audioEnabled || !('speechSynthesis' in window)) return;
    
    // Play quick chime sound via AudioContext
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.4);
    } catch (e) {
      console.warn('AudioContext failed', e);
    }

    // Voice announcement after short chime
    setTimeout(() => {
      const speech = new SpeechSynthesisUtterance(
        `Token ${ticketNumber}, please proceed to Counter ${counterNumber}`
      );
      speech.rate = 0.9;
      speech.pitch = 1.0;
      window.speechSynthesis.speak(speech);
    }, 350);
  };

  // Poll backend every 2.5 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE}/queue/status/`);
        setQueueData(res.data);

        // Check if there is a new called ticket to announce
        if (res.data.now_serving && res.data.now_serving.length > 0) {
          const latest = res.data.now_serving[0];
          if (latest && latest.ticket_number !== lastAnnouncedTicket.current) {
            if (lastAnnouncedTicket.current !== null) {
              announceTicket(latest.ticket_number, latest.counter_number);
            }
            lastAnnouncedTicket.current = latest.ticket_number;
          }
        }
      } catch (err) {
        console.error('Failed to fetch public queue status', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2500);
    return () => clearInterval(interval);
  }, [audioEnabled]);

  // Live clock
  useEffect(() => {
    const clock = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(clock);
  }, []);

  return (
    <div className="display-board-container">
      {/* Top Banner */}
      <div className="display-board-top">
        <div className="top-title">
          <Radio size={24} className="live-dot" />
          <div>
            <h1>College Account Section — Live Queue Board</h1>
            <p>Please watch for your token number and listen for the announcement.</p>
          </div>
        </div>

        <div className="top-controls">
          <div className="live-clock">{currentTime}</div>
          <button 
            onClick={() => setAudioEnabled(!audioEnabled)} 
            className={`audio-btn ${audioEnabled ? 'active' : ''}`}
            title="Enable voice chime"
          >
            {audioEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
            <span>{audioEnabled ? 'Chime ON' : 'Chime Muted'}</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Now Serving vs Upcoming Line */}
      <div className="display-board-grid">
        {/* Left Side: Large Now Serving Grid */}
        <div className="serving-section">
          <div className="section-title">
            <MonitorPlay size={20} />
            <h2>NOW SERVING</h2>
          </div>

          <div className="serving-cards-grid">
            {queueData.now_serving.length > 0 ? (
              queueData.now_serving.map((item, idx) => (
                <div key={idx} className={`now-serving-card ${idx === 0 ? 'pulse' : ''}`}>
                  <div className="counter-badge">Counter {item.counter_number}</div>
                  <div className="ticket-hero">{item.ticket_number}</div>
                  <div className="called-time">Called at {item.called_at}</div>
                </div>
              ))
            ) : (
              <div className="no-active-serving">
                <h3>Counters Ready</h3>
                <p>Waiting for the next ticket to be called.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Upcoming Waiting List */}
        <div className="upcoming-section">
          <div className="section-title">
            <Users size={20} />
            <h2>NEXT IN LINE ({queueData.total_waiting} WAITING)</h2>
          </div>

          <div className="upcoming-list">
            {queueData.upcoming.length > 0 ? (
              queueData.upcoming.map((t, idx) => (
                <div key={idx} className="upcoming-row">
                  <div className="upcoming-pos">#{idx + 1}</div>
                  <div className="upcoming-ticket">{t.ticket_number}</div>
                  <div className="upcoming-time">
                    <Clock size={14} /> ~{t.estimated_wait_minutes} min wait
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-upcoming">
                <p>Queue is currently empty. Next arrival will be served immediately!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
