import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Bar, Pie, Doughnut } from 'react-chartjs-2';
import { Compass, Smartphone, HeartHandshake, Gauge } from 'lucide-react';

export default function CustomerAnalytics() {
  const [channelData, setChannelData] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);
  const [rfmData, setRfmData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getChannelAttribution(),
      api.getSentimentAnalysis(),
      api.getRFMDistributions()
    ])
      .then(([chan, sent, rfm]) => {
        setChannelData(chan);
        setSentimentData(sent);
        setRfmData(rfm);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading analytics:', err);
        setLoading(false);
      });
  }, []);

  if (loading || !channelData || !sentimentData || !rfmData) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Loading Multi-Source Analytics...</div>
        </div>
      </div>
    );
  }

  // Traffic Source Chart
  const trafficChartData = {
    labels: channelData.traffic_sources.map((s) => s.source),
    datasets: [
      {
        label: 'Sessions',
        data: channelData.traffic_sources.map((s) => s.count),
        backgroundColor: '#3b82f6',
        borderRadius: 6
      }
    ]
  };

  // Device Chart
  const deviceChartData = {
    labels: channelData.device_types.map((d) => d.device),
    datasets: [
      {
        data: channelData.device_types.map((d) => d.count),
        backgroundColor: ['#6366f1', '#06b6d4', '#f59e0b']
      }
    ]
  };

  // Sentiment Polarity Chart
  const sentimentChartData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [
          sentimentData.sentiment_counts['Positive'] || 0,
          sentimentData.sentiment_counts['Neutral'] || 0,
          sentimentData.sentiment_counts['Negative'] || 0
        ],
        backgroundColor: ['#10b981', '#64748b', '#ef4444']
      }
    ]
  };

  // Spend Distribution Chart
  const spendChartData = {
    labels: rfmData.spend.map((s) => s.bin),
    datasets: [
      {
        label: 'Customer Count',
        data: rfmData.spend.map((s) => s.count),
        backgroundColor: '#10b981',
        borderRadius: 6
      }
    ]
  };

  // Recency Distribution Chart
  const recencyChartData = {
    labels: rfmData.recency.map((r) => r.bin),
    datasets: [
      {
        label: 'Customer Count',
        data: rfmData.recency.map((r) => r.count),
        backgroundColor: '#f59e0b',
        borderRadius: 6
      }
    ]
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Customer Behavioral Analytics</h1>
        <p className="page-subtitle">
          In-depth exploration of clickstream pathways, device preference, sentiment polarity, and RFM distributions.
        </p>
      </div>

      {/* Traffic & Device Breakdown */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <Compass size={18} color="#3b82f6" />
            <span>Web Traffic Acquisition Channels</span>
          </div>
          <div style={{ height: '280px' }}>
            <Bar data={trafficChartData} options={barOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Smartphone size={18} color="#6366f1" />
            <span>Client Device Type Split</span>
          </div>
          <div style={{ height: '280px' }}>
            <Doughnut data={deviceChartData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      {/* Sentiment & Social Analysis */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <HeartHandshake size={18} color="#10b981" />
            <span>Social Sentiment Polarity (8,828 Records)</span>
          </div>
          <div style={{ height: '280px' }}>
            <Pie data={sentimentChartData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <span>Social Engagement by Platform</span>
          </div>
          <div className="table-container" style={{ maxHeight: '280px' }}>
            <table>
              <thead>
                <tr>
                  <th>Platform</th>
                  <th>Posts</th>
                  <th>Mean Polarity</th>
                  <th>Engagement</th>
                </tr>
              </thead>
              <tbody>
                {sentimentData.platform_breakdown.map((p) => (
                  <tr key={p.platform}>
                    <td style={{ fontWeight: '600' }}>{p.platform}</td>
                    <td>{p.count.toLocaleString()}</td>
                    <td>
                      <span className={`badge ${p.avg_sentiment >= 0 ? 'badge-emerald' : 'badge-rose'}`}>
                        {p.avg_sentiment > 0 ? `+${p.avg_sentiment}` : p.avg_sentiment}
                      </span>
                    </td>
                    <td>{p.avg_engagement} / 100</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* RFM Distributions */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">
            <Gauge size={18} color="#10b981" />
            <span>Monetary Spend Distribution (USD)</span>
          </div>
          <div style={{ height: '280px' }}>
            <Bar data={spendChartData} options={barOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Gauge size={18} color="#f59e0b" />
            <span>Recency Distribution (Days Since Last Order)</span>
          </div>
          <div style={{ height: '280px' }}>
            <Bar data={recencyChartData} options={barOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
