import axios from 'axios';

// Vite proxy forwards /api to http://127.0.0.1:5000 in dev
const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const api = {
  // System Health
  getHealth: () => client.get('/health').then(r => r.data),

  // Overview Page
  getKPIs: () => client.get('/overview/kpis').then(r => r.data),
  getSegmentDistribution: () => client.get('/overview/segment-distribution').then(r => r.data),
  getRevenueByCategory: () => client.get('/overview/revenue-by-category').then(r => r.data),
  getMonthlyTrends: () => client.get('/overview/monthly-trends').then(r => r.data),

  // Analytics Page
  getChannelAttribution: () => client.get('/analytics/channel-attribution').then(r => r.data),
  getSentimentAnalysis: () => client.get('/analytics/sentiment-analysis').then(r => r.data),
  getRFMDistributions: () => client.get('/analytics/rfm-distributions').then(r => r.data),

  // Segmentation Page
  getSegmentationEvaluation: () => client.get('/segmentation/evaluation').then(r => r.data),
  getPCAScatter: (limit = 1200) => client.get(`/segmentation/pca-scatter?limit=${limit}`).then(r => r.data),

  // Customer Details Page
  getCustomers: (params = {}) => client.get('/customers', { params }).then(r => r.data.data || r.data),
  getCustomerDetail: (id) => client.get(`/customers/${id}`).then(r => r.data.data || r.data),

  // Recommendations Page
  getRecommendations: (customerId) => client.get(`/recommendations/${customerId}`).then(r => {
    const payload = r.data.data || r.data;
    return {
      ...payload,
      recommendations: payload.top_recommendations || payload.recommendations || []
    };
  }),
  getAssociationRules: (limit = 30) => client.get(`/recommendations/rules?limit=${limit}`).then(r => r.data.data || r.data),
  getRecommendationEvaluation: () => client.get('/recommendations/evaluation').then(r => r.data.data || r.data),

  // Data Pipeline Page
  getPipelineSummary: () => client.get('/pipeline/summary').then(r => r.data.data || r.data)
};
