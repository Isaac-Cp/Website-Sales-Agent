import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, 
  Cpu, 
  Zap, 
  Shield, 
  Users, 
  Activity, 
  Search, 
  Play, 
  ChevronDown, 
  Save, 
  RefreshCcw,
  Globe,
  Database,
  Lock,
  Mail,
  Sliders,
  Terminal
} from 'lucide-react';

const SettingsPage = ({ data, personas, onSave, onBotAction }) => {
  const [activeCategory, setActiveCategory] = useState('neural');
  const [formData, setFormData] = useState(data || {});

  const categories = [
    { id: 'neural', label: 'Neural Core', icon: Cpu, desc: 'Global intelligence processing' },
    { id: 'fleet', label: 'Outreach Fleet', icon: Mail, desc: 'Harvester & transmission nodes' },
    { id: 'security', label: 'Security Protocols', icon: Shield, desc: 'Access & neural encryption' },
    { id: 'network', label: 'Network Relay', icon: Globe, desc: 'Proxy & uplink configuration' }
  ];

  const handleUpdate = (path, value) => {
    // Simple deep merge simulation
    const newData = { ...formData };
    const keys = path.split('.');
    let current = newData;
    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = { ...current[keys[i]] };
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    setFormData(newData);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-[var(--s-10)] pb-[var(--s-20)] px-[var(--s-4)]">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-[var(--s-6)]">
        <div>
          <h2 className="text-[var(--fs-2xl)] font-black tracking-tighter text-[var(--ink)] leading-[var(--lh-tight)] italic uppercase">
            System<span className="text-[var(--brand)]">Protocols</span>
          </h2>
          <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-[0.3em] mt-[var(--s-1)]">
            Adjust operational parameters for the autonomous fleet
          </p>
        </div>
        <div className="flex gap-[var(--s-4)]">
          <button 
            onClick={() => onBotAction('refresh')}
            className="p-[var(--s-3)] clay-card hover:bg-[var(--glass-hover)] rounded-[var(--r-md)] text-[var(--muted)] transition-all"
          >
            <RefreshCcw size={20} />
          </button>
          <button 
            onClick={() => onSave(formData)}
            className="btn-primary px-[var(--s-10)] py-[var(--s-3)] rounded-[var(--r-md)] font-black uppercase tracking-widest flex items-center gap-[var(--s-3)]"
          >
            <Save size={18} />
            Apply Changes
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-[var(--s-8)] items-start">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-3 space-y-[var(--s-4)]">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`w-full flex items-center gap-[var(--s-4)] p-[var(--s-4)] rounded-[var(--r-md)] transition-all group relative overflow-hidden ${activeCategory === cat.id ? 'clay-card bg-[var(--brand)]/10 border-[var(--brand)]/30' : 'hover:bg-[var(--glass-hover)]'}`}
            >
              {activeCategory === cat.id && (
                <motion.div layoutId="cat-active" className="absolute left-0 w-1 h-full bg-[var(--brand)]" />
              )}
              <div className={`p-[var(--s-2)] rounded-[var(--r-sm)] ${activeCategory === cat.id ? 'bg-[var(--brand)] text-white' : 'bg-[var(--bg-subtle)] text-[var(--muted)] group-hover:text-[var(--brand)]'} transition-colors`}>
                <cat.icon size={20} />
              </div>
              <div className="text-left">
                <p className={`text-[var(--fs-sm)] font-black uppercase tracking-tighter ${activeCategory === cat.id ? 'text-[var(--ink)]' : 'text-[var(--muted)]'}`}>{cat.label}</p>
                <p className="text-[10px] text-[var(--muted)] font-bold opacity-60 leading-none">{cat.desc}</p>
              </div>
            </button>
          ))}

          <div className="pt-[var(--s-10)] mt-[var(--s-10)] border-t border-[var(--line)]">
            <div className="clay-card p-[var(--s-5)] bg-[var(--error)]/5 border-[var(--error)]/10 space-y-[var(--s-3)]">
              <div className="flex items-center gap-[var(--s-2)] text-[var(--error)]">
                <AlertCircle size={16} />
                <span className="text-[10px] font-black uppercase tracking-widest">Neural Override</span>
              </div>
              <p className="text-[10px] text-[var(--muted)] font-bold leading-relaxed">Emergency termination of all active nodes and data wipes.</p>
              <button className="w-full py-[var(--s-2)] rounded-[var(--r-sm)] bg-[var(--error)] text-white font-black text-[9px] uppercase tracking-widest hover:brightness-110 transition-all">
                Factory Reset
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-9">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeCategory}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="clay-card p-[var(--s-10)] space-y-[var(--s-12)]"
            >
              {activeCategory === 'neural' && (
                <div className="space-y-[var(--s-10)]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-10)]">
                    <div className="space-y-[var(--s-4)]">
                      <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                        <Terminal size={14} className="text-[var(--brand)]" />
                        Parallel Worker Count
                      </label>
                      <div className="relative group">
                        <input 
                          type="number" 
                          value={formData?.runtime?.parallel_workers || 4} 
                          onChange={(e) => handleUpdate('runtime.parallel_workers', parseInt(e.target.value))}
                          className="w-full bg-black/30 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-black text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner text-[var(--ink)]" 
                        />
                      </div>
                      <p className="text-[10px] text-[var(--muted)] font-bold italic opacity-60">Determines concurrent scraping and validation threads.</p>
                    </div>
                    <div className="space-y-[var(--s-4)]">
                      <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                        <Sliders size={14} className="text-[var(--purple)]" />
                        Neural Batch Size
                      </label>
                      <input 
                        type="number" 
                        value={formData?.runtime?.batch_size || 50} 
                        className="w-full bg-black/30 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-black text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner text-[var(--ink)]" 
                      />
                      <p className="text-[10px] text-[var(--muted)] font-bold italic opacity-60">Number of leads processed in a single neural cycle.</p>
                    </div>
                  </div>

                  <div className="space-y-[var(--s-6)]">
                    <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                      <Zap size={14} className="text-[var(--accent)]" />
                      Inference Priority
                    </label>
                    <div className="grid grid-cols-3 gap-[var(--s-4)]">
                      {['Performance', 'Balanced', 'Accuracy'].map(p => (
                        <button key={p} className={`py-[var(--s-4)] rounded-[var(--r-md)] border font-black text-[var(--fs-xs)] uppercase tracking-widest transition-all ${p === 'Performance' ? 'bg-[var(--brand)] text-white border-[var(--brand)] shadow-lg shadow-[var(--brand-glow)]' : 'bg-black/20 border-transparent text-[var(--muted)] hover:bg-black/30'}`}>
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeCategory === 'fleet' && (
                <div className="space-y-[var(--s-10)]">
                  <div className="space-y-[var(--s-6)]">
                    <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                      <Activity size={14} className="text-[var(--success)]" />
                      Transmission Mode
                    </label>
                    <div className="grid grid-cols-2 gap-[var(--s-6)]">
                      <button 
                        onClick={() => onBotAction('config', { dry_run: true })}
                        className={`p-[var(--s-8)] rounded-[var(--r-lg)] font-black text-[var(--fs-xs)] uppercase tracking-widest border transition-all flex flex-col items-center gap-[var(--s-4)] ${data?.runtime?.dry_run ? 'bg-[var(--accent)]/10 border-[var(--accent)] text-[var(--accent)] clay-card shadow-lg shadow-[var(--accent)]/10' : 'bg-black/20 border-transparent text-[var(--muted)] hover:bg-black/30'}`}
                      >
                        <Search size={32} />
                        <div className="text-center">
                          <span>Simulation (Dry Run)</span>
                          <p className="text-[9px] mt-1 font-bold opacity-60 normal-case">No real emails will be transmitted.</p>
                        </div>
                      </button>
                      <button 
                        onClick={() => onBotAction('config', { dry_run: false })}
                        className={`p-[var(--s-8)] rounded-[var(--r-lg)] font-black text-[var(--fs-xs)] uppercase tracking-widest border transition-all flex flex-col items-center gap-[var(--s-4)] ${!data?.runtime?.dry_run ? 'bg-[var(--success)]/10 border-[var(--success)] text-[var(--success)] clay-card shadow-lg shadow-[var(--success)]/10' : 'bg-black/20 border-transparent text-[var(--muted)] hover:bg-black/30'}`}
                      >
                        <Play size={32} />
                        <div className="text-center">
                          <span>Live Operations</span>
                          <p className="text-[9px] mt-1 font-bold opacity-60 normal-case">Nodes will transmit live signals.</p>
                        </div>
                      </button>
                    </div>
                  </div>

                  <div className="space-y-[var(--s-4)]">
                    <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest ml-1 flex items-center gap-[var(--s-2)]">
                      <Users size={14} className="text-[var(--brand)]" />
                      Default Persona Protocol
                    </label>
                    <div className="relative">
                      <select 
                        className="w-full bg-black/30 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-black text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner appearance-none cursor-pointer text-[var(--ink)]"
                        value={formData?.runtime?.default_persona}
                        onChange={(e) => handleUpdate('runtime.default_persona', e.target.value)}
                      >
                        {personas.map(p => (
                          <option key={p.name} value={p.name} className="bg-[var(--bg-alt)]">{p.name}</option>
                        ))}
                      </select>
                      <div className="absolute right-[var(--s-4)] top-1/2 -translate-y-1/2 pointer-events-none text-[var(--muted)]">
                        <ChevronDown size={18} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeCategory === 'security' && (
                <div className="space-y-[var(--s-10)]">
                  <div className="clay-card p-[var(--s-6)] bg-black/20 border-white/5 space-y-[var(--s-6)]">
                    <div className="flex items-center gap-[var(--s-4)]">
                      <div className="w-12 h-12 rounded-[var(--r-md)] bg-[var(--brand)]/10 flex items-center justify-center text-[var(--brand)]">
                        <Lock size={24} />
                      </div>
                      <div>
                        <p className="text-[var(--fs-sm)] font-black uppercase tracking-tighter text-[var(--ink)]">Uplink Authorization</p>
                        <p className="text-[10px] text-[var(--muted)] font-bold uppercase tracking-widest">Neural access key rotation</p>
                      </div>
                    </div>
                    <div className="space-y-[var(--s-4)]">
                      <input 
                        type="password" 
                        value="••••••••••••••••"
                        readOnly
                        className="w-full bg-black/30 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-black tracking-[0.5em] text-[var(--fs-sm)] text-[var(--brand)]/50" 
                      />
                      <button className="text-[var(--fs-xs)] font-black text-[var(--brand)] uppercase tracking-widest hover:underline">Rotate Neural Key</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-6)]">
                    <div className="p-[var(--s-5)] rounded-[var(--r-md)] border border-[var(--line)] flex items-center justify-between group hover:bg-[var(--glass-hover)] transition-all">
                      <div className="flex items-center gap-[var(--s-3)]">
                        <Shield size={18} className="text-[var(--success)]" />
                        <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--ink-dim)]">Biometric Sync</span>
                      </div>
                      <div className="w-10 h-5 rounded-full bg-[var(--success)]/20 p-1 flex justify-end items-center">
                        <div className="w-3 h-3 rounded-full bg-[var(--success)] shadow-[0_0_8px_var(--success)]" />
                      </div>
                    </div>
                    <div className="p-[var(--s-5)] rounded-[var(--r-md)] border border-[var(--line)] flex items-center justify-between group hover:bg-[var(--glass-hover)] transition-all opacity-50">
                      <div className="flex items-center gap-[var(--s-3)]">
                        <Database size={18} className="text-[var(--muted)]" />
                        <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--muted)]">Ledger Audit</span>
                      </div>
                      <div className="w-10 h-5 rounded-full bg-[var(--bg-subtle)] p-1 flex justify-start items-center">
                        <div className="w-3 h-3 rounded-full bg-[var(--muted)]" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeCategory === 'network' && (
                <div className="space-y-[var(--s-10)]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-10)]">
                    <div className="space-y-[var(--s-4)]">
                      <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                        <Globe size={14} className="text-[var(--brand)]" />
                        Uplink Proxy
                      </label>
                      <input 
                        type="text" 
                        placeholder="http://proxy.relay.nn:8080"
                        value={formData?.network?.proxy_url || ''} 
                        onChange={(e) => handleUpdate('network.proxy_url', e.target.value)}
                        className="w-full bg-black/30 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-mono text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner text-[var(--ink)]" 
                      />
                    </div>
                    <div className="space-y-[var(--s-4)]">
                      <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                        <Zap size={14} className="text-[var(--accent)]" />
                        Uplink Latency Cap
                      </label>
                      <div className="flex items-center gap-[var(--s-4)]">
                        <input 
                          type="range" 
                          min="50" 
                          max="2000" 
                          step="50"
                          value={formData?.network?.latency_cap || 500} 
                          onChange={(e) => handleUpdate('network.latency_cap', parseInt(e.target.value))}
                          className="flex-1 h-1 bg-[var(--line)] rounded-full appearance-none cursor-pointer accent-[var(--brand)]" 
                        />
                        <span className="text-[var(--fs-xs)] font-black text-[var(--brand)] w-16">{formData?.network?.latency_cap || 500}ms</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-[var(--s-6)]">
                    <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                      <Database size={14} className="text-[var(--purple)]" />
                      Neural Relay Nodes
                    </label>
                    <div className="space-y-[var(--s-3)]">
                      {[
                        { id: 'us-east-1', region: 'US East (N. Virginia)', status: 'Active', ping: '12ms' },
                        { id: 'eu-west-1', region: 'EU West (Dublin)', status: 'Active', ping: '84ms' },
                        { id: 'ap-northeast-1', region: 'Asia Pacific (Tokyo)', status: 'Standby', ping: '142ms' }
                      ].map(node => (
                        <div key={node.id} className="p-[var(--s-4)] rounded-[var(--r-md)] bg-black/20 border border-white/5 flex items-center justify-between group hover:bg-black/30 transition-all">
                          <div className="flex items-center gap-[var(--s-4)]">
                            <div className={`w-2 h-2 rounded-full ${node.status === 'Active' ? 'bg-[var(--success)] shadow-[0_0_8px_var(--success)]' : 'bg-[var(--muted)]'}`} />
                            <div>
                              <p className="text-[var(--fs-xs)] font-black uppercase text-[var(--ink)]">{node.region}</p>
                              <p className="text-[9px] text-[var(--muted)] font-bold">{node.id} • Latency: {node.ping}</p>
                            </div>
                          </div>
                          <button className="text-[9px] font-black uppercase text-[var(--brand)] opacity-0 group-hover:opacity-100 transition-opacity">Reroute</button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
