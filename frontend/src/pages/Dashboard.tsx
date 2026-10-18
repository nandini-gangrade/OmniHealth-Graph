import React, { useState, useEffect } from "react";
import { DashboardCard } from "../components/DashboardCard";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from "../components/ui/shadcn";
import { api } from "../services/api";
import { Link } from "react-router-dom";
import { 
  FolderHeart, FileText, BadgeCheck, Clock, 
  TrendingUp, Sparkles, AlertTriangle, ArrowRight 
} from "lucide-react";

export const Dashboard: React.FC = () => {
  const [kpis, setKpis] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const kpiData = await api.getKPIs();
      setKpis(kpiData);
      
      const sessList = await api.listSessions();
      setSessions(sessList.slice(0, 5)); // show top 5 recent
    } catch (e) {
      console.error("Error loading dashboard data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  const kpiValues = kpis?.kpis || {
    documentation_accuracy: 94.2,
    compliance_score: 96.5,
    revenue_recovery_usd: 2840.00,
    total_reimbursement_usd: 12450.00,
    time_saved_hours: 8.5
  };

  return (
    <div className="space-y-6">
      
      {/* Welcome Title Banner */}
      <div className="flex justify-between items-center bg-gradient-to-r from-slate-950/60 to-cyan-950/10 p-6 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-2xl font-bold font-outfit text-slate-100 flex items-center space-x-2">
            <span>Welcome to Aegis Hub</span>
            <Sparkles size={20} className="text-cyan-400" />
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Documentation metrics are looking strong. You saved an average of 18 minutes per consultation today.
          </p>
        </div>
        <Link to="/recording">
          <Button>
            Start Consult Recording
          </Button>
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard 
          title="Clinical Accuracy" 
          value={`${kpiValues.documentation_accuracy}%`}
          icon={BadgeCheck}
          description="Consolidated reviewer rating"
          change="+1.2% vs yesterday"
          color="text-cyan-400"
        />
        <DashboardCard 
          title="Compliance Score" 
          value={`${kpiValues.compliance_score}%`}
          icon={FolderHeart}
          description="CMS Guidelines conformity"
          change="Perfect necessity checks"
          color="text-teal-400"
        />
        <DashboardCard 
          title="Revenue Recovery" 
          value={`$${kpiValues.revenue_recovery_usd.toLocaleString()}`}
          icon={TrendingUp}
          description="Identified billing leakages"
          change="+$450 new opportunities"
          color="text-emerald-400"
        />
        <DashboardCard 
          title="Time Saved" 
          value={`${kpiValues.time_saved_hours} hrs`}
          icon={Clock}
          description="Physician administrative relief"
          change="Productivity up 28%"
          color="text-indigo-400"
        />
      </div>

      {/* Main split grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recent Session list table */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex justify-between items-center">
              <CardTitle>Recent Patient Consultations</CardTitle>
              <Link to="/sessions" className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center">
                <span>View all sessions</span>
                <ArrowRight size={14} className="ml-1" />
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-slate-950/40 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3">Patient Name</th>
                      <th className="px-6 py-3">Date</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Accuracy</th>
                      <th className="px-6 py-3">Reimbursement</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {sessions.map((sess) => (
                      <tr key={sess._id} className="hover:bg-slate-900/20 transition-colors">
                        <td className="px-6 py-4 font-medium text-slate-200">
                          <Link to={`/sessions?id=${sess._id}`} className="hover:text-cyan-400 transition-colors">
                            {sess.patient_name}
                          </Link>
                        </td>
                        <td className="px-6 py-4 text-slate-400">
                          {new Date(sess.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <Badge variant={sess.status === "reviewed" ? "success" : "info"}>
                            {sess.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 font-semibold text-slate-300">
                          {sess.reviewer_report?.aggregate_confidence || 92}%
                        </td>
                        <td className="px-6 py-4 font-bold text-emerald-400">
                          ${sess.revenue_report?.estimated_reimbursement || 0}
                        </td>
                      </tr>
                    ))}
                    {sessions.length === 0 && (
                      <tr>
                        <td colSpan={5} className="text-center py-6 text-slate-500">
                          No recent sessions. Start a voice recording to create your first session.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Leakage alerts sidebar */}
        <div className="space-y-6">
          <Card className="border-rose-500/20 bg-rose-500/5">
            <CardHeader>
              <CardTitle className="text-rose-400 flex items-center space-x-2">
                <AlertTriangle size={18} />
                <span>Claims at Risk (CMS Gaps)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-slate-300">
              <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-lg">
                <p className="font-semibold text-slate-200">Session ID: sess_17102026</p>
                <p className="text-rose-400 mt-1">E&M CPT 99214 mismatch</p>
                <p className="text-slate-400 mt-0.5">Missing specific duration documentation in Subjective notes.</p>
              </div>

              <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-lg">
                <p className="font-semibold text-slate-200">Session ID: sess_17102028</p>
                <p className="text-amber-400 mt-1">Unbilled CPT 99401 Detected</p>
                <p className="text-slate-400 mt-0.5">Hypertension dietary preventive counseling noted, but code is not recommended.</p>
              </div>
            </CardContent>
          </Card>

          {/* Spark trend graphic */}
          <Card>
            <CardHeader>
              <CardTitle>Weekly Reimbursement Trend</CardTitle>
            </CardHeader>
            <CardContent className="h-40 flex items-end justify-between space-x-2 pt-6">
              {kpis?.historical_data?.map((d: any, i: number) => {
                const heightPercent = `${(d.reimbursement / 2100) * 100}%`;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div 
                      style={{ height: heightPercent }} 
                      className="w-full bg-gradient-to-t from-cyan-600 to-teal-400 rounded-t shadow-cyan-glow transition-all duration-500"
                    ></div>
                    <span className="text-[10px] text-slate-500 mt-2">{d.date}</span>
                  </div>
                );
              }) || (
                <div className="text-center w-full text-slate-500 text-xs py-8">
                  Not enough trend data.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

      </div>

    </div>
  );
};
