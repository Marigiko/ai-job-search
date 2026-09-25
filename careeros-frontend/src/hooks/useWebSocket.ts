import { useCallback, useEffect, useRef, useState } from "react";
import type { WebSocketMessage, WebSocketStatus } from "@/types";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8001/ws";
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

export function useWebSocket() {
  const [status, setStatus] = useState<WebSocketStatus>("closed");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus("connecting");
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("open");
      reconnectAttempts.current = 0;
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage;
        setLastMessage(data);
      } catch {
        // Ignore malformed messages silently
      }
    };

    socket.onerror = () => {
      setStatus("error");
    };

    socket.onclose = () => {
      setStatus("closed");
      socketRef.current = null;

      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current += 1;
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    reconnectAttempts.current = MAX_RECONNECT_ATTEMPTS;
    socketRef.current?.close();
  }, []);

  const send = useCallback((type: string, payload: unknown) => {
    const socket = socketRef.current;
    if (socket?.readyState !== WebSocket.OPEN) {
      return false;
    }
    socket.send(JSON.stringify({ type, payload, timestamp: new Date().toISOString() }));
    return true;
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { status, lastMessage, connect, disconnect, send };
}
