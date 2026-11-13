import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart3,
  PieChart,
  Users,
  Sparkles,
  Database,
  Layers
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Overview Dashboard', icon: LayoutDashboard },
  { path: '/analytics', label: 'Customer Analytics', icon: BarChart3 },
  { path: '/segmentation', label: 'Customer Segmentation', icon: PieChart },
  { path: '/customers', label: 'Customer Details', icon: Users },
  { path: '/recommendations', label: 'Personalized Recommendations', icon: Sparkles },
  { path: '/pipeline', label: 'Data Integration & Spark', icon: Database },
];

export default function Sidebar() {
  return (
    <aside style={{
      width: '260px',
      backgroundColor: '#0f172a',
      borderRight: '1px solid #1e293b',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '1.5rem',
        borderBottom: '1px solid #1e293b',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem'
      }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
        }}>
          <Layers size={22} color="#fff" />
        </div>
        <div>
          <div style={{ fontWeight: '700', fontSize: '1rem', color: '#fff', letterSpacing: '-0.01em' }}>
            SmartAnalytics
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Big Data & ML Platform
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav style={{ padding: '1rem 0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.7rem 1rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: isActive ? '600' : '500',
                textDecoration: 'none',
                color: isActive ? '#fff' : '#94a3b8',
                backgroundColor: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                transition: 'all 0.15s ease'
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div style={{
        padding: '1.25rem',
        borderTop: '1px solid #1e293b',
        fontSize: '0.75rem',
        color: '#64748b'
      }}>
        <div style={{ fontWeight: '600', color: '#94a3b8', marginBottom: '0.25rem' }}>
          Final-Year Academic Project
        </div>
        <div>PySpark 3.5 • Scikit-Learn • Flask • React</div>
      </div>
    </aside>
  );
}
