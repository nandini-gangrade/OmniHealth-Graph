import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";

interface UserProfile {
  email: string;
  role: string;
  fullName: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const cachedToken = localStorage.getItem("auth_token");
    const cachedRole = localStorage.getItem("auth_role");
    const cachedName = localStorage.getItem("auth_name");
    const cachedEmail = localStorage.getItem("auth_email");

    if (cachedToken && cachedRole && cachedName && cachedEmail) {
      setToken(cachedToken);
      setUser({
        email: cachedEmail,
        role: cachedRole,
        fullName: cachedName
      });
    }
    setLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", pass);

      const res = await api.login(formData);
      
      localStorage.setItem("auth_token", res.access_token);
      localStorage.setItem("auth_role", res.role);
      localStorage.setItem("auth_name", res.full_name);
      localStorage.setItem("auth_email", email);

      setToken(res.access_token);
      setUser({
        email,
        role: res.role,
        fullName: res.full_name
      });
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_role");
    localStorage.removeItem("auth_name");
    localStorage.removeItem("auth_email");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
