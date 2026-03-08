import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components';
import {
  DashboardPage,
  UploadPage,
  JobsPage,
  DownloadsPage,
  SystemPage,
  DepthValidationPage,
  ModelComparisonPage,
} from './pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="upload" element={<UploadPage />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route path="downloads" element={<DownloadsPage />} />
            <Route path="system" element={<SystemPage />} />
            <Route path="compare" element={<ModelComparisonPage />} />
            <Route path="jobs/:jobId/validate" element={<DepthValidationPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

