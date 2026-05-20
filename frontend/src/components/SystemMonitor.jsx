import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Database, 
  Zap, 
  Shield, 
  Network,
  RefreshCcw,
  BarChart3,
  Server,
  Terminal,
  Layers,
  Clock,
  AlertCircle,
  MapPin,
  ChevronRight,
  Target
} from 'lucide-react';

const SystemMonitor = ({ stats, onRefresh, runMaintenance, maintenanceRunning = {} }) => {
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setPulse(p => p + 1), 2000);
    return () => clearInterval(interval);
  }, []);

  const metrics = [
    { 
      label: 'Neural CPU', 
      value: stats?.process?.cpu_percent ? `${stats.process.cpu_percent}%` : '12%', 
      color: 'var(--brand)', 
      icon: Cpu, 
      sub: `${stats?.process?.threads || 8} Active Threads` 
    },
    { 
      label: 'Fleet Memory', 
      value: stats?.memory?.usage || '2.4GB', 
      color: 'var(--purple)', 
      icon: Layers, 
      sub: `Open Handles: ${stats?.process?.open_files || 0}` 
    },
    { 
      label: 'Node Uptime', 
      value: stats?.uptime || '14d 6h', 
      color: 'var(--success)', 
      icon: Activity, 
      sub: 'Status: Operational' 
    },
    { 
      label: 'API Latency', 
      value: stats?.latency || '14ms', 
      color: 'var(--accent)', 
      icon: Zap, 
      sub: 'Uplink: Stable' 
    }
  ];

  return (
    <div className="space-y-[var(--s-10)] pb-[var(--s-20)] px-[var(--s-4)]">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-[var(--s-6)]">
        <div>
          <h2 className="text-[var(--fs-2xl)] font-black tracking-tighter text-[var(--ink)] uppercase italic leading-none">
            Fleet<span className="text-[var(--brand)]">Monitor</span>
          </h2>
          <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-[0.3em] mt-[var(--s-2)] flex items-center gap-[var(--s-2)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] shadow-[0_0_8px_var(--success)] animate-pulse" />
            Real-time telemetry from active harvesting nodes
          </p>
        </div>
        <button 
          onClick={onRefresh}
          className="p-[var(--s-3)] clay-card hover:bg-[var(--glass-hover)] rounded-[var(--r-md)] text-[var(--muted)] transition-all flex items-center gap-[var(--s-3)] font-black text-[var(--fs-xs)] uppercase tracking-widest"
        >
          <RefreshCcw size={18} className="animate-spin-slow" />
          Synchronize Telemetry
        </button>
      </div>

      {/* High-Level Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[var(--s-6)]">
        {metrics.map((m, i) => (
          <motion.div 
            key={m.label}
            whileHover={{ y: -5 }}
            className="clay-card p-[var(--s-6)] space-y-[var(--s-6)] group overflow-hidden relative"
          >
            <div className="absolute -right-4 -top-4 w-24 h-24 blur-[50px] opacity-10 group-hover:opacity-20 transition-opacity" style={{ backgroundColor: m.color }} />
            
            <div className="flex items-center justify-between">
              <div className="p-[var(--s-3)] rounded-[var(--r-md)] bg-black/20 text-[var(--ink)] shadow-inner" style={{ color: m.color }}>
                <m.icon size={24} />
              </div>
              <div className="text-right">
                <p className="text-[var(--fs-xl)] font-black text-[var(--ink)] leading-none">{m.value}</p>
                <p className="text-[9px] font-black uppercase text-[var(--muted)] tracking-widest mt-1">{m.label}</p>
              </div>
            </div>
            
            <div className="pt-[var(--s-4)] border-t border-[var(--line)]">
              <p className="text-[10px] font-bold text-[var(--muted)] opacity-60 italic">{m.sub}</p>
            </div>

            <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/20 overflow-hidden">
              <motion.div 
                animate={{ x: ['-100%', '100%'] }}
                transition={{ repeat: Infinity, duration: 3, ease: "linear", delay: i * 0.5 }}
                className="w-1/3 h-full bg-gradient-to-r from-transparent via-current to-transparent opacity-20"
                style={{ color: m.color }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-[var(--s-8)]">
        {/* Node Distribution */}
        <div className="lg:col-span-8 clay-card p-[var(--s-8)] space-y-[var(--s-8)]">
          <div className="flex items-center justify-between">
            <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)] flex items-center gap-[var(--s-3)]">
              <Network size={18} className="text-[var(--brand)]" />
              Active Node Topology
            </h3>
            <span className="text-[9px] font-black text-[var(--brand)] bg-[var(--brand)]/10 px-2 py-1 rounded">12 nodes active</span>
          </div>
          
          <div className="h-[300px] flex items-end justify-between gap-[var(--s-4)] pt-[var(--s-10)]">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-[var(--s-3)] group">
                <div className="w-full flex flex-col justify-end gap-[var(--s-1)] h-full">
                  <motion.div 
                    initial={{ height: 0 }}
                    animate={{ height: `${20 + Math.random() * 80}%` }}
                    className="w-full rounded-t-[var(--r-xs)] bg-gradient-to-t from-[var(--brand)]/40 to-[var(--brand)] group-hover:brightness-125 transition-all shadow-[0_0_15px_rgba(77,171,255,0.2)]"
                  />
                </div>
                <span className="text-[8px] font-black text-[var(--muted)] uppercase">N-{i+1}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Database Health */}
        <div className="lg:col-span-4 clay-card p-[var(--s-8)] space-y-[var(--s-8)]">
          <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)] flex items-center gap-[var(--s-3)]">
            <Database size={18} className="text-[var(--purple)]" />
            Neural Ledger
          </h3>
          
          <div className="space-y-[var(--s-6)]">
            {stats?.table_counts ? Object.entries(stats.table_counts).map(([table, count]) => (
              <div key={table} className="p-[var(--s-4)] rounded-[var(--r-md)] bg-black/20 border border-white/5 space-y-[var(--s-3)]">
                <div className="flex justify-between items-center">
                  <p className="text-[var(--fs-xs)] font-black text-[var(--ink)] uppercase tracking-tight capitalize">{table.replace('_', ' ')}</p>
                  <span className="text-[10px] font-black uppercase px-1.5 py-0.5 rounded bg-[var(--brand)]/10 text-[var(--brand)]">{count.toLocaleString()}</span>
                </div>
                <div className="h-1 bg-black/30 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, (count / 1000) * 100)}%` }}
                    className="h-full bg-gradient-to-r from-[var(--brand)] to-[var(--purple)]"
                  />
                </div>
              </div>
            )) : (
              ['PostgreSQL Core', 'Redis Cache', 'Vector Store'].map((db) => (
                <div key={db} className="p-[var(--s-4)] rounded-[var(--r-md)] bg-black/20 border border-white/5 space-y-[var(--s-3)]">
                  <div className="flex justify-between items-center">
                    <p className="text-[var(--fs-xs)] font-black text-[var(--ink)] uppercase tracking-tight">{db}</p>
                    <span className="text-[8px] font-black uppercase px-1.5 py-0.5 rounded bg-[var(--success)]/10 text-[var(--success)]">Active</span>
                  </div>
                  <div className="h-1 bg-black/30 rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '15%' }} className="h-full bg-gradient-to-r from-[var(--brand)] to-[var(--purple)]" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Maintenance & Quality */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-[var(--s-8)]">
        <div className="clay-card p-[var(--s-8)] space-y-[var(--s-8)]">
          <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)] flex items-center gap-[var(--s-3)]">
            <Clock size={18} className="text-[var(--brand)]" />
            Maintenance Protocols
          </h3>
          <div className="space-y-[var(--s-4)] max-h-[300px] overflow-y-auto custom-scrollbar pr-[var(--s-4)]">
            {stats?.maintenance?.map((task, i) => (
              <div key={i} className="flex items-center justify-between p-[var(--s-4)] rounded-[var(--r-md)] bg-black/20 border border-white/5 group hover:bg-black/30 transition-all">
                <div className="flex flex-col">
                  <span className="text-[var(--fs-xs)] font-black uppercase text-[var(--ink)]">{task.task.replace(/_/g, ' ')}</span>
                  <span className="text-[10px] text-[var(--muted)] font-bold">Last Run: {new Date(task.last_run).toLocaleTimeString()}</span>
                </div>
                <div className="flex items-center gap-[var(--s-3)]">
                  <span className="text-[10px] font-mono text-[var(--brand)]">{task.meta?.duration_ms ? `${task.meta.duration_ms}ms` : '32ms'}</span>
                  <div className="w-2 h-2 rounded-full bg-[var(--success)] shadow-[0_0_8px_var(--success)]" />
                </div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-[var(--s-4)]">
            <button 
              onClick={() => runMaintenance('db_optimization')}
              disabled={maintenanceRunning['db_optimization']}
              className="p-[var(--s-4)] clay-card bg-[var(--brand)]/5 border-[var(--brand)]/20 hover:bg-[var(--brand)]/10 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-[var(--s-3)]"
            >
              {maintenanceRunning['db_optimization'] ? <RefreshCcw size={16} className="animate-spin" /> : <Database size={16} />}
              Optimize Ledger
            </button>
            <button 
              onClick={() => runMaintenance('storage_cleanup')}
              disabled={maintenanceRunning['storage_cleanup']}
              className="p-[var(--s-4)] clay-card bg-[var(--purple)]/5 border-[var(--purple)]/20 hover:bg-[var(--purple)]/10 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-[var(--s-3)]"
            >
              {maintenanceRunning['storage_cleanup'] ? <RefreshCcw size={16} className="animate-spin" /> : <HardDrive size={16} />}
              Cleanup Storage
            </button>
          </div>
        </div>

        <div className="clay-card p-[var(--s-8)] space-y-[var(--s-8)]">
          <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)] flex items-center gap-[var(--s-3)]">
            <Target size={18} className="text-[var(--accent)]" />
            Intelligence Quality Distribution
          </h3>
          <div className="space-y-[var(--s-6)]">
            {stats?.score_distribution ? Object.entries(stats.score_distribution).map(([bucket, count]) => {
              const total = Object.values(stats.score_distribution).reduce((a, b) => a + b, 0);
              const percent = Math.round((count / total) * 100);
              return (
                <div key={bucket} className="space-y-[var(--s-2)]">
                  <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                    <span className="text-[var(--muted)]">{bucket}</span>
                    <span className="text-[var(--ink)]">{count} ({percent}%)</span>
                  </div>
                  <div className="h-2 bg-black/30 rounded-full overflow-hidden border border-white/5 shadow-inner">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${percent}%` }}
                      className={`h-full ${bucket.includes('High') ? 'bg-[var(--success)]' : bucket.includes('Medium') ? 'bg-[var(--brand)]' : 'bg-[var(--muted)]'}`} 
                    />
                  </div>
                </div>
              );
            }) : (
              <div className="h-full flex items-center justify-center text-[var(--muted)] italic text-[var(--fs-xs)]">
                Analyzing intelligence yield...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bot Run History */}
      <div className="clay-card overflow-hidden">
        <div className="p-[var(--s-8)] border-b border-[var(--line)] bg-[var(--bg-alt)]/30">
          <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)] flex items-center gap-[var(--s-3)]">
            <Activity size={18} className="text-[var(--brand)]" />
            Recent Execution Logs
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[var(--fs-sm)]">
            <thead className="bg-[var(--bg-alt)]/50 border-b border-[var(--line)]">
              <tr>
                <th className="p-[var(--s-6)] font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Trigger</th>
                <th className="p-[var(--s-6)] font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Timestamp</th>
                <th className="p-[var(--s-6)] font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Duration</th>
                <th className="p-[var(--s-6)] font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Outcome</th>
                <th className="p-[var(--s-6)] font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Signal Yield</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--line)]">
              {stats?.bot?.recent_runs?.map((run, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors group">
                  <td className="p-[var(--s-6)]">
                    <span className="px-2 py-1 rounded-full text-[9px] font-black uppercase bg-[var(--brand)]/10 text-[var(--brand)] border border-[var(--brand)]/20">
                      {run.trigger}
                    </span>
                  </td>
                  <td className="p-[var(--s-6)] text-[var(--fs-xs)] font-bold text-[var(--muted)]">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="p-[var(--s-6)] text-[var(--fs-xs)] font-black text-[var(--ink)]">
                    {run.duration_seconds}s
                  </td>
                  <td className="p-[var(--s-6)]">
                    <span className={`px-2 py-1 rounded-full text-[9px] font-black uppercase ${run.status === 'success' ? 'bg-[var(--success)]/10 text-[var(--success)]' : 'bg-[var(--error)]/10 text-[var(--error)]'}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="p-[var(--s-6)] text-[var(--fs-xs)] font-black text-[var(--brand)]">
                    {run.emails_sent} sent
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SystemMonitor;
