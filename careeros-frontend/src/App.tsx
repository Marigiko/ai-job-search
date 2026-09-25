import { Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "@/components/layout/MainLayout";
import {
  Dashboard,
  Pipeline,
  Jobs,
  Outreach,
  Documents,
  Analytics,
  Settings,
  Search,
} from "@/pages";

export function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/search" element={<Search />} />
        <Route path="/outreach" element={<Outreach />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
