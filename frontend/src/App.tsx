import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Sidebar } from "./components/layout/Sidebar";
import { Navbar } from "./components/layout/Navbar";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Sessions } from "./pages/Sessions";
import { LiveRecording } from "./pages/LiveRecording";
import { Analytics } from "./pages/Analytics";
import { Settings } from "./pages/Settings";
import { AuditLogs } from "./pages/AuditLogs";

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#040814] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#040814] text-slate-100 flex font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen overflow-y-auto">
        <Navbar />
        <main className="p-6 max-w-7xl w-full mx-auto flex-1">
          {children}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={
            <ProtectedLayout>
              <Dashboard />
            </ProtectedLayout>
          } />
          
          <Route path="/sessions" element={
            <ProtectedLayout>
              <Sessions />
            </ProtectedLayout>
          } />

          <Route path="/recording" element={
            <ProtectedLayout>
              <LiveRecording />
            </ProtectedLayout>
          } />

          <Route path="/analytics" element={
            <ProtectedLayout>
              <Analytics />
            </ProtectedLayout>
          } />

          <Route path="/settings" element={
            <ProtectedLayout>
              <Settings />
            </ProtectedLayout>
          } />

          <Route path="/audit-logs" element={
            <ProtectedLayout>
              <AuditLogs />
            </ProtectedLayout>
          } />

          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};
