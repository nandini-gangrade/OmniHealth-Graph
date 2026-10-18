import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Dialog } from "../components/ui/shadcn";
import { SessionDetails } from "../components/SessionDetails";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { FolderHeart, Plus, Search, Calendar, User, ArrowLeft, RefreshCw } from "lucide-react";

export const Sessions: React.FC = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  
  // New session modal variables
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [patientName, setPatientName] = useState("");
  const [patientDob, setPatientDob] = useState("");

  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Parse session ID from query parameters
  const queryParams = new URLSearchParams(location.search);
  const selectedSessionId = queryParams.get("id");

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await api.listSessions();
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientName || !patientDob) return;
    try {
      const newSess = await api.createSession({
        patient_name: patientName,
        patient_dob: patientDob,
        doctor_id: user?.email || "doc_1",
        doctor_name: user?.fullName || "Dr. Elizabeth"
      });
      setIsModalOpen(false);
      setPatientName("");
      setPatientDob("");
      // Refresh list
      await loadSessions();
      // Auto navigate to recording page with the new session active
      navigate(`/recording?id=${newSess._id}`);
    } catch (e) {
      alert("Error creating session.");
    }
  };

  const selectedSession = sessions.find(s => s._id === selectedSessionId);

  const filteredSessions = sessions.filter(s => 
    s.patient_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s._id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading && sessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  // Render detail inspector if session is selected
  if (selectedSessionId && selectedSession) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" onClick={() => navigate("/sessions")}>
            <ArrowLeft size={16} className="mr-2" /> Back to lists
          </Button>
          <div>
            <h2 className="text-xl font-bold font-outfit text-slate-100">{selectedSession.patient_name}</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              DOB: {selectedSession.patient_dob} | ID: {selectedSession._id}
            </p>
          </div>
        </div>

        <SessionDetails session={selectedSession} onRefresh={loadSessions} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 font-outfit">Patient Consultation Portals</h2>
          <p className="text-sm text-slate-400 mt-1">Review generated electronic health records, coding accuracy, and compliance checklists.</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="secondary" onClick={loadSessions}>
            <RefreshCw size={16} />
          </Button>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus size={16} className="mr-1.5" /> New Patient File
          </Button>
        </div>
      </div>

      {/* Search Filter Panel */}
      <div className="flex items-center space-x-3 bg-slate-950/40 border border-slate-800 rounded-lg p-3">
        <Search size={18} className="text-slate-400" />
        <input 
          placeholder="Filter by Patient name or Consultation ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-transparent border-0 text-slate-200 text-sm w-full focus:outline-none"
        />
      </div>

      {/* Sessions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSessions.map((sess) => (
          <Card key={sess._id} className="hover:border-slate-700/60 transition-all duration-300 flex flex-col justify-between h-48">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-slate-200 font-outfit truncate w-40">{sess.patient_name}</h3>
                  <p className="text-[10px] text-slate-400 mt-1">DOB: {sess.patient_dob}</p>
                </div>
                <Badge variant={sess.status === "reviewed" ? "success" : "info"}>
                  {sess.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pb-3 text-xs text-slate-400 flex-1 flex flex-col justify-between">
              <div className="space-y-1 mt-2">
                <p>Consultant: <span className="text-slate-200 font-semibold">{sess.doctor_name}</span></p>
                <p>Created: <span>{new Date(sess.created_at).toLocaleString()}</span></p>
              </div>
              <div className="flex items-center justify-between border-t border-slate-850 pt-2 mt-4">
                <div>
                  <p className="text-[10px] uppercase text-slate-400">Est. Billing</p>
                  <span className="font-bold text-emerald-400 text-sm">
                    ${sess.revenue_report?.estimated_reimbursement || 0}
                  </span>
                </div>
                <Button size="sm" variant="glass" onClick={() => navigate(`/sessions?id=${sess._id}`)}>
                  Open EHR
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}

        {filteredSessions.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-500 bg-slate-950/20 border border-slate-800 border-dashed rounded-lg">
            No patient sessions matching filter found.
          </div>
        )}
      </div>

      {/* New Session Dialog Modal */}
      <Dialog isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Consultation File">
        <form onSubmit={handleCreateSession} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Patient Full Name</label>
            <input 
              type="text"
              required
              placeholder="e.g. John Doe"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Date of Birth</label>
            <input 
              type="text"
              required
              placeholder="MM/DD/YYYY"
              value={patientDob}
              onChange={(e) => setPatientDob(e.target.value)}
              className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">
              Initialize File
            </Button>
          </div>
        </form>
      </Dialog>

    </div>
  );
};
