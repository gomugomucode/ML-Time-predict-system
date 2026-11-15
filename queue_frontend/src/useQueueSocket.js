import { useEffect, useState, useRef } from 'react';

export function useQueueSocket(onMessageReceived) {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Connect to Django Channels ASGI server
    ws.current = new WebSocket('ws://127.0.0.1:8000/ws/queue/');

    ws.current.onopen = () => {
      console.log('✅ WebSocket Connected to Queue Server');
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (onMessageReceived) {
          onMessageReceived(data);
        }
      } catch (err) {
        console.error('WebSocket message parsing error:', err);
      }
    };

    ws.current.onclose = () => {
      console.log('❌ WebSocket Disconnected');
      setIsConnected(false);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  return { isConnected };
}

