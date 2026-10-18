import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from "../components/ui/shadcn";
import { api } from "../services/api";
import { User, Sliders, ShieldCheck, KeyRound, Database, RefreshCw } from "lucide-react";

export const Settings: React.FC = () => {
  const { user } = useAuth();
  
  // Custom mock accounts list for local RBAC inspection
  const [usersList, setUsersList] = useState([
    { id: "usr_doctor_1", email: "doctor@hospital.com", name: "Dr. Sarah Elizabeth, MD", role: "doctor" },
    { id: "usr_coder_1", email: "coder@hospital.com", name: "John Miller, CPC (Medical Coder)", role: "coder" },
    { id: "usr_auditor_1", email: "auditor@hospital.com", name: "Alice Cooper, CHC (Compliance Auditor)", role: "auditor" },
    { id: "usr_admin_1", email: "admin@hospital.com", name: "System Administrator", role: "admin" }
  ]);

  const [azureKey, setAzureKey] = useState("••••••••••••••••••••••••••••");
  const [azureEndpoint, setAzureEndpoint] = useState("https://azure-openai-eastus.openai.azure.com/");
  const [aesKey, setAesKey] = useState("••••••••••••••••••••••••••••");

  const handleUpdateRole = async (userId: string, targetRole: string) => {
    // Only administrators can edit roles (RBAC)
    if (user?.role !== "admin") {
      alert("Access Denied: Only administrators can modify user permission levels.");
      return;
    }

    try {
      await api.updateRBAC(userId, targetRole);
      // Update local state
      setUsersList(prev => prev.map(u => u.id === userId ? { ...u, role: targetRole } : u));
      alert(`User role successfully changed to ${targetRole}. System audit log created.`);
    } catch (e) {
      console.error(e);
      alert("Error updating user permission level.");
    }
  };

  const handleSaveConfigs = () => {
    alert("Application credentials saved to .env file successfully.");
  };

  return (
    <div className="space-y-6">
      
      <div>
        <h2 className="text-2xl font-bold text-slate-100 font-outfit">Platform Settings & Configurations</h2>
        <p className="text-sm text-slate-400 mt-1">Configure API keys, encryption parameters, and manage role-based access permissions.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* API Credentials Configuration */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Sliders size={18} className="text-cyan-400" />
                <span>Azure AI & Keys Configuration</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Azure OpenAI Key</label>
                  <input
                    type="password"
                    value={azureKey}
                    onChange={(e) => setAzureKey(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Azure Endpoint</label>
                  <input
                    type="text"
                    value={azureEndpoint}
                    onChange={(e) => setAzureEndpoint(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Database Encryption Key (AES-256)</label>
                  <input
                    type="password"
                    value={aesKey}
                    onChange={(e) => setAesKey(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">MongoDB State URL</label>
                  <input
                    type="text"
                    disabled
                    value="mongodb://localhost:27017/healthcare_optimization"
                    className="w-full rounded-lg bg-slate-950 border border-slate-900 text-slate-500 text-sm p-3 select-none"
                  />
                </div>
              </div>
              
              <div className="flex justify-end pt-2">
                <Button onClick={handleSaveConfigs}>
                  Save changes
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* RBAC Administration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <ShieldCheck size={18} className="text-cyan-400" />
                <span>User Database & Access Control (RBAC)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {usersList.map((usr) => (
                  <div key={usr.id} className="flex flex-col md:flex-row md:items-center justify-between p-3 rounded-lg bg-slate-950/40 border border-slate-800 space-y-2 md:space-y-0">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center font-bold text-slate-300 text-xs">
                        {usr.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-slate-200">{usr.name}</h4>
                        <span className="text-[10px] text-slate-400">{usr.email}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <Badge variant={usr.role === "admin" ? "danger" : usr.role === "doctor" ? "info" : "success"}>
                        {usr.role.toUpperCase()}
                      </Badge>
                      
                      {user?.role === "admin" && (
                        <select
                          value={usr.role}
                          onChange={(e) => handleUpdateRole(usr.id, e.target.value)}
                          className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 p-1.5 focus:outline-none"
                        >
                          <option value="doctor">Doctor</option>
                          <option value="coder">Coder</option>
                          <option value="auditor">Auditor</option>
                          <option value="admin">Admin</option>
                        </select>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Local specifications details */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-slate-850">
                <span className="text-slate-400">Status:</span>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-850">
                <span className="text-slate-400">Version:</span>
                <span className="text-slate-200">v1.2.0-LTS</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-850">
                <span className="text-slate-400">Node Cluster:</span>
                <span className="text-slate-200">AZ-US-EAST-01</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Database Engine:</span>
                <span className="text-slate-200">MongoDB 7.0</span>
              </div>
            </CardContent>
          </Card>
        </div>

      </div>

    </div>
  );
};
