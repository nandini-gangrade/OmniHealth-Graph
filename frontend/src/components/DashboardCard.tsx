import React from "react";
import { Card, CardContent } from "./ui/shadcn";
import { LucideIcon } from "lucide-react";

interface DashboardCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  color?: string;
}

export const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  icon: Icon,
  description,
  change,
  changeType = "positive",
  color = "text-cyan-400"
}) => {
  return (
    <Card className="hover:border-slate-700/60 transition-all duration-300">
      <CardContent className="p-5 flex flex-col justify-between h-32">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
            <h3 className="text-2xl font-bold text-slate-100 font-outfit mt-1">{value}</h3>
          </div>
          <div className={`p-2 bg-slate-900/60 rounded-lg border border-slate-800 ${color}`}>
            <Icon size={20} />
          </div>
        </div>

        <div className="flex items-center justify-between text-xs mt-2 border-t border-slate-850/40 pt-2">
          {change && (
            <span className={`font-semibold ${
              changeType === "positive" ? "text-emerald-400" : 
              changeType === "negative" ? "text-rose-400" : "text-slate-400"
            }`}>
              {change}
            </span>
          )}
          {description && (
            <span className="text-slate-400 truncate ml-2">{description}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
