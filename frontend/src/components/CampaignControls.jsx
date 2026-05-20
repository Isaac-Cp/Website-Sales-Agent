import React from 'react';
import { Play, Pause, StopCircle, RefreshCw, Send, Shield, Activity, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const CampaignControls = ({ status = 'idle', progress = 0, onAction }) => {
  const actions = [
    { id: 'start', label: 'Start', icon: Play, color: 'var(--success)', disabled: status === 'running' },
    { id: 'pause', label: 'Pause', icon: Pause, color: 'var(--accent)', disabled: status === 'paused' || status === 'stopped' || status === 'idle' },
    { id: 'stop', label: 'Stop', icon: StopCircle, color: 'var(--error)', disabled: status === 'stopped' || status === 'idle' },
  ];

  const normalizedProgress = Number.isFinite(progress) ? Math.max(0, Math.min(progress, 100)) : 0;
  const statusTone =
    status === 'running'
      ? 'text-[var(--success)]'
      : status === 'paused'
        ? 'text-[var(--accent)]'
        : status === 'stopped'
          ? 'text-[var(--error)]'
          : 'text-[var(--muted)]';

  const handleAction = (id) => {
    if (id === 'stop' && !window.confirm('Neural Override: Are you sure you want to terminate all active processes?')) {
      return;
    }
    onAction(id);
  };

  return (
    <div className="relative space-y-[var(--s-6)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-[var(--s-3)]">
          <div className="relative">
            <div
              className={`h-3 w-3 rounded-full ${
                status === 'running'
                  ? 'bg-[var(--success)]'
                  : status === 'paused'
                    ? 'bg-[var(--accent)]'
                    : status === 'stopped'
                      ? 'bg-[var(--error)]'
                      : 'bg-[var(--muted)]'
              }`}
            />
            {status === 'running' && (
              <div className="absolute inset-0 h-3 w-3 rounded-full bg-[var(--success)] opacity-40 animate-ping shadow-[0_0_8px_var(--success)]" />
            )}
          </div>
          <span className="text-[var(--fs-xs)] font-black uppercase tracking-[0.16em] text-[var(--muted)]">
            Neural Status
            <span className={`ml-[var(--s-2)] ${statusTone}`}>{status}</span>
          </span>
        </div>
        <button
          onClick={() => onAction('refresh')}
          className="flex h-[var(--s-8)] w-[var(--s-8)] items-center justify-center rounded-full text-[var(--muted)] transition-all hover:bg-[var(--glass-hover)] hover:text-[var(--ink)] has-tooltip shadow-inner"
        >
          <RefreshCw size={14} className={status === 'running' ? 'animate-spin' : ''} />
          <span className="nn-tooltip">Force Sync</span>
        </button>
      </div>

      <div className="grid grid-cols-2 gap-[var(--s-4)]">
        <div className="clay-card p-[var(--s-4)] has-tooltip cursor-help">
          <p className="section-kicker mb-[var(--s-2)]">Throughput</p>
          <p className="metric-value text-[var(--fs-xl)] font-black text-[var(--ink)]">{normalizedProgress}%</p>
          <p className="mt-[var(--s-1)] text-[var(--fs-xs)] text-[var(--muted)]">Daily quota in use</p>
          <span className="nn-tooltip">System Load Balance</span>
        </div>
        <div className="clay-card p-[var(--s-4)] has-tooltip cursor-help">
          <p className="section-kicker mb-[var(--s-2)]">Execution</p>
          <div className="flex items-center gap-[var(--s-2)]">
            <Activity size={16} className={statusTone} />
            <p className={`text-[var(--fs-lg)] font-black capitalize ${statusTone}`}>{status}</p>
          </div>
          <p className="mt-[var(--s-1)] text-[var(--fs-xs)] text-[var(--muted)]">Live automation state</p>
          <span className="nn-tooltip">Process State</span>
        </div>
      </div>

      <div className="space-y-[var(--s-4)] rounded-[var(--r-md)] border border-[var(--glass-border)] clay-card p-[var(--s-5)]">
        <div className="flex items-end justify-between">
          <div className="space-y-[var(--s-1)]">
            <p className="section-kicker">Run Capacity</p>
            <p className="text-[var(--fs-xs)] font-bold text-[var(--muted)] uppercase tracking-widest">Daily quota pacing</p>
          </div>
          <span className="text-[var(--fs-lg)] font-black tracking-tight text-[var(--ink)]">
            {normalizedProgress}%
          </span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full border border-[var(--glass-border)] bg-black/20 shadow-inner">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${normalizedProgress}%` }}
            className="h-full rounded-full bg-gradient-to-r from-[var(--brand)] via-[var(--purple)] to-[var(--accent)]"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-[var(--s-3)]">
        {actions.map((action) => (
          <button
            key={action.id}
            disabled={action.disabled}
            onClick={() => handleAction(action.id)}
            aria-label={`${action.label} campaign`}
            className={`flex flex-col items-center justify-center gap-[var(--s-2)] rounded-[var(--r-md)] border p-[var(--s-4)] transition-all duration-300 has-tooltip ${
              action.disabled ? 'cursor-not-allowed border-transparent bg-transparent opacity-30 grayscale' : 'clay-card hover:-translate-y-1 hover:scale-105 active:scale-95'
            }`}
            style={{
              color: action.disabled ? 'var(--muted)' : action.color,
              borderColor: action.disabled ? 'transparent' : 'var(--line)',
            }}
          >
            <action.icon size={20} className={action.disabled ? '' : 'drop-shadow-sm'} />
            <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest">{action.label}</span>
            <span className="nn-tooltip">{action.id} protocol</span>
          </button>
        ))}
      </div>

      <div className="border-t border-[var(--line)] pt-[var(--s-6)]">
        <h3 className="section-kicker mb-[var(--s-6)]">Neural Commands</h3>
        <div className="space-y-[var(--s-3)]">
          {[
            { label: 'Manual Blast', icon: Send, color: 'var(--brand)' },
            { label: 'Security Audit', icon: Shield, color: 'var(--purple)' },
          ].map((item, i) => (
            <button
              key={i}
              className="group flex w-full items-center justify-between rounded-[var(--r-md)] border border-[var(--glass-border)] clay-card p-[var(--s-4)] transition-all hover:-translate-y-1 hover:bg-[var(--glass-hover)]"
            >
              <div className="flex items-center gap-[var(--s-4)]">
                <div className="rounded-[var(--r-sm)] p-[var(--s-2)] border border-white/5 shadow-inner" style={{ backgroundColor: `${item.color}15`, color: item.color }}>
                  <item.icon size={18} />
                </div>
                <span className="text-[var(--fs-sm)] font-black tracking-tight text-[var(--ink-dim)] uppercase">{item.label}</span>
              </div>
              <ChevronRight size={16} className="text-[var(--muted)] transition-transform group-hover:translate-x-1" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CampaignControls;
