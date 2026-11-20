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
  getDataComposition: () => client.get('/overview/data-composition').then(r => r.data),

  // Analytics Page
  getChannelAttribution: () => client.get('/analytics/channel-attribution').then(r => r.data),
  getSentimentAnalysis: () => client.get('/analytics/sentiment-analysis').then(r => r.data),
  getRFMDistributions: () => client.get('/analytics/rfm-distributions').then(r => r.data),

  // Segmentation Page
  getSegmentationEvaluation: () => client.get('/segmentation/evaluation').then(r => r.data),
  getPCAScatter: (limit) => client.get(limit ? `/segmentation/pca-scatter?limit=${limit}` : "/segmentation/pca-scatter").then(r => r.data),

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
  getAssociationRules: (limit = 30) => client.get(`/recommendations/rules?limit=${limit}`).then(r => r.data),
  getRecommendationMetadata: () => client.get('/recommendations/metadata').then(r => r.data.data || r.data),
  getRecommendationEvaluation: () => client.get('/recommendations/evaluation').then(r => r.data.data || r.data),

  // Data Pipeline Page
  getPipelineSummary: () => client.get('/pipeline/summary').then(r => r.data.data || r.data),

  // Supervised Churn & Retention Analytics
  getChurnSummary: () => client.get('/churn/summary').then(r => r.data.data || r.data),
  getChurnCustomers: (params = {}) => client.get('/churn/customers', { params }).then(r => r.data.data || r.data),
  getCustomerChurnDetail: (id) => client.get(`/churn/customer/${id}`).then(r => r.data.data || r.data),

  // Student Dataset Ingestion & HDFS Staging (Stage B)
  uploadBatch: (formData) => client.post('/ingestion/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data),
  validateBatch: (batchId, options = {}) => client.post(`/ingestion/validate/${batchId}`, options).then(r => r.data),
  commitBatchToHDFS: (batchId) => client.post(`/ingestion/commit/${batchId}`).then(r => r.data),
  retryHDFSIngestion: (batchId) => client.post(`/ingestion/retry-hdfs/${batchId}`).then(r => r.data),
  recoverBatch: (batchId) => client.post(`/ingestion/recover/${batchId}`).then(r => r.data),
  getBatchStatus: (batchId) => client.get(`/ingestion/status/${batchId}`).then(r => r.data),
  getBatchHistory: () => client.get('/ingestion/history').then(r => r.data),

  // PySpark Batch Processing & ML Retraining (Stage C)
  runBatchProcessing: (batchId, options = {}) => client.post(`/ingestion/process/${batchId}`, options).then(r => r.data),
  getProcessingStatus: (versionId) => client.get(`/ingestion/process/status/${versionId}`).then(r => r.data),
  retrainModels: (versionId) => client.post(`/ingestion/train/${versionId}`).then(r => r.data),
  getTrainingEvaluation: (versionId) => client.get(`/ingestion/evaluation/${versionId}`).then(r => r.data),

  // Versioned Preview, Promotion & Rollback (Stage D)
  evaluateAndApply: (batchId) => client.post(`/ingestion/evaluate-and-apply/${batchId}`).then(r => r.data),
  getVersions: () => client.get('/ingestion/versions').then(r => r.data),
  getPreviewOverview: (versionId) => client.get(`/ingestion/preview/${versionId}/overview`).then(r => r.data),
  getPreviewSegmentation: (versionId) => client.get(`/ingestion/preview/${versionId}/segmentation`).then(r => r.data),
  getPreviewRecommendations: (versionId) => client.get(`/ingestion/preview/${versionId}/recommendations`).then(r => r.data),
  getPreviewChurn: (versionId) => client.get(`/ingestion/preview/${versionId}/churn`).then(r => r.data),
  promoteVersion: (versionId) => client.post(`/ingestion/promote/${versionId}`).then(r => r.data),
  rollbackVersion: () => client.post('/ingestion/rollback').then(r => r.data),

  // Multi-Format Ingestion, Field Mapping & Data Export
  uploadMultiFormat: (formData) => client.post('/ingestion/upload-multi', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data),
  updateFieldMapping: (batchId, mappingData) => client.post(`/ingestion/mapping/${batchId}`, mappingData).then(r => r.data),
  generateSyntheticBatch: (customerCount = 100) => client.post('/ingestion/generate-synthetic-batch', { customer_count: customerCount }).then(r => r.data),
  getTemplates: () => client.get('/ingestion/templates').then(r => r.data),
  downloadTemplateUrl: (sourceType) => `/api/ingestion/templates/${sourceType}/download`,
  exportRawUrl: (batchId, fileKey) => `/api/ingestion/export/raw/${batchId}/${fileKey}`,
  exportProcessedUrl: (versionId, datasetName, format = 'csv') => `/api/ingestion/export/processed/${versionId}/${datasetName}?format=${format}`,
  exportAnalyticsUrl: (versionId, reportName) => `/api/ingestion/export/analytics/${versionId}/${reportName}`,

  // Dual Dataset Processing Modes (Cumulative vs New Batch Only)
  getDatasetMode: () => client.get('/dataset-mode').then(r => r.data),
  setDatasetMode: (mode, batchId = null) => client.post('/dataset-mode', { mode, batch_id: batchId }).then(r => r.data),
  processBatchOnly: (batchId) => client.post(`/ingestion/process-batch-only/${batchId}`).then(r => r.data)
};
