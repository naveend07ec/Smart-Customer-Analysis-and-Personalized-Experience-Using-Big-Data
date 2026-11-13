import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Sparkles, BrainCircuit, ArrowRight, Tag, HelpCircle, Layers } from 'lucide-react';

export default function PersonalizedRecommendations() {
  const [selectedCustomerId, setSelectedCustomerId] = useState('CUST_0001');
  const [recommendations, setRecommendations] = useState([]);
  const [associationRules, setAssociationRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recsLoading, setRecsLoading] = useState(false);

  // Quick select archetypes
  const sampleArchetypes = [
    { id: 'CUST_0001', label: 'CUST_0001 (Casual)' },
    { id: 'CUST_0002', label: 'CUST_0002 (VIP Spender)' },
    { id: 'CUST_0003', label: 'CUST_0003 (Bargain Hunter)' },
    { id: 'CUST_0005', label: 'CUST_0005 (Social Advocate)' },
    { id: 'CUST_0016', label: 'CUST_0016 (At-Risk Lapsed)' }
  ];

  useEffect(() => {
    // Initial fetch of association rules and first customer recs
    Promise.all([
      api.getRecommendations(selectedCustomerId),
      api.getAssociationRules(25)
    ])
      .then(([recsData, rulesData]) => {
        setRecommendations(recsData.recommendations || []);
        setAssociationRules(rulesData || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading recommendations:', err);
        setLoading(false);
      });
  }, []);

  const handleFetchCustomerRecs = (cid) => {
    setSelectedCustomerId(cid);
    setRecsLoading(true);
    api.getRecommendations(cid)
      .then((data) => {
        setRecommendations(data.recommendations || []);
        setRecsLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching recs for customer:', err);
        setRecsLoading(false);
      });
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Loading Collaborative Filtering & Association Rules...</div>
        </div>
      </div>
    );
  }

  const getReasonBadge = (reasonType) => {
    switch (reasonType) {
      case 'association_rule':
        return <span className="badge badge-purple">Association Rule (Market Basket)</span>;
      case 'collaborative_peer':
        return <span className="badge badge-emerald">Collaborative Filtering (Peers)</span>;
      case 'browsing_intent':
        return <span className="badge badge-blue">Browsing Intent (Clickstream)</span>;
      case 'cluster_affinity':
        return <span className="badge badge-amber">Cluster Persona Affinity</span>;
      default:
        return <span className="badge badge-blue">Hybrid Model</span>;
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Explainable Personalized Recommendations</h1>
        <p className="page-subtitle">
          Multi-strategy recommendation engine combining User-Item Collaborative Filtering, Market Basket Association Rules, and Segment Behavioral Affinity.
        </p>
      </div>

      {/* Customer Selection Card */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Select Target Customer:</div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {sampleArchetypes.map((arch) => (
                <button
                  key={arch.id}
                  className={`btn ${selectedCustomerId === arch.id ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                  onClick={() => handleFetchCustomerRecs(arch.id)}
                >
                  {arch.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="e.g. CUST_0042"
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value.toUpperCase())}
              style={{
                padding: '0.45rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #334155',
                backgroundColor: '#0f172a',
                color: '#fff',
                fontSize: '0.875rem'
              }}
            />
            <button
              className="btn btn-secondary"
              onClick={() => handleFetchCustomerRecs(selectedCustomerId)}
            >
              Analyze
            </button>
          </div>
        </div>
      </div>

      {/* Recommendations Output Grid */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Sparkles size={20} color="#10b981" />
          <h2 style={{ fontSize: '1.2rem', fontWeight: '600', color: '#fff' }}>
            Top Tailored Recommendations for {selectedCustomerId}
          </h2>
        </div>

        {recsLoading ? (
          <div className="card loading-spinner">
            <div className="spinner"></div>
            <div>Evaluating Collaborative Similarity & Co-Purchases...</div>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
            No recommendations generated for this customer ID.
          </div>
        ) : (
          <div className="grid-3" style={{ gap: '1.25rem' }}>
            {recommendations.map((rec, idx) => (
              <div key={rec.product_id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span className="badge badge-blue">Rank #{idx + 1}</span>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#10b981' }}>
                      {rec.score}%
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Confidence Match</div>
                  </div>
                </div>

                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: '600', color: '#fff', marginBottom: '0.25rem' }}>
                    {rec.product_name}
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                    <Tag size={14} />
                    <span>{rec.category}</span>
                    <span>•</span>
                    <span style={{ fontWeight: '600', color: '#fff' }}>${rec.unit_price}</span>
                  </div>
                </div>

                <div>
                  {getReasonBadge(rec.reason_type)}
                </div>

                <div style={{
                  backgroundColor: '#0f172a',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #1e293b',
                  fontSize: '0.8rem',
                  color: '#93c5fd',
                  marginTop: 'auto',
                  lineHeight: '1.4'
                }}>
                  <div style={{ fontWeight: '600', color: '#38bdf8', marginBottom: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <BrainCircuit size={14} />
                    <span>Explainable Reasoning:</span>
                  </div>
                  {rec.explanation}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Market Basket Association Rules Mining Section */}
      <div className="card">
        <div className="card-title">
          <BrainCircuit size={20} color="#8b5cf6" />
          <span>Market Basket Association Rules (Mined from 12,214 Transactions)</span>
        </div>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.25rem' }}>
          High-confidence product co-occurrence patterns: Rule <code style={{ color: '#60a5fa' }}>A → B</code> indicates when a customer purchases item A, they are significantly more likely to purchase item B.
        </p>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Antecedent Item (A)</th>
                <th></th>
                <th>Consequent Item (B)</th>
                <th>Support</th>
                <th>Confidence</th>
                <th>Lift Multiplier</th>
                <th>Significance</th>
              </tr>
            </thead>
            <tbody>
              {associationRules.map((rule, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: '600', color: '#93c5fd' }}>{rule.antecedent}</td>
                  <td><ArrowRight size={14} color="#64748b" /></td>
                  <td style={{ fontWeight: '600', color: '#34d399' }}>{rule.consequent}</td>
                  <td>{(rule.support * 100).toFixed(2)}%</td>
                  <td>{(rule.confidence * 100).toFixed(1)}%</td>
                  <td>
                    <span style={{ fontWeight: '700', color: rule.lift > 1.0 ? '#10b981' : '#f59e0b' }}>
                      {rule.lift}x
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${rule.lift >= 1.0 ? 'badge-emerald' : 'badge-amber'}`}>
                      {rule.lift >= 1.0 ? 'High Affinity' : 'Moderate'}
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
