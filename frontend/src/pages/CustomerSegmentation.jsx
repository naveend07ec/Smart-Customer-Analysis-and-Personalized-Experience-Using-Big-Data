import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';
import { Scatter, Line } from 'react-chartjs-2';
import { Award, Layers, Target, Info } from 'lucide-react';

export default function CustomerSegmentation() {
  const [evalData, setEvalData] = useState(null);
  const [pcaPoints, setPcaPoints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getSegmentationEvaluation(),
      api.getPCAScatter(1200)
    ])
      .then(([evaluation, scatter]) => {
        setEvalData(evaluation);
        setPcaPoints(scatter);
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

  const { metrics, elbow_curve, clusters } = evalData;

  // Elbow & Silhouette Chart Data (Series 1 & Series 5)
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
        pointRadius: 3
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
        pointRadius: 3
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

  // Group PCA points by cluster for scatter legend (Apple Muted Series)
  const clusterColors = {
    0: '#6E96CE', // Casual Occasional Shoppers (Series 1)
    1: '#D0A16E', // High-Value VIP Tech Spenders (Series 4)
    2: '#C77F83', // At-Risk / Dissatisfied (Series 6)
    3: '#A394BF', // Social Brand Advocates (Series 5)
    4: '#70AFA6'  // Active Bargain Hunters (Series 2)
  };

  const scatterDatasets = clusters.map((c) => {
    const pts = pcaPoints.filter((p) => p.cluster_id === c.cluster_id);
    return {
      label: c.cluster_name,
      data: pts.map((p) => ({ x: p.pca_x, y: p.pca_y, customer_id: p.customer_id, spend: p.total_spend })),
      backgroundColor: clusterColors[c.cluster_id] || '#6E96CE',
      pointRadius: 3.5,
      pointHoverRadius: 5
    };
  });

  const scatterOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#F5F5F7', boxWidth: 10, font: { family: 'var(--font-sans)', size: 11 }, padding: 12 } },
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
            return `${pt.customer_id} (${ctx.dataset.label}): Spend $${pt.spend}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: '#303035' },
        ticks: { color: '#A1A1A8' },
        title: { display: true, text: 'Principal Component 1 (40.85% Variance)', color: '#A1A1A8' }
      },
      y: {
        grid: { color: '#303035' },
        ticks: { color: '#A1A1A8' },
        title: { display: true, text: 'Principal Component 2 (16.11% Variance)', color: '#A1A1A8' }
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Customer Segmentation & Clustering</h1>
        <p className="page-subtitle">
          Unsupervised K-Means clustering ($K=5$) over 23 PySpark engineered behavioral features.
        </p>
      </div>

      {/* Model Quality Cards */}
      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <MetricCard
          title="Silhouette Coefficient"
          value={metrics.silhouette_score}
          subtitle="Score > 0.35 denotes robust cluster cohesion"
          badgeText="Optimal Separation"
          badgeColor="sage"
          icon={Award}
        />
        <MetricCard
          title="Davies-Bouldin Index"
          value={metrics.davies_bouldin_index}
          subtitle="Lower values indicate lower cluster similarity"
          badgeText="1.1554 (Compact)"
          badgeColor="steel"
          icon={Target}
        />
        <MetricCard
          title="Calinski-Harabasz Score"
          value={metrics.calinski_harabasz_score?.toFixed(1)}
          subtitle="Variance ratio criterion between clusters"
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
            <span>Optimal K Evaluation (Elbow & Silhouette)</span>
          </div>
          <div style={{ height: '340px' }}>
            <Line data={elbowChartData} options={elbowOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Layers size={18} color="#A59ABF" />
            <span>2D PCA Projection (1,200 Customers)</span>
          </div>
          <div style={{ height: '340px' }}>
            <Scatter data={{ datasets: scatterDatasets }} options={scatterOptions} />
          </div>
        </div>
      </div>

      {/* Cluster Persona Profiles Table */}
      <div className="card">
        <div className="card-title">
          <span>Detailed Cluster Behavioral Centroids (K=5)</span>
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
              {clusters.map((c) => (
                <tr key={c.cluster_id}>
                  <td>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '600' }}>
                        <span style={{
                          width: '10px',
                          height: '10px',
                          borderRadius: '50%',
                          backgroundColor: clusterColors[c.cluster_id] || '#6E9FCB',
                          display: 'inline-block'
                        }}></span>
                        <span>{c.cluster_name}</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                        {c.description || (c.cluster_name?.includes('VIP') ? 'Highest lifetime value, high-volume checkout' : c.cluster_name?.includes('Risk') ? 'Low engagement, high recency days, churn target' : c.cluster_name?.includes('Advocate') ? 'High brand loyalty and positive sentiment' : c.cluster_name?.includes('Bargain') ? 'High frequency, deal and coupon focused' : 'Moderate activity and standard order values')}
                      </div>
                    </div>
                  </td>
                  <td style={{ fontWeight: '600' }}>{(c.customer_count ?? 0).toLocaleString()} ({c.percentage_of_total ?? c.percentage ?? 0}%)</td>
                  <td>${Number(c.avg_spend ?? c.avg_total_spend ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td>${c.avg_order_value}</td>
                  <td>{c.avg_recency_days != null ? `${Number(c.avg_recency_days).toFixed(0)}d` : (c.avg_cancellation_rate != null ? `${(c.avg_cancellation_rate * 100).toFixed(1)}%` : '—')}</td>
                  <td>{Number(c.avg_web_activities ?? 0).toLocaleString()}</td>
                  <td>{typeof (c.avg_social_interactions ?? c.avg_engagement_score) === 'number' ? Number(c.avg_social_interactions ?? c.avg_engagement_score).toFixed(1) : (c.avg_social_interactions ?? c.avg_engagement_score ?? 0)}</td>
                  <td>
                    <span className={`badge ${c.avg_sentiment >= 0 ? 'badge-sage' : 'badge-rose'}`}>
                      {(() => { const s = c.avg_sentiment_score ?? c.avg_sentiment ?? 0; return s > 0 ? `+${Number(s).toFixed(2)}` : Number(s).toFixed(2); })()}
                    </span>
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
