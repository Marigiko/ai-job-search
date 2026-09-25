import { useCallback, useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon, Search, Bell, Wifi, WifiOff, X, CheckCircle2, AlertCircle, Info } from "lucide-react";
import { useThemeStore } from "@/stores/themeStore";
import { useNavigate } from "react-router-dom";
import type { WebSocketStatus } from "@/types";

interface Notification {
  id: number;
  type: "success" | "error" | "info";
  message: string;
  read: boolean;
}

// Simple in-memory notifications — replace with real data when available
const INITIAL_NOTIFICATIONS: Notification[] = [
  { id: 1, type: "info", message: "Welcome to CareerOS — your job search OS", read: false },
  { id: 2, type: "success", message: "Backend connected successfully", read: false },
];

function StatusBadge({ status }: { readonly status: WebSocketStatus }) {
  const config: Record<WebSocketStatus, { color: string; icon: typeof Wifi; label: string }> = {
    open: { color: "text-accent-success", icon: Wifi, label: "Connected" },
    connecting: { color: "text-accent-warning", icon: Wifi, label: "Connecting..." },
    closed: { color: "text-text-muted", icon: WifiOff, label: "Disconnected" },
    error: { color: "text-accent-danger", icon: WifiOff, label: "Error" },
  };

  const { color, icon: Icon, label } = config[status];

  return (
    <motion.div
      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-surface-elevated ${color}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      key={status}
    >
      <Icon className="w-3 h-3" />
      <span className="hidden sm:inline">{label}</span>
    </motion.div>
  );
}

export default function TopBar({ wsStatus }: TopBarProps) {
  const { isDark, toggle } = useThemeStore();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(INITIAL_NOTIFICATIONS);
  const notificationsRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const clearNotifications = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const dismissNotification = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (searchQuery.trim()) {
        navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      }
    },
    [searchQuery, navigate],
  );

  const clearSearch = useCallback(() => {
    setSearchQuery("");
  }, []);

  // Close notifications when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const notificationIcon = {
    success: CheckCircle2,
    error: AlertCircle,
    info: Info,
  };

  const notificationColor = {
    success: "text-accent-success",
    error: "text-accent-danger",
    info: "text-accent-primary",
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-bg-secondary/80 backdrop-blur-xl border-b border-border shrink-0">
      {/* Search */}
      <div className="flex-1 max-w-xl">
        <form onSubmit={handleSearchSubmit}>
          <motion.div
            className={`relative flex items-center rounded-lg border transition-all duration-200 ${
              searchFocused
                ? "border-accent-primary/50 bg-surface shadow-glow"
                : "border-border bg-surface-elevated"
            }`}
          >
            <Search className="absolute left-3 w-4 h-4 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              placeholder="Search jobs, companies, contacts..."
              className="w-full pl-10 pr-10 py-2 text-sm bg-transparent text-text-primary placeholder:text-text-muted focus:outline-none"
            />
            <AnimatePresence>
              {searchQuery.length > 0 && (
                <motion.button
                  type="button"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  onClick={clearSearch}
                  className="absolute right-3 p-0.5 rounded text-text-muted hover:text-text-primary transition-colors"
                  aria-label="Clear search"
                >
                  <X className="w-3.5 h-3.5" />
                </motion.button>
              )}
            </AnimatePresence>
          </motion.div>
        </form>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 ml-4">
        <StatusBadge status={wsStatus} />

        {/* Notifications */}
        <div className="relative" ref={notificationsRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 flex items-center justify-center text-[10px] font-bold rounded-full bg-accent-danger text-white ring-2 ring-bg-secondary">
                {unreadCount}
              </span>
            )}
          </button>

          <AnimatePresence>
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.95 }}
                className="absolute right-0 mt-2 w-80 rounded-lg border border-border bg-surface-elevated shadow-xl z-50 overflow-hidden"
              >
                <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                  <h3 className="text-sm font-medium text-text-primary">Notifications</h3>
                  {unreadCount > 0 && (
                    <button
                      onClick={clearNotifications}
                      className="text-xs text-accent-primary hover:underline"
                    >
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="px-4 py-8 text-center text-text-muted text-sm">
                      No notifications
                    </div>
                  ) : (
                    notifications.map((n) => {
                      const Icon = notificationIcon[n.type];
                      return (
                        <div
                          key={n.id}
                          className={`flex items-start gap-3 px-4 py-3 border-b border-border last:border-0 hover:bg-surface-hover transition-colors ${
                            n.read ? "opacity-50" : ""
                          }`}
                        >
                          <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${notificationColor[n.type]}`} />
                          <p className="text-sm text-text-secondary flex-1">{n.message}</p>
                          <button
                            onClick={() => dismissNotification(n.id)}
                            className="p-1 rounded text-text-muted hover:text-text-primary"
                            aria-label="Dismiss"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Dark mode toggle */}
        <motion.button
          onClick={toggle}
          className="relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors"
          whileTap={{ scale: 0.92 }}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          <AnimatePresence mode="wait">
            {isDark ? (
              <motion.div
                key="moon"
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Moon className="w-5 h-5" />
              </motion.div>
            ) : (
              <motion.div
                key="sun"
                initial={{ rotate: 90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: -90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Sun className="w-5 h-5" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </header>
  );
}

interface TopBarProps {
  readonly wsStatus: WebSocketStatus;
}
