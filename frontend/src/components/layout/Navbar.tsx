import React from "react";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../ui/shadcn";
import { LogOut, HeartPulse, Activity, Brain } from "lucide-react";

export const Navbar: React.FC = () => {
  const { logout, user } = useAuth();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/20 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-40">
      <div className="flex items-center space-x-6">
        <h2 className="text-sm font-semibold text-slate-400 font-outfit hidden md:block">
          Hospital Node: <span className="text-cyan-400">Central-East-US</span>
        </h2>
        
        {/* System Health Indicators */}
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5 text-emerald-400 font-medium">
            <HeartPulse size={12} />
            <span>DB Online</span>
          </div>
          <div className="flex items-center space-x-1.5 text-cyan-400 font-medium">
            <Brain size={12} />
            <span>Agents Active</span>
          </div>
          <div className="flex items-center space-x-1.5 text-teal-400 font-medium">
            <Activity size={12} />
            <span>RAG Indexed</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {user && (
          <span className="text-xs text-slate-400">
            Session: <span className="text-slate-200 font-semibold">{user.fullName.split(",")[0]}</span>
          </span>
        )}
        <Button variant="ghost" size="sm" onClick={logout} className="text-slate-400 hover:text-rose-400 hover:bg-rose-500/10">
          <LogOut size={16} className="mr-2" />
          Sign out
        </Button>
      </div>
    </header>
  );
};
