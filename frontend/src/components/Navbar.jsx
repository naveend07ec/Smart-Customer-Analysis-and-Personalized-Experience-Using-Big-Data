import React from 'react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/analytics', label: 'Analytics' },
  { path: '/segmentation', label: 'Segmentation' },
  { path: '/customers', label: 'Customer 360' },
  { path: '/recommendations', label: 'Recommendations' },
  { path: '/churn', label: 'Retention AI' },
  { path: '/pipeline', label: 'Data Pipeline' },
];

export default function Navbar() {
  return (
    <header className="top-header-bar">
      {/* Left: Purple Gradient Orb + S M A R T Logo */}
      <NavLink to="/" className="dune-brand-logo" title="SMART Customer Analytics">
        <span className="brand-orb" />
        <span className="brand-text">S M A R T</span>
      </NavLink>

      {/* Center: Floating Pill Navigation Capsule */}
      <nav className="pill-nav-container">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `pill-nav-item ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
