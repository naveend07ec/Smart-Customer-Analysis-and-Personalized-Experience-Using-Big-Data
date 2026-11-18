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

  // Traffic Source Chart (Apple Muted Series: #6E96CE, #70AFA6, #91A982, #D0A16E, #A394BF)
  const channelColorMap = {
    'Referral': '#6E96CE',
    'Social Media': '#70AFA6',
    'Organic Search': '#91A982',
    'Direct': '#D0A16E',
    'Email Newsletter': '#A394BF'
  };
  const fallbackTrafficColors = ['#6E96CE', '#70AFA6', '#91A982', '#D0A16E', '#A394BF', '#C77F83'];

  const trafficChartData = {
    labels: channelData.traffic_sources.map((s) => s.source),
    datasets: [
      {
        label: 'Sessions',
        data: channelData.traffic_sources.map((s) => s.count),
        backgroundColor: channelData.traffic_sources.map((s, i) => channelColorMap[s.source] || fallbackTrafficColors[i % fallbackTrafficColors.length]),
        borderRadius: 6
      }
    ]
  };

  // Device Chart (Series 1, 2, 4)
  const deviceChartData = {
    labels: channelData.device_types.map((d) => d.device),
    datasets: [
      {
        data: channelData.device_types.map((d) => d.count),
        backgroundColor: ['#6E96CE', '#70AFA6', '#D0A16E'],
        borderColor: '#171719',
        borderWidth: 2
      }
    ]
  };

  // Sentiment Polarity Chart (Soft Green, Muted Text, Soft Red)
  const sentimentChartData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [
          sentimentData.sentiment_counts['Positive'] || 0,
          sentimentData.sentiment_counts['Neutral'] || 0,
          sentimentData.sentiment_counts['Negative'] || 0
        ],
        backgroundColor: ['#91A982', '#74747C', '#C77F83'],
        borderColor: '#171719',
        borderWidth: 2
      }
    ]
  };

  // Spend Distribution Chart (Series 1: #6E96CE)
  const spendChartData = {
    labels: rfmData.spend.map((s) => s.bin),
    datasets: [
      {
        label: 'Customer Count',
        data: rfmData.spend.map((s) => s.count),
        backgroundColor: '#6E96CE',
        borderRadius: 6
      }
    ]
  };

  // Recency Distribution Chart (Series 2: #70AFA6)
  const recencyChartData = {
    labels: rfmData.recency.map((r) => r.bin),
    datasets: [
      {
        label: 'Customer Count',
        data: rfmData.recency.map((r) => r.count),
        backgroundColor: '#70AFA6',
        borderRadius: 6
      }
    ]
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1D1D20',
        borderColor: '#303035',
        borderWidth: 1,
        titleColor: '#F5F5F7',
        bodyColor: '#A1A1A8',
        padding: 10,
        boxPadding: 4
      }
    },
    scales: {
      x: {
        grid: { color: '#303035' },
        ticks: { color: '#A1A1A8', font: { family: 'var(--font-sans)' } }
      },
      y: {
        grid: { color: '#303035' },
        ticks: { color: '#A1A1A8', font: { family: 'var(--font-sans)' } }
      }
    }
  };

  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#F5F5F7',
          font: { family: 'var(--font-sans)', size: 12 },
          boxWidth: 12,
          padding: 16
        }
      },
      tooltip: {
        backgroundColor: '#1D1D20',
        borderColor: '#303035',
        borderWidth: 1,
        titleColor: '#F5F5F7',
        bodyColor: '#A1A1A8',
        padding: 10
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Customer Behavioral Analytics</h1>
          <p className="page-subtitle">
            In-depth exploration of clickstream pathways, device preference, sentiment polarity, and RFM distributions.
          </p>
        </div>
        <div className="hero-stats-group">
          <div className="hero-stat-box">
            <div className="hero-stat-number-row">
              <span className="hero-stat-number">120k</span>
              <span className="hero-stat-pill">+18%</span>
            </div>
            <span className="hero-stat-label">Web Touchpoints</span>
          </div>
          <div className="hero-stat-box">
            <div className="hero-stat-number-row">
              <span className="hero-stat-number">8.8k</span>
              <span className="hero-stat-pill">+12%</span>
            </div>
            <span className="hero-stat-label">Social Records</span>
          </div>
        </div>
      </div>

      {/* Traffic & Device Breakdown */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <Compass size={17} color="var(--accent-blue)" />
            <span>Web Traffic Acquisition Channels</span>
          </div>
          <div style={{ height: '280px' }}>
            <Bar data={trafficChartData} options={barOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Smartphone size={17} color="var(--accent-teal)" />
            <span>Client Device Type Split</span>
          </div>
          <div style={{ height: '280px' }}>
            <Doughnut data={deviceChartData} options={donutOptions} />
          </div>
        </div>
      </div>

      {/* Sentiment & Social Analysis */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">
            <HeartHandshake size={17} color="var(--accent-green)" />
            <span>Social Sentiment Polarity (8,828 Records)</span>
          </div>
          <div style={{ height: '280px' }}>
            <Pie data={sentimentChartData} options={donutOptions} />
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
                    <td style={{ fontWeight: '500' }}>{p.platform}</td>
                    <td>{p.count.toLocaleString()}</td>
                    <td>
                      <span className={`badge ${p.avg_sentiment >= 0 ? 'badge-sage' : 'badge-rose'}`}>
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
            <Gauge size={17} color="var(--accent-blue)" />
            <span>Monetary Spend Distribution (USD)</span>
          </div>
          <div style={{ height: '280px' }}>
            <Bar data={spendChartData} options={barOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <Gauge size={17} color="var(--accent-orange)" />
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
