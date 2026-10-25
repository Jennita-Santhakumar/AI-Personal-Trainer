/**
 * frontend/src/hooks/useCoach.js
 * React hook for streaming AI coach conversations.
 *
 * FIXES:
 *  - streamBufferRef was never reset between messages, causing new responses
 *    to append onto old content.
 *  - connectCoachStream now receives onError; WebSocket errors properly
 *    trigger the HTTP fallback instead of being silently swallowed.
 *  - clearHistory() now safely closes the WebSocket before nulling the ref,
 *    preventing a race where a concurrent sendMessage() could create a
 *    duplicate connection.
 */
import { useState, useRef, useCallback, useEffect } from "react";
import api from "../services/api";

export function useCoach() {
  const [messages, setMessages]   = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError]         = useState(null);
  const wsRef       = useRef(null);
  const streamBuf   = useRef("");
  const wsFailed    = useRef(false);

  const appendLastAssistant = (updater) => {
    setMessages(prev => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") msgs[msgs.length - 1] = updater(last);
      return msgs;
    });
  };

  const finaliseStream = () => {
    setStreaming(false);
    setMessages(prev => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last?.streaming) msgs[msgs.length - 1] = { ...last, streaming: false };
      return msgs;
    });
  };

  const doHttpFallback = useCallback(async (text, sessionId) => {
    if (wsFailed.current) return;
    wsFailed.current = true;
    wsRef.current?.close();
    wsRef.current = null;
    try {
      // POST to streaming NDJSON endpoint so tokens appear immediately
      const token = localStorage.getItem("access_token");
      const resp = await fetch("/api/v1/coach/message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || "Coach unavailable");
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop(); // keep incomplete line
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.error) throw new Error(parsed.error);
            if (parsed.done) { finaliseStream(); return; }
            if (parsed.chunk) {
              streamBuf.current += parsed.chunk;
              const snap = streamBuf.current;
              setMessages(prev => {
                const msgs = [...prev];
                const last = msgs[msgs.length - 1];
                if (last?.role === "assistant") msgs[msgs.length - 1] = { ...last, content: snap };
                return msgs;
              });
            }
          } catch (parseErr) {
            // Non-JSON line — treat as raw chunk
            streamBuf.current += line;
          }
        }
      }
      finaliseStream();
    } catch (e) {
      setError(e.message || "Coach unavailable");
      setMessages(prev => prev.filter((_, i) => i !== prev.length - 1));
      setStreaming(false);
    }
  }, []);

  const sendMessage = useCallback(async (text, sessionId = null) => {
    if (!text.trim() || streaming) return;

    setMessages(prev => [
      ...prev,
      { role: "user", content: text, ts: Date.now() },
      { role: "assistant", content: "", streaming: true, ts: Date.now() },
    ]);
    setStreaming(true);
    setError(null);
    streamBuf.current = ""; // FIX: reset buffer for each new message

    try {
      if (!wsRef.current) {
        wsFailed.current = false;
        wsRef.current = api.connectCoachStream(
          (chunk) => {
            streamBuf.current += chunk;
            const snap = streamBuf.current;
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.role === "assistant") msgs[msgs.length - 1] = { ...last, content: snap };
              return msgs;
            });
          },
          () => finaliseStream(),
          (errMsg) => {
            console.warn("WS error:", errMsg);
            doHttpFallback(text, sessionId);
          },
        );
      }
      wsRef.current.send(text, sessionId);
    } catch (err) {
      await doHttpFallback(text, sessionId);
    }
  }, [streaming, doHttpFallback]);

  const clearHistory = useCallback(() => {
    // FIX: close socket before nulling to prevent race with concurrent sendMessage
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    setMessages([]);
    setError(null);
    streamBuf.current = "";
  }, []);

  useEffect(() => () => { wsRef.current?.close(); }, []);

  return { messages, streaming, error, sendMessage, clearHistory };
}
