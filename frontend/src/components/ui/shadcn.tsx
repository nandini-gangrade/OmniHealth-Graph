import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// --- BUTTON ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "glass" | "accent";
  size?: "sm" | "md" | "lg";
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = "primary",
  size = "md",
  ...props
}) => {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed",
        {
          "bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-glow": variant === "primary",
          "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700": variant === "secondary",
          "bg-emerald-600 hover:bg-emerald-500 text-white shadow-teal-glow": variant === "accent",
          "bg-rose-600 hover:bg-rose-500 text-white": variant === "danger",
          "hover:bg-slate-800 text-slate-400 hover:text-white": variant === "ghost",
          "bg-slate-900/60 hover:bg-slate-850/80 text-cyan-400 border border-cyan-500/20 backdrop-blur-sm": variant === "glass",
        },
        {
          "px-3 py-1.5 text-xs": size === "sm",
          "px-4 py-2 text-sm": size === "md",
          "px-5 py-2.5 text-base": size === "lg",
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

// --- CARD ---
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className, ...props }) => {
  return (
    <div className={cn("glass-card rounded-xl border border-slate-800 shadow-glass overflow-hidden", className)} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className, ...props }) => {
  return <div className={cn("px-6 py-4 border-b border-slate-800/60 bg-slate-950/20", className)} {...props}>{children}</div>;
};

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ children, className, ...props }) => {
  return <h3 className={cn("text-lg font-semibold text-slate-100 font-outfit", className)} {...props}>{children}</h3>;
};

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className, ...props }) => {
  return <div className={cn("p-6", className)} {...props}>{children}</div>;
};

// --- BADGE ---
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "info" | "success" | "warning" | "danger" | "neutral";
}

export const Badge: React.FC<BadgeProps> = ({ children, className, variant = "info", ...props }) => {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold select-none",
        {
          "bg-cyan-500/10 text-cyan-400 border border-cyan-500/25": variant === "info",
          "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25": variant === "success",
          "bg-amber-500/10 text-amber-400 border border-amber-500/25": variant === "warning",
          "bg-rose-500/10 text-rose-400 border border-rose-500/25": variant === "danger",
          "bg-slate-700/30 text-slate-400 border border-slate-700/30": variant === "neutral",
        },
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

// --- TABS ---
interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}
export const Tabs: React.FC<TabsProps> = ({ children, className, ...props }) => {
  return <div className={cn("w-full", className)} {...props}>{children}</div>;
};

export const TabsList: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className, ...props }) => {
  return (
    <div className={cn("flex space-x-1 p-1 bg-slate-950/40 border border-slate-800 rounded-lg backdrop-blur-md", className)} {...props}>
      {children}
    </div>
  );
};

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
  activeTab: string;
  setActiveTab: (val: string) => void;
}
export const TabsTrigger: React.FC<TabsTriggerProps> = ({ children, className, value, activeTab, setActiveTab, ...props }) => {
  const isActive = activeTab === value;
  return (
    <button
      onClick={() => setActiveTab(value)}
      className={cn(
        "flex-1 px-3 py-2 text-xs font-medium rounded-md transition-all duration-200 focus:outline-none",
        isActive 
          ? "bg-slate-800 text-cyan-400 border-b border-cyan-500 shadow-sm" 
          : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/30",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  activeTab: string;
}
export const TabsContent: React.FC<TabsContentProps> = ({ children, className, value, activeTab, ...props }) => {
  if (activeTab !== value) return null;
  return <div className={cn("py-4", className)} {...props}>{children}</div>;
};

// --- DIALOG ---
interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}
export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}></div>
      {/* Modal */}
      <div className="relative glass-panel border border-slate-700/50 w-full max-w-md rounded-xl p-6 shadow-2xl z-10 animate-in fade-in zoom-in duration-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-slate-100 font-outfit">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};
