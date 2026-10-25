/**
 * frontend/src/services/api.js
 *
 * ROOT CAUSE FIX: REACT_APP_API_URL was being baked into the JS bundle at
 * build time as "http://localhost:8100". The browser then tried to call that
 * directly, bypassing nginx entirely — and hit CORS + connection errors.
 *
 * THE FIX: Use empty string as BASE_URL so ALL requests go to relative paths
 * (e.g. /api/v1/auth/login). Nginx running on port 3000 then proxies
 * /api/* → http://api:8000 internally inside Docker. No CORS, no cross-origin
 * issues, works on any machine regardless of port mappings.
 */

// Empty string = relative URLs → nginx proxies to the API container
const BASE_URL = "";

class ApiClient {
  constructor() {
    this._token = localStorage.getItem("access_token") || null;
  }

  setToken(token) {
    this._token = token;
    localStorage.setItem("access_token", token);
  }

  clearToken() {
    this._token = null;
    localStorage.removeItem("access_token");
  }

  get _headers() {
    const h = { "Content-Type": "application/json" };
    if (this._token) h["Authorization"] = `Bearer ${this._token}`;
    return h;
  }

  async _fetch(path, options = {}) {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { ...this._headers, ...(options.headers || {}) },
    });
    if (res.status === 401) {
      this.clearToken();
      window.location.href = "/";
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  }

  // ── Auth ──────────────────────────────────────────────────────────────────
  async register(data)   { return this._fetch("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }); }
  async login(email, pw) { return this._fetch("/api/v1/auth/login",    { method: "POST", body: JSON.stringify({ email, password: pw }) }); }
  async getMe()          { return this._fetch("/api/v1/auth/me"); }

  // ── Roadmap (LLM Multi-Week Fitness & Nutrition) ─────────────────────────
  async generateRoadmap(data)       { return this._fetch("/api/v1/roadmap/generate", { method: "POST", body: JSON.stringify(data) }); }
  async getCurrentRoadmap()         { return this._fetch("/api/v1/roadmap/current"); }
  async getRoadmapHistory()         { return this._fetch("/api/v1/roadmap/history"); }
  async updateRoadmapProgress(id, taskId, completed) {
    return this._fetch(`/api/v1/roadmap/${id}/progress`, {
      method: "POST",
      body: JSON.stringify({ task_id: taskId, completed }),
    });
  }
  async activateRoadmap(id)         { return this._fetch(`/api/v1/roadmap/${id}/activate`, { method: "PUT" }); }
  async deleteRoadmap(id)           { return this._fetch(`/api/v1/roadmap/${id}`, { method: "DELETE" }); }
  async getRoadmapProviders()       { return this._fetch("/api/v1/roadmap/providers"); }

  // ── Plans ─────────────────────────────────────────────────────────────────
  async generatePlan(data) { return this._fetch("/api/v1/plans/generate", { method: "POST", body: JSON.stringify(data) }); }
  async getCurrentPlan()   { return this._fetch("/api/v1/plans/current"); }
  async getPlanHistory()   { return this._fetch("/api/v1/plans/history"); }

  // ── Sessions ──────────────────────────────────────────────────────────────
  async submitSession(data)      { return this._fetch("/api/v1/sessions/",              { method: "POST", body: JSON.stringify(data) }); }
  async getMetricsSummary(days)  { return this._fetch(`/api/v1/sessions/summary?days=${days}`); }
  async getInjuryRisk()          { return this._fetch("/api/v1/sessions/injury-risk"); }
  async getSessionHistory(limit = 30) { return this._fetch(`/api/v1/sessions/?limit=${limit}`); }

  // ── Coach ─────────────────────────────────────────────────────────────────
  async coachMessage(message, sessionId = null) {
    return this._fetch("/api/v1/coach/message", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  }
  async getDailyBriefing() { return this._fetch("/api/v1/coach/briefing"); }
  async getCoachHistory()  { return this._fetch("/api/v1/coach/history"); }

  // WebSocket coach stream — uses ws:// relative to current page host
  connectCoachStream(onChunk, onDone, onError) {
    // Derive WebSocket URL from current browser location (works behind any proxy)
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${proto}//${window.location.host}`;
    const ws = new WebSocket(`${wsUrl}/api/v1/coach/stream?token=${this._token}`);

    let ready = false;
    const queue = [];

    ws.onopen = () => {
      ready = true;
      queue.forEach(msg => ws.send(msg));
      queue.length = 0;
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.error) { onError?.(data.error); return; }
        if (data.done)  { onDone(); return; }
      } catch {
        // Not JSON → it's a text chunk
        onChunk(e.data);
      }
    };

    ws.onerror = () => onError?.("Connection error — retrying via HTTP");

    ws.onclose = (e) => {
      if (e.code !== 1000 && e.code !== 1005) {
        onError?.("Stream disconnected");
      }
    };

    return {
      send: (message, sessionId = null) => {
        const payload = JSON.stringify({ message, session_id: sessionId });
        if (ready) ws.send(payload);
        else queue.push(payload);
      },
      close: () => ws.close(1000, "done"),
      get readyState() { return ws.readyState; },
    };
  }

  // ── Gamification ──────────────────────────────────────────────────────────
  async getGamificationStatus() { return this._fetch("/api/v1/gamification/status"); }
  async getPersonalRecords()    { return this._fetch("/api/v1/gamification/personal-records"); }
}

export const api = new ApiClient();
export default api;
