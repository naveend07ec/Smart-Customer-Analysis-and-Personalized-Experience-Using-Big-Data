import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';
import { DollarSign, Users, ShoppingCart, MousePointerClick, MessageSquareHeart, CheckCircle2 } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function OverviewDashboard() {
  const [kpis, setKpis] = useState(null);
  const [segments, setSegments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [monthlyTrends, setMonthlyTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getKPIs(),
      api.getSegmentDistribution(),
      api.getRevenueByCategory(),
      api.getMonthlyTrends()
    ])
      .then(([kpiData, segData, catData, trendData]) => {
        setKpis(kpiData);
        setSegments(segData);
        setCategories(catData);
        setMonthlyTrends(trendData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading overview data:', err);
        setLoading(false);
      });
  }, []);

  if (loading || !kpis) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Loading Big Data Analytics...</div>
        </div>
      </div>
    );
  }

  // Monthly Revenue Chart Data
  const monthlyChartData = {
    labels: monthlyTrends.map((t) => t.month),
    datasets: [
      {
        label: 'Revenue ($)',
        data: monthlyTrends.map((t) => t.revenue),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderRadius: 6
      }
    ]
  };

  const monthlyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `Revenue: $${ctx.raw.toLocaleString()}`
        }
      }
    },
    scales: {
      x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8', callback: (val) => `$${(val / 1000).toFixed(0)}k` }
      }
    }
  };

  // Segment Distribution Chart Data
  const segmentChartData = {
    labels: segments.map((s) => s.cluster_name),
    datasets: [
      {
        data: segments.map((s) => s.customer_count),
        backgroundColor: segments.map((s) => s.color || '#3b82f6'),
        borderColor: '#1e293b',
        borderWidth: 2
      }
    ]
  };

  const segmentChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 12, padding: 15 } }
    }
  };

  // Category Revenue Chart Data
  const categoryChartData = {
    labels: categories.map((c) => c.product_category),
    datasets: [
      {
        data: categories.map((c) => c.revenue),
        backgroundColor: [
          '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'
        ],
        borderColor: '#1e293b',
        borderWidth: 2
      }
    ]
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Executive Analytics Overview</h1>
          <p className="page-subtitle">
            Consolidated Big Data customer metrics derived from PySpark batch processing and multi-source integration.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <span className="badge badge-emerald">
            <CheckCircle2 size={12} /> Live PySpark Outputs
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <MetricCard
          title="Total Gross Revenue"
          value={`$${kpis.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtitle="From completed sales orders"
          badgeText="+100% Validated"
          badgeColor="emerald"
          icon={DollarSign}
        />
        <MetricCard
          title="Integrated Customers"
          value={kpis.total_customers.toLocaleString()}
          subtitle="Unified cross-source profile"
          badgeText="100% Coverage"
          badgeColor="blue"
          icon={Users}
        />
        <MetricCard
          title="Total Orders Processed"
          value={kpis.total_transactions.toLocaleString()}
          subtitle={`${kpis.fulfillment_rate}% fulfillment rate`}
          badgeText={`${kpis.completed_orders.toLocaleString()} completed`}
          badgeColor="amber"
          icon={ShoppingCart}
        />
        <MetricCard
          title="Web & Social Touchpoints"
          value={`${(kpis.total_web_touchpoints / 1000).toFixed(1)}k / ${(kpis.total_social_interactions / 1000).toFixed(1)}k`}
          subtitle={`Avg Sentiment: +${kpis.avg_sentiment_score}`}
          badgeText="Clickstream + Sentiment"
          badgeColor="purple"
          icon={MousePointerClick}
        />
      </div>

      {/* Charts Grid: Monthly Revenue & Category Breakdown */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <span>Monthly Revenue Progression (2024)</span>
          </div>
          <div style={{ height: '300px' }}>
            <Bar data={monthlyChartData} options={monthlyChartOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <span>Revenue Contribution by Category</span>
          </div>
          <div style={{ height: '300px' }}>
            <Doughnut data={categoryChartData} options={segmentChartOptions} />
          </div>
        </div>
      </div>

      {/* Segment Breakdown & Comparison */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">
            <span>Customer Behavioral Segment Shares</span>
          </div>
          <div style={{ height: '300px' }}>
            <Doughnut data={segmentChartData} options={segmentChartOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <span>Cluster Persona Executive Summary</span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Persona</th>
                  <th>Share</th>
                  <th>Avg Spend</th>
                  <th>Avg Recency</th>
                </tr>
              </thead>
              <tbody>
                {segments.map((seg) => (
                  <tr key={seg.cluster_id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{
                          width: '10px',
                          height: '10px',
                          borderRadius: '50%',
                          backgroundColor: seg.color || '#3b82f6',
                          display: 'inline-block'
                        }}></span>
                        <span style={{ fontWeight: '600' }}>{seg.cluster_name}</span>
                      </div>
                    </td>
                    <td>{seg.percentage}% ({seg.customer_count})</td>
                    <td>${seg.avg_total_spend.toLocaleString()}</td>
                    <td>{seg.avg_recency_days} days</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
