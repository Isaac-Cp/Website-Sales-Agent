import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, 
  Shield, 
  Database, 
  Cpu, 
  RefreshCcw, 
  AlertCircle, 
  ChevronRight, 
  Settings2,
  Lock,
  ArrowRight,
  Terminal,
  Activity
} from 'lucide-react';
import NeuralTagManager from './NeuralTagManager';

const AuthPage = ({ onLogin, loading, loginError }) => {
  const [apiKey, setApiKey] = useState('');
  const [showTagConfig, setShowTagConfig] = useState(false);
  const [step, setStandardStep] = useState('auth'); // 'auth' or 'config'

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(apiKey);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] p-[var(--s-4)] relative overflow-hidden font-sans">
      {/* Dynamic Background */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-[var(--brand)] opacity-[0.03] blur-[150px] rounded-full animate-pulse" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-[var(--purple)] opacity-[0.03] blur-[150px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
      
      {/* Decorative Grid */}
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(var(--ink) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-6xl z-10 grid grid-cols-1 lg:grid-cols-12 gap-[var(--s-10)] items-center"
      >
        {/* Left Side: Brand & Visuals */}
        <div className="lg:col-span-5 space-y-[var(--s-12)]">
          <div className="space-y-[var(--s-6)]">
            <motion.div 
              whileHover={{ rotate: 10, scale: 1.1 }}
              className="w-[var(--s-20)] h-[var(--s-20)] bg-gradient-to-br from-[var(--brand)] to-[var(--brand-dim)] rounded-[var(--r-lg)] flex items-center justify-center shadow-2xl border border-white/10"
            >
              <Zap className="text-white drop-shadow-[0_4px_12px_rgba(255,255,255,0.3)]" size={48} />
            </motion.div>
            <div className="space-y-[var(--s-2)]">
              <h1 className="text-[var(--fs-display)] font-black tracking-tighter text-[var(--ink)] leading-none italic uppercase">
                Neural<span className="text-[var(--brand)]">Ops</span>
              </h1>
              <div className="flex items-center gap-[var(--s-3)]">
                <div className="h-px w-12 bg-[var(--brand)]" />
                <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-[0.4em]">Autonomous Command v6.0</p>
              </div>
            </div>
          </div>

          <div className="space-y-[var(--s-8)]">
            <p className="text-[var(--fs-lg)] text-[var(--ink-dim)] font-medium leading-[var(--lh-relaxed)] max-w-md">
              Establish a secure neural uplink to the intelligence fleet. Monitor scraping nodes, outreach protocols, and real-time conversion metrics.
            </p>

            <div className="grid grid-cols-2 gap-[var(--s-6)]">
              <div className="space-y-[var(--s-2)] p-[var(--s-4)] rounded-[var(--r-md)] bg-[var(--bg-alt)]/30 border border-[var(--line)] shadow-inner">
                <Activity size={20} className="text-[var(--success)]" />
                <p className="text-[10px] font-black uppercase tracking-widest text-[var(--muted)]">Fleet Health</p>
                <p className="text-[var(--fs-sm)] font-bold text-[var(--ink)]">Optimal (99.8%)</p>
              </div>
              <div className="space-y-[var(--s-2)] p-[var(--s-4)] rounded-[var(--r-md)] bg-[var(--bg-alt)]/30 border border-[var(--line)] shadow-inner">
                <Database size={20} className="text-[var(--brand)]" />
                <p className="text-[10px] font-black uppercase tracking-widest text-[var(--muted)]">Node Count</p>
                <p className="text-[var(--fs-sm)] font-bold text-[var(--ink)]">12 active relays</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-[var(--s-4)] text-[var(--muted)] opacity-30">
            <Terminal size={18} />
            <Shield size={18} />
            <Cpu size={18} />
            <Database size={18} />
            <div className="h-px flex-1 bg-[var(--line)]" />
          </div>
        </div>

        {/* Right Side: Interactive Auth/Config */}
        <div className="lg:col-span-7">
          <AnimatePresence mode="wait">
            {step === 'auth' ? (
              <motion.div 
                key="auth-card"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="clay-card p-[var(--s-10)] md:p-[var(--s-12)] space-y-[var(--s-10)] relative"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-[var(--fs-xl)] font-black tracking-tighter text-[var(--ink)] leading-tight uppercase italic">Access Authorization</h2>
                    <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-[0.2em] mt-1">Uplink verification required</p>
                  </div>
                  <div className="p-[var(--s-3)] bg-[var(--brand)]/10 rounded-[var(--r-md)] text-[var(--brand)]">
                    <Lock size={24} />
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-[var(--s-8)]">
                  <div className="space-y-[var(--s-4)]">
                    <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest ml-1 flex items-center gap-2">
                      <Shield size={12} className="text-[var(--brand)]" />
                      Neural Key
                    </label>
                    <div className="relative group">
                      <input 
                        type="password" 
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="••••••••••••••••"
                        className="w-full bg-black/40 border border-[var(--glass-border)] rounded-[var(--r-md)] py-[var(--s-5)] px-[var(--s-6)] font-bold text-[var(--fs-base)] outline-none focus:border-[var(--brand)] transition-all placeholder:text-[var(--muted)]/20 shadow-inner group-hover:border-[var(--muted)]/30 text-[var(--ink)]"
                      />
                    </div>
                  </div>

                  {loginError && (
                    <motion.div 
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-[var(--s-4)] bg-[var(--error)]/10 border border-[var(--error)]/20 rounded-[var(--r-md)] text-[var(--error)] text-[var(--fs-xs)] font-bold flex items-center gap-[var(--s-3)] shadow-lg"
                    >
                      <AlertCircle size={18} />
                      {loginError}
                    </motion.div>
                  )}

                  <div className="flex flex-col sm:flex-row gap-[var(--s-4)]">
                    <button 
                      type="submit" 
                      disabled={loading || !apiKey}
                      className="flex-1 btn-primary py-[var(--s-5)] text-[var(--fs-xs)] uppercase tracking-[0.2em] font-black disabled:opacity-30 disabled:grayscale transition-all flex items-center justify-center gap-[var(--s-3)] shadow-xl shadow-[var(--brand-glow)] group"
                    >
                      {loading ? (
                        <>
                          <RefreshCcw className="animate-spin" size={20} />
                          <span>Syncing...</span>
                        </>
                      ) : (
                        <>
                          <Zap size={20} className="fill-current group-hover:scale-110 transition-transform" />
                          <span>Establish Uplink</span>
                        </>
                      )}
                    </button>
                    <button 
                      type="button"
                      onClick={() => setStandardStep('config')}
                      className="px-[var(--s-8)] py-[var(--s-5)] rounded-[var(--r-md)] border border-[var(--line)] bg-[var(--bg-alt)]/40 text-[var(--muted)] font-black text-[var(--fs-xs)] uppercase tracking-widest hover:bg-[var(--glass-hover)] hover:text-[var(--ink)] transition-all flex items-center justify-center gap-[var(--s-3)] group"
                    >
                      <Settings2 size={20} className="group-hover:rotate-90 transition-transform" />
                      <span>Protocols</span>
                    </button>
                  </div>
                </form>

                <div className="pt-[var(--s-10)] border-t border-[var(--line)] flex justify-between items-center opacity-40">
                  <p className="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--muted)]">End-to-End Encryption</p>
                  <div className="flex gap-[var(--s-4)]">
                    <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] shadow-[0_0_8px_var(--success)]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-[var(--purple)]" />
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div 
                key="config-card"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="clay-card p-[var(--s-10)] space-y-[var(--s-8)]"
              >
                <div className="flex items-center justify-between mb-[var(--s-6)]">
                  <button 
                    onClick={() => setStandardStep('auth')}
                    className="flex items-center gap-[var(--s-2)] text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--muted)] hover:text-[var(--brand)] transition-colors"
                  >
                    <ArrowRight className="rotate-180" size={16} />
                    Back to Auth
                  </button>
                  <div className="flex items-center gap-[var(--s-3)]">
                    <div className="h-2 w-2 rounded-full bg-[var(--brand)] animate-pulse shadow-[0_0_8px_var(--brand)]" />
                    <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--ink)]">Neural Configuration Mode</span>
                  </div>
                </div>

                <div className="max-h-[600px] overflow-y-auto custom-scrollbar pr-[var(--s-4)]">
                  <NeuralTagManager onUpdate={() => {}} />
                </div>

                <div className="pt-[var(--s-8)] border-t border-[var(--line)] flex justify-between items-center">
                  <p className="text-[var(--fs-xs)] text-[var(--muted)] font-medium italic">Changes here affect all active harvesting nodes.</p>
                  <button 
                    onClick={() => setStandardStep('auth')}
                    className="btn-primary px-[var(--s-8)] py-[var(--s-3)] text-[var(--fs-xs)] uppercase font-black tracking-widest flex items-center gap-[var(--s-2)]"
                  >
                    Confirm Protocols
                    <ChevronRight size={16} />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

export default AuthPage;
