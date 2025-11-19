/**
 * Hook for WebSocket connection
 */

import { useEffect, useCallback, useState } from "react";
import { wsManager } from "@/lib/websocket";
import type { WebSocketMessage } from "@/lib/types";

export function useWebSocket(sessionId: string | null) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    if (!sessionId) {
      wsManager.disconnect();
      setIsConnected(false);
      return;
    }

    wsManager.connect(sessionId);

    const unsubscribe = wsManager.onMessage((message) => {
      setLastMessage(message);
    });

    const interval = setInterval(() => {
      setIsConnected(wsManager.isConnected);
    }, 1000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [sessionId]);

  const send = useCallback((data: any) => {
    wsManager.send(data);
  }, []);

  return {
    isConnected,
    lastMessage,
    send,
  };
}

