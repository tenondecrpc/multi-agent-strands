import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query/client";
import { useConnectionStore } from "@/lib/stores/connectionStore";
import { socket } from "@/lib/socket";
import "./index.css";
import App from "./App";
import type { ReactNode } from "react";

function SocketProvider({ children }: { children: ReactNode }) {
  const setStatus = useConnectionStore((state) => state.setStatus);
  const setLastPing = useConnectionStore((state) => state.setLastPing);

  socket.on("connect", () => {
    setStatus("connected");
    setLastPing(new Date());
  });

  socket.on("disconnect", () => {
    setStatus("disconnected");
  });

  socket.on("connect_error", () => {
    setStatus("reconnecting");
  });

  return <>{children}</>;
}

export default function Root() {
  return (
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SocketProvider>
            <App />
          </SocketProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </StrictMode>
  );
}

createRoot(document.getElementById("root")!).render(<Root />);
