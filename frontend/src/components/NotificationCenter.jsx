import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, CheckCircle, AlertCircle, Info } from 'lucide-react';

const NotificationCenter = ({ isOpen, onClose, notifications }) => {
  const getIcon = (level) => {
    switch (level) {
      case 'good': return <CheckCircle className="text-[var(--success)]" size={18} />;
      case 'error': return <AlertCircle className="text-[var(--error)]" size={18} />;
      default: return <Info className="text-[var(--brand)]" size={18} />;
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-md z-[100]"
          />
          <motion.div 
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md glass-panel m-[var(--s-2)] z-[101] flex flex-col overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.3)]"
          >
            <div className="p-6 border-b border-[var(--glass-border)] flex items-center justify-between bg-[var(--bg-alt)]/50 backdrop-blur-2xl">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[var(--brand)]/10 text-[var(--brand)]">
                  <Bell size={20} />
                </div>
                <div>
                  <h2 className="text-[var(--fs-xl)] font-black tracking-tighter">Neural Feed</h2>
                  <p className="text-[10px] font-bold text-[var(--muted)] uppercase tracking-widest">System Updates</p>
                </div>
              </div>
              <button 
                onClick={onClose} 
                aria-label="Close notifications"
                className="w-10 h-10 flex items-center justify-center hover:bg-[var(--glass-hover)] rounded-xl transition-all text-[var(--muted)] hover:text-[var(--ink)]"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              {notifications.length > 0 ? (
                notifications.map((n, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="p-5 rounded-[var(--r-lg)] bg-[var(--glass)] border border-[var(--glass-border)] hover:bg-[var(--glass-hover)] hover:border-[var(--brand)]/30 cursor-pointer group transition-all duration-300 hover:-translate-x-1"
                  >
                    <div className="flex gap-4">
                      <div className="mt-1 p-2 rounded-lg bg-[var(--bg)]/50 group-hover:scale-110 transition-transform">
                        {getIcon(n.level)}
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="text-[var(--fs-sm)] font-black tracking-tight group-hover:text-[var(--brand)] transition-colors">{n.title}</h4>
                          <span className="text-[9px] font-bold text-[var(--muted)] opacity-60">
                            {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-[var(--fs-xs)] text-[var(--muted)] leading-relaxed">{n.message}</p>
                        
                        <div className="mt-3 flex items-center gap-2">
                          <div className={`w-1 h-1 rounded-full ${
                            n.level === 'good' ? 'bg-[var(--success)]' : 
                            n.level === 'error' ? 'bg-[var(--error)]' : 
                            'bg-[var(--brand)]'
                          }`} />
                          <span className="text-[8px] font-black uppercase tracking-[0.2em] text-[var(--muted)]">{n.level || 'info'} protocol</span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center opacity-40 text-center p-12">
                  <div className="w-20 h-20 rounded-3xl bg-[var(--glass-border)] flex items-center justify-center mb-6 animate-float">
                    <Bell size={40} strokeWidth={1.5} className="text-[var(--muted)]" />
                  </div>
                  <h3 className="text-[var(--fs-lg)] font-bold mb-2">Neural Silence</h3>
                  <p className="text-[var(--fs-xs)] max-w-[200px] leading-relaxed">The command center is quiet. All systems are operating within normal parameters.</p>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-[var(--glass-border)] bg-[var(--bg-alt)]/30">
              <button className="w-full py-4 text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--brand)] hover:bg-[var(--brand)]/10 rounded-2xl transition-all border border-[var(--brand)]/20 hover:border-[var(--brand)]">
                Purge All Feed
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default NotificationCenter;
