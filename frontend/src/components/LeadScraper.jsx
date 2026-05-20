import React, { useState } from 'react';
import { Search, MapPin, Zap, Loader2, Target, AlertCircle, Info, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LeadScraper = ({ onStarted }) => {
  const [niche, setNiche] = useState('');
  const [location, setLocation] = useState('');
  const [isScraping, setIsScraping] = useState(false);
  const [message, setMessage] = useState(null);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!niche.trim()) newErrors.niche = 'Market niche is required';
    if (!location.trim()) newErrors.location = 'Geographic zone is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleStartScrape = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsScraping(true);
    setMessage(null);

    try {
      const response = await fetch('/api/bot/scrape', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('nn-api-key') || ''
        },
        body: JSON.stringify({ niche, location }),
      });
      const data = await response.json();
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Deployment Successful: Harvester fleet is now scanning for leads.' });
        setNiche('');
        setLocation('');
        if (onStarted) onStarted();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Neural connection refused. Verify authorization.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Neural link failed. Check your uplink connection.' });
    } finally {
      setIsScraping(false);
    }
  };

  return (
    <div className="clay-card p-[var(--s-6)] md:p-[var(--s-10)] space-y-[var(--s-10)] relative overflow-hidden group">
      {/* Decorative Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--brand)] opacity-[0.03] blur-[100px] pointer-events-none group-hover:opacity-[0.06] transition-opacity duration-1000" />
      
      <div className="flex items-center gap-[var(--s-5)] relative z-10">
        <div className="w-[var(--s-16)] h-[var(--s-14)] bg-gradient-to-br from-[var(--brand)] to-[var(--purple)] rounded-[var(--r-md)] flex items-center justify-center shadow-xl border border-white/10 group-hover:rotate-6 transition-transform">
          <Zap className="text-white drop-shadow-md" size={28} />
        </div>
        <div>
          <h3 className="text-[var(--fs-xl)] md:text-[var(--fs-2xl)] font-black tracking-tighter text-[var(--ink)] italic leading-[var(--lh-tight)]">HARVESTER<span className="text-[var(--brand)]">PRO</span></h3>
          <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-[0.4em] mt-[var(--s-1)] flex items-center gap-[var(--s-2)]">
            <span className="w-1 h-1 rounded-full bg-[var(--brand)] animate-pulse shadow-[0_0_8px_var(--brand)]" />
            Autonomous Lead Acquisition Protocol
          </p>
        </div>
      </div>

      <form onSubmit={handleStartScrape} className="space-y-[var(--s-8)] relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--s-10)]">
          <div className="space-y-[var(--s-3)]">
            <div className="flex items-center justify-between px-1">
              <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                <Search size={12} className="text-[var(--brand)]" />
                Target Industry
              </label>
              {errors.niche && <span className="text-[var(--fs-xs)] font-bold text-[var(--error)] uppercase animate-pulse">{errors.niche}</span>}
            </div>
            <div className={`relative group ${errors.niche ? 'shake-error' : ''}`}>
              <input
                type="text"
                value={niche}
                onChange={(e) => { setNiche(e.target.value); if(errors.niche) setErrors(prev => ({...prev, niche: null})); }}
                placeholder="e.g. Modern Dentistry, SaaS Startups"
                className={`w-full bg-black/30 border ${errors.niche ? 'border-[var(--error)]/50' : 'border-[var(--glass-border)]'} rounded-[var(--r-md)] p-[var(--s-5)] font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all text-[var(--ink)] placeholder:text-[var(--muted)]/20 shadow-inner`}
              />
            </div>
          </div>
          <div className="space-y-[var(--s-3)]">
            <div className="flex items-center justify-between px-1">
              <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest flex items-center gap-[var(--s-2)]">
                <MapPin size={12} className="text-[var(--accent)]" />
                Geographic Zone
              </label>
              {errors.location && <span className="text-[var(--fs-xs)] font-bold text-[var(--error)] uppercase animate-pulse">{errors.location}</span>}
            </div>
            <div className={`relative group ${errors.location ? 'shake-error' : ''}`}>
              <input
                type="text"
                value={location}
                onChange={(e) => { setLocation(e.target.value); if(errors.location) setErrors(prev => ({...prev, location: null})); }}
                placeholder="e.g. Austin, TX • Global"
                className={`w-full bg-black/30 border ${errors.location ? 'border-[var(--error)]/50' : 'border-[var(--glass-border)]'} rounded-[var(--r-md)] p-[var(--s-5)] font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all text-[var(--ink)] placeholder:text-[var(--muted)]/20 shadow-inner`}
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isScraping}
          aria-busy={isScraping}
          aria-label={isScraping ? 'Deploying Neural Fleet' : 'Establish Acquisition Link'}
          className={`
            w-full flex items-center justify-center gap-[var(--s-4)] py-[var(--s-6)] rounded-[var(--r-lg)] font-black uppercase tracking-[0.2em] transition-all text-[var(--fs-xs)]
            ${isScraping ? 'bg-[var(--muted)]/10 text-[var(--muted)] cursor-not-allowed grayscale border border-[var(--line)]' : 'btn-primary shadow-[0_12px_24px_-8px_var(--brand-glow)]'}
          `}
        >
          {isScraping ? (
            <>
              <Loader2 className="animate-spin" size={24} />
              Deploying Neural Fleet...
            </>
          ) : (
            <>
              <Target size={24} className="fill-white" />
              Establish Acquisition Link
            </>
          )}
        </button>
      </form>

      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`p-[var(--s-6)] rounded-[var(--r-lg)] border flex items-start gap-[var(--s-5)] ${
              message.type === 'success' 
                ? 'bg-[var(--success)]/5 text-[var(--success)] border-[var(--success)]/20' 
                : 'bg-[var(--error)]/5 text-[var(--error)] border-[var(--error)]/20'
            }`}
          >
            <div className={`p-[var(--s-3)] rounded-[var(--r-md)] ${message.type === 'success' ? 'bg-[var(--success)]/10' : 'bg-[var(--error)]/10'}`}>
              {message.type === 'success' ? <Zap size={24} /> : <AlertCircle size={24} />}
            </div>
            <div className="flex-1 space-y-[var(--s-1)]">
              <p className="text-[var(--fs-xs)] font-black uppercase tracking-widest opacity-60">{message.type === 'success' ? 'Protocol Success' : 'Neural Error'}</p>
              <p className="text-[var(--fs-sm)] font-bold leading-[var(--lh-relaxed)]">{message.text}</p>
            </div>
            <button onClick={() => setMessage(null)} className="opacity-40 hover:opacity-100 transition-opacity p-[var(--s-2)]">
              <X size={18} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="pt-[var(--s-10)] border-t border-[var(--line)]">
        <h4 className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-[0.3em] mb-[var(--s-6)] flex items-center gap-[var(--s-3)]">
          <Database size={14} className="text-[var(--brand)]" />
          Neural Acquisition Streams
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-[var(--s-4)]">
          {[
            { name: 'Google Fleet', icon: Search, color: 'var(--brand)', tooltip: 'Global Search Engine Scraper' },
            { name: 'OSM Nodes', icon: MapPin, color: 'var(--accent)', tooltip: 'Map-based Location Extraction' },
            { name: 'Yelp Signals', icon: Target, color: 'var(--error)', tooltip: 'Business Directory Analysis' }
          ].map((source) => (
            <div key={source.name} className="clay-card p-[var(--s-5)] flex items-center justify-between group/source has-tooltip cursor-help transition-all hover:scale-[1.02] hover:bg-[var(--glass-hover)]">
              <div className="flex items-center gap-[var(--s-4)]">
                <div className="w-2 h-2 rounded-full bg-[var(--success)] shadow-[0_0_8px_var(--success)] animate-pulse" />
                <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--ink)]">{source.name}</span>
              </div>
              <source.icon size={16} className="text-[var(--muted)] group-hover/source:text-[var(--brand)] transition-colors" />
              <span className="nn-tooltip">{source.tooltip}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LeadScraper;
