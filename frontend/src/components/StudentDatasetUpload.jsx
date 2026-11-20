import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import {
  UploadCloud,
  FileSpreadsheet,
  Activity,
  MessageSquare,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Trash2,
  RefreshCw,
  HardDrive,
  Cpu,
  Boxes,
  Sparkles,
  BarChart3,
  Layers,
  ArrowRight,
  RotateCcw,
  Eye,
  Check,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
  Info,
  Download,
  FileCode,
  Table,
  Settings2,
  Zap
} from 'lucide-react';

const REQUIRED_FILES = [
  {
    key: 'transactions',
    label: 'Transactions Dataset',
    expectedFile: 'transactions.csv',
    icon: FileSpreadsheet,
    desc: 'Orders, products, unit prices, quantities, payment methods & statuses',
    accentColor: '#5E8FD5'
  },
  {
    key: 'web_activity',
    label: 'Web Activity Clickstream',
    expectedFile: 'web_activity.csv',
    icon: Activity,
    desc: 'Session durations, page URLs, action types, device types & sources',
    accentColor: '#70AFA6'
  },
  {
    key: 'social_media',
    label: 'Social Media Sentiment',
    expectedFile: 'social_media.csv',
    icon: MessageSquare,
    desc: 'Customer sentiment scores, platform interactions, feedback & categories',
    accentColor: '#9C8CBF'
  }
];

const CANONICAL_TARGET_FIELDS = {
  transactions: [
    'customer_id',
    'transaction_id',
    'transaction_date',
    'product_id',
    'product_category',
    'product_name',
    'quantity',
    'unit_price',
    'discount_percent',
    'total_amount',
    'payment_method',
    'order_status'
  ],
  web_activity: [
    'customer_id',
    'activity_id',
    'session_id',
    'timestamp',
    'page_url',
    'action_type',
    'product_id',
    'duration_seconds',
    'device_type',
    'traffic_source'
  ],
  social_media: [
    'customer_id',
    'interaction_id',
    'timestamp',
    'platform',
    'interaction_type',
    'sentiment',
    'sentiment_score',
    'engagement_score',
    'feedback_content',
    'associated_category'
  ],
  other: []
};

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function StudentDatasetUpload() {
  const [ingestionMode, setIngestionMode] = useState('multi'); // 'multi' or 'classic'

  // Multi-Format Ingestion State
  const [multiFiles, setMultiFiles] = useState([]);
  const multiFileInputRef = useRef(null);

  // Classic 3-CSV State
  const [classicFiles, setClassicFiles] = useState({
    transactions: null,
    web_activity: null,
    social_media: null
  });
  const fileInputRefs = {
    transactions: useRef(null),
    web_activity: useRef(null),
    social_media: useRef(null)
  };

  // Pipeline Execution State
  const [activeBatch, setActiveBatch] = useState(null);
  const [activeVersionId, setActiveVersionId] = useState(null);
  const [processingReport, setProcessingReport] = useState(null);
  const [evaluationReport, setEvaluationReport] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewTab, setPreviewTab] = useState('overview');

  // Schema Mapping Modal State
  const [selectedMappingFile, setSelectedMappingFile] = useState(null);
  const [customSource, setCustomSource] = useState('transactions');
  const [tempMapping, setTempMapping] = useState({});
  const [isSavingMapping, setIsSavingMapping] = useState(false);

  // Metadata Catalogs
  const [history, setHistory] = useState([]);
  const [versions, setVersions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Action Loading States
  const [isUploading, setIsUploading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [isPromoting, setIsPromoting] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [isEvaluatingAndApplying, setIsEvaluatingAndApplying] = useState(false);
  const [evalProgressStep, setEvalProgressStep] = useState('');
  const [autoApplyAfterUpload, setAutoApplyAfterUpload] = useState(false);
  const [isGeneratingSynthetic, setIsGeneratingSynthetic] = useState(false);

  const [uiError, setUiError] = useState(null);
  const [uiSuccess, setUiSuccess] = useState(null);

  // Dual Dataset Processing Modes ('cumulative' vs 'batch_only')
  const [datasetMode, setDatasetMode] = useState('cumulative');
  const [isProcessingBatchOnly, setIsProcessingBatchOnly] = useState(false);
  const [batchOnlyReport, setBatchOnlyReport] = useState(null);

  const loadMetadata = () => {
    setLoadingHistory(true);
    Promise.all([
      api.getBatchHistory().catch(() => ({ data: { batches: [] } })),
      api.getVersions().catch(() => ({ data: { versions: [] } })),
      api.getDatasetMode().catch(() => ({ data: { mode: 'cumulative' } }))
    ])
      .then(([bRes, vRes, mRes]) => {
        if (bRes?.data?.batches) setHistory(bRes.data.batches);
        if (vRes?.data?.versions) setVersions(vRes.data.versions);
        if (mRes?.data?.mode) setDatasetMode(mRes.data.mode);
        setLoadingHistory(false);
      })
      .catch((err) => {
        console.error('Failed to load metadata:', err);
        setLoadingHistory(false);
      });
  };

  useEffect(() => {
    loadMetadata();
    const handleModeUpdate = (e) => {
      if (e?.detail?.mode) {
        setDatasetMode(e.detail.mode);
      }
    };
    window.addEventListener('smart-dataset-mode-changed', handleModeUpdate);
    return () => window.removeEventListener('smart-dataset-mode-changed', handleModeUpdate);
  }, []);

  const handleDatasetModeChange = async (targetMode) => {
    setDatasetMode(targetMode);
    try {
      const res = await api.setDatasetMode(targetMode, activeBatch?.batch_id);
      if (res?.data) {
        window.dispatchEvent(new CustomEvent('smart-dataset-mode-changed', { detail: res.data }));
      }
      loadMetadata();
    } catch (err) {
      console.error('Mode change error:', err);
    }
  };

  const handleProcessBatchOnly = async () => {
    const bid = activeBatch?.batch_id;
    if (!bid) return;
    setIsProcessingBatchOnly(true);
    setUiError(null);
    try {
      const res = await api.processBatchOnly(bid);
      if (res?.data) {
        setBatchOnlyReport(res.data.pipeline_report);
        setActiveVersionId(res.data.version_id);
        setDatasetMode('batch_only');
        const dur = res.data.pipeline_report?.duration_seconds || 0;
        const custs = res.data.pipeline_report?.data_composition?.overall?.total_customers || 0;
        setUiSuccess(`New Batch Only processed successfully in ${dur}s! Mode set to NEW BATCH ONLY (${custs} customers). All 7 modules updated.`);
        window.dispatchEvent(new CustomEvent('smart-dataset-mode-changed', { detail: res.data.mode_context }));
        loadMetadata();
      }
    } catch (err) {
      setUiError('New Batch Only processing failed: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsProcessingBatchOnly(false);
    }
  };

  // Multi-Format File Management
  const handleAddMultiFiles = (newFiles) => {
    if (!newFiles || newFiles.length === 0) return;
    const allowed = ['.csv', '.tsv', '.json', '.jsonl', '.txt', '.log', '.xlsx'];
    const valid = [];
    let rejectedCount = 0;

    Array.from(newFiles).forEach((f) => {
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      if (allowed.includes(ext)) {
        valid.push(f);
      } else {
        rejectedCount++;
      }
    });

    if (rejectedCount > 0) {
      setUiError(`Ignored ${rejectedCount} file(s) with unsupported extensions. Supported: ${allowed.join(', ')}`);
    } else {
      setUiError(null);
    }

    setMultiFiles((prev) => [...prev, ...valid]);
  };

  const handleRemoveMultiFile = (index) => {
    setMultiFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Classic File Management
  const handleClassicFileChange = (key, selectedFile) => {
    if (!selectedFile) return;
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setUiError(`Invalid format for ${key}. Please select a .csv file.`);
      return;
    }
    setUiError(null);
    setClassicFiles((prev) => ({ ...prev, [key]: selectedFile }));
  };

  const handleClassicFileRemove = (key) => {
    setClassicFiles((prev) => ({ ...prev, [key]: null }));
    if (fileInputRefs[key]?.current) {
      fileInputRefs[key].current.value = '';
    }
  };

  // Generate Realistic Synthetic Batch with Next Available IDs (CUST_1201+)
  const handleGenerateSyntheticBatch = async (count = 100) => {
    setIsGeneratingSynthetic(true);
    setUiError(null);
    try {
      const res = await api.generateSyntheticBatch(count);
      if (res?.data) {
        setActiveBatch(res.data);
        setUiSuccess(res.message || `Generated and staged ${count} new unique customer records (CUST_1201+) with zero ID collisions! Click 'Evaluate Old + New' to apply.`);
        loadMetadata();
      }
    } catch (err) {
      setUiError('Synthetic data generation failed: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsGeneratingSynthetic(false);
    }
  };

  // 1-Click Master Integration: Evaluate Old + New and Update Main Dashboard
  const handleEvaluateAndApply = async (targetBatchId) => {
    const bid = targetBatchId || activeBatch?.batch_id;
    if (!bid) return;
    setUiError(null);
    setIsEvaluatingAndApplying(true);
    setEvalProgressStep('Staging batch and merging historical baseline with new incoming records via PySpark...');

    try {
      const response = await api.evaluateAndApply(bid);
      if (response?.data) {
        setProcessingReport(response.data.processing);
        setEvaluationReport(response.data.evaluation);
        setActiveVersionId(response.data.version_id);
        const comp = response.data.data_composition || {};
        const custCount = comp?.overall?.total_customers?.toLocaleString() || 'Combined';
        const revTotal = comp?.overall?.total_revenue ? `$${comp.overall.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '';
        setUiSuccess(
          `Success! New data evaluated with historical baseline. Main Dashboard and all modules updated with combined data (${custCount} total customers, ${revTotal} total revenue)!`
        );
      }
      loadMetadata();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Evaluation and dashboard update failed.';
      setUiError(msg);
    } finally {
      setIsEvaluatingAndApplying(false);
      setEvalProgressStep('');
    }
  };

  // Upload Multi-Format Batch
  const handleUploadMultiBatch = async (autoApply = false) => {
    if (multiFiles.length === 0) {
      setUiError('Please select at least one file to upload.');
      return;
    }
    setUiError(null);
    setUiSuccess(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      multiFiles.forEach((f) => formData.append('files', f));

      const response = await api.uploadMultiFormat(formData);
      if (response?.data) {
        setActiveBatch(response.data);
        setActiveVersionId(`v_${response.data.batch_id}`);
        setIsEvaluatingAndApplying(false);
        setUiSuccess(`Batch ${response.data.batch_id} uploaded and verified in HDFS. Select your processing mode below to proceed:`);
        setMultiFiles([]);
        loadMetadata();
      }
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Upload failed.';
      setUiError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  // Upload Classic 3-CSV Batch
  const handleUploadClassicBatch = async (autoApply = false) => {
    const selectedCount = Object.values(classicFiles).filter(Boolean).length;
    if (selectedCount !== 3) {
      setUiError('All three CSV files must be selected in Classic mode.');
      return;
    }
    setUiError(null);
    setUiSuccess(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('transactions', classicFiles.transactions);
      formData.append('web_activity', classicFiles.web_activity);
      formData.append('social_media', classicFiles.social_media);
      formData.append('auto_validate', 'true');

      const response = await api.uploadBatch(formData);
      if (response?.data) {
        setActiveBatch(response.data);
        setActiveVersionId(`v_${response.data.batch_id}`);
        setIsEvaluatingAndApplying(false);
        setUiSuccess(`Batch ${response.data.batch_id} validated and verified in HDFS. Select your processing mode below to proceed:`);
        loadMetadata();
      }
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Validation failed.';
      setUiError(msg);
      if (err.response?.data?.data) setActiveBatch(err.response.data.data);
    } finally {
      setIsUploading(false);
    }
  };

  // Commit to HDFS
  const handleCommitToHDFS = async () => {
    if (!activeBatch?.batch_id) return;
    setUiError(null);
    setIsCommitting(true);

    try {
      const response = await api.commitBatchToHDFS(activeBatch.batch_id);
      if (response?.data) {
        setActiveBatch(response.data);
        setUiSuccess(`Raw files successfully stored and verified in Hadoop HDFS!`);
      }
      loadMetadata();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'HDFS ingestion halted.';
      setUiError(msg);
      if (err.response?.data?.data) setActiveBatch(err.response.data.data);
    } finally {
      setIsCommitting(false);
    }
  };

  // Retry HDFS Ingestion & Batch Recovery (Phase G.3)
  const handleRetryHDFS = async () => {
    if (!activeBatch?.batch_id) return;
    setUiError(null);
    setIsCommitting(true);

    try {
      const response = await api.retryHDFSIngestion(activeBatch.batch_id);
      if (response?.data) {
        setActiveBatch(response.data);
        setUiSuccess(`Batch ${activeBatch.batch_id} successfully verified and recovered in Hadoop HDFS!`);
      }
      loadMetadata();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'HDFS ingestion recovery failed.';
      setUiError(msg);
      if (err.response?.data?.data) setActiveBatch(err.response.data.data);
    } finally {
      setIsCommitting(false);
    }
  };

  // Run PySpark Batch
  const handleRunPySpark = async () => {
    if (!activeBatch?.batch_id) return;
    setUiError(null);
    setIsProcessing(true);

    try {
      const response = await api.runBatchProcessing(activeBatch.batch_id, { force_local_input: false });
      if (response?.data) {
        setProcessingReport(response.data);
        setActiveVersionId(response.data.version_id);
        setUiSuccess(`PySpark batch processing completed in ${response.data.duration_seconds}s! Canonical 23-column customer feature matrix generated.`);
      }
      loadMetadata();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'PySpark processing failed.';
      setUiError(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  // Retrain Models
  const handleRetrainModels = async () => {
    const vid = activeVersionId || `v_${activeBatch?.batch_id}`;
    if (!vid) return;
    setUiError(null);
    setIsTraining(true);

    try {
      const response = await api.retrainModels(vid);
      if (response?.data) {
        setEvaluationReport(response.data);
        setUiSuccess(`Machine learning retraining complete! K-Means, Recommender, and Churn models evaluated.`);
      }
      loadMetadata();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Model retraining failed.';
      setUiError(msg);
    } finally {
      setIsTraining(false);
    }
  };

  // Preview Analytics
  const handleOpenPreview = async () => {
    const vid = activeVersionId || `v_${activeBatch?.batch_id}`;
    if (!vid) return;

    try {
      const [ov, seg, rec, ch] = await Promise.all([
        api.getPreviewOverview(vid).catch(() => ({ data: {} })),
        api.getPreviewSegmentation(vid).catch(() => ({ data: {} })),
        api.getPreviewRecommendations(vid).catch(() => ({ data: {} })),
        api.getPreviewChurn(vid).catch(() => ({ data: {} }))
      ]);

      setPreviewData({
        version_id: vid,
        overview: ov?.data || {},
        segmentation: seg?.data || {},
        recommendations: rec?.data || {},
        churn: ch?.data || {}
      });
      setShowPreviewModal(true);
    } catch (err) {
      setUiError('Failed to load batch preview: ' + err.message);
    }
  };

  // Promote Version
  const handlePromote = async (targetVid) => {
    let vid = (typeof targetVid === 'string' && targetVid.trim()) ? targetVid.trim() : null;
    if (!vid) {
      if (typeof activeVersionId === 'string' && activeVersionId.trim()) {
        vid = activeVersionId.trim();
      } else if (activeVersionId && typeof activeVersionId === 'object' && activeVersionId.version_id) {
        vid = String(activeVersionId.version_id).trim();
      } else if (activeBatch?.batch_id) {
        vid = `v_${activeBatch.batch_id}`;
      }
    }

    if (!vid || typeof vid !== 'string' || vid === '[object Object]') {
      setUiError('No valid version selected to promote.');
      return;
    }

    if (vid.startsWith('v_batch_only_')) {
      setUiError(`Version '${vid}' is an isolated New Batch Only demonstration and cannot be promoted to cumulative production. Switch to Cumulative Analysis mode to promote integrated candidate versions.`);
      return;
    }

    setIsPromoting(true);
    setUiError(null);

    try {
      const res = await api.promoteVersion(vid);
      setUiSuccess(res.message || `Version '${vid}' successfully promoted to live production! All dashboards and charts updated with combined old + new data.`);
      loadMetadata();
    } catch (err) {
      setUiError('Promotion failed: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsPromoting(false);
    }
  };

  // Rollback to Baseline
  const handleRollback = async () => {
    if (!window.confirm('Restore the original Academic Baseline? This will restore baseline processed datasets and ML models.')) {
      return;
    }

    setIsRollingBack(true);
    setUiError(null);

    try {
      const res = await api.rollbackVersion();
      setUiSuccess(res.message || 'Successfully rolled back to Academic Baseline.');
      loadMetadata();
    } catch (err) {
      setUiError('Rollback failed: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsRollingBack(false);
    }
  };

  // Field Mapping Drawer Open
  const handleOpenMappingDrawer = (fileId, fileInfo) => {
    setSelectedMappingFile({ fileId, ...fileInfo });
    setCustomSource(fileInfo.source_type || 'transactions');
    setTempMapping(fileInfo.active_mapping || fileInfo.discovered_schema?.suggested_mapping || {});
  };

  // Field Mapping Save
  const handleSaveFieldMapping = async () => {
    if (!activeBatch?.batch_id || !selectedMappingFile?.fileId) return;
    setIsSavingMapping(true);

    try {
      const res = await api.updateFieldMapping(activeBatch.batch_id, {
        file_id: selectedMappingFile.fileId,
        custom_source: customSource,
        custom_mapping: tempMapping
      });
      if (res?.data) {
        setActiveBatch(res.data);
        setUiSuccess(`Field mapping saved for '${selectedMappingFile.original_filename}'.`);
        setSelectedMappingFile(null);
      }
    } catch (err) {
      setUiError('Failed to update field mapping: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsSavingMapping(false);
    }
  };

  const stagedFilesList = activeBatch?.staged_files ? Object.entries(activeBatch.staged_files) : [];

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Boxes size={20} color="var(--accent-blue)" />
            <h2 style={{ fontSize: '1.05rem', fontWeight: '600', color: 'var(--text-primary)', margin: 0 }}>
              Multi-Format Big Data Ingestion & Analytics Pipeline
            </h2>
            <span className="pill-badge" style={{ backgroundColor: 'var(--surface-elevated)', color: 'var(--accent-blue)', fontSize: '0.725rem' }}>
              Multi-Format Engine
            </span>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.35rem', marginBottom: 0 }}>
            Upload raw CSV, JSON, JSONL, TXT, or LOG files. Preserves original bytes in Hadoop HDFS, performs schema discovery, and builds the canonical 23-column customer feature matrix via PySpark.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <button
            type="button"
            onClick={handleRollback}
            disabled={isRollingBack}
            style={{
              padding: '0.45rem 0.85rem',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              color: 'var(--text-secondary)',
              fontSize: '0.775rem',
              cursor: isRollingBack ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
            title="Restore Academic Baseline"
          >
            <RotateCcw size={13} className={isRollingBack ? 'spin' : ''} />
            Rollback to Baseline
          </button>
        </div>
      </div>

      {/* Mode Switcher */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
        <button
          type="button"
          onClick={() => setIngestionMode('multi')}
          style={{
            padding: '0.45rem 0.95rem',
            borderRadius: '8px',
            border: ingestionMode === 'multi' ? '1px solid var(--accent-blue)' : '1px solid var(--border-subtle)',
            backgroundColor: ingestionMode === 'multi' ? 'rgba(94, 143, 213, 0.12)' : 'var(--surface-secondary)',
            color: ingestionMode === 'multi' ? '#FFF' : 'var(--text-secondary)',
            fontSize: '0.8rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Multi-Format Ingestion (CSV / JSON / JSONL / TXT / LOG)
        </button>
        <button
          type="button"
          onClick={() => setIngestionMode('classic')}
          style={{
            padding: '0.45rem 0.95rem',
            borderRadius: '8px',
            border: ingestionMode === 'classic' ? '1px solid var(--accent-blue)' : '1px solid var(--border-subtle)',
            backgroundColor: ingestionMode === 'classic' ? 'rgba(94, 143, 213, 0.12)' : 'var(--surface-secondary)',
            color: ingestionMode === 'classic' ? '#FFF' : 'var(--text-secondary)',
            fontSize: '0.8rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Classic 3-CSV Fixed Batch
        </button>
      </div>

      {/* Notifications */}
      {isEvaluatingAndApplying && (
        <div style={{ padding: '1rem 1.25rem', backgroundColor: 'rgba(112, 71, 235, 0.16)', border: '1px solid rgba(112, 71, 235, 0.45)', borderRadius: '12px', color: '#C4B5FD', marginBottom: '1.25rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.75rem', boxShadow: '0 4px 20px rgba(112, 71, 235, 0.25)' }}>
          <RefreshCw size={20} className="spin" color="#C4B5FD" />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: '700', color: '#FFF', fontSize: '0.9rem' }}>Evaluating New Data with Historical Baseline...</div>
            <div style={{ fontSize: '0.775rem', color: '#C4B5FD', marginTop: '3px' }}>
              {evalProgressStep || 'Merging Historical Baseline (1,200) with incoming batch in PySpark, retraining ML models, and pushing combined analytics to live dashboard...'}
            </div>
          </div>
        </div>
      )}

      {uiError && (
        <div style={{ padding: '0.85rem 1rem', backgroundColor: 'rgba(199, 127, 131, 0.1)', border: '1px solid rgba(199, 127, 131, 0.25)', borderRadius: '10px', color: '#F5F5F7', marginBottom: '1.25rem', fontSize: '0.825rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={16} color="#C77F83" />
          <span>{uiError}</span>
        </div>
      )}

      {uiSuccess && (
        <div style={{ padding: '0.85rem 1.15rem', backgroundColor: 'rgba(121, 168, 139, 0.12)', border: '1px solid rgba(121, 168, 139, 0.35)', borderRadius: '10px', color: '#79A88B', marginBottom: '1.25rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.6rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
            <CheckCircle size={17} color="#79A88B" />
            <span style={{ fontWeight: '500' }}>{uiSuccess}</span>
          </div>
          <Link
            to="/"
            style={{
              padding: '0.35rem 0.85rem',
              backgroundColor: '#79A88B',
              color: '#000',
              borderRadius: '6px',
              fontWeight: '700',
              textDecoration: 'none',
              fontSize: '0.775rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)'
            }}
          >
            View Main Dashboard <ArrowRight size={13} />
          </Link>
        </div>
      )}

      {/* 5-Step Progress Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {[
          { num: '1', title: 'Upload & Discovery', desc: 'Raw Format Staging', done: !!activeBatch, active: isUploading, failed: false },
          { num: '2', title: 'HDFS Raw Storage', desc: 'Preserve Untouched Bytes', done: activeBatch?.status === 'INGESTED', active: isCommitting, failed: activeBatch?.status === 'INGESTION_FAILED' },
          { num: '3', title: 'PySpark Processing', desc: 'Clean & 23-Feature Matrix', done: !!processingReport, active: isProcessing, failed: false },
          { num: '4', title: 'Model Retraining', desc: 'K-Means, CF, Churn RF', done: !!evaluationReport, active: isTraining, failed: false },
          { num: '5', title: 'Dashboard Preview', desc: 'Isolated Analytics', done: !!previewData, active: false, failed: false }
        ].map((step, idx) => (
          <div
            key={idx}
            className="glass-sub-card"
            style={{
              padding: '0.75rem',
              border: step.failed ? '1px solid rgba(239, 68, 68, 0.5)' : step.done ? '1px solid rgba(121, 168, 139, 0.4)' : step.active ? '1px solid rgba(94, 143, 213, 0.5)' : '1px solid var(--border-subtle)',
              backgroundColor: step.failed ? 'rgba(239, 68, 68, 0.08)' : step.done ? 'rgba(121, 168, 139, 0.05)' : step.active ? 'rgba(94, 143, 213, 0.05)' : 'var(--surface-secondary)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: step.failed ? '#EF4444' : step.done ? 'var(--accent-green)' : step.active ? 'var(--accent-blue)' : 'var(--text-muted)' }}>
                {step.failed ? '!' : step.done ? '✓' : step.num}.
              </span>
              <span style={{ fontSize: '0.8rem', fontWeight: '600', color: step.failed ? '#FCA5A5' : step.done ? 'var(--text-primary)' : step.active ? 'var(--accent-blue)' : 'var(--text-secondary)' }}>
                {step.title}
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: step.failed ? '#EF4444' : 'var(--text-muted)' }}>
              {step.failed ? 'Ingestion Failed' : step.desc}
            </div>
          </div>
        ))}
      </div>

      {/* INGESTION_FAILED Safe Recovery Banner */}
      {activeBatch?.status === 'INGESTION_FAILED' && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', flex: '1 1 300px' }}>
            <AlertTriangle size={20} color="#EF4444" style={{ marginTop: '0.15rem', flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: '0.9rem', fontWeight: '700', color: '#FCA5A5', marginBottom: '0.25rem' }}>
                HDFS Ingestion Halted for Batch <code style={{ color: '#F87171' }}>{activeBatch.batch_id}</code>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                {activeBatch.message || 'HDFS cluster was unavailable during ingestion. Original raw files are safely preserved locally.'}
              </div>
              {activeBatch.retry_history && activeBatch.retry_history.length > 0 && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                  Retry Attempts Logged: {activeBatch.retry_history.length}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              type="button"
              onClick={handleRetryHDFS}
              disabled={isCommitting}
              style={{
                padding: '0.55rem 1.15rem',
                backgroundColor: isCommitting ? 'var(--surface-elevated)' : '#DC2626',
                color: '#FFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.825rem',
                fontWeight: '600',
                cursor: isCommitting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                boxShadow: '0 2px 10px rgba(220, 38, 38, 0.4)'
              }}
            >
              {isCommitting ? <RefreshCw size={14} className="spin" /> : <RotateCcw size={14} />}
              {isCommitting ? 'Verifying & Retrying HDFS Ingestion...' : 'Retry HDFS Ingestion'}
            </button>
          </div>
        </div>
      )}

      {/* Ingestion Area */}
      {ingestionMode === 'multi' ? (
        /* Multi-Format Dropzone & Queue */
        <div style={{ marginBottom: '1.5rem' }}>
          <div
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (e.dataTransfer.files) handleAddMultiFiles(e.dataTransfer.files);
            }}
            onClick={() => multiFileInputRef.current?.click()}
            style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px dashed var(--border-subtle)',
              borderRadius: '12px',
              padding: '1.75rem 1.5rem',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'border-color 0.15s ease'
            }}
          >
            <input
              type="file"
              multiple
              ref={multiFileInputRef}
              style={{ display: 'none' }}
              onChange={(e) => handleAddMultiFiles(e.target.files)}
            />
            <UploadCloud size={28} color="var(--accent-blue)" style={{ margin: '0 auto 0.6rem auto' }} />
            <div style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
              Drag and drop raw multi-format datasets here, or click to browse
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Supported raw extensions: <code>.csv</code>, <code>.tsv</code>, <code>.json</code>, <code>.jsonl</code>, <code>.txt</code>, <code>.log</code>, <code>.xlsx</code> (50MB max per file)
            </div>
          </div>

          {/* Staging Queue List */}
          {multiFiles.length > 0 && (
            <div style={{ marginTop: '1rem', backgroundColor: 'var(--surface-secondary)', borderRadius: '10px', padding: '0.85rem 1rem', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', flexWrap: 'wrap', gap: '0.6rem' }}>
                <span style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                  Selected Queue ({multiFiles.length} files)
                </span>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => handleUploadMultiBatch(false)}
                    disabled={isUploading || isEvaluatingAndApplying}
                    style={{
                      padding: '0.55rem 1.3rem',
                      background: 'linear-gradient(135deg, #7047EB 0%, #3B82F6 100%)',
                      color: '#FFF',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '0.825rem',
                      fontWeight: '700',
                      cursor: isUploading || isEvaluatingAndApplying ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      boxShadow: '0 2px 10px rgba(112, 71, 235, 0.4)'
                    }}
                  >
                    {isUploading ? <RefreshCw size={13} className="spin" /> : <UploadCloud size={14} />}
                    Upload & Stage Batch Files
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {multiFiles.map((f, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--surface-elevated)', padding: '0.45rem 0.75rem', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span className="pill-badge" style={{ fontSize: '0.7rem', backgroundColor: 'rgba(94, 143, 213, 0.15)', color: '#5E8FD5' }}>
                        {f.name.split('.').pop()?.toUpperCase()}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>{f.name}</span>
                      <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>({formatBytes(f.size)})</span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleRemoveMultiFile(i); }}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Classic 3-CSV Fixed Batch Grid */
        <div>
          <div className="grid-3" style={{ marginBottom: '1.25rem' }}>
            {REQUIRED_FILES.map((rf) => {
            const selected = classicFiles[rf.key];
            const Icon = rf.icon;

            return (
              <div
                key={rf.key}
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleClassicFileChange(rf.key, e.dataTransfer.files[0]);
                  }
                }}
                style={{
                  backgroundColor: 'var(--surface-secondary)',
                  border: selected ? `1px solid ${rf.accentColor}55` : '1px dashed var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '1.1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minHeight: '160px'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                      <Icon size={16} color={rf.accentColor} />
                      <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>{rf.label}</span>
                    </div>
                    {selected && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.725rem', color: 'var(--accent-green)' }}>
                        <Check size={14} /> Ready
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: '1.4' }}>
                    {rf.desc}
                  </div>
                </div>

                <div>
                  <input
                    type="file"
                    accept=".csv"
                    ref={fileInputRefs[rf.key]}
                    style={{ display: 'none' }}
                    onChange={(e) => handleClassicFileChange(rf.key, e.target.files[0])}
                  />

                  {selected ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'var(--surface-elevated)', padding: '0.5rem 0.65rem', borderRadius: '8px' }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '0.5rem' }}>
                        <div style={{ fontSize: '0.775rem', fontWeight: '500', color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                          {selected.name}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {formatBytes(selected.size)}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleClassicFileRemove(rf.key)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '4px' }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => fileInputRefs[rf.key].current?.click()}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        backgroundColor: 'var(--surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '8px',
                        color: 'var(--text-primary)',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.4rem'
                      }}
                    >
                      <UploadCloud size={14} />
                      Select {rf.expectedFile}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Quick Action Bar for Classic 3-CSV */}
        {Object.values(classicFiles).filter(Boolean).length === 3 && (
          <div style={{ marginTop: '-0.75rem', marginBottom: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.6rem' }}>
            <button
              type="button"
              onClick={() => handleUploadClassicBatch(false)}
              disabled={isUploading || isEvaluatingAndApplying}
              style={{
                padding: '0.55rem 1.3rem',
                background: 'linear-gradient(135deg, #7047EB 0%, #3B82F6 100%)',
                color: '#FFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.825rem',
                fontWeight: '700',
                cursor: isUploading || isEvaluatingAndApplying ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                boxShadow: '0 2px 10px rgba(112, 71, 235, 0.4)'
              }}
            >
              {isUploading ? <RefreshCw size={14} className="spin" /> : <UploadCloud size={14} />}
              Upload & Stage 3-CSV Batch
            </button>
          </div>
        )}
      </div>
    )}

      {/* Dual Dataset Processing Mode Selector & Execution Card */}
      {activeBatch && (
        <div style={{
          backgroundColor: 'var(--surface-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '1.25rem 1.5rem',
          marginBottom: '1.5rem',
          boxShadow: 'none',
          transition: 'border-color 0.3s ease'
        }}>
          {/* Header & Mode Switcher Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.15rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: '700', color: '#FFF', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span>Dataset Processing Mode</span>
                <span style={{
                  fontSize: '0.72rem',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '9999px',
                  backgroundColor: 'var(--surface-elevated, #1A1A1E)',
                  color: 'var(--text-secondary, #A1A1AA)',
                  border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.1))',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.04em'
                }}>
                  {datasetMode === 'batch_only' ? `NEW BATCH ONLY — ${activeBatch.batch_id}` : 'CUMULATIVE ANALYSIS (BASELINE + BATCHES)'}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>
                Select whether to process this batch integrated into cumulative production or as an isolated lightweight demonstration.
              </p>
            </div>

            {/* Mode Selector Radio Pills */}
            <div style={{ display: 'flex', gap: '0.4rem', backgroundColor: 'rgba(0,0,0,0.3)', padding: '0.3rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                onClick={() => handleDatasetModeChange('cumulative')}
                style={{
                  padding: '0.45rem 0.95rem',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backgroundColor: datasetMode === 'cumulative' ? '#7047EB' : 'transparent',
                  color: datasetMode === 'cumulative' ? '#FFF' : 'var(--text-secondary)',
                  boxShadow: datasetMode === 'cumulative' ? '0 2px 8px rgba(112, 71, 235, 0.3)' : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                Cumulative Analysis
              </button>
              <button
                type="button"
                onClick={() => handleDatasetModeChange('batch_only')}
                style={{
                  padding: '0.45rem 0.95rem',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backgroundColor: datasetMode === 'batch_only' ? '#5B5BD6' : 'transparent',
                  color: datasetMode === 'batch_only' ? '#FFF' : 'var(--text-secondary)',
                  boxShadow: datasetMode === 'batch_only' ? '0 2px 8px rgba(91, 91, 214, 0.3)' : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                New Batch Only (Fast Demo)
              </button>
            </div>
          </div>

          {/* MODE 1: Cumulative Analysis Panel */}
          {datasetMode === 'cumulative' ? (
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              padding: '1rem',
              backgroundColor: 'rgba(112, 71, 235, 0.06)',
              borderRadius: '10px',
              border: '1px solid rgba(112, 71, 235, 0.25)'
            }}>
              <div style={{ flex: '1 1 340px' }}>
                <div style={{ fontWeight: '600', color: '#C4B5FD', fontSize: '0.86rem', marginBottom: '0.25rem' }}>
                  Cumulative Integration (1,200 Baseline + Accepted Batches + Incoming Batch)
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                  {activeBatch?.status === 'INGESTION_FAILED'
                    ? <>HDFS ingestion was previously halted. Original files are preserved. Click below to recover and process, or click <strong>Retry HDFS Ingestion</strong> above.</>
                    : <>Full enterprise lineage: cross-batch primary-key deduplication, cumulative 23-column PySpark feature engineering, ML retraining, and candidate version generation.</>
                  }
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => handleEvaluateAndApply()}
                  disabled={isEvaluatingAndApplying}
                  style={{
                    padding: '0.65rem 1.4rem',
                    background: isEvaluatingAndApplying ? 'var(--surface-elevated)' : 'linear-gradient(135deg, #7047EB 0%, #3B82F6 100%)',
                    color: '#FFF',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: isEvaluatingAndApplying ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    boxShadow: '0 4px 14px rgba(112, 71, 235, 0.4)'
                  }}
                >
                  {isEvaluatingAndApplying && <RefreshCw size={14} className="spin" />}
                  {isEvaluatingAndApplying ? 'Processing Cumulative Pipeline...' : activeBatch?.status === 'INGESTION_FAILED' ? 'Recover & Process Cumulative Data' : 'Process Cumulative Data (Old + New)'}
                </button>

                {activeVersionId && (
                  <Link
                    to="/"
                    style={{
                      padding: '0.65rem 1.15rem',
                      backgroundColor: 'rgba(255, 255, 255, 0.06)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '8px',
                      fontSize: '0.825rem',
                      fontWeight: '500',
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem'
                    }}
                  >
                    View Main Dashboard <ArrowRight size={13} />
                  </Link>
                )}
              </div>

              {isEvaluatingAndApplying && (
                <div style={{
                  width: '100%',
                  marginTop: '0.5rem',
                  padding: '0.65rem 0.85rem',
                  backgroundColor: 'rgba(112, 71, 235, 0.08)',
                  borderRadius: '8px',
                  border: '1px solid rgba(112, 71, 235, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)'
                }}>
                  <RefreshCw size={14} className="spin" color="#A78BFA" />
                  <span>
                    <strong style={{ color: '#FFF' }}>PySpark Big Data Pipeline Active:</strong> Merging historical records in HDFS, executing deduplication, computing 23 customer features, and retraining ML models (typically takes 2–3 minutes).
                  </span>
                </div>
              )}
            </div>
          ) : (
            /* MODE 2: New Batch Only Panel */
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem',
              padding: '1rem',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '10px',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ flex: '1 1 340px' }}>
                  <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.86rem', marginBottom: '0.25rem' }}>
                    Lightweight Batch Only Processing (Fast Demo — No Historical Union)
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    Reads only the 3 newly uploaded batch datasets. Runs PySpark cleaning and feature engineering strictly on batch data. Skips baseline union and baseline model retraining. Stores output in isolated batch preview directory.
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => handleProcessBatchOnly()}
                    disabled={isProcessingBatchOnly}
                    style={{
                      padding: '0.65rem 1.4rem',
                      background: isProcessingBatchOnly ? 'var(--surface-elevated)' : 'linear-gradient(135deg, #7047EB 0%, #4F46E5 100%)',
                      color: '#FFF',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '600',
                      cursor: isProcessingBatchOnly ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.25)'
                    }}
                  >
                    {isProcessingBatchOnly && <RefreshCw size={14} className="spin" />}
                    {isProcessingBatchOnly ? 'Processing Batch Only...' : 'Process New Batch Only (Fast Demo)'}
                  </button>

                  <Link
                    to="/"
                    style={{
                      padding: '0.65rem 1.15rem',
                      backgroundColor: 'rgba(255, 255, 255, 0.06)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '8px',
                      fontSize: '0.825rem',
                      fontWeight: '500',
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem'
                    }}
                  >
                    View Batch Only Dashboard <ArrowRight size={13} />
                  </Link>
                </div>
              </div>

              {/* Execution Timing Breakdown */}
              {batchOnlyReport?.stage_timings && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: '0.65rem',
                  marginTop: '0.4rem',
                  paddingTop: '0.65rem',
                  borderTop: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Stage 1 Ingestion</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FFF', fontFamily: 'var(--font-mono)' }}>
                      {batchOnlyReport.stage_timings.stage_1_ingestion_seconds}s
                    </div>
                  </div>
                  <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Stage 2 Cleaning</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FFF', fontFamily: 'var(--font-mono)' }}>
                      {batchOnlyReport.stage_timings.stage_2_cleaning_seconds}s
                    </div>
                  </div>
                  <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Stage 3 Features (23-Col)</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FFF', fontFamily: 'var(--font-mono)' }}>
                      {batchOnlyReport.stage_timings.stage_3_feature_engineering_seconds}s
                    </div>
                  </div>
                  <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Total Execution Time</div>
                    <div style={{ fontSize: '0.88rem', fontWeight: '700', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {batchOnlyReport.stage_timings.total_pipeline_seconds}s
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Advanced Step-by-Step Controls (Collapsible) */}
      <details style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '0.75rem 1.15rem', marginBottom: '1.5rem' }}>
        <summary style={{ cursor: 'pointer', fontSize: '0.78rem', fontWeight: '500', color: 'var(--text-muted)' }}>
          Advanced Step-by-Step Controls (Optional)
        </summary>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center', marginTop: '0.85rem' }}>
          {ingestionMode === 'classic' && (
            <button
              type="button"
              onClick={() => handleUploadClassicBatch(false)}
              disabled={Object.values(classicFiles).filter(Boolean).length !== 3 || isUploading}
              style={{
                padding: '0.45rem 0.85rem',
                backgroundColor: 'var(--surface-elevated)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                fontSize: '0.75rem',
                cursor: 'pointer'
              }}
            >
              1. Validate 3-CSV
            </button>
          )}
          <button
            type="button"
            onClick={handleCommitToHDFS}
            disabled={!activeBatch || activeBatch.status === 'INGESTED' || isCommitting}
            style={{
              padding: '0.45rem 0.85rem',
              backgroundColor: 'var(--surface-elevated)',
              color: activeBatch?.status === 'INGESTION_FAILED' ? '#EF4444' : 'var(--text-primary)',
              border: activeBatch?.status === 'INGESTION_FAILED' ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid var(--border-subtle)',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            {activeBatch?.status === 'INGESTION_FAILED' ? '2. Retry HDFS Ingestion' : '2. Commit to HDFS'}
          </button>
          <button
            type="button"
            onClick={handleRunPySpark}
            disabled={!activeBatch || activeBatch.status === 'INGESTION_FAILED' || isProcessing}
            style={{
              padding: '0.45rem 0.85rem',
              backgroundColor: 'var(--surface-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            3. Run PySpark Batch
          </button>
          <button
            type="button"
            onClick={handleRetrainModels}
            disabled={!activeVersionId || isTraining}
            style={{
              padding: '0.45rem 0.85rem',
              backgroundColor: 'var(--surface-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            4. Retrain Models
          </button>
          <button
            type="button"
            onClick={handleOpenPreview}
            disabled={!activeVersionId}
            style={{
              padding: '0.45rem 0.85rem',
              backgroundColor: 'var(--surface-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            5. Preview Analytics
          </button>
          <button
            type="button"
            onClick={() => handlePromote()}
            disabled={!activeVersionId || isPromoting}
            style={{
              padding: '0.45rem 0.85rem',
              backgroundColor: 'rgba(16, 185, 129, 0.2)',
              color: '#34D399',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Promote to Live
          </button>
        </div>
      </details>

      {/* Uploaded Files Registry Table (Phase G.2) */}
      {stagedFilesList.length > 0 && (
        <div style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Table size={16} color="var(--accent-blue)" />
              <span style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Active Batch Files Registry ({stagedFilesList.length} files in {activeBatch.batch_id})
              </span>
            </div>
            <span className="pill-badge" style={{ backgroundColor: 'var(--surface-elevated)', color: 'var(--text-secondary)' }}>
              Batch Type: {activeBatch.batch_type || 'STANDARD'}
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ fontSize: '0.775rem' }}>
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Format</th>
                  <th>Size</th>
                  <th>Source Classification</th>
                  <th>Schema Status</th>
                  <th>Analytics Eligibility</th>
                  <th>HDFS Raw</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {stagedFilesList.map(([fid, finfo]) => {
                  const isEligible = finfo.analytics_eligibility === 'ANALYTICS_ELIGIBLE';
                  return (
                    <tr key={fid}>
                      <td style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{finfo.original_filename}</td>
                      <td>
                        <span className="pill-badge" style={{ fontSize: '0.7rem', backgroundColor: 'var(--surface-elevated)', color: 'var(--accent-blue)' }}>
                          {(finfo.format || 'CSV').toUpperCase()}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{formatBytes(finfo.size_bytes)}</td>
                      <td>
                        <span style={{ textTransform: 'capitalize', color: 'var(--text-primary)' }}>
                          {finfo.source_type ? finfo.source_type.replace('_', ' ') : 'Unclassified'}
                        </span>
                      </td>
                      <td>
                        <span className="pill-badge" style={{ fontSize: '0.7rem', backgroundColor: 'var(--surface-elevated)', color: finfo.mapping_status === 'MAPPED' ? 'var(--accent-green)' : 'var(--text-secondary)' }}>
                          {finfo.mapping_status || finfo.schema_discovery_status || 'DISCOVERED'}
                        </span>
                      </td>
                      <td>
                        <span className="pill-badge" style={{ fontSize: '0.7rem', backgroundColor: isEligible ? 'rgba(121, 168, 139, 0.15)' : 'rgba(213, 161, 109, 0.15)', color: isEligible ? '#79A88B' : '#D5A16D' }}>
                          {isEligible ? '✓ ELIGIBLE' : 'MAPPING NEEDED'}
                        </span>
                      </td>
                      <td style={{ color: finfo.hdfs_status === 'STORED' ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                        {finfo.hdfs_status === 'STORED' ? '✓ In HDFS' : 'Local Staged'}
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={() => handleOpenMappingDrawer(fid, finfo)}
                          style={{
                            padding: '0.3rem 0.65rem',
                            backgroundColor: 'var(--surface-elevated)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: '6px',
                            color: 'var(--accent-blue)',
                            fontSize: '0.725rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem'
                          }}
                        >
                          <Settings2 size={12} /> Map Fields
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Schema Discovery & Field Mapping Modal (Phase G.3) */}
      {selectedMappingFile && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0, 0, 0, 0.75)', zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ backgroundColor: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '16px', width: '92%', maxWidth: '850px', maxHeight: '88vh', overflowY: 'auto', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.85rem', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: '600', color: 'var(--text-primary)', margin: 0 }}>
                  Schema Discovery & Canonical Field Mapping
                </h3>
                <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0 0' }}>
                  {selectedMappingFile.original_filename} ({selectedMappingFile.format?.toUpperCase()}) — Map discovered raw columns to analytical schemas.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMappingFile(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.1rem' }}
              >
                ✕
              </button>
            </div>

            {/* Target Source Selector */}
            <div style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Target Analytical Source:
              </label>
              <select
                value={customSource}
                onChange={(e) => setCustomSource(e.target.value)}
                style={{
                  padding: '0.4rem 0.8rem',
                  backgroundColor: 'var(--surface-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  fontSize: '0.8rem'
                }}
              >
                <option value="transactions">Transactions (Orders, GMV, Items)</option>
                <option value="web_activity">Web Activity (Clickstream, Sessions)</option>
                <option value="social_media">Social Media (Interactions, Sentiment)</option>
                <option value="other">Other / Unclassified (Raw Only)</option>
              </select>
            </div>

            {/* Column Mapping Table */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Discovered Columns & Target Mappings
              </div>
              <table className="data-table" style={{ fontSize: '0.775rem' }}>
                <thead>
                  <tr>
                    <th>Discovered Column</th>
                    <th>Inferred Type</th>
                    <th>Null Count</th>
                    <th>Map to Canonical Field</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedMappingFile.discovered_schema?.fields || []).map((f) => (
                    <tr key={f.name}>
                      <td style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{f.name}</td>
                      <td>
                        <span className="pill-badge" style={{ fontSize: '0.675rem', backgroundColor: 'var(--surface-elevated)' }}>
                          {f.inferred_type}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>{f.null_count ?? '-'}</td>
                      <td>
                        <select
                          value={tempMapping[f.name] || ''}
                          onChange={(e) => {
                            const val = e.target.value;
                            setTempMapping((prev) => {
                              const updated = { ...prev };
                              if (val) updated[f.name] = val;
                              else delete updated[f.name];
                              return updated;
                            });
                          }}
                          style={{
                            padding: '0.35rem 0.65rem',
                            backgroundColor: 'var(--surface-secondary)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: '6px',
                            color: 'var(--text-primary)',
                            fontSize: '0.75rem',
                            width: '100%'
                          }}
                        >
                          <option value="">[Do Not Map / Ignore]</option>
                          {(CANONICAL_TARGET_FIELDS[customSource] || []).map((tf) => (
                            <option key={tf} value={tf}>{tf}</option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Sample Records Preview */}
            {selectedMappingFile.discovered_schema?.sample_records?.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  Sample Records Preview
                </div>
                <div style={{ overflowX: 'auto', maxHeight: '180px', backgroundColor: 'var(--surface-secondary)', borderRadius: '8px', padding: '0.65rem' }}>
                  <pre style={{ margin: 0, fontSize: '0.725rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                    {JSON.stringify(selectedMappingFile.discovered_schema.sample_records, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
              <button
                type="button"
                onClick={() => setSelectedMappingFile(null)}
                style={{ padding: '0.45rem 1rem', backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: 'var(--text-secondary)', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveFieldMapping}
                disabled={isSavingMapping}
                style={{ padding: '0.45rem 1.15rem', backgroundColor: 'var(--accent-blue)', color: '#FFF', border: 'none', borderRadius: '8px', fontSize: '0.8rem', fontWeight: '600', cursor: isSavingMapping ? 'not-allowed' : 'pointer' }}
              >
                {isSavingMapping ? 'Saving...' : 'Save & Apply Mapping'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export & Data Downloads Section (Phase G.5) */}
      <div style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
          <Download size={16} color="var(--accent-blue)" />
          <span style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
            Data Export & Canonical Templates Center
          </span>
        </div>

        <div className="grid-3" style={{ gap: '0.85rem' }}>
          {/* Canonical Templates */}
          <div className="glass-sub-card" style={{ padding: '0.85rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--accent-blue)', marginBottom: '0.4rem' }}>
              CANONICAL CSV TEMPLATES
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Download reference templates with standard headers and sample data rows.
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <a
                href={api.downloadTemplateUrl('transactions')}
                download="transactions_template.csv"
                style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Transactions Template (.csv)
              </a>
              <a
                href={api.downloadTemplateUrl('web_activity')}
                download="web_activity_template.csv"
                style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Web Activity Template (.csv)
              </a>
              <a
                href={api.downloadTemplateUrl('social_media')}
                download="social_media_template.csv"
                style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Social Media Template (.csv)
              </a>
            </div>
          </div>

          {/* Processed Datasets */}
          <div className="glass-sub-card" style={{ padding: '0.85rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--accent-green)', marginBottom: '0.4rem' }}>
              EXPORT PROCESSED DATASETS
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Export PySpark cleaned datasets and unified customer matrices (CSV or Parquet).
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <a
                href={api.exportProcessedUrl(activeVersionId || 'baseline', 'unified_customer_features', 'csv')}
                style={{ fontSize: '0.75rem', color: 'var(--accent-green)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Unified Features (23 Columns) [.csv]
              </a>
              <a
                href={api.exportProcessedUrl(activeVersionId || 'baseline', 'cleaned_transactions', 'csv')}
                style={{ fontSize: '0.75rem', color: 'var(--accent-green)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Cleaned Transactions [.csv]
              </a>
              <a
                href={api.exportProcessedUrl(activeVersionId || 'baseline', 'cleaned_web_activity', 'csv')}
                style={{ fontSize: '0.75rem', color: 'var(--accent-green)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Cleaned Web Activity [.csv]
              </a>
            </div>
          </div>

          {/* Analytics Reports */}
          <div className="glass-sub-card" style={{ padding: '0.85rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--accent-purple)', marginBottom: '0.4rem' }}>
              ANALYTICS & ML REPORTS
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Export execution telemetry and model evaluation reports in JSON format.
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <a
                href={api.exportAnalyticsUrl(activeVersionId || 'baseline', 'processing')}
                style={{ fontSize: '0.75rem', color: 'var(--accent-purple)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> PySpark Processing Report [.json]
              </a>
              <a
                href={api.exportAnalyticsUrl(activeVersionId || 'baseline', 'evaluation')}
                style={{ fontSize: '0.75rem', color: 'var(--accent-purple)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <Download size={12} /> Model Evaluation Report [.json]
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Model Evaluation Comparison Table */}
      {evaluationReport && (
        <div style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BarChart3 size={17} color="var(--accent-purple)" />
              <span style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Model Evaluation & Baseline Benchmark Comparison
              </span>
            </div>
            <span className="pill-badge" style={{ backgroundColor: 'rgba(121, 168, 139, 0.15)', color: '#79A88B' }}>
              Evaluation Completed
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  <th>Machine Learning Model</th>
                  <th>Evaluation Metric</th>
                  <th>Academic Baseline</th>
                  <th>New Batch Score</th>
                  <th>Variance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {evaluationReport.comparison?.map((row, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{row.model}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{row.metric}</td>
                    <td style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{row.baseline}</td>
                    <td style={{ fontFamily: 'monospace', fontWeight: '600', color: 'var(--accent-blue)' }}>{row.new_batch}</td>
                    <td style={{ fontFamily: 'monospace', color: typeof row.difference === 'number' ? (row.difference >= 0 ? 'var(--accent-green)' : 'var(--accent-orange)') : 'var(--text-muted)' }}>
                      {typeof row.difference === 'number' ? `${row.difference > 0 ? '+' : ''}${row.difference}` : row.difference}
                    </td>
                    <td>
                      <span className="pill-badge" style={{ fontSize: '0.7rem', backgroundColor: row.status === 'COMPLETED' || row.status === 'TRAINING_COMPLETED' ? 'rgba(121, 168, 139, 0.15)' : 'rgba(213, 161, 109, 0.15)', color: row.status === 'COMPLETED' || row.status === 'TRAINING_COMPLETED' ? '#79A88B' : '#D5A16D' }}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
            <button
              type="button"
              onClick={() => handlePromote()}
              disabled={isPromoting}
              style={{
                padding: '0.5rem 1.15rem',
                backgroundColor: 'var(--accent-blue)',
                color: '#FFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: isPromoting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <CheckCircle size={13} />
              {isPromoting ? 'Promoting...' : 'Promote Version to Production Dashboard'}
            </button>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreviewModal && previewData && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0, 0, 0, 0.75)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ backgroundColor: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '16px', width: '92%', maxWidth: '900px', maxHeight: '88vh', overflowY: 'auto', padding: '1.5rem' }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.85rem', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: '600', color: 'var(--text-primary)', margin: 0 }}>
                  Isolated Batch Analytics Preview ({previewData.version_id})
                </h3>
                <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0 0' }}>
                  Previewing newly processed batch without modifying active baseline production data.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowPreviewModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '6px' }}
              >
                ✕
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
              {['overview', 'segmentation', 'recommendations', 'churn'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setPreviewTab(t)}
                  style={{
                    padding: '0.45rem 0.95rem',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '0.775rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    backgroundColor: previewTab === t ? 'var(--surface-elevated)' : 'transparent',
                    color: previewTab === t ? 'var(--text-primary)' : 'var(--text-secondary)'
                  }}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Tab: Overview */}
            {previewTab === 'overview' && (
              <div>
                <div className="grid-3" style={{ marginBottom: '1rem' }}>
                  <div className="glass-sub-card" style={{ padding: '0.85rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>BATCH CUSTOMERS</div>
                    <div style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                      {previewData.overview?.kpis?.total_customers || 0}
                    </div>
                  </div>
                  <div className="glass-sub-card" style={{ padding: '0.85rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL REVENUE</div>
                    <div style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--accent-blue)', marginTop: '0.2rem' }}>
                      ${previewData.overview?.kpis?.total_revenue?.toLocaleString() || '0.00'}
                    </div>
                  </div>
                  <div className="glass-sub-card" style={{ padding: '0.85rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ORDER FULFILLMENT</div>
                    <div style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--accent-green)', marginTop: '0.2rem' }}>
                      {previewData.overview?.kpis?.fulfillment_rate || 0}%
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                  Segment Distribution
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1rem' }}>
                  {previewData.overview?.segment_distribution?.map((sd, idx) => (
                    <div key={idx} className="glass-sub-card" style={{ padding: '0.65rem', display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>{sd.cluster_name}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{sd.customer_count} cust ({sd.percentage_of_total}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab: Segmentation */}
            {previewTab === 'segmentation' && (
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                  K-Means Behavioral Clusters ({previewData.segmentation?.profiles?.length || 0})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {previewData.segmentation?.profiles?.map((p, idx) => (
                    <div key={idx} className="glass-sub-card" style={{ padding: '0.85rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                        <span style={{ fontWeight: '600', fontSize: '0.85rem', color: 'var(--accent-blue)' }}>{p.cluster_name}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.customer_count} customers ({p.percentage_of_total}%)</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Avg Spend: ${p.avg_spend} | Orders: {p.avg_transactions} | Web Touchpoints: {p.avg_web_activities} | Sentiment: {p.avg_sentiment_score}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab: Recommendations */}
            {previewTab === 'recommendations' && (
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                  Top Association Rules Mined ({previewData.recommendations?.rules?.length || 0})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {previewData.recommendations?.rules?.slice(0, 5).map((r, idx) => (
                    <div key={idx} className="glass-sub-card" style={{ padding: '0.65rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: 'var(--text-primary)' }}>{r.antecedent} → {r.consequent}</span>
                      <span style={{ color: 'var(--accent-green)' }}>Confidence: {(r.confidence * 100).toFixed(1)}% | Lift: {r.lift}x</span>
                    </div>
                  ))}
                  {(!previewData.recommendations?.rules || previewData.recommendations.rules.length === 0) && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Single item transactions detected; minimum support threshold not exceeded.</div>
                  )}
                </div>
              </div>
            )}

            {/* Tab: Churn */}
            {previewTab === 'churn' && (
              <div>
                {previewData.churn?.skip_info ? (
                  <div style={{ padding: '0.85rem', backgroundColor: 'rgba(213, 161, 109, 0.1)', border: '1px solid rgba(213, 161, 109, 0.25)', borderRadius: '8px', fontSize: '0.8rem', color: '#D5A16D' }}>
                    <strong>Notice:</strong> {previewData.churn.skip_info.reason}
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                      Risk Tiers Breakdown ({previewData.churn?.summary?.total_customers_evaluated || 0} evaluated)
                    </div>
                    <div className="grid-3">
                      {Object.entries(previewData.churn?.summary?.risk_distribution || {}).map(([tier, cnt]) => (
                        <div key={tier} className="glass-sub-card" style={{ padding: '0.75rem' }}>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{tier.toUpperCase()}</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: '600', color: tier.includes('High') ? 'var(--accent-red)' : tier.includes('Medium') ? 'var(--accent-orange)' : 'var(--accent-green)' }}>
                            {cnt}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Registered Versions Catalog */}
      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>
            Pipeline & Model Versions Registry ({versions.length})
          </span>
          <button
            type="button"
            onClick={loadMetadata}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
          >
            <RefreshCw size={12} className={loadingHistory ? 'spin' : ''} /> Refresh
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table" style={{ fontSize: '0.775rem' }}>
            <thead>
              <tr>
                <th>Version ID</th>
                <th>Status</th>
                <th>Customers</th>
                <th>ML Models</th>
                <th>Created</th>
                <th>Active Production</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((v) => (
                <tr key={v.version_id}>
                  <td style={{ fontFamily: 'monospace', color: 'var(--accent-blue)', fontWeight: '600' }}>{v.version_id}</td>
                  <td>
                    <span className="pill-badge" style={{ backgroundColor: v.is_active ? 'rgba(121, 168, 139, 0.15)' : 'var(--surface-elevated)', color: v.is_active ? '#79A88B' : 'var(--text-secondary)' }}>
                      {v.is_active ? 'ACTIVE' : v.status}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-primary)' }}>{v.total_customers?.toLocaleString() || '-'}</td>
                  <td style={{ color: v.models_trained ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                    {v.models_trained ? 'Trained' : 'Pending'}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{v.created_at ? v.created_at.replace('T', ' ').split('.')[0] : '-'}</td>
                  <td>
                    {v.is_active ? (
                      <span style={{ color: 'var(--accent-green)', fontWeight: '600' }}>Current Live</span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setActiveVersionId(v.version_id);
                          handleOpenPreview();
                        }}
                        style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer', textDecoration: 'underline', fontSize: '0.75rem' }}
                      >
                        Preview Version
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
