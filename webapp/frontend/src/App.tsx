import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HomePage } from "./pages/HomePage";
import { TopPairsPage } from "./pages/TopPairsPage";
import { SpeciesDetailPage } from "./pages/SpeciesDetailPage";
import { FeaturesPage } from "./pages/FeaturesPage";
import { FieldGuidePage } from "./pages/FieldGuidePage";
import { CommunityPage } from "./pages/CommunityPage";
import { PredicateExplorerPage } from "./pages/PredicateExplorerPage";
import { DebugPanel } from "./components/DebugPanel";
import "./App.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 60_000 } },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div style={{ marginRight: "25vw" }}>
          <header>
            <nav>
              <Link to="/" style={{ textDecoration: "none" }}>
                <h1>Arborphy</h1>
              </Link>
            </nav>
          </header>
          <main>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/co-occurrence" element={<TopPairsPage />} />
              <Route path="/features" element={<FeaturesPage />} />
              <Route path="/field-guide" element={<FieldGuidePage />} />
              <Route path="/community" element={<CommunityPage />} />
              <Route path="/predicates" element={<PredicateExplorerPage />} />
              <Route path="/species/:name" element={<SpeciesDetailPage />} />
            </Routes>
          </main>
        </div>
        <DebugPanel />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
