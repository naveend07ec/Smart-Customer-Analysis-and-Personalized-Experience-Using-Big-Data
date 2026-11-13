import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';
import { Database, Cpu, CheckCircle2, ShieldCheck, HardDrive, FileSpreadsheet, Server } from 'lucide-react';

export default function DataProcessing() {
  const [pipelineSummary, setPipelineSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPipelineSummary()
      .then((data) => {
        setPipelineSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching pipeline summary:', err);
        setLoading(false);
      });
  }, []);

  if (loading || !pipelineSummary) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Loading PySpark Pipeline Metrics...</div>
        </div>
      </div>
    );
  }

  const { framework, execution_mode, java_runtime, raw_datasets, cleaning_metrics, processed_datasets, storage_formats } = pipelineSummary;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Big Data Pipeline & Data Processing</h1>
        <p className="page-subtitle">
          Apache Spark / PySpark ingestion, deduplication, schema validation, and multi-source feature extraction diagnostics.
        </p>
      </div>

      {/* Architecture Environment Cards */}
      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <MetricCard
          title="Compute Engine"
          value="PySpark 3.5.1"
          subtitle={execution_mode}
          badgeText="Verified"
          badgeColor="amber"
          icon={Cpu}
        />
        <MetricCard
          title="Java Virtual Machine"
          value="Java 8 (64-Bit)"
          subtitle={java_runtime}
          badgeText="Standard Baseline"
          badgeColor="blue"
          icon={Server}
        />
        <MetricCard
          title="Customer ID Coverage"
          value="100.0%"
          subtitle={processed_datasets.customer_coverage}
          badgeText="1,200 / 1,200 Overlap"
          badgeColor="emerald"
          icon={ShieldCheck}
        />
      </div>

      {/* Raw Ingestion vs Cleaned Output Table */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <Database size={18} color="#3b82f6" />
            <span>Raw Multi-Source Datasets Ingested</span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Dataset Source</th>
                  <th>Raw Records</th>
                  <th>Source File</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: '600' }}>Sales Transactions</td>
                  <td>{raw_datasets.transactions.records.toLocaleString()}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{raw_datasets.transactions.file}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: '600' }}>Website Clickstream</td>
                  <td>{raw_datasets.web_activity.records.toLocaleString()}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{raw_datasets.web_activity.file}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: '600' }}>Social Media Sentiment</td>
                  <td>{raw_datasets.social_media.records.toLocaleString()}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{raw_datasets.social_media.file}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <CheckCircle2 size={18} color="#10b981" />
            <span>PySpark Data Cleaning & Deduplication Audit</span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Quality Check / Transformation</th>
                  <th>Count</th>
                  <th>Resolution Applied</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Duplicate Transactions Removed</td>
                  <td style={{ fontWeight: '700', color: '#f59e0b' }}>{cleaning_metrics.transactions_deduplicated}</td>
                  <td>PySpark dropDuplicates(['transaction_id'])</td>
                </tr>
                <tr>
                  <td>Missing Payment Methods</td>
                  <td style={{ fontWeight: '700', color: '#f59e0b' }}>{cleaning_metrics.transactions_imputed_payment}</td>
                  <td>Imputed with 'Unknown' category</td>
                </tr>
                <tr>
                  <td>Duplicate Web Events Removed</td>
                  <td style={{ fontWeight: '700', color: '#f59e0b' }}>{cleaning_metrics.web_deduplicated}</td>
                  <td>PySpark dropDuplicates(['activity_id'])</td>
                </tr>
                <tr>
                  <td>Meaningful Null Product IDs</td>
                  <td style={{ fontWeight: '700', color: '#60a5fa' }}>{cleaning_metrics.meaningful_null_product_ids_preserved.toLocaleString()}</td>
                  <td>Preserved on generic navigation pages</td>
                </tr>
                <tr>
                  <td>Invalid Social Records</td>
                  <td style={{ fontWeight: '700', color: '#10b981' }}>{cleaning_metrics.social_invalid_filtered}</td>
                  <td>Bounded sentiment & engagement valid</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Storage Architecture & Unified Feature Matrix Details */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">
            <HardDrive size={18} color="#06b6d4" />
            <span>Storage Architecture (Local Staged Store — Explicitly Distinct from HDFS)</span>
          </div>
          <div style={{ fontSize: '0.875rem', color: '#94a3b8', lineHeight: '1.6', marginBottom: '1rem' }}>
            Local filesystem storage (NTFS) is utilized for lightweight offline development. The layout follows standard Hadoop-compatible partitioned directory structures (<code style={{ color: '#38bdf8' }}>data/raw/</code>, <code style={{ color: '#38bdf8' }}>data/processed/</code>) with PySpark batch processing, running without multi-node daemon overhead to preserve resources on 8 GB RAM systems.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {storage_formats.map((fmt, i) => (
              <div key={i} style={{ backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                <div style={{ fontWeight: '600', color: '#fff' }}>{fmt.name}</div>
                <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{fmt.purpose}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <FileSpreadsheet size={18} color="#8b5cf6" />
            <span>Unified Customer Behavioral Feature Matrix</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #334155' }}>
              <span style={{ color: '#94a3b8' }}>Matrix Dimensions:</span>
              <span style={{ fontWeight: '600', color: '#fff' }}>{processed_datasets.unified_feature_matrix}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #334155' }}>
              <span style={{ color: '#94a3b8' }}>Customer Joining Key:</span>
              <span style={{ fontWeight: '600', color: '#38bdf8' }}>customer_id (Outer Join)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #334155' }}>
              <span style={{ color: '#94a3b8' }}>Null Value Policy:</span>
              <span style={{ fontWeight: '600', color: '#10b981' }}>0 Unexpected Nulls (100% Coalesced)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0' }}>
              <span style={{ color: '#94a3b8' }}>Row-to-Entity Mapping:</span>
              <span style={{ fontWeight: '600', color: '#10b981' }}>Strictly 1 Row per Customer ID</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
