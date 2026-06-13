import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Elevated } from "@/pages/elevated";
import { FileOwner } from "@/pages/file-owner";
import { FileRecovery } from "@/pages/file-recovery";
import { Help } from "@/pages/help";
import Logs from "@/pages/logs";
import { Processes } from "@/pages/processes";
import { Services } from "@/pages/services";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";
import { Volumes } from "@/pages/volumes";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/status" element={<Status />} />
          <Route path="/processes" element={<Processes />} />
          <Route path="/services" element={<Services />} />
          <Route path="/volumes" element={<Volumes />} />
          <Route path="/file-owner" element={<FileOwner />} />
          <Route path="/file-recovery" element={<FileRecovery />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/elevated" element={<Elevated />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
