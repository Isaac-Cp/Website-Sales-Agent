import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

const KPIWidget = ({ label, value, change, icon: Icon, color, trend }) => {
  const [mousePosition, setMousePosition] = React.useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setMousePosition({ x, y });
  };

  const trendLabel = trend === 'up' ? 'UP' : trend === 'down' ? 'DOWN' : 'INFO';
  const description = {
    'Total Leads': 'Accumulated potential business signals',
    'Emails Sent': 'Outbound transmission volume',
    'Replies': 'Engagement and response quality',
    'Conversions': 'Successful acquisition signals'
  }[label] || 'Neural metric tracking';

  return (
    <motion.div
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setMousePosition({ x: 0, y: 0 })}
      whileHover={{ 
        y: -8, 
        scale: 1.05,
        rotateX: -mousePosition.y * 20,
        rotateY: mousePosition.x * 20
      }}
      style={{ transformStyle: 'preserve-3d' }}
      className="clay-card p-[var(--s-6)] group flex flex-col justify-between relative overflow-hidden has-tooltip cursor-pointer"
    >
      <span className="nn-tooltip">{description}</span>
      
      {/* Dynamic 3D Glow */}
      <div
        className="absolute h-40 w-40 blur-[50px] opacity-10 transition-opacity duration-500 group-hover:opacity-20 pointer-events-none"
        style={{ 
          backgroundColor: color,
          left: `calc(50% + ${mousePosition.x * 100}%)`,
          top: `calc(50% + ${mousePosition.y * 100}%)`,
          transform: 'translate(-50%, -50%) translateZ(-10px)'
        }}
      />
      
      <div className="relative z-10 flex items-start justify-between mb-[var(--s-6)]" style={{ transform: 'translateZ(30px)' }}>
        <div 
          className="flex h-[var(--s-12)] w-[var(--s-12)] items-center justify-center rounded-[var(--r-md)] border shadow-lg transition-all duration-500 group-hover:scale-110 group-hover:rotate-12"
          style={{ 
            backgroundColor: `${color}15`, 
            borderColor: `${color}40`, 
            color: color,
            boxShadow: `0 8px 16px ${color}20`
          }}
        >
          <Icon size={24} />
        </div>
        <div className={`flex items-center gap-[var(--s-1)] rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-widest ${
          trend === 'up' ? 'bg-[var(--success)]/10 text-[var(--success)]' : 
          trend === 'down' ? 'bg-[var(--error)]/10 text-[var(--error)]' : 
          'bg-[var(--brand)]/10 text-[var(--brand)]'
        } border border-current/10 shadow-sm`}>
          {trend === 'up' ? <TrendingUp size={12} /> : trend === 'down' ? <TrendingDown size={12} /> : null}
          {change}%
        </div>
      </div>

      <div className="relative z-10" style={{ transform: 'translateZ(20px)' }}>
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--muted)] mb-1.5 opacity-80">{label}</p>
        <h3 className="text-[var(--fs-xl)] font-black tracking-tighter text-[var(--ink)] leading-[var(--lh-tight)]">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </h3>
      </div>

      {/* 3D Depth Decoration */}
      <div 
        className="absolute -bottom-2 -right-2 opacity-[0.03] group-hover:opacity-[0.08] transition-all duration-700 pointer-events-none"
        style={{ transform: 'translateZ(-20px)' }}
      >
        <Icon size={80} />
      </div>
    </motion.div>
  );
};

export default KPIWidget;
