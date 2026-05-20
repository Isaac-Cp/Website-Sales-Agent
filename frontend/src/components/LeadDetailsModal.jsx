import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Globe, Mail, MapPin, Calendar, CheckCircle2, Copy, Zap, Target, Shield, Database } from 'lucide-react';

const LeadDetailsModal = ({ lead, onClose }) => {
  const [emailPreview, setEmailPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    if (lead) {
      fetchEmailPreview();
    }
  }, [lead]);

  const fetchEmailPreview = async () => {
    setLoadingPreview(true);
    try {
      const res = await fetch(`/api/leads/${lead.id}/email-preview`);
      const data = await res.json();
      setEmailPreview(data);
    } catch (e) {
      console.error('Failed to fetch email preview:', e);
    } finally {
      setLoadingPreview(false);
    }
  };

  if (!lead) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/80 backdrop-blur-md"
        />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-2xl clay-card overflow-hidden flex flex-col max-h-[90vh] m-[var(--s-4)]"
        >
          {/* Header */}
          <div className="p-[var(--s-8)] border-b border-[var(--line)] flex items-start justify-between bg-gradient-to-r from-[var(--brand)]/5 to-transparent relative overflow-hidden">
            <div className="absolute top-0 right-0 p-[var(--s-8)] opacity-[0.03] pointer-events-none">
              <Target size={120} />
            </div>
            <div className="relative z-10">
              <h2 className="text-[var(--fs-2xl)] font-black tracking-tighter mb-[var(--s-2)] italic leading-[var(--lh-tight)] text-[var(--ink)]">{lead.business_name}</h2>
              <div className="flex items-center gap-[var(--s-3)] text-[var(--fs-xs)] font-black uppercase tracking-[0.2em]">
                <span className={`px-[var(--s-3)] py-[var(--s-1)] rounded-[var(--r-sm)] shadow-sm ${lead.status === 'contacted' ? 'bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20' : 'bg-[var(--muted)]/10 text-[var(--muted)] border border-[var(--muted)]/20'}`}>
                  {lead.status}
                </span>
                <span className="opacity-30">•</span>
                <span className="text-[var(--brand)]">{lead.niche}</span>
              </div>
            </div>
            <button 
              onClick={onClose}
              aria-label="Close lead details"
              className="p-[var(--s-3)] bg-black/20 hover:bg-black/40 rounded-[var(--r-md)] transition-all hover:rotate-90 active:scale-90 shadow-inner group has-tooltip"
            >
              <X size={20} className="text-[var(--muted)] group-hover:text-[var(--error)]" />
              <span className="nn-tooltip">Close Neural View</span>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-[var(--s-8)] space-y-[var(--s-10)] custom-scrollbar">
            {/* Quick Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-6)]">
              <div className="clay-card p-[var(--s-6)] space-y-[var(--s-5)] bg-black/10">
                <div className="flex items-center gap-[var(--s-4)] group cursor-pointer has-tooltip">
                  <div className="p-[var(--s-2)] rounded-[var(--r-sm)] bg-[var(--brand)]/10 text-[var(--brand)] group-hover:bg-[var(--brand)] group-hover:text-white transition-all shadow-inner">
                    <Globe size={18} />
                  </div>
                  <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-[var(--fs-sm)] font-bold hover:text-[var(--brand)] transition-colors truncate text-[var(--ink-dim)]">
                    {lead.website ? new URL(lead.website).hostname : 'No Website'}
                  </a>
                  <span className="nn-tooltip">Visit Domain</span>
                </div>
                <div className="flex items-center gap-[var(--s-4)] group cursor-pointer has-tooltip" onClick={() => { if (lead.email) { navigator.clipboard.writeText(lead.email); alert('Neural Copy: Email Address'); } }}>
                  <div className="p-[var(--s-2)] rounded-[var(--r-sm)] bg-[var(--purple)]/10 text-[var(--purple)] group-hover:bg-[var(--purple)] group-hover:text-white transition-all shadow-inner">
                    <Mail size={18} />
                  </div>
                  <span className="text-[var(--fs-sm)] font-bold truncate text-[var(--ink-dim)]">{lead.email || 'No email found'}</span>
                  <span className="nn-tooltip">Copy Signal</span>
                </div>
                <div className="flex items-center gap-[var(--s-4)] group cursor-pointer">
                  <div className="p-[var(--s-2)] rounded-[var(--r-sm)] bg-[var(--accent)]/10 text-[var(--accent)] transition-all shadow-inner">
                    <MapPin size={18} />
                  </div>
                  <span className="text-[var(--fs-sm)] font-bold text-[var(--ink-dim)]">{lead.city || 'Unknown Zone'}</span>
                </div>
              </div>

              <div className="clay-card p-[var(--s-6)] space-y-[var(--s-6)] bg-gradient-to-br from-[var(--brand)]/5 to-transparent">
                <div className="flex justify-between items-center">
                  <span className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest">Neural Stage</span>
                  <span className="text-[var(--fs-xs)] font-black text-[var(--brand)] uppercase tracking-widest bg-[var(--brand)]/10 px-[var(--s-2)] py-[var(--s-1)] rounded-[var(--r-sm)]">Stage 1/3</span>
                </div>
                <div className="space-y-[var(--s-4)]">
                  <div className="flex items-center gap-[var(--s-3)] text-[var(--fs-sm)] font-bold text-[var(--ink)]">
                    <div className="w-5 h-5 rounded-full bg-[var(--success)]/20 flex items-center justify-center">
                      <CheckCircle2 size={12} className="text-[var(--success)]" />
                    </div>
                    <span>Intelligence Acquired</span>
                  </div>
                  <div className="flex items-center gap-[var(--s-3)] text-[var(--fs-sm)] font-bold opacity-40 text-[var(--ink)]">
                    <div className="w-5 h-5 rounded-full bg-white/5 flex items-center justify-center">
                      <Calendar size={12} />
                    </div>
                    <span>Outreach Pending</span>
                  </div>
                  <div className="flex items-center gap-[var(--s-3)] text-[var(--fs-sm)] font-bold opacity-40 text-[var(--ink)]">
                    <div className="w-5 h-5 rounded-full bg-white/5 flex items-center justify-center">
                      <Zap size={12} />
                    </div>
                    <span>AI Analysis Pending</span>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Analysis Preview */}
            <div className="space-y-4">
              <h3 className="text-[var(--fs-lg)] font-black tracking-tight flex items-center gap-2">
                <Zap size={20} className="text-[var(--brand)]" />
                Neural Insight
              </h3>
              <div className="p-4 rounded-[var(--r-md)] bg-[var(--bg)]/40 border border-[var(--brand)]/20 text-[var(--fs-sm)] leading-relaxed italic text-[var(--muted)]">
                "Based on the initial scan of {lead.business_name}, we've identified key optimization opportunities in their local SEO and mobile performance. Outreach strategy is set to focus on high-conversion technical improvements."
              </div>
            </div>

            {/* Technical Audit & Business Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-panel p-4 space-y-3 border-[var(--glass-border)]">
                <h4 className="text-[10px] font-black uppercase text-[var(--brand)] tracking-widest flex items-center gap-2">
                  <Shield size={14} /> Technical Audit
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">SPF Status</p>
                    <p className={`text-[10px] font-bold ${lead.spf_status === 'pass' ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
                      {lead.spf_status || 'Unknown'}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">DMARC</p>
                    <p className={`text-[10px] font-bold ${lead.dmarc_status === 'pass' ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
                      {lead.dmarc_status || 'Unknown'}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">PageSpeed</p>
                    <p className="text-[10px] font-bold text-[var(--brand)]">{lead.pagespeed_score || 'N/A'}</p>
                  </div>
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">Email Quality</p>
                    <p className="text-[10px] font-bold text-[var(--purple)]">{lead.email_quality || 'N/A'}</p>
                  </div>
                </div>
              </div>

              <div className="glass-panel p-4 space-y-3 border-[var(--glass-border)]">
                <h4 className="text-[10px] font-black uppercase text-[var(--accent)] tracking-widest flex items-center gap-2">
                  <Database size={14} /> Firmographics
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">Size</p>
                    <p className="text-[10px] font-bold">{lead.business_size || 'N/A'}</p>
                  </div>
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">Staff</p>
                    <p className="text-[10px] font-bold">{lead.staff_count || '0'}</p>
                  </div>
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">Booking Widget</p>
                    <p className={`text-[10px] font-bold ${lead.booking_widget ? 'text-[var(--success)]' : 'text-[var(--muted)]'}`}>
                      {lead.booking_widget ? 'Detected' : 'None'}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-[var(--glass)] border border-[var(--glass-border)]">
                    <p className="text-[8px] text-[var(--muted)] uppercase font-bold">Pricing Mention</p>
                    <p className={`text-[10px] font-bold ${lead.pricing_mention ? 'text-[var(--brand)]' : 'text-[var(--muted)]'}`}>
                      {lead.pricing_mention ? 'Found' : 'Not found'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Email Template Preview */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-[var(--fs-lg)] font-black tracking-tight flex items-center gap-2">
                  <Mail size={20} className="text-[var(--brand)]" />
                  Generated Outreach Preview
                </h3>
                {emailPreview?.body && (
                  <button 
                    className="flex items-center gap-1.5 text-[var(--fs-xs)] font-bold text-[var(--brand)] hover:underline"
                    onClick={() => {
                      const template = `Subject: ${emailPreview.subject}\n\n${emailPreview.body}`;
                      navigator.clipboard.writeText(template);
                    }}
                  >
                    <Copy size={12} />
                    Copy Template
                  </button>
                )}
              </div>
              <div className="glass-panel p-6 bg-[var(--bg)]/20 border-[var(--glass-border)] font-mono text-[12px] space-y-4 relative min-h-[150px]">
                {loadingPreview ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-6 h-6 border-2 border-[var(--brand)]/20 border-t-[var(--brand)] rounded-full animate-spin" />
                  </div>
                ) : emailPreview?.body ? (
                  <>
                    <div className="pb-4 border-b border-[var(--glass-border)]">
                      <span className="text-[var(--muted)] uppercase font-bold text-[10px]">Subject:</span>
                      <p className="mt-1 font-bold">{emailPreview.subject}</p>
                    </div>
                    <div className="text-[var(--ink)] opacity-80 space-y-4 leading-relaxed whitespace-pre-wrap">
                      {emailPreview.body}
                    </div>
                    <div className="mt-4 pt-4 border-t border-[var(--glass-border)] flex justify-between items-center text-[10px] text-[var(--muted)] font-bold uppercase">
                      <span>Source: {emailPreview.source || 'AI Generation'}</span>
                      <span className="text-[var(--success)] flex items-center gap-1">
                        <Zap size={10} /> Neural Ready
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full py-8 text-[var(--muted)] italic text-center">
                    <Mail size={32} className="opacity-10 mb-2" />
                    <p>No outreach template has been generated for this lead yet.</p>
                    <button 
                      onClick={fetchEmailPreview}
                      className="mt-4 px-4 py-2 rounded-full border border-[var(--brand)]/30 text-[var(--brand)] font-bold not-italic hover:bg-[var(--brand)]/5 transition-all"
                    >
                      Retry Analysis
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-6 border-t border-[var(--line)] flex gap-3 bg-[var(--bg-alt)]">
            <button 
              className="flex-1 btn-primary py-3 flex items-center justify-center gap-2 font-black uppercase tracking-tighter"
              onClick={async () => {
                await fetch('/api/bot/run-now', { 
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ lead_id: lead.id })
                });
                onClose();
              }}
            >
              <Mail size={18} />
              Manual Outreach
            </button>
            <button 
              className="px-6 py-3 glass-panel hover:bg-[var(--accent)]/10 hover:text-[var(--accent)] hover:border-[var(--accent)]/30 transition-all font-bold uppercase text-[var(--fs-xs)]"
              onClick={async () => {
                await fetch('/api/leads/mark-high-value', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ id: lead.id })
                });
              }}
            >
              Prioritize
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default LeadDetailsModal;
