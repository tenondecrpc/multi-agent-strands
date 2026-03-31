import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { Dashboard } from "@/pages/Dashboard";
import { SessionDetail } from "@/pages/SessionDetail";
import { connectSocket } from "@/lib/socket";
import { useUIStore } from "@/lib/stores/uiStore";

function AppContent() {
  const theme = useUIStore((state) => state.theme);

  useEffect(() => {
    console.log("[App] Initializing socket connection");
    connectSocket();
  }, []);

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/session/:ticketId" element={<SessionDetail />} />
    </Routes>
  );
}

export default AppContent;
