import React, { useState, useEffect } from 'react';
import { motion, useScroll, useSpring, useTransform } from 'framer-motion';
import { 
  Zap, 
  Cpu, 
  Search, 
  Users, 
  Target, 
  Activity, 
  Shield,
  TrendingUp,
  Globe,
  BarChart3,
  ArrowUpRight,
  MousePointer2
} from 'lucide-react';
import KPIWidget from './KPIWidget';
import { 
  MultiMetricTrendChart, 
  TrafficSourceChart, 
  ComparativePerformanceChart, 
  CumulativeGrowthChart, 
  GeographicEngagementChart, 
  PerformanceGauge 
} from './AnalyticsCharts';

const OverviewDashboard = ({ data, kpis, onBotAction, setIsScrapeModalOpen }) => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [timeRange, setTimeRange] = useState('7d');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [refreshCountdown, setRefreshCountdown] = useState(60);

  const { scrollYProgress } = useScroll();
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });
  
  // Parallax transforms for sections
  const y1 = useTransform(scrollYProgress, [0, 1], [0, -50]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, 50]);
  const opacity = useTransform(scrollYProgress, [0, 0.05, 0.95, 1], [1, 1, 1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.1], [0.98, 1]);

  // 60-second real-time refresh interval
  useEffect(() => {
    const timer = setInterval(() => {
      setRefreshCountdown((prev) => {
        if (prev <= 1) {
          setLastUpdated(new Date());
          // In a real app, this would trigger a data re-fetch
          return 60;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleMouseMove = (e) => {
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;
    const x = (clientX / innerWidth - 0.5) * 20;
    const y = (clientY / innerHeight - 0.5) * 20;
    setMousePosition({ x, y });
  };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <motion.div 
      style={{ opacity, scale }}
      className="space-y-[var(--s-10)] pb-[var(--s-20)] px-[var(--s-4)] overflow-x-hidden relative"
    >
      {/* Scroll Progress Indicator */}
      <motion.div 
        className="fixed top-0 left-0 right-0 h-1 bg-[var(--brand)] z-[100] origin-left"
        style={{ scaleX: smoothProgress }}
      />

      {/* Background Decorative 3D elements (Abstract) */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <motion.div 
          animate={{ 
            rotate: [0, 360],
            x: [0, 100, 0],
            y: [0, -50, 0]
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          className="absolute -top-20 -left-20 w-[500px] h-[500px] bg-[var(--brand)] rounded-full blur-[150px] opacity-[0.07]"
          style={{ y: y1 }}
        />
        <motion.div 
          animate={{ 
            rotate: [360, 0],
            x: [0, -100, 0],
            y: [0, 50, 0]
          }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
          className="absolute -bottom-20 -right-20 w-[500px] h-[500px] bg-[var(--purple)] rounded-full blur-[150px] opacity-[0.07]"
          style={{ y: y2 }}
        />

        {/* Floating 3D Nodes */}
        <motion.div 
          style={{ x: mousePosition.x * 2, y: mousePosition.y * 2 + 100, rotateZ: 15 }}
          animate={{ y: [100, 120, 100] }}
          transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[20%] right-[10%] p-6 clay-card opacity-20 blur-[1px] rotate-12"
        >
          <Cpu size={40} className="text-[var(--brand)]" />
        </motion.div>

        <motion.div 
          style={{ x: mousePosition.x * -3, y: mousePosition.y * -3 + 400, rotateZ: -10 }}
          animate={{ y: [400, 380, 400] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[50%] left-[5%] p-4 clay-card opacity-15 blur-[2px] -rotate-12"
        >
          <Zap size={30} className="text-[var(--accent)]" />
        </motion.div>

        <motion.div 
          style={{ x: mousePosition.x * 1.5, y: mousePosition.y * 1.5 + 700, rotateZ: 5 }}
          animate={{ y: [700, 730, 700] }}
          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[80%] right-[15%] p-8 clay-card opacity-10 blur-[3px] rotate-6"
        >
          <Globe size={50} className="text-[var(--purple)]" />
        </motion.div>
      </div>
      
      {/* 1. Critical Real-Time Metrics & Performance Benchmarks */}
      <motion.section 
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        className="space-y-[var(--s-6)] relative"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-[var(--fs-lg)] font-black uppercase tracking-[0.3em] text-[var(--brand)] flex items-center gap-3">
              <Activity size={24} className="animate-pulse" />
              Neural Pulse Monitor
            </h2>
            <p className="text-[var(--fs-xs)] text-[var(--muted)] font-bold mt-1">Live telemetry nodes refreshing in {refreshCountdown}s</p>
          </div>
          
          <div className="flex items-center gap-4 bg-black/20 p-2 pl-4 rounded-full border border-white/5 shadow-inner backdrop-blur-md">
            <div className="flex flex-col items-end">
              <span className="text-[9px] font-black uppercase text-[var(--muted)] tracking-widest">Last Sync</span>
              <span className="text-[10px] font-bold text-[var(--ink)]">{lastUpdated.toLocaleTimeString()}</span>
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div className="flex items-center gap-2 pr-2">
              <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse shadow-[0_0_8px_var(--success)]" />
              <span className="text-[10px] font-black uppercase text-[var(--success)] tracking-widest">System Optimal</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[var(--s-6)]">
          {[
            { value: data?.system?.cpu_usage || 42, label: "Neural CPU", color: "var(--brand)", icon: <Cpu /> },
            { value: data?.system?.uptime_score || 99, label: "Core Uptime", color: "var(--success)", icon: <Shield /> },
            { value: data?.system?.vitals_score || 85, label: "Web Vitals", color: "var(--accent)", icon: <Zap /> },
            { value: data?.system?.active_users_threshold || 64, label: "Active Nodes", color: "var(--purple)", icon: <Users /> }
          ].map((gauge, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ 
                scale: 1.05, 
                rotateY: mousePosition.x * 0.4, 
                rotateX: -mousePosition.y * 0.4,
                translateZ: 20
              }}
              className="clay-card p-[var(--s-6)] h-[240px] relative group cursor-pointer"
            >
              <PerformanceGauge value={gauge.value} label={gauge.label} color={gauge.color} />
              <div className="absolute top-4 right-4 opacity-10 group-hover:opacity-40 transition-all duration-500 group-hover:scale-125 group-hover:rotate-12">
                {React.cloneElement(gauge.icon, { size: 48 })}
              </div>
              <div className="nn-tooltip">View Granular {gauge.label} Logs</div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-[var(--s-6)]">
          {kpis.map((kpi, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 + i * 0.1 }}
            >
              <KPIWidget {...kpi} />
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* 2. Historical Trend Analysis & Growth Visualization */}
      <motion.section 
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        className="space-y-[var(--s-6)]"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-[var(--fs-lg)] font-black uppercase tracking-[0.3em] text-[var(--ink)] flex items-center gap-3">
              <TrendingUp size={24} className="text-[var(--brand)]" />
              Longitudinal Growth
            </h2>
            <p className="text-[var(--fs-xs)] text-[var(--muted)] font-bold mt-1">Multi-metric performance vectors across time-space</p>
          </div>
          <div className="flex bg-black/20 p-1 rounded-full border border-white/5 shadow-inner self-start md:self-center">
            {['7d', '30d', '90d'].map(range => (
              <button 
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-6 py-2 rounded-full text-[10px] font-black uppercase tracking-widest transition-all duration-300 ${timeRange === range ? 'bg-[var(--brand)] text-white shadow-[0_8px_24px_var(--brand-glow)] scale-105' : 'text-[var(--muted)] hover:text-[var(--ink)]'}`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-[var(--s-8)]">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            whileHover={{ translateZ: 10 }}
            className="lg:col-span-8 clay-card p-[var(--s-8)] min-h-[480px] flex flex-col group"
          >
            <div className="flex items-center justify-between mb-[var(--s-8)]">
              <div>
                <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)]">Neural Engagement Velocity</h3>
                <div className="flex items-center gap-4 mt-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[var(--brand)] shadow-[0_0_8px_var(--brand)]" />
                    <span className="text-[9px] font-black text-[var(--muted)] uppercase tracking-tighter">Sessions</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[var(--purple)] shadow-[0_0_8px_var(--purple)]" />
                    <span className="text-[9px] font-black text-[var(--muted)] uppercase tracking-tighter">Conversions</span>
                  </div>
                </div>
              </div>
              <div className="p-3 bg-black/20 rounded-[var(--r-md)] border border-white/5 opacity-0 group-hover:opacity-100 transition-opacity">
                <BarChart3 size={18} className="text-[var(--brand)]" />
              </div>
            </div>
            <div className="flex-1">
              <MultiMetricTrendChart data={data?.trends} timeRange={timeRange} />
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            whileHover={{ translateZ: 10 }}
            className="lg:col-span-4 clay-card p-[var(--s-8)] min-h-[480px] flex flex-col group"
          >
            <div className="flex items-center justify-between mb-[var(--s-8)]">
              <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)]">Cumulative User Base</h3>
              <div className="p-3 bg-black/20 rounded-[var(--r-md)] border border-white/5 opacity-0 group-hover:opacity-100 transition-opacity">
                <Users size={18} className="text-[var(--success)]" />
              </div>
            </div>
            <div className="flex-1">
              <CumulativeGrowthChart data={data?.growth} />
            </div>
            <div className="mt-[var(--s-6)] pt-[var(--s-6)] border-t border-[var(--line)] flex items-center justify-between">
              <div>
                <p className="text-[10px] font-black text(--muted)] uppercase tracking-widest">Lifetime Value Accumulation</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[var(--fs-sm)] font-black text-[var(--success)]">$142,850.00</span>
                  <span className="text-[9px] font-bold text-[var(--success)] flex items-center bg-[var(--success)]/10 px-1.5 py-0.5 rounded-full">
                    <ArrowUpRight size={10} />
                    12.4%
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* 3. Segment-Specific Breakdowns & Geographic Distribution */}
      <motion.section 
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        className="space-y-[var(--s-6)]"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[var(--fs-lg)] font-black uppercase tracking-[0.3em] text-[var(--ink)] flex items-center gap-3">
              <Target size={24} className="text-[var(--accent)]" />
              Segmentation Matrix
            </h2>
            <p className="text-[var(--fs-xs)] text-[var(--muted)] font-bold mt-1">Regional density and traffic source attribution nodes</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-[var(--s-8)]">
          {[
            { title: "Traffic Attribution", component: <TrafficSourceChart data={data?.sources} />, delay: 0 },
            { title: "MoM Benchmarks", component: <ComparativePerformanceChart data={data?.benchmarks} />, delay: 0.1 },
            { title: "Engagement Density", component: <GeographicEngagementChart data={data?.geo_density} />, delay: 0.2 }
          ].map((segment, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: segment.delay }}
              whileHover={{ 
                translateZ: 15,
                rotateY: i === 0 ? 2 : i === 2 ? -2 : 0
              }}
              className="clay-card p-[var(--s-8)] h-[420px] flex flex-col group relative"
            >
              <div className="flex items-center justify-between mb-[var(--s-8)]">
                <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)]">{segment.title}</h3>
                <div className="w-8 h-8 rounded-full bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <MousePointer2 size={14} className="text-[var(--muted)]" />
                </div>
              </div>
              <div className="flex-1 min-h-0">
                {segment.component}
              </div>
              <div className="nn-tooltip">Interact with {segment.title} Node</div>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* 4. AI Insights Banner */}
      <motion.div 
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-50px" }}
        className="clay-card p-[var(--s-10)] bg-gradient-to-br from-[var(--brand)]/10 via-[var(--bg-alt)] to-[var(--purple)]/10 relative group overflow-hidden border-2 border-[var(--brand)]/20"
      >
        <div className="absolute top-0 right-0 p-[var(--s-10)] opacity-[0.05] group-hover:opacity-[0.1] transition-all duration-1000 group-hover:rotate-12 group-hover:scale-125">
          <Cpu size={240} />
        </div>
        
        <div className="relative z-10 space-y-[var(--s-6)]">
          <div className="flex items-center gap-[var(--s-4)]">
            <div className="p-3 bg-[var(--brand)]/20 rounded-2xl border border-[var(--brand)]/30 shadow-[0_0_20px_var(--brand-glow)]">
              <Zap className="text-[var(--brand)] animate-pulse" size={24} />
            </div>
            <div>
              <h2 className="text-[var(--fs-xl)] font-black uppercase tracking-widest text-[var(--ink)]">Neural Strategy Node</h2>
              <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-tighter mt-1">AI-generated growth vector analysis</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-8)] pt-[var(--s-4)]">
            <div className="p-[var(--s-6)] bg-black/20 rounded-[var(--r-md)] border border-white/5 backdrop-blur-md clay-card">
              <h4 className="text-[10px] font-black uppercase text-[var(--brand)] tracking-widest mb-2 flex items-center gap-2">
                <Target size={12} />
                Conversion Optimization
              </h4>
              <p className="text-[var(--fs-sm)] text-[var(--ink-dim)] leading-relaxed font-medium">
                Detected 14% friction in checkout node on mobile viewports. Recommending neural-path simplification for high-intent traffic clusters.
              </p>
            </div>
            <div className="p-[var(--s-6)] bg-black/20 rounded-[var(--r-md)] border border-white/5 backdrop-blur-md clay-card">
              <h4 className="text-[10px] font-black uppercase text-[var(--purple)] tracking-widest mb-2 flex items-center gap-2">
                <Globe size={12} />
                Regional Expansion
              </h4>
              <p className="text-[var(--fs-sm)] text-[var(--ink-dim)] leading-relaxed font-medium">
                Emerging engagement cluster identified in Northern Europe. Growth velocity indicates 3.2x higher conversion probability with localized outreach.
              </p>
            </div>
          </div>

          <div className="pt-[var(--s-8)] border-t border-[var(--line)] flex flex-wrap gap-[var(--s-6)] items-center justify-between">
            <div className="flex items-center gap-[var(--s-4)]">
              <button 
                onClick={() => setIsScrapeModalOpen(true)}
                className="btn-primary px-[var(--s-8)] py-[var(--s-4)] text-[var(--fs-xs)] uppercase tracking-[0.2em] font-black flex items-center gap-3"
              >
                <Search size={18} />
                Establish New Link
              </button>
              <button className="px-[var(--s-8)] py-[var(--s-4)] clay-card bg-black/30 text-[var(--muted)] font-black text-[var(--fs-xs)] uppercase tracking-[0.2em] hover:text-[var(--ink)] transition-colors">
                View Full Audit
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default OverviewDashboard;
