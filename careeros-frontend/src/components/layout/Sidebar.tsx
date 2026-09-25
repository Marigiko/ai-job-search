import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Columns3,
  Briefcase,
  Search as SearchIcon,
  Mail,
  FileText,
  BarChart3,
  Settings,
  Rocket,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  readonly label: string;
  readonly path: string;
  readonly icon: LucideIcon;
}

const navItems: readonly NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Pipeline", path: "/pipeline", icon: Columns3 },
  { label: "Jobs", path: "/jobs", icon: Briefcase },
  { label: "Search", path: "/search", icon: SearchIcon },
  { label: "Outreach", path: "/outreach", icon: Mail },
  { label: "Documents", path: "/documents", icon: FileText },
  { label: "Analytics", path: "/analytics", icon: BarChart3 },
];

export default function Sidebar() {
  return (
    <aside className="flex flex-col h-full w-64 bg-bg-secondary border-r border-border">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-border shrink-0">
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-glow"
          whileHover={{ scale: 1.05 }}
        >
          <Rocket className="w-4 h-4 text-white" />
        </motion.div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight text-text-primary">CareerOS</span>
          <span className="text-[10px] text-text-muted uppercase tracking-widest">Operating System</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                {({ isActive }) => (
                  <>
                    <item.icon
                      className={`w-[18px] h-[18px] ${
                        isActive ? "text-accent-primary" : ""
                      }`}
                    />
                    <span>{item.label}</span>
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active-indicator"
                        className="absolute left-0 w-0.5 h-8 bg-accent-primary rounded-r"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Settings */}
      <div className="px-3 py-4 border-t border-border">
        <NavLink
          to="/settings"
          className={({ isActive }) => `nav-link ${isActive ? "nav-link-active" : ""}`}
        >
          <Settings className="w-[18px] h-[18px]" />
          <span>Settings</span>
        </NavLink>
      </div>
    </aside>
  );
}
