import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, User, ShoppingBag, Globe, MessageSquare } from 'lucide-react';

export default function CustomerDetails() {
  const [customers, setCustomers] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('all');
  const [sortBy, setSortBy] = useState('total_spend');
  const [sortDir, setSortDir] = useState('desc');
  const [loading, setLoading] = useState(true);

  // Selected Customer 360 State
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetail, setCustomerDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load customer table list
  const loadCustomers = () => {
    setLoading(true);
    api.getCustomers({ page, pageSize: 15, search, segment, sortBy, sortDir })
      .then((res) => {
        setCustomers(res.customers);
        setTotalRecords(res.total_records);
        setTotalPages(res.total_pages);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching customers:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadCustomers();
  }, [page, segment, sortBy, sortDir]);

  // Handle Search submit
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadCustomers();
  };

  // Load individual customer 360 detail
  const handleSelectCustomer = (cid) => {
    setSelectedCustomer(cid);
    setDetailLoading(true);
    api.getCustomerDetail(cid)
      .then((data) => {
        setCustomerDetail(data);
        setDetailLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching customer detail:', err);
        setDetailLoading(false);
      });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Customer 360 & Exploratory Directory</h1>
        <p className="page-subtitle">
          Search, filter, and inspect individual customer behavioral touchpoints across transactions, clickstreams, and social feedback.
        </p>
      </div>

      {/* Search and Filters Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '260px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="Search by Customer ID (e.g. CUST_0001)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.55rem 1rem 0.55rem 2.25rem',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  backgroundColor: '#0f172a',
                  color: '#fff',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            <button type="submit" className="btn btn-primary">Search</button>
          </form>

          {/* Segment Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={16} color="#94a3b8" />
            <select
              value={segment}
              onChange={(e) => { setSegment(e.target.value); setPage(1); }}
              style={{
                padding: '0.55rem 1rem',
                borderRadius: '8px',
                border: '1px solid #334155',
                backgroundColor: '#0f172a',
                color: '#fff',
                fontSize: '0.875rem'
              }}
            >
              <option value="all">All Segments</option>
              <option value="High-Value VIP Tech Spenders">High-Value VIP Tech Spenders</option>
              <option value="Active Bargain Hunters">Active Bargain Hunters</option>
              <option value="Casual Occasional Shoppers">Casual Occasional Shoppers</option>
              <option value="Social Brand Advocates">Social Brand Advocates</option>
              <option value="At-Risk / Dissatisfied Customers">At-Risk / Dissatisfied Customers</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Grid: Customer Table + Customer 360 Detail Card */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedCustomer ? '1fr 480px' : '1fr', gap: '1.5rem' }}>
        {/* Customer Table */}
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
              Showing {customers.length} of {totalRecords} customers
            </span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th>Segment Persona</th>
                  <th>Spend ($)</th>
                  <th>Orders</th>
                  <th>AOV</th>
                  <th>Recency</th>
                  <th>Sentiment</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                      Loading customer records...
                    </td>
                  </tr>
                ) : customers.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                      No customers match your criteria.
                    </td>
                  </tr>
                ) : (
                  customers.map((c) => (
                    <tr
                      key={c.customer_id}
                      style={{
                        backgroundColor: selectedCustomer === c.customer_id ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                        cursor: 'pointer'
                      }}
                      onClick={() => handleSelectCustomer(c.customer_id)}
                    >
                      <td style={{ fontWeight: '600', color: '#38bdf8' }}>{c.customer_id}</td>
                      <td>
                        <span className="badge badge-blue">{c.cluster_name}</span>
                      </td>
                      <td style={{ fontWeight: '600' }}>${c.total_spend.toLocaleString()}</td>
                      <td>{c.total_transactions}</td>
                      <td>${c.avg_order_value}</td>
                      <td>{c.recency_days}d</td>
                      <td>
                        <span className={`badge ${c.avg_sentiment_score >= 0 ? 'badge-emerald' : 'badge-rose'}`}>
                          {c.avg_sentiment_score > 0 ? `+${c.avg_sentiment_score}` : c.avg_sentiment_score}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                          onClick={(e) => { e.stopPropagation(); handleSelectCustomer(c.customer_id); }}
                        >
                          View 360°
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Page {page} of {totalPages}
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                style={{ padding: '0.4rem 0.75rem', opacity: page <= 1 ? 0.4 : 1 }}
              >
                <ChevronLeft size={16} /> Prev
              </button>
              <button
                className="btn btn-secondary"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                style={{ padding: '0.4rem 0.75rem', opacity: page >= totalPages ? 0.4 : 1 }}
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Customer 360 Detail View Pane */}
        {selectedCustomer && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxHeight: '820px', overflowY: 'auto' }}>
            {detailLoading || !customerDetail ? (
              <div className="loading-spinner">
                <div className="spinner"></div>
                <div>Fetching Customer 360 Profile...</div>
              </div>
            ) : (
              <>
                {/* Profile Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #334155', paddingBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <User size={22} color="#fff" />
                    </div>
                    <div>
                      <div style={{ fontSize: '1.2rem', fontWeight: '700', color: '#fff' }}>
                        {customerDetail.profile.customer_id}
                      </div>
                      <div className="badge badge-emerald" style={{ marginTop: '0.2rem' }}>
                        {customerDetail.profile.cluster_name}
                      </div>
                    </div>
                  </div>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                    onClick={() => setSelectedCustomer(null)}
                  >
                    Close
                  </button>
                </div>

                {/* RFM & Behavioral Stats Grid */}
                <div className="grid-2">
                  <div style={{ backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Total Lifetime Spend</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#10b981' }}>
                      ${customerDetail.profile.total_spend?.toLocaleString()}
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Recency (Lapse)</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f59e0b' }}>
                      {customerDetail.profile.recency_days} days
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Web Touchpoints</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#38bdf8' }}>
                      {customerDetail.profile.total_web_activities} actions
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Social Sentiment</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#a78bfa' }}>
                      {customerDetail.profile.avg_sentiment_score > 0 ? `+${customerDetail.profile.avg_sentiment_score}` : customerDetail.profile.avg_sentiment_score}
                    </div>
                  </div>
                </div>

                {/* Top Personalized Recommendations */}
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: '600', color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShoppingBag size={16} color="#10b981" />
                    <span>Top Tailored Recommendations</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {customerDetail.recommendations.slice(0, 3).map((r, i) => (
                      <div key={i} style={{ backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: '600', fontSize: '0.85rem', color: '#fff' }}>{r.product_name}</span>
                          <span className="badge badge-emerald">{r.score}% Match</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                          ${r.unit_price} • {r.category}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#38bdf8', marginTop: '0.35rem', fontStyle: 'italic' }}>
                          "{r.explanation}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Transaction History */}
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: '600', color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShoppingBag size={16} color="#3b82f6" />
                    <span>Purchase History ({customerDetail.transactions.length})</span>
                  </div>
                  <div className="table-container" style={{ maxHeight: '180px' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Product</th>
                          <th>Amount</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customerDetail.transactions.map((tx) => (
                          <tr key={tx.transaction_id}>
                            <td style={{ fontSize: '0.75rem' }}>{tx.transaction_date?.slice(0, 10)}</td>
                            <td style={{ fontSize: '0.75rem' }}>{tx.product_name}</td>
                            <td style={{ fontSize: '0.75rem', fontWeight: '600' }}>${tx.total_amount}</td>
                            <td>
                              <span className={`badge ${tx.order_status === 'Completed' ? 'badge-emerald' : 'badge-rose'}`} style={{ fontSize: '0.65rem' }}>
                                {tx.order_status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Recent Clickstream Events */}
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: '600', color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Globe size={16} color="#06b6d4" />
                    <span>Browsing Touchpoints ({customerDetail.web_activity.length})</span>
                  </div>
                  <div className="table-container" style={{ maxHeight: '160px' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Action</th>
                          <th>Page Path</th>
                          <th>Dwell</th>
                          <th>Device</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customerDetail.web_activity.map((w) => (
                          <tr key={w.activity_id}>
                            <td>
                              <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>{w.action_type}</span>
                            </td>
                            <td style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{w.page_url}</td>
                            <td style={{ fontSize: '0.75rem' }}>{w.duration_seconds}s</td>
                            <td style={{ fontSize: '0.75rem' }}>{w.device_type}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
