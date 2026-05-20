import React from 'react';
import { Search, Target, Zap } from 'lucide-react';
import LeadScraper from './LeadScraper';

const HarvesterPanel = ({ data, fetchData }) => {
  return (
    <div className="max-w-5xl mx-auto space-y-[var(--s-8)]">
      <div className="clay-card p-[var(--s-8)] bg-gradient-to-br from-[var(--brand)]/5 to-transparent">
        <LeadScraper onStarted={fetchData} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-8)]">
        <div className="clay-card p-[var(--s-8)]">
          <h4 className="text-[10px] font-black uppercase tracking-[0.2em] mb-[var(--s-6)] text-[var(--muted)]">Intelligence Fleet Nodes</h4>
          <div className="space-y-[var(--s-4)]">
            {[
              { name: 'SerpCore Alpha', status: data?.runtime?.integrations?.serpapi ? 'Active' : 'Offline', icon: Search, color: 'var(--brand)' },
              { name: 'Yelp Vector Node', status: data?.runtime?.integrations?.yelp ? 'Active' : 'Offline', icon: Target, color: 'var(--accent)' },
              { name: 'Neural Scraper', status: 'Ready', icon: Zap, color: 'var(--success)' },
            ].map((fleet, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-[var(--r-md)] bg-black/20 border border-white/5 group hover:border-[var(--brand)]/30 transition-all shadow-inner">
                <div className="flex items-center gap-4">
                  <div 
                    className="p-2.5 rounded-xl shadow-lg transition-transform group-hover:scale-110"
                    style={{ backgroundColor: `${fleet.color}15`, color: fleet.color, border: `1px solid ${fleet.color}20` }}
                  >
                    <fleet.icon size={18} />
                  </div>
                  <span className="text-[var(--fs-xs)] font-black uppercase tracking-tight text-[var(--ink)] opacity-90">{fleet.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${fleet.status === 'Active' || fleet.status === 'Ready' ? 'bg-[var(--success)] shadow-[0_0_8px_var(--success)]' : 'bg-[var(--error)] shadow-[0_0_8px_var(--error)]'}`} />
                  <span className={`text-[10px] font-black uppercase tracking-widest ${fleet.status === 'Active' || fleet.status === 'Ready' ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>{fleet.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="clay-card p-[var(--s-8)]">
          <h4 className="text-[10px] font-black uppercase tracking-[0.2em] mb-[var(--s-6)] text-[var(--muted)]">Neural Load Telemetry</h4>
          <div className="space-y-[var(--s-8)]">
            <div className="p-4 bg-black/20 rounded-[var(--r-md)] border border-white/5 shadow-inner">
              <div className="flex justify-between text-[10px] font-black uppercase tracking-widest mb-3 text-[var(--muted)]">
                <span>API Utilization</span>
                <span className="text-[var(--brand)]">42%</span>
              </div>
              <div className="h-2 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: '42%' }}
                  className="h-full bg-gradient-to-r from-[var(--brand)] to-[var(--purple)] rounded-full shadow-[0_0_12px_var(--brand-glow)]" 
                />
              </div>
            </div>
            <div className="p-4 bg-black/20 rounded-[var(--r-md)] border border-white/5 shadow-inner">
              <div className="flex justify-between text-[10px] font-black uppercase tracking-widest mb-3 text-[var(--muted)]">
                <span>Proxy Grid Health</span>
                <span className="text-[var(--success)]">98%</span>
              </div>
              <div className="h-2 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: '98%' }}
                  className="h-full bg-gradient-to-r from-[var(--success)] to-[var(--brand)] rounded-full shadow-[0_0_12px_var(--success)]/30" 
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HarvesterPanel;
