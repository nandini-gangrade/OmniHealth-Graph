import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "../components/ui/shadcn";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { ShieldCheck, FileClock, ShieldAlert } from "lucide-react";

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await api.getAuditLogs();
        setLogs(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    if (user?.role === "admin") {
      fetchLogs();
    }
  }, [user]);

  if (user?.role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] p-4 text-center">
        <ShieldAlert className="text-rose-500 mb-4" size={48} />
        <h2 className="text-xl font-bold text-slate-100 font-outfit">Access Denied</h2>
        <p className="text-sm text-slate-400 mt-2 max-w-md">
          You do not have permission to view system audit logs. Only System Administrators can access security logs.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      <div>
        <h2 className="text-2xl font-bold text-slate-100 font-outfit">Security & Compliance Audit Logs</h2>
        <p className="text-sm text-slate-400 mt-1">Immutable session history records detailing user activities, PII masking, and data modifications.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-rose-400">
            <FileClock size={18} />
            <span>Audit Trail Ledger</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-slate-950/40 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Action</th>
                  <th className="px-6 py-3">Actor (Role)</th>
                  <th className="px-6 py-3">Resource Target</th>
                  <th className="px-6 py-3">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 text-xs">
                {logs.map((log, idx) => (
                  <tr key={log._id || idx} className="hover:bg-slate-900/10 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-300 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={
                        log.action.includes("RBAC") || log.action.includes("DELETED") ? "danger" : 
                        log.action.includes("EDIT") ? "warning" : "success"
                      }>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-200">{log.user_name}</div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest">{log.role}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-[10px] text-cyan-400">
                      {log.resource_id || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-slate-450 leading-relaxed max-w-sm">
                      {log.details}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-slate-500">
                      No system events registered in the audit database.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

    </div>
  );
};
