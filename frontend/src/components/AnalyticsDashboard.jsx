import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Search, Zap, Mail, MessageSquare, TrendingUp, Target, Shield, CheckCircle2 } from 'lucide-react';
import { OutreachChart, NicheDistribution } from './AnalyticsCharts';

const AnalyticsDashboard = ({ data }) => {
  return (
    <div className="space-y-[var(--s-10)]">
      {/* Neural Yield Funnel */}
      <div className="clay-card p-[var(--s-10)]">
        <h3 className="text-[var(--fs-xl)] font-black mb-[var(--s-12)] flex items-center gap-[var(--s-3)] text-[var(--ink)] leading-[var(--lh-tight)] uppercase tracking-[0.2em]">
          <Activity size={24} className="text-[var(--brand)]" />
          Neural Intelligence Funnel
        </h3>
        
        <div className="relative max-w-4xl mx-auto py-[var(--s-10)]">
          <div className="flex flex-col gap-[var(--s-1)] relative z-10">
            {[
              { label: 'Intelligence Scraped', value: data?.overview?.total_leads || 0, color: 'var(--brand)', icon: Search, width: '100%' },
              { label: 'Lead Audited', value: data?.overview?.total_leads || 0, color: 'var(--purple)', icon: Zap, width: '85%' },
              { label: 'Outreach Contacted', value: data?.health?.sent_total || 0, color: 'var(--accent)', icon: Mail, width: '70%' },
              { label: 'Engagement Replies', value: data?.health?.reply_total || 0, color: 'var(--success)', icon: MessageSquare, width: '55%' },
            ].map((step, i, arr) => {
              const nextValue = arr[i+1]?.value || step.value;
              const dropoff = step.value > 0 ? Math.round((nextValue / step.value) * 100) : 0;
              
              return (
                <div key={step.label} className="relative flex flex-col items-center group">
                  {/* Funnel Segment */}
                  <motion.div 
                    initial={{ opacity: 0, scaleX: 0 }}
                    animate={{ opacity: 1, scaleX: 1 }}
                    className="h-[var(--s-14)] flex items-center justify-between px-[var(--s-10)] relative overflow-hidden transition-all group-hover:brightness-110 cursor-help clay-card"
                    style={{ 
                      width: step.width,
                      backgroundColor: `${step.color}10`,
                      borderColor: `${step.color}30`,
                      clipPath: i < arr.length - 1 
                        ? `polygon(0% 0%, 100% 0%, ${88 + (i * 2)}% 100%, ${12 - (i * 2)}% 100%)` 
                        : 'polygon(0% 0%, 100% 0%, 95% 100%, 5% 100%)',
                      marginBottom: '-1px'
                    }}
                  >
                    <div className="flex items-center gap-[var(--s-6)]">
                      <div className="p-[var(--s-4)] rounded-[var(--r-md)] bg-black/20 border border-white/5 shadow-inner transition-transform group-hover:scale-110">
                        <step.icon size={24} style={{ color: `var(--${step.color})` }} />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-40 text-[var(--muted)]">{step.label}</p>
                        <p className="text-[var(--fs-xl)] font-black text-[var(--ink)] tracking-tight">{step.value.toLocaleString()}</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-[10px] font-black opacity-30 uppercase tracking-widest text-[var(--muted)]">Efficiency</p>
                      <p className="text-[var(--fs-lg)] font-black" style={{ color: `var(--${step.color})` }}>{dropoff}%</p>
                    </div>

                    {/* Glow Effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                  </motion.div>

                  {/* Connection/Dropoff Label */}
                  {i < arr.length - 1 && (
                    <div className="h-[var(--s-10)] flex items-center justify-center relative z-20">
                      <div className="px-4 py-1.5 rounded-full bg-black/40 border border-white/5 text-[10px] font-black text-[var(--muted)] backdrop-blur-md shadow-lg uppercase tracking-widest">
                        <span className="text-[var(--error)]">-{100 - dropoff}%</span> dropoff signal
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-[var(--s-8)]">
        <div className="lg:col-span-2 clay-card p-[var(--s-8)] h-[450px] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-[0.2em] flex items-center gap-3 text-[var(--ink)]">
              <TrendingUp size={20} className="text-[var(--brand)]" />
              Outreach Velocity
            </h3>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--brand)] animate-pulse shadow-[0_0_8px_var(--brand)]" />
              <span className="text-[10px] font-black uppercase tracking-widest text-[var(--brand)]">Live Data Feed</span>
            </div>
          </div>
          <div className="flex-1 min-h-0">
            <OutreachChart data={data} />
          </div>
        </div>
        <div className="clay-card p-[var(--s-8)] h-[450px] flex flex-col">
          <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-[0.2em] flex items-center gap-3 text-[var(--ink)] mb-8">
            <Target size={20} className="text-[var(--accent)]" />
            Market Segments
          </h3>
          <div className="flex-1 min-h-0">
            <NicheDistribution data={data} />
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-[var(--s-8)]">
        {[
          { label: 'Conversion Rate', value: `${data?.health?.conversion_rate || 0}%`, trend: '+1.2%', color: 'var(--success)', icon: Activity },
          { label: 'Avg. Response Time', value: '2.4h', trend: '-15m', color: 'var(--brand)', icon: Zap },
          { label: 'Lead Quality Score', value: `${Math.round((data?.ai_insights?.avg_opportunity_score || 0) * 100)}/100`, trend: '+5', color: 'var(--accent)', icon: Target },
        ].map((m, i) => (
          <div key={i} className="clay-card p-[var(--s-8)] group hover:scale-[1.03] transition-all">
            <div className="flex items-center justify-between mb-4">
              <p className="text-[10px] text-[var(--muted)] font-black uppercase tracking-[0.2em]">{m.label}</p>
              <div className="p-2 bg-black/20 rounded-lg border border-white/5">
                <m.icon size={14} style={{ color: `var(--${m.color})` }} />
              </div>
            </div>
            <div className="flex items-end justify-between">
              <p className="text-[var(--fs-2xl)] font-black text-[var(--ink)] tracking-tight">{m.value}</p>
              <span className={`text-[10px] font-black px-2 py-1 rounded-md bg-black/20 tracking-widest`} style={{ color: `var(--${m.color})` }}>{m.trend}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Deliverability Risk Report */}
      <div className="clay-card p-[var(--s-10)]">
        <h3 className="text-[var(--fs-xl)] font-black mb-[var(--s-10)] flex items-center gap-[var(--s-4)] text-[var(--ink)] uppercase tracking-[0.2em]">
          <Shield size={24} className="text-[var(--error)]" />
          Deliverability Risk Node
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-[var(--s-10)]">
          <div className="space-y-[var(--s-6)]">
            <div className="flex items-center justify-between p-6 bg-[var(--error)]/5 border border-[var(--error)]/20 rounded-[var(--r-lg)] clay-card shadow-sm">
              <div>
                <p className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--error)] mb-1">Hard Bounces</p>
                <p className="text-[var(--fs-xs)] text-[var(--muted)] font-medium">Neural targets with invalid link addresses</p>
              </div>
              <p className="text-[var(--fs-xl)] font-black text-[var(--error)]">{data?.health?.risk_total || 0}</p>
            </div>
            <div className="flex items-center justify-between p-6 bg-black/20 border border-white/5 rounded-[var(--r-lg)] clay-card shadow-sm">
              <div>
                <p className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--muted)] mb-1">Unsubscribed</p>
                <p className="text-[var(--fs-xs)] text-[var(--muted)] font-medium">Entities opting out from neural outreach</p>
              </div>
              <p className="text-[var(--fs-xl)] font-black text-[var(--ink)] tracking-tight">0</p>
            </div>
          </div>
          <div className="clay-card p-[var(--s-8)] bg-black/20 shadow-inner">
             <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--muted)] mb-6 border-b border-[var(--line)] pb-4">Risk Mitigation Strategy</p>
             <ul className="space-y-4">
                {[
                  'Verified leads are automatically prioritized',
                  'SPF/DMARC checks enforced on all targets',
                  'Outreach throttling enabled by default',
                  'Automatic blacklist for repeated failures'
                ].map((s, i) => (
                  <li key={i} className="flex items-center gap-4 text-[11px] font-bold text-[var(--ink-dim)]">
                     <div className="p-1 rounded-full bg-[var(--success)]/20 text-[var(--success)]">
                        <CheckCircle2 size={14} />
                     </div>
                     {s}
                  </li>
                ))}
             </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
