import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Sparkles, BrainCircuit, ArrowRight, Tag, Award } from 'lucide-react';

export default function PersonalizedRecommendations() {
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [sampleArchetypes, setSampleArchetypes] = useState([]);
  const [customerNotFound, setCustomerNotFound] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [associationRules, setAssociationRules] = useState([]);
  const [rulesMetadata, setRulesMetadata] = useState(null);
  const [evaluationMetrics, setEvaluationMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recsLoading, setRecsLoading] = useState(false);

  const fetchCustomerRecs = (cid) => {
    if (!cid) return;
    setRecsLoading(true);
    setCustomerNotFound(null);
    api.getRecommendations(cid)
      .then((data) => {
        const recList = data?.top_recommendations || data?.recommendations || data?.data?.top_recommendations || [];
        setRecommendations(recList);
        setRecsLoading(false);
      })
      .catch((err) => {
        console.warn('Error fetching recs for customer:', err);
        setRecommendations([]);
        setCustomerNotFound(`Customer '${cid}' was not found in the active dataset.`);
        setRecsLoading(false);
      });
  };

  useEffect(() => {
    // 1. Fetch association rules and offline evaluation metrics independently
    api.getAssociationRules(50)
      .then((rulesData) => {
        const ruleList = Array.isArray(rulesData) ? rulesData : (rulesData?.data || []);
        const rulesMeta = rulesData?.metadata || null;
        setAssociationRules(ruleList);
        setRulesMetadata(rulesMeta);
      })
      .catch((err) => console.error('Error loading association rules:', err));

    api.getRecommendationEvaluation()
      .then((evalData) => {
        const evalList = Array.isArray(evalData) ? evalData : (evalData?.data || []);
        setEvaluationMetrics(evalList);
      })
      .catch((err) => console.error('Error loading evaluation metrics:', err));

    // 2. Fetch customers dynamically from the active dataset so quick-select archetypes match current data
    api.getCustomers({ page: 1, pageSize: 6 })
      .then((custRes) => {
        const custList = custRes?.customers || custRes?.data?.customers || [];
        if (custList.length > 0) {
          const archetypes = custList.slice(0, 5).map((c) => ({
            id: c.customer_id,
            label: `${c.customer_id} (${c.cluster_name ? c.cluster_name.split('&')[0].trim() : 'Cohort'})`
          }));
          setSampleArchetypes(archetypes);
          const firstId = custList[0].customer_id;
          setSelectedCustomerId(firstId);
          fetchCustomerRecs(firstId);
        } else {
          setSelectedCustomerId('CUST_0001');
          fetchCustomerRecs('CUST_0001');
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading active customers for recommendations:', err);
        setSelectedCustomerId('CUST_0001');
        fetchCustomerRecs('CUST_0001');
        setLoading(false);
      });
  }, []);

  const handleFetchCustomerRecs = (cid) => {
    setSelectedCustomerId(cid);
    fetchCustomerRecs(cid);
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div>Loading Recommendation Engine...</div>
        </div>
      </div>
    );
  }

  const getReasonBadge = (reasonType) => {
    switch (reasonType) {
      case 'association_rule':
        return <span className="badge badge-purple">Association Rule (Market Basket)</span>;
      case 'collaborative_peer':
        return <span className="badge badge-sage">Collaborative Filtering (Peers)</span>;
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
        <div>
          <h1 className="page-title">Explainable Personalized Recommendations</h1>
          <p className="page-subtitle">
            Multi-strategy recommendation engine combining User-Item Collaborative Filtering, Market Basket Association Rules, and Segment Behavioral Affinity.
          </p>
        </div>
      </div>

      {/* Offline Recommendation Model Evaluation Banner */}
      {evaluationMetrics && evaluationMetrics.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '3px solid var(--accent-blue)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Award size={17} color="var(--accent-blue)" />
              <span style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.9rem' }}>Recommender Offline Validation (Zero-Leakage 80/20 Holdout)</span>
            </div>
            <span className="badge badge-sage">Verified Zero-Leakage Protocol</span>
          </div>
          <div className="grid-4" style={{ gap: '0.75rem' }}>
            {evaluationMetrics.map((m, i) => (
              <div key={i} className="glass-sub-card" style={{ padding: '0.75rem' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{m.metric}</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)' }}>{m.value}</div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{m.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Customer Selection Card */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.45rem' }}>Select Target Customer:</div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {sampleArchetypes.map((arch) => (
                <button
                  key={arch.id}
                  className={`btn ${selectedCustomerId === arch.id ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '1rem' }}>
          <Sparkles size={17} color="var(--accent-blue)" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
            Top Tailored Recommendations for {selectedCustomerId}
          </h2>
        </div>

        {recsLoading ? (
          <div className="card loading-spinner">
            <div className="spinner"></div>
            <div>Evaluating Collaborative Similarity & Co-Purchases...</div>
          </div>
        ) : customerNotFound ? (
          <div className="card" style={{ padding: '1.5rem', borderLeft: '3px solid var(--accent-orange)' }}>
            <div style={{ color: 'var(--accent-orange)', fontWeight: '600', marginBottom: '0.35rem', fontSize: '0.9rem' }}>
              Customer Not Found in Active Dataset
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', lineHeight: '1.5' }}>
              {customerNotFound} Please select one of the active customer profiles from the quick-select list above or enter a valid ID from this dataset.
            </div>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
            No recommendations generated for this customer ID.
          </div>
        ) : (
          <div className="grid-3" style={{ gap: '1.25rem' }}>
            {recommendations.map((rec, idx) => (
              <div key={rec.product_id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span className="badge badge-purple">Rank #{idx + 1}</span>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--accent-green)' }}>
                      {rec.score} / 100
                    </div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Recommendation Score</div>
                  </div>
                </div>

                <div>
                  <h3 style={{ fontSize: '0.975rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                    {rec.product_name}
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    <Tag size={13} />
                    <span>{rec.category}</span>
                    <span>•</span>
                    <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>${rec.unit_price}</span>
                  </div>
                </div>

                <div>
                  {getReasonBadge(rec.reason_type)}
                </div>

                <div className="glass-sub-card" style={{
                  padding: '0.75rem',
                  fontSize: '0.78rem',
                  color: 'var(--text-primary)',
                  marginTop: 'auto',
                  lineHeight: '1.4'
                }}>
                  <div style={{ fontWeight: '600', color: 'var(--accent-blue)', marginBottom: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <BrainCircuit size={13} />
                    <span>Explainable Reasoning:</span>
                  </div>
                  <div style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                    "{rec.explanation}"
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Market Basket Association Rules Mining Section */}
      <div className="card">
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <BrainCircuit size={18} color="var(--accent-purple)" />
              <span>
                Market Basket Association Rules
                {rulesMetadata?.completed_transactions ? (
                  ` (Mined from ${Number(rulesMetadata.completed_transactions || 0).toLocaleString()} Completed Transactions across ${Number(rulesMetadata.multi_item_baskets || 0).toLocaleString()} Customer Baskets)`
                ) : (
                  ''
                )}
              </span>
            </div>
            {rulesMetadata && (
              <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.72rem' }}>
                <span className="badge badge-purple">Version: {rulesMetadata.dataset_version}</span>
                <span className="badge badge-sage">Min Support: {rulesMetadata.min_support}</span>
                <span className="badge badge-blue">Min Lift: {rulesMetadata.min_lift}x</span>
              </div>
            )}
          </div>
        </div>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          High-confidence product co-occurrence patterns: Rule <code style={{ color: 'var(--accent-blue)', background: 'var(--bg-secondary)', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>A → B</code> indicates when a customer purchases item A, they are significantly more likely to purchase item B.
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
              {associationRules.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)' }}>
                    No market basket association rules generated for this dataset.
                  </td>
                </tr>
              ) : (
                associationRules.map((rule, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: '500', color: 'var(--accent-blue)' }}>{rule.antecedent}</td>
                    <td><ArrowRight size={13} color="var(--text-muted)" /></td>
                    <td style={{ fontWeight: '500', color: 'var(--accent-teal)' }}>{rule.consequent}</td>
                    <td>{(rule.support * 100).toFixed(2)}%</td>
                    <td>{(rule.confidence * 100).toFixed(1)}%</td>
                    <td>
                      <span style={{ fontWeight: '600', color: rule.lift > 1.0 ? 'var(--accent-green)' : 'var(--accent-orange)' }}>
                        {rule.lift}x
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${rule.lift >= 1.0 ? 'badge-sage' : 'badge-amber'}`}>
                        {rule.lift >= 1.0 ? 'High Affinity' : 'Moderate'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
