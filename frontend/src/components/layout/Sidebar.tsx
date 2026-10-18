import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { 
  LayoutDashboard, 
  FileText, 
  Mic, 
  BarChart3, 
  Settings as SettingsIcon, 
  ShieldCheck,
  ShieldAlert,
  FolderHeart
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { user } = useAuth();
  
  const menuItems = [
    { path: "/", name: "Doctor Dashboard", icon: LayoutDashboard },
    { path: "/sessions", name: "Patient Sessions", icon: FolderHeart },
    { path: "/recording", name: "Live Recording", icon: Mic },
    { path: "/analytics", name: "KPI & Analytics", icon: BarChart3 },
    { path: "/settings", name: "Settings & RBAC", icon: SettingsIcon },
  ];

  // Admin Audit Log menu item
  const isAdmin = user?.role === "admin";

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <aside className="w-64 bg-slate-950/60 border-r border-slate-800 flex flex-col justify-between p-4 h-screen sticky top-0 backdrop-blur-lg">
      <div>
        {/* Brand Logo */}
        <div className="flex items-center space-x-2 px-3 py-4 mb-6">
          <div className="p-2 bg-gradient-to-tr from-cyan-600 to-teal-500 rounded-lg text-white shadow-cyan-glow">
            <ShieldCheck size={22} />
          </div>
          <div>
            <h1 className="text-md font-bold bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent font-outfit leading-tight">
              OmniHealth Graph
            </h1>
            <p className="text-[10px] text-cyan-400 uppercase tracking-widest font-semibold">
              EHR & Rev Optimization
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  active 
                    ? "bg-cyan-500/10 text-cyan-400 border-l-2 border-cyan-400 shadow-cyan-glow" 
                    : "text-slate-400 hover:bg-slate-900/40 hover:text-slate-200"
                }`}
              >
                <Icon size={18} />
                <span>{item.name}</span>
              </Link>
            );
          })}

          {isAdmin && (
            <Link
              to="/audit-logs"
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive("/audit-logs") 
                  ? "bg-rose-500/10 text-rose-400 border-l-2 border-rose-400" 
                  : "text-slate-400 hover:bg-slate-900/40 hover:text-slate-200"
              }`}
            >
              <ShieldAlert size={18} />
              <span>Audit logs</span>
            </Link>
          )}
        </nav>
      </div>

      {/* User display badge */}
      {user && (
        <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-lg flex items-center space-x-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center font-bold text-slate-100 text-xs">
            {user.fullName.split(" ").pop()?.substring(0, 2).toUpperCase() || "DR"}
          </div>
          <div className="overflow-hidden flex-1">
            <h4 className="text-xs font-semibold text-slate-200 truncate">{user.fullName}</h4>
            <span className="text-[10px] text-cyan-400 uppercase tracking-widest font-semibold">{user.role}</span>
          </div>
        </div>
      )}
    </aside>
  );
};
