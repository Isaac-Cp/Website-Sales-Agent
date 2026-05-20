import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, Cpu, TrendingUp, Zap, Shield } from 'lucide-react';

const PersonaModal = ({ persona, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    icon: 'Zap',
    strategy_prompt: '',
    active: true
  });

  useEffect(() => {
    if (persona) {
      setFormData({
        name: persona.name || '',
        description: persona.description || '',
        icon: persona.icon || 'Zap',
        strategy_prompt: persona.strategy_prompt || '',
        active: persona.active !== undefined ? persona.active : true
      });
    }
  }, [persona]);

  if (!persona) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/80 backdrop-blur-md"
        />
        
        <motion.div 
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          className="relative w-full max-w-2xl glass-panel overflow-hidden flex flex-col max-h-[90vh] shadow-2xl border-[var(--brand)]/20"
        >
          {/* Header */}
          <div className="p-6 border-b border-[var(--glass-border)] flex justify-between items-center bg-[var(--brand)]/5">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[var(--brand)]/20 flex items-center justify-center text-[var(--brand)]">
                {formData.icon === 'Cpu' ? <Cpu size={24} /> : formData.icon === 'TrendingUp' ? <TrendingUp size={24} /> : <Zap size={24} />}
              </div>
              <div>
                <h2 className="text-[var(--fs-xl)] font-black tracking-tighter">
                  {formData.name ? `Edit ${formData.name}` : 'New Neural Persona'}
                </h2>
                <p className="text-[var(--fs-xs)] text-[var(--muted)] font-bold uppercase tracking-widest">Strategy Protocol Configuration</p>
              </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl transition-all"><X size={20} /></button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest">Persona Name</label>
                <input 
                  type="text" 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-[var(--bg)]/40 border border-[var(--glass-border)] rounded-[var(--r-md)] p-3 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all text-[var(--ink)]"
                  placeholder="e.g. Technical Auditor"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest">Icon Style</label>
                <div className="flex gap-2">
                  {['Cpu', 'TrendingUp', 'Zap'].map(icon => (
                    <button 
                      key={icon}
                      onClick={() => setFormData({...formData, icon})}
                      className={`flex-1 p-3 rounded-[var(--r-md)] border transition-all flex justify-center ${formData.icon === icon ? 'bg-[var(--brand)]/20 border-[var(--brand)] text-[var(--brand)]' : 'bg-[var(--bg)]/40 border-[var(--glass-border)] text-[var(--muted)]'}`}
                    >
                      {icon === 'Cpu' ? <Cpu size={18} /> : icon === 'TrendingUp' ? <TrendingUp size={18} /> : <Zap size={18} />}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest">Brief Description</label>
              <textarea 
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="w-full bg-[var(--bg)]/40 border border-[var(--glass-border)] rounded-[var(--r-md)] p-3 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all resize-none text-[var(--ink)]"
                placeholder="How should this persona be described in the interface?"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest">Neural Strategy Prompt</label>
                <span className="text-[8px] font-bold text-[var(--brand)] px-2 py-0.5 bg-[var(--brand)]/10 rounded uppercase">AI Logic Core</span>
              </div>
              <textarea 
                rows={6}
                value={formData.strategy_prompt}
                onChange={(e) => setFormData({...formData, strategy_prompt: e.target.value})}
                className="w-full bg-[var(--bg)]/40 border border-[var(--glass-border)] rounded-[var(--r-md)] p-4 font-mono text-[12px] outline-none focus:border-[var(--brand)] transition-all resize-none leading-relaxed text-[var(--ink)]"
                placeholder="Define the specific instructions, tone, and goals for this AI personality..."
              />
            </div>

            <div className="flex items-center gap-3 p-4 bg-[var(--brand)]/5 rounded-[var(--r-lg)] border border-[var(--brand)]/10">
              <Shield size={20} className="text-[var(--brand)]" />
              <div className="flex-1">
                <p className="text-[var(--fs-xs)] font-bold">Protocol Safety Check</p>
                <p className="text-[10px] text-[var(--muted)]">This strategy will be injected into the LLM system prompt for all outreach generated using this persona.</p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-[var(--glass-border)] flex gap-3 bg-[var(--bg-alt)]">
            <button 
              onClick={onClose}
              className="px-6 py-3 glass-panel hover:bg-white/5 transition-all font-bold uppercase text-[var(--fs-xs)]"
            >
              Discard Changes
            </button>
            <button 
              onClick={() => onSave(formData)}
              className="flex-1 btn-primary py-3 flex items-center justify-center gap-2 font-black uppercase tracking-tighter"
            >
              <Save size={18} />
              Commit Strategy to Memory
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default PersonaModal;
