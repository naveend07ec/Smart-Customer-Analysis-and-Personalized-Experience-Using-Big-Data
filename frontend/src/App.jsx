import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import OverviewDashboard from './pages/OverviewDashboard';
import CustomerAnalytics from './pages/CustomerAnalytics';
import CustomerSegmentation from './pages/CustomerSegmentation';
import CustomerDetails from './pages/CustomerDetails';
import PersonalizedRecommendations from './pages/PersonalizedRecommendations';
import DataProcessing from './pages/DataProcessing';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Navbar />
          <main style={{ flex: 1, overflowY: 'auto' }}>
            <Routes>
              <Route path="/" element={<OverviewDashboard />} />
              <Route path="/analytics" element={<CustomerAnalytics />} />
              <Route path="/segmentation" element={<CustomerSegmentation />} />
              <Route path="/customers" element={<CustomerDetails />} />
              <Route path="/recommendations" element={<PersonalizedRecommendations />} />
              <Route path="/pipeline" element={<DataProcessing />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
