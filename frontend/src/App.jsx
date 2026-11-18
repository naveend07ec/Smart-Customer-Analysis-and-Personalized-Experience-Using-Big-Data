import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/ErrorBoundary';
import OverviewDashboard from './pages/OverviewDashboard';
import CustomerAnalytics from './pages/CustomerAnalytics';
import CustomerSegmentation from './pages/CustomerSegmentation';
import CustomerDetails from './pages/CustomerDetails';
import PersonalizedRecommendations from './pages/PersonalizedRecommendations';
import CustomerRetention from './pages/CustomerRetention';
import DataProcessing from './pages/DataProcessing';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navbar />
        <main className="main-content-viewport">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<OverviewDashboard />} />
              <Route path="/analytics" element={<CustomerAnalytics />} />
              <Route path="/segmentation" element={<CustomerSegmentation />} />
              <Route path="/customers" element={<CustomerDetails />} />
              <Route path="/recommendations" element={<PersonalizedRecommendations />} />
              <Route path="/churn" element={<CustomerRetention />} />
              <Route path="/pipeline" element={<DataProcessing />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  );
}
