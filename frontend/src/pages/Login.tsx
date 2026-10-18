import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle } from "../components/ui/shadcn";
import { ShieldCheck, HeartPulse, Loader2, Sparkles } from "lucide-react";

export const Login: React.FC = () => {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Failed to authenticate");
    } finally {
      setIsLoading(false);
    }
  };

  // Quick sign-in helper for hackathon reviewers
  const handleQuickSignIn = async (emailPreset: string, passPreset: string) => {
    setEmail(emailPreset);
    setPassword(passPreset);
    setIsLoading(true);
    setError("");
    try {
      await login(emailPreset, passPreset);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Failed to authenticate");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#02050E] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      
      {/* Decorative ambient blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md relative z-10 space-y-6">
        
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-gradient-to-tr from-cyan-600 to-teal-500 rounded-xl text-white shadow-cyan-glow mb-2">
            <HeartPulse size={32} />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent font-outfit">
            Aegis Healthcare
          </h1>
          <p className="text-sm text-slate-400">
            EHR Documentation & Revenue Optimization Platform
          </p>
        </div>

        {/* Login form card */}
        <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-lg text-slate-200">Sign in to workspace</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs font-semibold">
                  {error}
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Corporate Email</label>
                <input
                  type="email"
                  required
                  placeholder="doctor@hospital.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
              </div>

              <Button type="submit" className="w-full py-3" disabled={isLoading}>
                {isLoading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
                Login Securely
              </Button>
            </form>

            {/* Quick Demo Sign-ins */}
            <div className="mt-6 pt-6 border-t border-slate-900 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-400 flex items-center justify-center space-x-1">
                <Sparkles size={10} className="text-cyan-400" />
                <span>Hackathon Reviewer Presets</span>
              </p>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button 
                  onClick={() => handleQuickSignIn("doctor@hospital.com", "doctor123")}
                  className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800/80 text-left transition-colors"
                >
                  <p className="font-semibold text-slate-200">Clinician Account</p>
                  <span className="text-[10px] text-cyan-400">Dr. Sarah (Doctor)</span>
                </button>

                <button 
                  onClick={() => handleQuickSignIn("coder@hospital.com", "coder123")}
                  className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800/80 text-left transition-colors"
                >
                  <p className="font-semibold text-slate-200">Medical Coder</p>
                  <span className="text-[10px] text-emerald-400">John Miller (Coder)</span>
                </button>

                <button 
                  onClick={() => handleQuickSignIn("auditor@hospital.com", "auditor123")}
                  className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800/80 text-left transition-colors"
                >
                  <p className="font-semibold text-slate-200">Policy Auditor</p>
                  <span className="text-[10px] text-teal-400">Alice (Auditor)</span>
                </button>

                <button 
                  onClick={() => handleQuickSignIn("admin@hospital.com", "admin123")}
                  className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800/80 text-left transition-colors"
                >
                  <p className="font-semibold text-slate-200">System Admin</p>
                  <span className="text-[10px] text-rose-400">Full Access (RBAC)</span>
                </button>
              </div>
            </div>

          </CardContent>
        </Card>
      </div>
    </div>
  );
};
