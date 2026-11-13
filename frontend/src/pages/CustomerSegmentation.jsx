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

  // Elbow & Silhouette Chart Data
  const elbowChartData = {
    labels: elbow_curve.map((e) => `K=${e.k}`),
    datasets: [
      {
        label: 'Silhouette Score',
        data: elbow_curve.map((e) => e.silhouette_score),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        yAxisID: 'y1',
        tension: 0.3
      },
      {
        label: 'Inertia (WCSS)',
        data: elbow_curve.map((e) => e.inertia),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        yAxisID: 'y2',
        borderDash: [5, 5],
        tension: 0.3
      }
    ]
  };

  const elbowOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', labels: { color: '#94a3b8' } }
    },
    scales: {
      x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
      y1: {
        type: 'linear',
        position: 'left',
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#10b981' },
        title: { display: true, text: 'Silhouette Score', color: '#10b981' }
      },
      y2: {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: '#3b82f6' },
        title: { display: true, text: 'Inertia (WCSS)', color: '#3b82f6' }
      }
    }
  };

  // Group PCA points by cluster for scatter legend
  const clusterColors = {
    0: '#3b82f6', // Casual (Blue)
    1: '#10b981', // VIP (Emerald)
    2: '#ef4444', // At-Risk (Red)
    3: '#8b5cf6', // Social (Purple)
    4: '#f59e0b'  // Bargain (Amber)
  };

  const scatterDatasets = clusters.map((c) => {
    const pts = pcaPoints.filter((p) => p.cluster_id === c.cluster_id);
    return {
      label: c.cluster_name,
      data: pts.map((p) => ({ x: p.pca_x, y: p.pca_y, customer_id: p.customer_id, spend: p.total_spend })),
      backgroundColor: c.color || clusterColors[c.cluster_id] || '#94a3b8',
      pointRadius: 4,
      pointHoverRadius: 6
    };
  });

  const scatterOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 10 } },
      tooltip: {
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
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8' },
        title: { display: true, text: 'Principal Component 1 (40.85% Variance)', color: '#94a3b8' }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8' },
        title: { display: true, text: 'Principal Component 2 (16.11% Variance)', color: '#94a3b8' }
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
          badgeColor="emerald"
          icon={Award}
        />
        <MetricCard
          title="Davies-Bouldin Index"
          value={metrics.davies_bouldin_index}
          subtitle="Lower values indicate lower cluster similarity"
          badgeText="1.1554 (Compact)"
          badgeColor="blue"
          icon={Target}
        />
        <MetricCard
          title="Calinski-Harabasz Score"
          value={metrics.calinski_harabasz_score?.toFixed(1)}
          subtitle="Variance ratio criterion between clusters"
          badgeText="High Dispersion"
          badgeColor="purple"
          icon={Layers}
        />
      </div>

      {/* Elbow Method & PCA 2D Scatter Charts */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <Info size={18} color="#3b82f6" />
            <span>Optimal K Evaluation (Elbow & Silhouette)</span>
          </div>
          <div style={{ height: '340px' }}>
            <Line data={elbowChartData} options={elbowOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Layers size={18} color="#8b5cf6" />
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
                <th>Cancel Rate</th>
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
                          backgroundColor: c.color || '#3b82f6',
                          display: 'inline-block'
                        }}></span>
                        <span>{c.cluster_name}</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
                        {c.description}
                      </div>
                    </div>
                  </td>
                  <td style={{ fontWeight: '600' }}>{c.customer_count} ({c.percentage}%)</td>
                  <td>${c.avg_total_spend.toLocaleString()}</td>
                  <td>${c.avg_order_value}</td>
                  <td>{(c.avg_cancellation_rate * 100).toFixed(1)}%</td>
                  <td>{c.avg_web_activities}</td>
                  <td>{c.avg_engagement_score}</td>
                  <td>
                    <span className={`badge ${c.avg_sentiment >= 0 ? 'badge-emerald' : 'badge-rose'}`}>
                      {c.avg_sentiment > 0 ? `+${c.avg_sentiment}` : c.avg_sentiment}
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
