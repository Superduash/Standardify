import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ChatPanel from "./components/ChatPanel";
import GapCheckPanel from "./components/GapCheckPanel";
import SearchPanel from "./components/SearchPanel";
import GraphView from "./components/GraphView";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ChatPanel />} />
        <Route path="/gap-check" element={<GapCheckPanel />} />
        <Route path="/search" element={<SearchPanel />} />
        <Route path="/graph" element={<GraphView />} />
        {/* catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
