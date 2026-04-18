"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Newspaper,
  TrendingUp,
  UserCheck,
  CalendarDays,
  BarChart3,
  PieChart,
  Bell,
  Zap,
  Server,
  Gauge,
  Settings,
  User,
  Crosshair,
} from "lucide-react";
import { cn } from "@/lib/utils";

const mainNav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/feed", label: "News Feed", icon: Newspaper },
  { href: "/sentiment", label: "Sentiment", icon: TrendingUp },
  { href: "/insider-trades", label: "Insider Trades", icon: UserCheck },
  { href: "/earnings", label: "Earnings", icon: CalendarDays },
  { href: "/short-interest", label: "Short Interest", icon: BarChart3 },
  { href: "/options-flow", label: "Options Flow", icon: Zap },
  { href: "/analytics", label: "Analytics", icon: PieChart },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/sources", label: "Sources", icon: Server },
  { href: "/admin/scheduler", label: "Scheduler", icon: Gauge },
  { href: "/settings", label: "Settings", icon: Settings },
];

const footerNav = [
  { href: "#", label: "Profile", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-56 h-full bg-[#0b1326] border-r border-[#3c4947]/15 shrink-0">
      {/* Logo */}
      <div className="px-6 py-6 mb-2">
        <div className="flex items-center gap-2">
          <Crosshair className="h-5 w-5 text-[#14b8a6]" />
          <span className="font-black text-[#14b8a6] tracking-tighter text-lg">
            ALPHASNIPER
          </span>
        </div>
        <p className="text-[10px] text-[#bbcac6] uppercase tracking-widest font-semibold mt-1 pl-7">
          Precision Terminal
        </p>
      </div>

      {/* Main navigation */}
      <nav className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {mainNav.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 py-2.5 px-4 text-sm rounded transition-all duration-150",
                isActive
                  ? "text-[#14b8a6] bg-[#171f33] border-l-2 border-[#14b8a6] rounded-l-none"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#2d3449] border-l-2 border-transparent"
              )}
            >
              <item.icon className="h-[18px] w-[18px] shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="mt-auto px-2 pt-4 pb-4 border-t border-[#3c4947]/15 space-y-0.5">
        {footerNav.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="flex items-center gap-3 text-slate-400 hover:text-slate-200 py-2.5 px-4 text-sm rounded transition-all duration-150 hover:bg-[#2d3449]"
          >
            <item.icon className="h-[18px] w-[18px] shrink-0" />
            <span>{item.label}</span>
          </Link>
        ))}
      </div>
    </aside>
  );
}
