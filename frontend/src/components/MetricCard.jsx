import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  badgeText,
  badgeColor = 'blue',
  isHero = false,
  trend = '+17%',
  icon: Icon
}) {
  const badgeClass = `badge badge-${badgeColor}`;

  if (isHero) {
    return (
      <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
              {title}
            </span>
            {Icon && <Icon size={16} color="var(--accent-blue)" />}
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '1.95rem', fontWeight: '600', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              {value}
            </span>
            {trend && (
              <span className="badge badge-sage">
                {trend}
              </span>
            )}
          </div>
          {subtitle && (
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {subtitle}
            </div>
          )}
        </div>

        {/* Apple-style restrained sparkline */}
        <div style={{ height: '36px', width: '100%', marginTop: '0.75rem' }}>
          <svg viewBox="0 0 100 30" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
            <path
              d="M0,22 Q15,10 30,18 T60,12 T85,6 T100,16"
              fill="none"
              stroke="var(--accent-blue)"
              strokeWidth="1.75"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
            {title}
          </span>
          {Icon && <Icon size={16} color="var(--text-secondary)" />}
        </div>
        <div style={{ fontSize: '1.75rem', fontWeight: '600', color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '0.35rem' }}>
          {value}
        </div>
        {subtitle && (
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            {subtitle}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
        {badgeText ? (
          <span className={badgeClass}>{badgeText}</span>
        ) : (
          <div style={{ width: '48px', height: '16px' }}>
            <svg viewBox="0 0 48 16" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
              <path
                d="M0,12 Q12,4 24,10 T48,3"
                fill="none"
                stroke="var(--accent-blue)"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        )}

        {trend && (
          <div style={{ fontSize: '0.74rem', fontWeight: '500', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <span>↑</span>
            <span>{trend}</span>
          </div>
        )}
      </div>
    </div>
  );
}
