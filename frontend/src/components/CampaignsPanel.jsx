import React from 'react';
import { Plus, Cpu, TrendingUp, Zap, Settings, ChevronRight } from 'lucide-react';

const CampaignsPanel = ({ data, personas, setEditingPersona, handleBotAction }) => {
  return (
    <div className="space-y-[var(--s-10)]">
      <div className="clay-card p-[var(--s-10)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-[var(--s-10)]">
          <div>
            <h2 className="text-[var(--fs-xl)] font-black tracking-[0.2em] uppercase text-[var(--ink)]">Neural Personas</h2>
            <p className="text-[var(--fs-xs)] text-[var(--muted)] font-bold mt-2 uppercase tracking-widest opacity-80">AI Personality Core Protocols</p>
          </div>
          <button 
            onClick={() => setEditingPersona({ name: '', description: '', icon: 'Zap', strategy_prompt: '', active: true })}
            className="btn-primary px-8 py-4 flex items-center gap-3 shadow-[0_8px_32px_var(--brand-glow)]"
          >
            <Plus size={20} />
            Initialize Persona
          </button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-[var(--s-8)]">
          {personas.map((p, i) => (
            <div 
              key={p.id || i} 
              className={`clay-card p-[var(--s-8)] border-[var(--line)] hover:scale-[1.02] transition-all cursor-pointer group relative ${data?.runtime?.default_persona === p.name ? 'border-[var(--brand)]/40 bg-[var(--brand)]/5' : ''}`}
            >
              {data?.runtime?.default_persona === p.name && (
                <div className="absolute -top-3 -right-3 w-10 h-10 bg-[var(--success)] rounded-full flex items-center justify-center text-white shadow-[0_0_20px_var(--success)] z-10 border-4 border-[var(--card-bg)]">
                  <Zap size={18} fill="currentColor" />
                </div>
              )}

              <div className="flex items-start justify-between mb-[var(--s-6)]">
                <div 
                  onClick={() => handleBotAction('config', { default_persona: p.name })}
                  className={`w-[var(--s-14)] h-[var(--s-14)] rounded-[var(--r-lg)] flex items-center justify-center transition-all duration-500 shadow-inner ${data?.runtime?.default_persona === p.name ? 'bg-[var(--brand)] text-white shadow-[0_8px_24px_var(--brand-glow)]' : 'bg-black/20 text-[var(--brand)] border border-white/5'}`}
                >
                  {p.icon === 'Cpu' ? <Cpu size={28} /> : p.icon === 'TrendingUp' ? <TrendingUp size={28} /> : <Zap size={28} />}
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={(e) => { e.stopPropagation(); setEditingPersona(p); }}
                    className="p-3 bg-black/20 hover:bg-black/30 rounded-[var(--r-md)] transition-all text-[var(--muted)] hover:text-[var(--brand)] border border-white/5 shadow-inner"
                  >
                    <Settings size={16} />
                  </button>
                  <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest shadow-sm ${data?.runtime?.default_persona === p.name ? 'bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20' : 'bg-black/20 text-[var(--muted)] border border-white/5'}`}>
                    {data?.runtime?.default_persona === p.name ? 'Primary' : 'Standby'}
                  </div>
                </div>
              </div>
              <h3 className="text-[var(--fs-lg)] font-black text-[var(--ink)] tracking-tight mb-2 uppercase">{p.name}</h3>
              <p className="text-[var(--fs-sm)] text-[var(--muted)] mb-8 font-medium leading-relaxed opacity-80">{p.description}</p>
              
              <div 
                onClick={() => handleBotAction('config', { default_persona: p.name })}
                className="flex items-center justify-between pt-6 border-t border-[var(--line)]"
              >
                <span className="text-[10px] font-black text-[var(--brand)] uppercase tracking-[0.2em]">
                  {data?.runtime?.default_persona === p.name ? 'Protocol Active' : 'Engage Protocol'}
                </span>
                <div className={`p-2 rounded-full transition-all duration-500 ${data?.runtime?.default_persona === p.name ? 'bg-[var(--success)]/10 text-[var(--success)] rotate-90 shadow-[0_0_12px_var(--success)]' : 'bg-black/20 text-[var(--muted)]'}`}>
                  <ChevronRight size={18} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CampaignsPanel;
