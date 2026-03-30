import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { Dashboard } from "@/pages/Dashboard";
import { SessionDetail } from "@/pages/SessionDetail";
import { connectSocket } from "@/lib/socket";

function AppContent() {
  useEffect(() => {
    console.log("[App] Initializing socket connection");
    connectSocket();
  }, []);

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/session/:ticketId" element={<SessionDetail />} />
    </Routes>
  );
}

export default AppContent;
