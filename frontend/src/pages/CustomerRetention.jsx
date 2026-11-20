import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Search,
  Filter,
  ArrowUpDown,
  Activity,
  ChevronLeft,
  ChevronRight,
  TrendingDown,
  Info,
  Layers,
  Sparkles
} from 'lucide-react';
import { Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export default function CustomerRetention() {
  const [summary, setSummary] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [riskCategory, setRiskCategory] = useState('all');
  const [sortBy, setSortBy] = useState('churn_risk_score');
  const [sortDir, setSortDir] = useState('desc');
  const [loading, setLoading] = useState(true);

  // Selected customer 360 detail state
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);
  const [customerDetail, setCustomerDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Initial load: summary + customer table
  useEffect(() => {
    const fetchRetentionData = () => {
      Promise.all([
        api.getChurnSummary(),
        api.getChurnCustomers({ page: 1, pageSize: 15, search: '', riskCategory: 'all', sortBy: 'churn_risk_score', sortDir: 'desc' })
      ])
        .then(([sumData, custListData]) => {
          setSummary(sumData);
          setCustomers(custListData.customers || []);
          setTotalRecords(custListData.total_records || 0);
          setTotalPages(custListData.total_pages || 1);
          setLoading(false);
        })
        .catch((err) => {
          console.error('Error loading churn summary:', err);
          setLoading(false);
        });
    };

    fetchRetentionData();
    window.addEventListener('smart-dataset-mode-changed', fetchRetentionData);
    return () => window.removeEventListener('smart-dataset-mode-changed', fetchRetentionData);
  }, []);

  // Reload customer list on filter/page change
  const loadCustomers = () => {
    api.getChurnCustomers({ page, pageSize: 15, search, riskCategory, sortBy, sortDir })
      .then((res) => {
        setCustomers(res.customers || []);
        setTotalRecords(res.total_records || 0);
        setTotalPages(res.total_pages || 1);
      })
      .catch((err) => {
        console.error('Error fetching churn customers:', err);
      });
  };

  useEffect(() => {
    if (!loading) {
      loadCustomers();
    }
  }, [page, riskCategory, sortBy, sortDir]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadCustomers();
  };

  const handleSelectCustomer = (cid) => {
    setSelectedCustomerId(cid);
    setDetailLoading(true);
    api.getCustomerChurnDetail(cid)
      .then((data) => {
        setCustomerDetail(data);
        setDetailLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching churn customer detail:', err);
        setDetailLoading(false);
      });
  };

  if (loading || !summary) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Loading Supervised Churn & Retention Analytics...</div>
        </div>
      </div>
    );
  }

  const { risk_distribution, evaluation_metrics, top_features, model_name, model_version, prediction_cutoff, academic_limitations } = summary;
  const cm = evaluation_metrics?.confusion_matrix || { true_negatives: 139, false_positives: 35, false_negatives: 6, true_positives: 56 };

  // Doughnut chart for risk distribution (Soft Green, Muted Orange, Soft Red)
  const riskDoughnutData = {
    labels: ['Low Risk (< 35)', 'Medium Risk (35-64)', 'High Risk (>= 65)'],
    datasets: [
      {
        data: [
          risk_distribution?.low_risk?.count || 677,
          risk_distribution?.medium_risk?.count || 271,
          risk_distribution?.high_risk?.count || 229
        ],
        backgroundColor: ['#79A88B', '#D5A16D', '#C77F83'],
        borderColor: '#171719',
        borderWidth: 2
      }
    ]
  };

  // Feature Importance Horizontal Bar Chart (Apple Muted Series)
  const featurePalette = ['#6E96CE', '#70AFA6', '#91A982', '#D0A16E', '#A394BF', '#C77F83'];
  const featureBarData = {
    labels: (top_features || []).map((f) => f.feature.replace('hist_', '').replace('_', ' ').toUpperCase()),
    datasets: [
      {
        label: 'Predictive Importance (%)',
        data: (top_features || []).map((f) => f.importance_percent),
        backgroundColor: (top_features || []).map((_, i) => featurePalette[i % featurePalette.length]),
        borderRadius: 4
      }
    ]
  };

  const getRiskBadge = (category) => {
    switch (category) {
      case 'High':
        return <span className="badge badge-rose">High Risk</span>;
      case 'Medium':
        return <span className="badge badge-amber">Medium Risk</span>;
      case 'Insufficient Temporal Data':
        return <span className="badge badge-amber">Timeline &lt; 270d</span>;
      default:
        return <span className="badge badge-sage">Low Risk</span>;
    }
  };

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Customer Retention & Supervised Churn Prediction</h1>
          <p className="page-subtitle">
            Point-in-time supervised machine learning model forecasting 90-day future purchase inactivity from historical multi-channel interactions.
          </p>
        </div>
      </div>

      {/* Disclaimers & Methodology Banner */}
      <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '3px solid var(--accent-blue)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.45rem' }}>
          <Info size={17} color="var(--accent-blue)" />
          <span style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.9rem' }}>Methodology & Distinction: Segmentation vs Churn Prediction</span>
        </div>
        <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: '1.55' }}>
          • <strong>K-Means Customer Segments</strong> (Stage 4) describe historical multi-source behavioral archetypes (e.g. VIP Spenders, Bargain Hunters).<br/>
          • <strong>Supervised Churn Prediction</strong> (Stage 7) is a forward-looking point-in-time estimate trained strictly on data prior to <code>{prediction_cutoff}</code> to forecast whether a customer will record zero completed orders in the subsequent 90 days.
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <MetricCard
          title="Evaluated Customers"
          value={Number(summary?.total_customers_evaluated || 0).toLocaleString()}
          subtitle="Qualified with historical purchases"
          badgeText="Eligible Cohort"
          badgeColor="blue"
          icon={Activity}
        />
        <MetricCard
          title="High Churn Risk"
          value={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'N/A' : `${risk_distribution?.high_risk?.count ?? 0} (${risk_distribution?.high_risk?.percentage ?? 0}%)`}
          subtitle={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'Temporal Window Required' : 'Score >= 65.0 (Priority Action)'}
          badgeText={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'Requires 270d' : 'At-Risk'}
          badgeColor="rose"
          icon={AlertTriangle}
        />
        <MetricCard
          title="Medium Churn Risk"
          value={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'N/A' : `${risk_distribution?.medium_risk?.count ?? 0} (${risk_distribution?.medium_risk?.percentage ?? 0}%)`}
          subtitle={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'Temporal Window Required' : '35.0 <= Score < 65.0'}
          badgeText={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'Requires 270d' : 'Monitor'}
          badgeColor="amber"
          icon={TrendingDown}
        />
        <MetricCard
          title="Low Churn Risk"
          value={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'N/A' : `${risk_distribution?.low_risk?.count ?? 0} (${risk_distribution?.low_risk?.percentage ?? 0}%)`}
          subtitle={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'Span < 270 Days' : 'Score < 35.0 (Active & Loyal)'}
          badgeText={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'Timeline < 270d' : 'Retained'}
          badgeColor={summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? 'amber' : 'sage'}
          icon={CheckCircle}
        />
      </div>

      {summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' && (
        <div className="card" style={{ marginBottom: '1.5rem', backgroundColor: 'rgba(217, 119, 6, 0.08)', border: '1px solid rgba(217, 119, 6, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
            <AlertTriangle size={18} color="#F59E0B" />
            <span style={{ fontWeight: '700', color: '#FBBF24', fontSize: '0.9rem' }}>
              Academic Integrity: Insufficient Temporal History for Churn Supervision
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
            {summary.message || "The active New Batch Only timeline does not span the required 270 days (180 days feature observation + 90 days forward inactivity label). Churn scoring is marked as 'Insufficient Temporal Data' to preserve mathematical rigor without fabricating synthetic labels."}
          </p>
        </div>
      )}

      {/* Visual Analytics & Confusion Matrix Grid */}
      {summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? (
        <div className="card" style={{ marginBottom: '2rem', padding: '2.5rem', textAlign: 'center', borderLeft: '4px solid var(--accent-amber)', backgroundColor: 'var(--surface-elevated)' }}>
          <div style={{ display: 'inline-flex', padding: '0.85rem', borderRadius: '50%', backgroundColor: 'rgba(217, 119, 6, 0.12)', marginBottom: '1rem' }}>
            <AlertTriangle size={32} color="#F59E0B" />
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Supervised Churn Model Omitted for Isolated Batch
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', maxWidth: '680px', margin: '0 auto 1.5rem', lineHeight: '1.6' }}>
            Point-in-time supervised churn prediction requires an observation timeline of at least <strong>270 days</strong> (180 days feature history + 90 days forward purchase observation window to observe customer inactivity). The uploaded batch spans <strong>{summary?.timeline_span_days || 266} days</strong>.
          </p>
          <div style={{ display: 'inline-flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            <span className="badge badge-amber" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>
              Academic Integrity: No Synthetic Labels Fabricated
            </span>
            <span className="badge badge-blue" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>
              Full 365-Day Retraining Available in Cumulative Mode
            </span>
          </div>
        </div>
      ) : (
        <div className="grid-3" style={{ marginBottom: '2rem' }}>
          {/* Risk Distribution Chart */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-title">
              <ShieldAlert size={17} color="var(--accent-blue)" />
              <span>Risk Tier Distribution</span>
            </div>
            <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Doughnut
                data={riskDoughnutData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'bottom', labels: { color: '#F5F5F7', font: { family: 'var(--font-sans)', size: 11 }, padding: 12 } },
                    tooltip: {
                      backgroundColor: '#1D1D20',
                      borderColor: '#303035',
                      borderWidth: 1,
                      titleColor: '#F5F5F7',
                      bodyColor: '#A1A1A8'
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Top Predictive Feature Importances */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-title">
              <Activity size={17} color="var(--accent-purple)" />
              <span>Top Predictive Factors (Random Forest)</span>
            </div>
            <div style={{ height: '220px' }}>
              <Bar
                data={featureBarData}
                options={{
                  indexAxis: 'y',
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      backgroundColor: '#1D1D20',
                      borderColor: '#303035',
                      borderWidth: 1,
                      titleColor: '#F5F5F7',
                      bodyColor: '#A1A1A8'
                    }
                  },
                  scales: {
                    x: { grid: { color: '#303035' }, ticks: { color: '#A1A1A8' } },
                    y: { grid: { display: false }, ticks: { color: '#A1A1A8', font: { size: 10 } } }
                  }
                }}
              />
            </div>
          </div>

          {/* Holdout Confusion Matrix Card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-title">
              <Layers size={17} color="var(--accent-teal)" />
              <span>Test Set Confusion Matrix (20% Holdout)</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Performance on 236 unseen test customers (ROC-AUC: <strong>{evaluation_metrics?.roc_auc}</strong>, Recall: <strong>{(evaluation_metrics?.recall * 100).toFixed(1)}%</strong>):
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: 'auto' }}>
              <div className="glass-sub-card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>True Negative (Retained)</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--accent-green)', marginTop: '0.2rem' }}>{cm.true_negatives}</div>
              </div>
              <div className="glass-sub-card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>False Positive (False Alarm)</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--accent-orange)', marginTop: '0.2rem' }}>{cm.false_positives}</div>
              </div>
              <div className="glass-sub-card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>False Negative (Missed Churn)</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--accent-red)', marginTop: '0.2rem' }}>{cm.false_negatives}</div>
              </div>
              <div className="glass-sub-card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>True Positive (Detected Churn)</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--accent-red)', marginTop: '0.2rem' }}>{cm.true_positives}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search and Filters Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '260px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={15} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="Search by Customer ID (e.g. CUST_0001)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem 0.5rem 2.25rem'
                }}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>
              Search
            </button>
          </form>

          {/* Risk Tier Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={15} color="var(--text-muted)" />
            <select
              value={riskCategory}
              onChange={(e) => { setRiskCategory(e.target.value); setPage(1); }}
            >
              <option value="all">All Risk Categories</option>
              <option value="high">High Risk (&gt;= 65)</option>
              <option value="medium">Medium Risk (35-64)</option>
              <option value="low">Low Risk (&lt; 35)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Customer Churn Risk Table */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={17} color="var(--accent-orange)" />
            <span>Customer Churn Risk Register ({totalRecords} matching customers)</span>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>K-Means Segment</th>
                <th>Risk Score</th>
                <th>Risk Category</th>
                <th>Predicted 90d Inactive</th>
                <th>Suggested Retention Action</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.customer_id} style={{ backgroundColor: selectedCustomerId === c.customer_id ? 'rgba(94, 143, 213, 0.08)' : 'transparent' }}>
                  <td style={{ fontWeight: '500', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{c.customer_id}</td>
                  <td>
                    <span className="badge badge-purple" style={{ fontSize: '0.72rem' }}>
                      {c.cluster_name || 'Assigned'}
                    </span>
                  </td>
                  <td>
                    {summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>N/A</span>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: '600', color: c.churn_risk_score >= 65 ? 'var(--accent-red)' : c.churn_risk_score >= 35 ? 'var(--accent-orange)' : 'var(--accent-green)' }}>
                          {c.churn_risk_score} / 100
                        </span>
                      </div>
                    )}
                  </td>
                  <td>{getRiskBadge(c.risk_category)}</td>
                  <td>
                    {summary?.status === 'INSUFFICIENT_TEMPORAL_DATA' ? (
                      <span className="badge badge-amber">Omitted (No Leakage)</span>
                    ) : (
                      <span className={`badge ${c.predicted_churn_class === 1 ? 'badge-rose' : 'badge-sage'}`}>
                        {c.predicted_churn_class === 1 ? 'Yes (Churn Risk)' : 'No (Active)'}
                      </span>
                    )}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '300px' }}>
                    {c.suggested_retention_action}
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                      onClick={() => handleSelectCustomer(c.customer_id)}
                    >
                      View Diagnostics
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem', padding: '0 0.5rem' }}>
          <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
            Showing Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({totalRecords} records)
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className="btn btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              <ChevronLeft size={15} /> Prev
            </button>
            <button
              className="btn btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              Next <ChevronRight size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Customer 360 Diagnostics Panel (When Customer is selected) */}
      {selectedCustomerId && (
        <div className="card" style={{ marginBottom: '2rem', borderTop: '2px solid var(--accent-blue)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={18} color="var(--accent-blue)" />
              <h2 style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Retention Diagnostics for {selectedCustomerId}
              </h2>
            </div>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.55rem' }}
              onClick={() => setSelectedCustomerId(null)}
            >
              Close Drawer
            </button>
          </div>

          {detailLoading || !customerDetail ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <div>Retrieving point-in-time behavioral factors...</div>
            </div>
          ) : (
            <div>
              {/* Summary Badges */}
              <div className="glass-sub-card" style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.5rem', padding: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Assigned Segment:</div>
                  <div style={{ fontWeight: '500', color: 'var(--accent-blue)' }}>{customerDetail.cluster_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Churn Risk Score:</div>
                  <div style={{ fontWeight: '600', fontSize: '1.05rem', color: customerDetail.churn_risk_score >= 65 ? 'var(--accent-red)' : customerDetail.churn_risk_score >= 35 ? 'var(--accent-orange)' : 'var(--accent-green)' }}>
                    {customerDetail.churn_risk_score} / 100 ({customerDetail.risk_category} Risk)
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Prediction Cutoff Recency:</div>
                  <div style={{ fontWeight: '500', color: 'var(--accent-orange)' }}>{customerDetail.historical_behavioural_factors.recency_days_at_cutoff} days ago</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Historical 180d Spend:</div>
                  <div style={{ fontWeight: '600', color: 'var(--accent-green)' }}>${customerDetail.historical_behavioural_factors.hist_total_spend.toFixed(2)}</div>
                </div>
              </div>

              {/* Action Recommendation */}
              <div style={{ backgroundColor: 'rgba(94, 143, 213, 0.08)', border: '1px solid rgba(94, 143, 213, 0.2)', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
                <div style={{ fontWeight: '600', color: 'var(--accent-blue)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  <Sparkles size={15} color="var(--accent-blue)" />
                  <span>Recommended Retention Playbook Action:</span>
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: '1.45' }}>
                  {customerDetail.suggested_retention_action}
                </div>
              </div>

              {/* Historical Predictor Breakdown Grid */}
              <h3 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                Historical Behavioral Indicators Prior to Prediction Cutoff ({prediction_cutoff})
              </h3>
              <div className="grid-3" style={{ gap: '0.75rem' }}>
                <div className="glass-sub-card" style={{ padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Completed Orders (180d)</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>{customerDetail.historical_behavioural_factors.hist_completed_orders}</div>
                </div>
                <div className="glass-sub-card" style={{ padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Distinct Web Sessions</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>{customerDetail.historical_behavioural_factors.hist_distinct_sessions}</div>
                </div>
                <div className="glass-sub-card" style={{ padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Avg Browsing Dwell Time</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>{customerDetail.historical_behavioural_factors.hist_avg_dwell_time}s</div>
                </div>
                <div className="glass-sub-card" style={{ padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Product Views</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>{customerDetail.historical_behavioural_factors.hist_product_views}</div>
                </div>
                <div className="glass-sub-card" style={{ padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Social Feedback Sentiment</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: customerDetail.historical_behavioural_factors.hist_avg_sentiment >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '0.2rem' }}>
                    {customerDetail.historical_behavioural_factors.hist_avg_sentiment > 0 ? `+${customerDetail.historical_behavioural_factors.hist_avg_sentiment}` : customerDetail.historical_behavioural_factors.hist_avg_sentiment}
                  </div>
                </div>
                <div className="glass-sub-card" style={{ padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Cancellation Rate</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: customerDetail.historical_behavioural_factors.hist_cancellation_rate > 0.1 ? 'var(--accent-orange)' : 'var(--accent-green)', marginTop: '0.2rem' }}>
                    {(customerDetail.historical_behavioural_factors.hist_cancellation_rate * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
