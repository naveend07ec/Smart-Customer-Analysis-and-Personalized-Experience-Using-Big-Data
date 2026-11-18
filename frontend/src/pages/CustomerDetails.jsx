import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Search, Filter, ChevronLeft, ChevronRight, User, ShoppingBag, Globe, Maximize2, Minimize2, X } from 'lucide-react';

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

  // Selected Customer 360 State & Layout Expansion
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetail, setCustomerDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  // Helper for richly colored segment badges
  const getSegmentBadge = (clusterName) => {
    const name = String(clusterName || '').toLowerCase();
    if (name.includes('vip') || name.includes('high-value')) {
      return <span className="badge badge-amber">{clusterName}</span>;
    }
    if (name.includes('bargain')) {
      return <span className="badge badge-teal">{clusterName}</span>;
    }
    if (name.includes('social') || name.includes('advocate')) {
      return <span className="badge badge-purple">{clusterName}</span>;
    }
    if (name.includes('risk') || name.includes('dissatisfied')) {
      return <span className="badge badge-rose">{clusterName}</span>;
    }
    return <span className="badge badge-blue">{clusterName}</span>;
  };

  // Load customer table list
  const loadCustomers = () => {
    setLoading(true);
    api.getCustomers({ page, pageSize: 15, search, segment, sortBy, sortDir })
      .then((res) => {
        const payload = res?.data || res || {};
        setCustomers(payload.customers || []);
        setTotalRecords(payload.total_records || 0);
        setTotalPages(payload.total_pages || 1);
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
    setCustomerDetail(null);
    setDetailLoading(true);
    api.getCustomerDetail(cid)
      .then((data) => {
        const payload = data?.data || data;
        if (payload && payload.profile) {
          setCustomerDetail(payload);
        } else {
          setCustomerDetail(null);
        }
        setDetailLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching customer detail:', err);
        setCustomerDetail(null);
        setDetailLoading(false);
      });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Customer 360 & Exploratory Directory</h1>
          <p className="page-subtitle">
            Search, filter, and inspect individual customer behavioral touchpoints across transactions, clickstreams, and social feedback.
          </p>
        </div>
      </div>

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
            <button type="submit" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>Search</button>
          </form>

          {/* Segment Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={15} color="var(--text-muted)" />
            <select
              value={segment}
              onChange={(e) => { setSegment(e.target.value); setPage(1); }}
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
      <div className={`customer-directory-grid ${selectedCustomer ? (isExpanded ? 'full-detail' : 'with-detail') : ''}`}>
        {/* Customer Table */}
        {(!isExpanded || !selectedCustomer) && (
          <div className="card" style={{ padding: '1.25rem', minWidth: 0, overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
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
                      <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        Loading customer records...
                      </td>
                    </tr>
                  ) : !customers || customers.length === 0 ? (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        No customers match your criteria.
                      </td>
                    </tr>
                  ) : (
                    customers.filter(c => c && c.customer_id).map((c) => (
                      <tr
                        key={c.customer_id}
                        style={{
                          backgroundColor: selectedCustomer === c.customer_id ? 'rgba(94, 143, 213, 0.08)' : 'transparent',
                          cursor: 'pointer'
                        }}
                        onClick={() => handleSelectCustomer(c.customer_id)}
                      >
                        <td style={{ fontWeight: '500', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{c.customer_id}</td>
                        <td>{getSegmentBadge(c.cluster_name)}</td>
                        <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                          ${Number(c.total_spend || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{c.total_transactions || 0}</td>
                        <td>${Number(c.avg_order_value || 0).toFixed(2)}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{c.recency_days ?? 0}d</td>
                        <td>
                          <span className={`badge ${Number(c.avg_sentiment_score || 0) >= 0 ? 'badge-sage' : 'badge-rose'}`}>
                            {Number(c.avg_sentiment_score || 0) > 0 ? `+${c.avg_sentiment_score}` : c.avg_sentiment_score}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Page {page} of {totalPages}
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  style={{ padding: '0.35rem 0.75rem', opacity: page <= 1 ? 0.4 : 1 }}
                >
                  <ChevronLeft size={15} /> Prev
                </button>
                <button
                  className="btn btn-secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  style={{ padding: '0.35rem 0.75rem', opacity: page >= totalPages ? 0.4 : 1 }}
                >
                  Next <ChevronRight size={15} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Customer 360 Detail View Pane */}
        {selectedCustomer && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', minWidth: 0, maxHeight: '880px', overflowY: 'auto' }}>
            {detailLoading || !customerDetail?.profile ? (
              <div className="loading-spinner">
                <div className="spinner"></div>
                <div>Fetching Customer 360 Profile...</div>
              </div>
            ) : (
              <>
                {/* Profile Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-color)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <User size={18} color="var(--text-primary)" />
                    </div>
                    <div>
                      <div style={{ fontSize: '1.15rem', fontWeight: '600', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                        {customerDetail.profile?.customer_id}
                      </div>
                      <div style={{ marginTop: '0.2rem' }}>
                        {getSegmentBadge(customerDetail.profile?.cluster_name)}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      onClick={() => setIsExpanded(!isExpanded)}
                      title={isExpanded ? "Split Screen" : "Expand Full Width"}
                    >
                      {isExpanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
                      <span>{isExpanded ? "Split" : "Expand"}</span>
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      onClick={() => {
                        setSelectedCustomer(null);
                        setCustomerDetail(null);
                        setIsExpanded(false);
                      }}
                      title="Close Customer 360"
                    >
                      <X size={13} />
                      <span>Close</span>
                    </button>
                  </div>
                </div>

                {/* RFM & Behavioral Stats Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '0.75rem' }}>
                  <div className="glass-sub-card" style={{ padding: '0.75rem 0.85rem', minWidth: 0 }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Total Lifetime Spend</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                      ${Number(customerDetail.profile?.total_spend || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="glass-sub-card" style={{ padding: '0.75rem 0.85rem', minWidth: 0 }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Recency (Lapse)</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                      {customerDetail.profile?.recency_days ?? 0} days
                    </div>
                  </div>
                  <div className="glass-sub-card" style={{ padding: '0.75rem 0.85rem', minWidth: 0 }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Web Touchpoints</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--accent-blue)', marginTop: '0.2rem' }}>
                      {customerDetail.profile?.total_web_activities || 0} actions
                    </div>
                  </div>
                  <div className="glass-sub-card" style={{ padding: '0.75rem 0.85rem', minWidth: 0 }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Social Sentiment</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: '600', color: Number(customerDetail.profile?.avg_sentiment_score || 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '0.2rem' }}>
                      {Number(customerDetail.profile?.avg_sentiment_score || 0) > 0 ? `+${customerDetail.profile?.avg_sentiment_score}` : customerDetail.profile?.avg_sentiment_score}
                    </div>
                  </div>
                </div>

                {/* Top Personalized Recommendations */}
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShoppingBag size={15} color="var(--accent-blue)" />
                    <span>Top Tailored Recommendations</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {(customerDetail.recommendations || []).slice(0, 3).map((r, i) => (
                      <div key={i} className="glass-sub-card" style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: '500', fontSize: '0.85rem', color: 'var(--text-primary)' }}>{r.product_name}</span>
                          <span className="badge badge-sage" style={{ flexShrink: 0 }}>{r.score}% Match</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>${r.unit_price}</span>
                          <span>•</span>
                          <span>{r.category}</span>
                        </div>
                        <div style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', marginTop: '0.35rem', fontStyle: 'italic', lineHeight: '1.35' }}>
                          "{r.explanation}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Transaction History */}
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShoppingBag size={15} color="var(--accent-teal)" />
                    <span>Purchase History ({(customerDetail.transactions || []).length})</span>
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
                        {(customerDetail.transactions || []).map((tx) => (
                          <tr key={tx.transaction_id}>
                            <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{tx.transaction_date?.slice(0, 10)}</td>
                            <td style={{ fontSize: '0.75rem', fontWeight: '500', color: 'var(--text-primary)' }}>{tx.product_name}</td>
                            <td style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-primary)' }}>${tx.total_amount}</td>
                            <td>
                              <span className={`badge ${tx.order_status === 'Completed' ? 'badge-sage' : 'badge-rose'}`} style={{ fontSize: '0.65rem' }}>
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
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Globe size={15} color="var(--accent-blue)" />
                    <span>Browsing Touchpoints ({(customerDetail.web_activity || []).length})</span>
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
                        {(customerDetail.web_activity || []).map((w, idx) => (
                          <tr key={w.activity_id || idx}>
                            <td>
                              <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>{w.action_type}</span>
                            </td>
                            <td style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{w.page_url}</td>
                            <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{w.duration_seconds}s</td>
                            <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{w.device_type}</td>
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
