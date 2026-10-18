// Set VITE_API_BASE in Vercel (e.g. https://your-backend.example.com/api); defaults to local backend
const API_BASE: string = (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8000/api";

function getHeaders() {
  const token = localStorage.getItem("auth_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
  };
}

export const api = {
  // Auth
  async login(formData: URLSearchParams) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail || "Authentication failed");
    }
    return res.json();
  },

  async register(data: any) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
  },

  // Sessions
  async listSessions() {
    const res = await fetch(`${API_BASE}/sessions`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load clinical sessions");
    return res.json();
  },

  async createSession(data: { patient_name: string; patient_dob: string; doctor_id: string; doctor_name: string }) {
    const res = await fetch(`${API_BASE}/sessions/create`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create session");
    return res.json();
  },

  async getSession(sessionId: string) {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch session details");
    return res.json();
  },

  async processSession(sessionId: string, rawTranscript: string) {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/process`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ raw_transcript: rawTranscript }),
    });
    if (!res.ok) throw new Error("Error executing agents on transcript");
    return res.json();
  },

  async updateNotes(sessionId: string, notes: any) {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/notes`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(notes),
    });
    if (!res.ok) throw new Error("Failed to save changes");
    return res.json();
  },

  async getDepartmentCompliance(dept: string) {
    const res = await fetch(`${API_BASE}/graph/department/${encodeURIComponent(dept)}`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load hospital brain");
    return res.json();
  },

  async approveSession(sessionId: string, reviewerNotes: string, acknowledgeAlerts = false) {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/approve`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify({ notes: reviewerNotes, acknowledge_alerts: acknowledgeAlerts ? "true" : "false" }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to approve session" }));
      throw new Error(err.detail || "Failed to approve session");
    }
    return res.json();
  },

  async uploadMultimodalDocument(sessionId: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    
    const token = localStorage.getItem("auth_token");
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/upload-document`, {
      method: "POST",
      headers: token ? { "Authorization": `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) throw new Error("Failed to upload document file");
    return res.json();
  },

  // Analytics KPIs
  async getKPIs() {
    const res = await fetch(`${API_BASE}/analytics/kpis`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load dashboard statistics");
    return res.json();
  },

  // Admin Audit Logs
  async getAuditLogs() {
    const res = await fetch(`${API_BASE}/admin/audit-logs`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Access denied: Admin permissions required");
    return res.json();
  },

  async updateRBAC(userId: string, role: string) {
    const res = await fetch(`${API_BASE}/admin/rbac/${userId}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify({ role }),
    });
    if (!res.ok) throw new Error("Failed to update user role");
    return res.json();
  },

  // WebSockets voice streaming URL builder
  getVoiceSocketUrl(sessionId: string): string {
    return `ws://127.0.0.1:8000/api/sessions/${sessionId}/voice`;
  }
};
