import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Tag, 
  Plus, 
  X, 
  Edit3, 
  Trash2, 
  Save, 
  GitBranch, 
  Eye, 
  Settings2,
  AlertCircle,
  CheckCircle2,
  Code2,
  Layers,
  Database,
  Network
} from 'lucide-react';

const NeuralTagManager = ({ onUpdate }) => {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingTag, setEditingTag] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [notification, setNotification] = useState(null);
  const containerRef = useRef(null);

  const API_KEY = localStorage.getItem('nn-api-key') || 'sales-agent-pro-2024';

  const fetchTags = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/admin/tags', {
        headers: { 'X-API-Key': API_KEY }
      });
      if (res.ok) {
        const data = await res.json();
        setTags(data);
      }
    } catch (err) {
      console.error('Failed to fetch tags', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    const isNew = !editingTag.id;
    try {
      const res = await fetch('/api/admin/tags', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify(editingTag)
      });
      if (res.ok) {
        showNotify(`Tag ${isNew ? 'registered' : 'updated'} successfully`);
        setEditingTag(null);
        fetchTags();
        if (onUpdate) onUpdate();
      }
    } catch (err) {
      showNotify('Failed to save protocol tag', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Terminate this protocol tag?')) return;
    try {
      const res = await fetch(`/api/admin/tags/${id}`, {
        method: 'DELETE',
        headers: { 'X-API-Key': API_KEY }
      });
      if (res.ok) {
        showNotify('Tag purged from neural core');
        fetchTags();
      }
    } catch (err) {
      showNotify('Purge failed', 'error');
    }
  };

  const showNotify = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Simplified dependency visualization logic
  const getDependencies = (tag) => {
    // In a real app, this would be structured data
    // For now, we simulate dependencies based on keywords in description
    const deps = tags.filter(t => 
      t.id !== tag.id && 
      (tag.description?.toLowerCase().includes(t.tag?.toLowerCase()) || 
       tag.tag?.toLowerCase().includes(t.tag?.toLowerCase().slice(0, -1)))
    );
    return deps;
  };

  const DependencyLines = () => {
    // This is a simplified visual representation of connections
    return (
      <div className="absolute inset-0 pointer-events-none opacity-20 overflow-hidden">
        <svg className="w-full h-full">
          {tags.map((tag, i) => {
            const deps = getDependencies(tag);
            return deps.map((dep, j) => (
              <motion.line
                key={`${tag.id}-${dep.id}`}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 2, delay: i * 0.1 }}
                x1={`${(i * 30) % 100}%`}
                y1={`${(i * 20) % 100}%`}
                x2={`${(tags.indexOf(dep) * 30) % 100}%`}
                y2={`${(tags.indexOf(dep) * 20) % 100}%`}
                stroke="var(--brand)"
                strokeWidth="1"
                strokeDasharray="4 2"
              />
            ));
          })}
        </svg>
      </div>
    );
  };

  return (
    <div className="space-y-[var(--s-6)] relative min-h-[400px]" ref={containerRef}>
      <DependencyLines />
      <div className="flex items-center justify-between relative z-10">
        <div className="flex items-center gap-[var(--s-3)]">
          <div className="p-[var(--s-2)] bg-[var(--brand)]/10 rounded-[var(--r-sm)] text-[var(--brand)]">
            <Layers size={20} />
          </div>
          <h3 className="text-[var(--fs-sm)] font-black uppercase tracking-widest text-[var(--ink)]">Neural Protocol Tags</h3>
        </div>
        <button 
          onClick={() => setEditingTag({ tag: '', description: '', priority: 'medium' })}
          className="flex items-center gap-[var(--s-2)] px-[var(--s-4)] py-[var(--s-2)] rounded-[var(--r-sm)] bg-[var(--brand)]/10 text-[var(--brand)] font-black text-[var(--fs-xs)] uppercase tracking-widest hover:bg-[var(--brand)] hover:text-white transition-all shadow-sm"
        >
          <Plus size={14} />
          Register Tag
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[var(--s-4)]">
        {tags.map((tag) => (
          <motion.div 
            key={tag.id}
            layoutId={`tag-${tag.id}`}
            className="clay-card p-[var(--s-5)] space-y-[var(--s-4)] group hover:bg-[var(--glass-hover)] transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-[var(--s-3)]">
                <div className="w-10 h-10 rounded-[var(--r-sm)] bg-black/20 flex items-center justify-center text-[var(--accent)] border border-white/5 shadow-inner">
                  <Code2 size={20} />
                </div>
                <div>
                  <p className="text-[var(--fs-sm)] font-black text-[var(--ink)] tracking-tight">#{tag.tag}</p>
                  <p className="text-[10px] text-[var(--muted)] font-bold uppercase tracking-widest">Protocol ID: {tag.id.slice(0, 8)}</p>
                </div>
              </div>
              <div className="flex gap-[var(--s-1)] opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => setEditingTag(tag)} className="p-2 hover:bg-[var(--brand)]/10 text-[var(--brand)] rounded-[var(--r-xs)] transition-all"><Edit3 size={14} /></button>
                <button onClick={() => handleDelete(tag.id)} className="p-2 hover:bg-[var(--error)]/10 text-[var(--error)] rounded-[var(--r-xs)] transition-all"><Trash2 size={14} /></button>
              </div>
            </div>

            <p className="text-[var(--fs-xs)] text-[var(--muted)] font-medium leading-[var(--lh-relaxed)] line-clamp-2">
              {tag.description}
            </p>

            {/* Dependency Visualization */}
            <div className="pt-[var(--s-3)] border-t border-[var(--line)]">
              <div className="flex items-center justify-between mb-[var(--s-2)]">
                <span className="text-[9px] font-black uppercase text-[var(--muted)] tracking-widest opacity-60">Neural Dependencies</span>
                <span className="text-[9px] font-black text-[var(--brand)] bg-[var(--brand)]/10 px-1.5 py-0.5 rounded uppercase">Active</span>
              </div>
              <div className="flex flex-wrap gap-[var(--s-2)]">
                {getDependencies(tag).length > 0 ? getDependencies(tag).map(dep => (
                  <div key={dep.id} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[var(--bg-subtle)] border border-[var(--line)] text-[8px] font-black text-[var(--muted)] uppercase tracking-tighter">
                    <GitBranch size={8} />
                    {dep.tag}
                  </div>
                )) : (
                  <span className="text-[8px] font-bold text-[var(--muted)] italic opacity-40">Root Protocol (No dependencies)</span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Edit Modal */}
      <AnimatePresence>
        {editingTag && (
          <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setEditingTag(null)} className="absolute inset-0 bg-black/95 backdrop-blur-2xl" />
            <motion.form 
              onSubmit={handleSave}
              initial={{ scale: 0.95, opacity: 0, y: 20 }} 
              animate={{ scale: 1, opacity: 1, y: 0 }} 
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="relative w-full max-w-xl clay-card overflow-hidden border-[var(--brand)]/30 shadow-2xl"
            >
              <div className="p-[var(--s-8)] border-b border-[var(--glass-border)] bg-[var(--brand)]/5 flex justify-between items-center">
                <div className="flex items-center gap-[var(--s-4)]">
                  <div className="w-12 h-12 rounded-[var(--r-md)] bg-[var(--brand)]/10 flex items-center justify-center text-[var(--brand)] shadow-inner">
                    <Settings2 size={24} />
                  </div>
                  <div>
                    <h2 className="text-[var(--fs-lg)] font-black uppercase tracking-tighter italic leading-none">
                      {editingTag.id ? 'Configure' : 'Initialize'} Protocol
                    </h2>
                    <p className="text-[9px] text-[var(--muted)] font-black uppercase tracking-[0.2em] mt-1">Direct Neural Core Interaction</p>
                  </div>
                </div>
                <button type="button" onClick={() => setEditingTag(null)} className="p-[var(--s-2)] hover:bg-white/5 rounded-full transition-all"><X size={20}/></button>
              </div>

              <div className="p-[var(--s-10)] space-y-[var(--s-8)]">
                <div className="space-y-[var(--s-3)]">
                  <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest ml-1 flex items-center gap-2">
                    <Tag size={12} className="text-[var(--brand)]" />
                    Tag Identifier
                  </label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. priority_scrape"
                    value={editingTag.tag} 
                    onChange={e => setEditingTag({...editingTag, tag: e.target.value})}
                    className="w-full bg-black/40 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner text-[var(--ink)]" 
                  />
                </div>

                <div className="space-y-[var(--s-3)]">
                  <label className="text-[var(--fs-xs)] font-black uppercase text-[var(--muted)] tracking-widest ml-1 flex items-center gap-2">
                    <Database size={12} className="text-[var(--purple)]" />
                    Protocol Logic
                  </label>
                  <textarea 
                    required
                    placeholder="Define neural processing rules for this tag..."
                    value={editingTag.description} 
                    onChange={e => setEditingTag({...editingTag, description: e.target.value})}
                    className="w-full bg-black/40 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-4)] font-medium text-[var(--fs-xs)] outline-none focus:border-[var(--brand)] resize-none transition-all shadow-inner text-[var(--ink)] leading-[var(--lh-relaxed)]" 
                    rows={4} 
                  />
                </div>

                {/* Real-time Preview */}
                <div className="p-[var(--s-4)] rounded-[var(--r-md)] bg-black/20 border border-white/5 space-y-[var(--s-3)]">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-black uppercase text-[var(--muted)] tracking-widest">Neural Preview</span>
                    <Eye size={12} className="text-[var(--brand)]" />
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="px-3 py-1 rounded-full bg-[var(--brand)]/10 border border-[var(--brand)]/20 text-[10px] font-black text-[var(--brand)] uppercase">
                      #{editingTag.tag || 'undefined'}
                    </div>
                    <div className="h-px flex-1 bg-[var(--line)]" />
                    <span className="text-[9px] font-bold text-[var(--muted)] uppercase">Status: Ready</span>
                  </div>
                </div>
              </div>

              <div className="p-[var(--s-8)] border-t border-[var(--glass-border)] flex gap-[var(--s-4)] bg-[var(--bg-alt)]/50">
                <button type="button" onClick={() => setEditingTag(null)} className="flex-1 py-[var(--s-3)] rounded-[var(--r-md)] border border-[var(--line)] font-black uppercase text-[var(--fs-xs)] tracking-widest hover:bg-white/5 transition-all text-[var(--muted)]">Discard</button>
                <button 
                  type="submit"
                  className="flex-[2] btn-primary py-[var(--s-3)] rounded-[var(--r-md)] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-[var(--s-3)] shadow-xl shadow-[var(--brand-glow)]"
                >
                  <Save size={18}/>
                  Commit Protocol
                </button>
              </div>
            </motion.form>
          </div>
        )}
      </AnimatePresence>

      {/* Global Notification */}
      <AnimatePresence>
        {notification && (
          <motion.div 
            initial={{ x: 100, opacity: 0 }} 
            animate={{ x: 0, opacity: 1 }} 
            exit={{ x: 100, opacity: 0 }} 
            className={`fixed bottom-10 right-10 z-[2000] p-[var(--s-4)] rounded-[var(--r-md)] border flex items-center gap-[var(--s-4)] shadow-2xl backdrop-blur-xl ${notification.type === 'error' ? 'bg-[var(--error)]/10 border-[var(--error)]/20 text-[var(--error)] shadow-[0_0_30px_rgba(239,68,68,0.2)]' : 'bg-[var(--success)]/10 border-[var(--success)]/20 text-[var(--success)] shadow-[0_0_30px_rgba(34,197,94,0.2)]'}`}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${notification.type === 'error' ? 'bg-[var(--error)]/20' : 'bg-[var(--success)]/20'}`}>
              {notification.type === 'error' ? <AlertCircle size={24}/> : <CheckCircle2 size={24}/>}
            </div>
            <div>
              <p className="font-black text-[var(--fs-xs)] uppercase tracking-tighter italic leading-none">{notification.type === 'error' ? 'Neural Error' : 'Uplink Success'}</p>
              <p className="text-[10px] font-bold uppercase opacity-80 mt-1">{notification.message}</p>
            </div>
            <button onClick={() => setNotification(null)} className="ml-4 opacity-40 hover:opacity-100 transition-opacity"><X size={16}/></button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NeuralTagManager;
