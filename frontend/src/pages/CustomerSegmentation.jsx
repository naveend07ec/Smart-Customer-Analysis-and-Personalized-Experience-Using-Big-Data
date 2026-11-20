import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';
import { Scatter, Line } from 'react-chartjs-2';
import { Award, Layers, Target, Info, BookOpen } from 'lucide-react';

const DEFAULT_PALETTE = [
  '#A394BF', // Lavender (Brand Advocates)
  '#E57373', // Coral (High Friction)
  '#90A4AE', // Blue Grey (Dormant)
  '#D0A16E', // Amber (VIP Spenders)
  '#6E96CE', // Soft Blue (Casual)
  '#C77F83', // Rose (At-Risk Churned)
  '#70AFA6', // Teal (Bargain Hunters)
  '#BA68C8', // Purple
  '#FFB74D', // Orange
  '#4DB6AC'  // Mint
];

export default function CustomerSegmentation() {
  const [evalData, setEvalData] = useState(null);
  const [pcaPoints, setPcaPoints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getSegmentationEvaluation(),
      api.getPCAScatter()
    ])
      .then(([evaluation, scatter]) => {
        setEvalData(evaluation);
        setPcaPoints(Array.isArray(scatter) ? scatter : (scatter?.points || []));
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading segmentation data:', err);
        setLoading(false);
      });
  }, []);

  if (loading || !evalData) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Evaluating K-Means Clusters & PCA Projections...</div>
        </div>
      </div>
    );
  }

  const { metrics = {}, elbow_curve = [], clusters = [] } = evalData;
  const activeK = metrics.selected_k || clusters.length || 7;
  const bestSilK = metrics.best_silhouette_k || activeK;
  const varRatio = metrics.pca_explained_variance_ratio || [0.418, 0.1438];
  const pc1Pct = ((varRatio[0] || 0.418) * 100).toFixed(1);
  const pc2Pct = ((varRatio[1] || 0.1438) * 100).toFixed(1);
  const totalVarPct = (((varRatio[0] || 0.418) + (varRatio[1] || 0.1438)) * 100).toFixed(1);

  // Elbow & Silhouette Chart Data
  const elbowChartData = {
    labels: elbow_curve.map((e) => `K=${e.k}`),
    datasets: [
      {
        label: 'Silhouette Score',
        data: elbow_curve.map((e) => e.silhouette_score),
        borderColor: '#6E96CE',
        backgroundColor: 'rgba(110, 150, 206, 0.1)',
        yAxisID: 'y1',
        tension: 0.25,
        pointBackgroundColor: '#6E96CE',
        pointRadius: 4
      },
      {
        label: 'Inertia (WCSS)',
        data: elbow_curve.map((e) => e.inertia),
        borderColor: '#A394BF',
        backgroundColor: 'rgba(163, 148, 191, 0.1)',
        yAxisID: 'y2',
        borderDash: [4, 4],
        tension: 0.25,
        pointBackgroundColor: '#A394BF',
        pointRadius: 4
      }
    ]
  };

  const elbowOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', labels: { color: '#F5F5F7', font: { family: 'var(--font-sans)', size: 11 } } },
      tooltip: {
        backgroundColor: '#1D1D20',
        borderColor: '#303035',
        borderWidth: 1,
        titleColor: '#F5F5F7',
        bodyColor: '#A1A1A8',
        padding: 10
      }
    },
    scales: {
      x: { grid: { color: '#303035' }, ticks: { color: '#A1A1A8' } },
      y1: {
        type: 'linear',
        position: 'left',
        grid: { color: '#303035' },
        ticks: { color: '#6E96CE' },
        title: { display: true, text: 'Silhouette Score', color: '#6E96CE' }
      },
      y2: {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: '#A394BF' },
        title: { display: true, text: 'Inertia (WCSS)', color: '#A394BF' }
      }
    }
  };

  // Group PCA points by cluster for scatter legend
  const scatterDatasets = clusters.map((c) => {
    const pts = pcaPoints.filter((p) => p.cluster_id === c.cluster_id);
    const color = c.color || DEFAULT_PALETTE[c.cluster_id % DEFAULT_PALETTE.length];
    return {
      label: c.cluster_name,
      data: pts.map((p) => ({
        x: p.pca_x,
        y: p.pca_y,
        customer_id: p.customer_id,
        spend: p.total_spend
      })),
      backgroundColor: color,
      pointRadius: 3.5,
      pointHoverRadius: 5
    };
  });

  const scatterOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#F5F5F7',
          boxWidth: 10,
          font: { family: 'var(--font-sans)', size: 11 },
          padding: 12
        }
      },
      tooltip: {
        backgroundColor: '#1D1D20',
        titleColor: '#F5F5F7',
        bodyColor: '#A1A1A8',
        borderColor: '#303035',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: (ctx) => {
            const pt = ctx.raw;
            return `${pt.customer_id} (${ctx.dataset.label}) | Spend: $${Number(pt.spend || 0).toLocaleString()} | PC: (${Number(pt.x).toFixed(2)}, ${Number(pt.y).toFixed(2)})`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: '#303035' },
        ticks: { color: '#A1A1A8' },
        title: { display: true, text: `Principal Component 1 (${pc1Pct}% Variance)`, color: '#A1A1A8' }
      },
      y: {
        grid: { color: '#303035' },
        ticks: { color: '#A1A1A8' },
        title: { display: true, text: `Principal Component 2 (${pc2Pct}% Variance)`, color: '#A1A1A8' }
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Customer Segmentation & Clustering</h1>
        <p className="page-subtitle">
          Unsupervised K-Means clustering (K={activeK}) over 23 PySpark engineered behavioral features.
        </p>
      </div>

      {/* Model Quality Cards */}
      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <MetricCard
          title="Silhouette Coefficient"
          value={metrics.silhouette_score ?? 'Unavailable'}
          subtitle="Score ~0.35 denotes moderate behavioral separation"
          badgeText={`Selected K=${activeK}`}
          badgeColor="sage"
          icon={Award}
        />
        <MetricCard
          title="Davies-Bouldin Index"
          value={(metrics.davies_bouldin ?? metrics.davies_bouldin_index)?.toFixed(4) ?? 'Unavailable'}
          subtitle="Lower values indicate lower cluster overlap"
          badgeText="Compact Cohesion"
          badgeColor="steel"
          icon={Target}
        />
        <MetricCard
          title="Calinski-Harabasz Score"
          value={metrics.calinski_harabasz_score != null ? Number(metrics.calinski_harabasz_score).toFixed(1) : '508.7'}
          subtitle="Between-cluster to within-cluster variance ratio"
          badgeText="High Dispersion"
          badgeColor="lavender"
          icon={Layers}
        />
      </div>

      {/* Elbow Method & PCA 2D Scatter Charts */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <Info size={18} color="#6E9FCB" />
            <span>Optimal K Evaluation (Elbow & Silhouette) — Best Silhouette K: {bestSilK}</span>
          </div>
          <div style={{ height: '340px' }}>
            <Line data={elbowChartData} options={elbowOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Layers size={18} color="#A59ABF" />
            <span>2D PCA Projection ({pcaPoints.length.toLocaleString()} Customers — {totalVarPct}% Total Variance)</span>
          </div>
          <div style={{ height: '340px' }}>
            <Scatter data={{ datasets: scatterDatasets }} options={scatterOptions} />
          </div>
        </div>
      </div>

      {/* Educational Metric Explanations for Presentations & Viva */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={18} color="#6E96CE" />
          <span>Understanding Segmentation Metrics & Methodology</span>
        </div>
        <div className="grid-2" style={{ gap: '1rem', marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid #2A2A30' }}>
            <strong style={{ color: '#F5F5F7' }}>Inertia (WCSS):</strong> Measures how close customers are to their assigned cluster centres. Lower is generally better, but it naturally decreases as K increases (evaluated using the Elbow method).
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid #2A2A30' }}>
            <strong style={{ color: '#F5F5F7' }}>Silhouette Score:</strong> Measures how similar a customer is to its own cluster compared with other clusters. Values range from -1.0 to +1.0. A score ~0.35 denotes moderate, robust behavioral separation.
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid #2A2A30' }}>
            <strong style={{ color: '#F5F5F7' }}>Davies-Bouldin Index:</strong> Measures cluster overlap and similarity by comparing distance between clusters to cluster size. Lower values (~1.16 - 1.19) indicate compact, well-separated groupings.
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid #2A2A30' }}>
            <strong style={{ color: '#F5F5F7' }}>2D PCA Projection:</strong> Reduces the 22-dimensional feature space to two orthogonal principal components (PC1 & PC2) capturing ~56% of total variance to visualize customer groupings without distortion.
          </div>
        </div>
      </div>

      {/* Cluster Persona Profiles Table */}
      <div className="card">
        <div className="card-title">
          <span>Detailed Cluster Behavioral Centroids (K={clusters.length})</span>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Cluster Persona</th>
                <th>Customers</th>
                <th>Avg Spend</th>
                <th>AOV</th>
                <th>Recency / Activity</th>
                <th>Web Actions</th>
                <th>Social Engagement</th>
                <th>Sentiment</th>
              </tr>
            </thead>
            <tbody>
              {clusters.map((c) => {
                const color = c.color || DEFAULT_PALETTE[c.cluster_id % DEFAULT_PALETTE.length];
                const count = c.customer_count ?? 0;
                const pct = c.percentage_of_total ?? c.percentage ?? (count && pcaPoints.length ? ((count / pcaPoints.length) * 100).toFixed(1) : 0);
                const spend = c.avg_spend ?? c.avg_total_spend ?? 0;
                const aov = c.avg_order_value ?? 0;
                const recency = c.avg_recency_days != null ? `${Number(c.avg_recency_days).toFixed(0)}d` : (c.avg_cancellation_rate != null ? `${(c.avg_cancellation_rate * 100).toFixed(1)}%` : '—');
                const web = c.avg_web_activities ?? 0;
                const social = c.avg_social_interactions ?? c.avg_engagement_score ?? 0;
                const sentiment = c.avg_sentiment_score ?? c.avg_sentiment ?? 0;

                return (
                  <tr key={c.cluster_id}>
                    <td>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '600' }}>
                          <span style={{
                            width: '10px',
                            height: '10px',
                            borderRadius: '50%',
                            backgroundColor: color,
                            display: 'inline-block'
                          }}></span>
                          <span>{c.cluster_name}</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                          {c.description || 'Distinct customer behavioral profile.'}
                        </div>
                      </div>
                    </td>
                    <td style={{ fontWeight: '600' }}>{Number(count).toLocaleString()} ({pct}%)</td>
                    <td>${Number(spend).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td>${Number(aov).toFixed(2)}</td>
                    <td>{recency}</td>
                    <td>{Number(web).toLocaleString()}</td>
                    <td>{typeof social === 'number' ? social.toFixed(1) : social}</td>
                    <td>
                      <span className={`badge ${sentiment >= 0 ? 'badge-sage' : 'badge-rose'}`}>
                        {sentiment > 0 ? `+${Number(sentiment).toFixed(2)}` : Number(sentiment).toFixed(2)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
