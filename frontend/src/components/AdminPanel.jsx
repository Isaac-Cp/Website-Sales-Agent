import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Trash2, 
  Edit3, 
  Save, 
  X, 
  Hash, 
  Tag, 
  Database, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCcw, 
  Lock, 
  ShieldCheck,
  UserCircle,
  Cpu,
  Zap,
  TrendingUp,
  Search
} from 'lucide-react';

const AdminPanel = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(() => localStorage.getItem('admin_authenticated') === 'true');
  const [password, setPassword] = useState('');
  const [activeSubTab, setActiveSubTab] = useState('keywords');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [notification, setNotification] = useState(null);
  const [formData, setFormData] = useState({});
  const [searchQuery, setSearchQuery] = useState('');

  const API_KEY = 'sales-agent-pro-2024';
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    'X-Admin-Token': localStorage.getItem('admin_token') || ''
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/admin/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      const data = await response.json();
      if (response.ok && data.token) {
        setIsAuthenticated(true);
        localStorage.setItem('admin_authenticated', 'true');
        localStorage.setItem('admin_token', data.token);
        showNotification('Access Granted');
      } else {
        showNotification(data.detail || 'Invalid Credentials', 'error');
      }
    } catch (err) {
      showNotification('Network error', 'error');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('admin_authenticated');
  };

  const fetchAdminData = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      let endpoint = '';
      if (activeSubTab === 'personas') {
        endpoint = '/api/personas';
      } else if (activeSubTab === 'users') {
        endpoint = '/api/admin/users';
      } else {
        endpoint = `/api/admin/${activeSubTab === 'metadata' ? 'metadata' : activeSubTab}`;
      }
      
      const res = await fetch(endpoint, { headers });
      if (!res.ok) throw new Error('Failed to fetch');
      const json = await res.json();
      setData(json);
    } catch (err) {
      showNotification('Failed to fetch data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, [activeSubTab, isAuthenticated]);

  useEffect(() => {
    if (editingItem) {
      setFormData(editingItem);
    } else {
      setFormData({});
    }
  }, [editingItem]);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      let endpoint = '';
      if (activeSubTab === 'personas') {
        endpoint = '/api/personas';
      } else {
        endpoint = `/api/admin/${activeSubTab === 'metadata' ? 'metadata' : activeSubTab}`;
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        showNotification(`${activeSubTab} saved successfully`);
        setEditingItem(null);
        fetchAdminData();
      } else {
        throw new Error('Save failed');
      }
    } catch (err) {
      showNotification(err.message || 'Save failed', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this entry permanently?')) return;
    try {
      let endpoint = '';
      if (activeSubTab === 'personas') {
        endpoint = `/api/personas/${id}`;
      } else {
        endpoint = `/api/admin/${activeSubTab}/${id}`;
      }

      const res = await fetch(endpoint, { method: 'DELETE', headers });
      if (res.ok) {
        showNotification('Deleted successfully');
        fetchAdminData();
      } else {
        throw new Error('Delete failed');
      }
    } catch (err) {
      showNotification(err.message || 'Delete failed', 'error');
    }
  };

  const filteredData = data.filter(item => {
    const searchStr = searchQuery.toLowerCase();
    if (activeSubTab === 'keywords') return (item.keyword || '').toLowerCase().includes(searchStr);
    if (activeSubTab === 'tags') return (item.tag || '').toLowerCase().includes(searchStr);
    if (activeSubTab === 'metadata') return (item.key || '').toLowerCase().includes(searchStr);
    if (activeSubTab === 'personas') return (item.name || '').toLowerCase().includes(searchStr);
    if (activeSubTab === 'users') return (item.username || item.email || '').toLowerCase().includes(searchStr);
    return true;
  });

  if (!isAuthenticated) {
    return (
      <div className="h-full flex items-center justify-center p-[var(--s-6)]">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md clay-card p-[var(--s-10)] text-center space-y-[var(--s-10)] relative overflow-hidden"
        >
          {/* Decorative Glow */}
          <div className="absolute -top-24 -left-24 w-48 h-48 bg-[var(--brand)]/10 blur-[60px]" />
          <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-[var(--purple)]/10 blur-[60px]" />

          <div className="w-[var(--s-20)] h-[var(--s-20)] bg-gradient-to-br from-[var(--brand)]/20 to-[var(--brand)]/5 rounded-[var(--r-md)] flex items-center justify-center mx-auto shadow-xl group hover:rotate-12 transition-transform duration-500 border border-white/5">
            <Lock size={48} className="text-[var(--brand)] drop-shadow-glow" />
          </div>
          <div>
            <h2 className="text-[var(--fs-2xl)] font-black tracking-tighter uppercase italic bg-gradient-to-r from-[var(--ink)] to-[var(--muted)] bg-clip-text text-transparent leading-[var(--lh-tight)]">Access Restricted</h2>
            <p className="text-[var(--fs-xs)] text-[var(--muted)] mt-[var(--s-3)] font-black uppercase tracking-[0.3em]">Neural Protocol Verification Required</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-[var(--s-6)] relative z-10">
            <div className="space-y-[var(--s-2)]">
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Neural Access Key"
                className="w-full bg-[var(--bg)]/50 border border-[var(--glass-border)] rounded-[var(--r-md)] p-[var(--s-5)] text-center font-black tracking-[0.5em] outline-none focus:border-[var(--brand)] transition-all text-[var(--ink)] shadow-inner placeholder:tracking-normal placeholder:opacity-30"
              />
            </div>
            <button type="submit" className="w-full btn-primary py-[var(--s-5)] rounded-[var(--r-md)] font-black uppercase tracking-widest flex items-center justify-center gap-[var(--s-3)] text-white shadow-xl shadow-[var(--brand-glow)] hover:scale-[1.02] active:scale-[0.98] hover:brightness-110 transition-all">
              <ShieldCheck size={20} />
              Bypass Security
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-[var(--s-10)] px-[var(--s-4)]">
      {/* Header & Sub-navigation */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-[var(--s-8)]">
        <div className="flex gap-[var(--s-2)] p-[var(--s-1)] bg-[var(--bg-alt)]/50 border border-[var(--glass-border)] rounded-[var(--r-md)] overflow-x-auto max-w-full backdrop-blur-xl shadow-xl">
          {[
            { id: 'keywords', label: 'Keywords', icon: Hash },
            { id: 'tags', label: 'Search Tags', icon: Tag },
            { id: 'metadata', label: 'Metadata', icon: Database },
            { id: 'personas', label: 'Personas', icon: UserCircle },
            { id: 'users', label: 'Users', icon: Users },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`flex items-center gap-[var(--s-3)] px-[var(--s-8)] py-[var(--s-3)] rounded-[var(--r-sm)] transition-all font-black text-[var(--fs-xs)] uppercase tracking-widest whitespace-nowrap ${activeSubTab === tab.id ? 'bg-[var(--brand)] text-white shadow-lg shadow-[var(--brand-glow)] scale-105' : 'text-[var(--muted)] hover:bg-[var(--glass-hover)] hover:text-[var(--ink)]'}`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>
        <button onClick={handleLogout} className="px-[var(--s-6)] py-[var(--s-3)] rounded-[var(--r-sm)] border border-[var(--error)]/20 text-[var(--fs-xs)] text-[var(--error)] hover:bg-[var(--error)]/10 font-black uppercase tracking-[0.2em] flex items-center gap-[var(--s-2)] transition-all hover:-translate-y-0.5">
          <Lock size={14} />
          Lock Terminal
        </button>
      </div>

      <div className="clay-card overflow-hidden border-[var(--brand)]/20 shadow-2xl relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--brand)]/5 blur-[80px] pointer-events-none" />
        
        <div className="p-[var(--s-10)] border-b border-[var(--glass-border)] flex flex-col lg:flex-row justify-between lg:items-center gap-[var(--s-8)] bg-gradient-to-br from-[var(--brand)]/10 via-transparent to-transparent relative z-10">
          <div className="flex items-center gap-[var(--s-6)]">
            <div className="w-[var(--s-16)] h-[var(--s-16)] rounded-[var(--r-md)] bg-gradient-to-br from-[var(--brand)]/20 to-[var(--brand)]/5 flex items-center justify-center text-[var(--brand)] shadow-lg border border-white/5">
              {activeSubTab === 'keywords' && <Hash size={32} />}
              {activeSubTab === 'tags' && <Tag size={32} />}
              {activeSubTab === 'metadata' && <Database size={32} />}
              {activeSubTab === 'personas' && <UserCircle size={32} />}
            </div>
            <div>
              <h2 className="text-[var(--fs-xl)] font-black tracking-tighter capitalize leading-none text-[var(--ink)]">{activeSubTab} Core</h2>
              <p className="text-[var(--fs-xs)] text-[var(--muted)] mt-[var(--s-2)] font-black uppercase tracking-widest opacity-60">Neural Search Parameters & AI Intelligence</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-[var(--s-4)]">
            <div className="relative group">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--muted)] group-focus-within:text-[var(--brand)] transition-colors" />
              <input 
                type="text" 
                placeholder={`Filter ${activeSubTab}...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-[var(--bg)]/50 border border-[var(--glass-border)] rounded-[var(--r-md)] py-[var(--s-4)] pl-[var(--s-12)] pr-[var(--s-8)] text-[var(--fs-sm)] font-bold outline-none focus:border-[var(--brand)] transition-all w-full md:w-80 text-[var(--ink)] placeholder:text-[var(--muted)]/40 shadow-inner"
              />
            </div>
            <div className="flex gap-[var(--s-3)]">
              <button 
                onClick={fetchAdminData}
                className="p-[var(--s-3)] clay-card hover:bg-white/5 rounded-[var(--r-sm)] text-[var(--muted)] transition-all"
                title="Refresh Data"
              >
                <RefreshCcw size={20} className={loading ? 'animate-spin' : ''} />
              </button>
              <button 
                onClick={() => setEditingItem({})}
                className="btn-primary flex items-center gap-[var(--s-2)] px-[var(--s-6)]"
              >
                <Plus size={20} />
                New Entry
              </button>
            </div>
          </div>
        </div>

        {loading && data.length === 0 ? (
          <div className="p-32 flex flex-col items-center justify-center gap-6">
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
              className="w-14 h-14 border-4 border-[var(--brand)]/20 border-t-[var(--brand)] rounded-full" 
            />
            <p className="text-[12px] font-black uppercase text-[var(--brand)] tracking-widest animate-pulse">Syncing Admin Data...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[var(--fs-sm)]">
              <thead className="bg-[var(--glass-hover)] border-b border-[var(--glass-border)]">
                <tr>
                  {activeSubTab === 'keywords' && (
                    <>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Keyword</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Category</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Weight</th>
                    </>
                  )}
                  {activeSubTab === 'tags' && (
                    <>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Tag</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Description</th>
                    </>
                  )}
                  {activeSubTab === 'metadata' && (
                    <>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Key</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Value</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Description</th>
                    </>
                  )}
                  {activeSubTab === 'personas' && (
                    <>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Name</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Status</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Strategy Snippet</th>
                    </>
                  )}
                  {activeSubTab === 'users' && (
                    <>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">User</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Role</th>
                      <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] tracking-[0.2em]">Last Access</th>
                    </>
                  )}
                  <th className="p-6 font-black uppercase text-[10px] text-[var(--muted)] text-right tracking-[0.2em]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--line)]">
                {filteredData.map((item, i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors group">
                    {activeSubTab === 'keywords' && (
                      <>
                        <td className="p-6 font-bold text-[var(--brand)]">{item.keyword}</td>
                        <td className="p-6"><span className="px-3 py-1 rounded-full bg-white/5 border border-white/5 text-[10px] font-black uppercase">{item.category}</span></td>
                        <td className="p-6 font-mono text-[var(--muted)] font-bold">{item.weight}</td>
                      </>
                    )}
                    {activeSubTab === 'tags' && (
                      <>
                        <td className="p-6 font-bold text-[var(--accent)]">{item.tag}</td>
                        <td className="p-6 text-[var(--muted)] text-[var(--fs-xs)] font-medium leading-relaxed max-w-md">{item.description}</td>
                      </>
                    )}
                    {activeSubTab === 'metadata' && (
                      <>
                        <td className="p-6 font-bold text-[var(--purple)]">{item.key}</td>
                        <td className="p-6">
                          <code className="px-3 py-1.5 bg-black/40 rounded-lg text-[10px] font-mono max-w-[240px] truncate block border border-white/5">
                            {item.value}
                          </code>
                        </td>
                        <td className="p-6 text-[var(--muted)] text-[var(--fs-xs)] font-medium">{item.description}</td>
                      </>
                    )}
                    {activeSubTab === 'personas' && (
                      <>
                        <td className="p-6">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-[var(--brand)]/10 flex items-center justify-center text-[var(--brand)]">
                              {item.icon === 'Cpu' ? <Cpu size={16}/> : item.icon === 'TrendingUp' ? <TrendingUp size={16}/> : <Zap size={16}/>}
                            </div>
                            <span className="font-bold">{item.name}</span>
                          </div>
                        </td>
                        <td className="p-6">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${item.active ? 'bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20' : 'bg-[var(--muted)]/10 text-[var(--muted)] border border-[var(--muted)]/20'}`}>
                            {item.active ? 'Active' : 'Disabled'}
                          </span>
                        </td>
                        <td className="p-6 text-[var(--muted)] text-[var(--fs-xs)] font-medium truncate max-w-[200px]">{item.strategy_prompt}</td>
                      </>
                    )}
                    {activeSubTab === 'users' && (
                      <>
                        <td className="p-6">
                          <div className="flex flex-col">
                            <span className="font-bold text-[var(--ink)]">{item.username}</span>
                            <span className="text-[10px] text-[var(--muted)]">{item.email}</span>
                          </div>
                        </td>
                        <td className="p-6">
                          <span className={`px-2 py-1 rounded bg-[var(--brand)]/10 text-[var(--brand)] text-[10px] font-black uppercase`}>
                            {item.role || 'Operator'}
                          </span>
                        </td>
                        <td className="p-6 text-[var(--fs-xs)] text-[var(--muted)] font-bold">
                          {item.last_login ? new Date(item.last_login).toLocaleString() : 'Never'}
                        </td>
                      </>
                    )}
                    <td className="p-6 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => setEditingItem(item)} className="p-2.5 hover:bg-[var(--brand)]/10 text-[var(--brand)] rounded-xl transition-all"><Edit3 size={18} /></button>
                        {(activeSubTab !== 'metadata') && (
                          <button onClick={() => handleDelete(item.id)} className="p-2.5 hover:bg-[var(--error)]/10 text-[var(--error)] rounded-xl transition-all"><Trash2 size={18} /></button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredData.length === 0 && !loading && (
                  <tr>
                    <td colSpan={5} className="p-24 text-center">
                      <div className="flex flex-col items-center gap-4 text-[var(--muted)]">
                        <Search size={40} className="opacity-20" />
                        <p className="font-bold italic text-[var(--fs-sm)] uppercase tracking-widest">No matching protocol entries found</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Admin Edit Modal */}
      <AnimatePresence>
        {editingItem && (
          <div className="fixed inset-0 z-[500] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setEditingItem(null)} className="absolute inset-0 bg-black/90 backdrop-blur-xl" />
            <motion.form 
              onSubmit={handleSave}
              initial={{ scale: 0.9, y: 40, opacity: 0 }} 
              animate={{ scale: 1, y: 0, opacity: 1 }} 
              exit={{ scale: 0.9, y: 40, opacity: 0 }}
              className="relative w-full max-w-2xl glass-panel overflow-hidden border-[var(--brand)]/30 shadow-[0_0_80px_rgba(14,165,233,0.15)]"
            >
              <div className="p-8 border-b border-[var(--glass-border)] bg-[var(--brand)]/5 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-[var(--brand)]/10 flex items-center justify-center text-[var(--brand)]">
                    <Edit3 size={24} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black uppercase tracking-tighter italic leading-none">
                      {editingItem.id ? 'Update' : 'Register'} {activeSubTab.slice(0, -1)}
                    </h2>
                    <p className="text-[10px] text-[var(--muted)] font-bold uppercase tracking-widest mt-1">Commit changes to neural database</p>
                  </div>
                </div>
                <button type="button" onClick={() => setEditingItem(null)} className="p-3 hover:bg-white/5 rounded-2xl transition-all"><X size={24}/></button>
              </div>
              <div className="p-10 space-y-8 max-h-[60vh] overflow-y-auto custom-scrollbar">
                {activeSubTab === 'keywords' && (
                  <>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Search Keyword</label>
                      <input 
                        type="text" 
                        required
                        placeholder="e.g. solar installers"
                        value={formData.keyword || ''} 
                        onChange={e => setFormData({...formData, keyword: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Category</label>
                        <input 
                          type="text" 
                          required
                          placeholder="e.g. Energy"
                          value={formData.category || ''} 
                          onChange={e => setFormData({...formData, category: e.target.value})}
                          className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                        />
                      </div>
                      <div className="space-y-3">
                        <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Neural Weight (0.1 - 5.0)</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          min="0.1"
                          max="5.0"
                          value={formData.weight || 1.0} 
                          onChange={e => setFormData({...formData, weight: parseFloat(e.target.value)})}
                          className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                        />
                      </div>
                    </div>
                  </>
                )}
                {activeSubTab === 'tags' && (
                  <>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Neural Tag Name</label>
                      <input 
                        type="text" 
                        required
                        placeholder="e.g. high_value_niche"
                        value={formData.tag || ''} 
                        onChange={e => setFormData({...formData, tag: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                      />
                    </div>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Tag Definition</label>
                      <textarea 
                        required
                        placeholder="Define how this tag should be applied..."
                        value={formData.description || ''} 
                        onChange={e => setFormData({...formData, description: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] resize-none transition-all shadow-inner" 
                        rows={4} 
                      />
                    </div>
                  </>
                )}
                {activeSubTab === 'metadata' && (
                  <>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Configuration Key</label>
                      <input 
                        type="text" 
                        required
                        readOnly={!!editingItem.id}
                        placeholder="e.g. MAX_DAILY_ACTIONS"
                        value={formData.key || ''} 
                        onChange={e => setFormData({...formData, key: e.target.value})}
                        className={`w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner ${editingItem.id ? 'opacity-50 cursor-not-allowed' : ''}`} 
                      />
                    </div>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Current Value</label>
                      <textarea 
                        required
                        placeholder="Enter configuration value..."
                        value={formData.value || ''} 
                        onChange={e => setFormData({...formData, value: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-mono text-[var(--fs-xs)] outline-none focus:border-[var(--brand)] resize-none transition-all shadow-inner" 
                        rows={4} 
                      />
                    </div>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Internal Description</label>
                      <input 
                        type="text" 
                        placeholder="What does this setting control?"
                        value={formData.description || ''} 
                        onChange={e => setFormData({...formData, description: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                      />
                    </div>
                  </>
                )}
                {activeSubTab === 'personas' && (
                  <>
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Persona Identity</label>
                        <input 
                          type="text" 
                          required
                          placeholder="e.g. Technical Auditor"
                          value={formData.name || ''} 
                          onChange={e => setFormData({...formData, name: e.target.value})}
                          className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                        />
                      </div>
                      <div className="space-y-3">
                        <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Icon Style</label>
                        <div className="flex gap-2 h-[58px]">
                          {['Cpu', 'TrendingUp', 'Zap'].map(icon => (
                            <button 
                              key={icon}
                              type="button"
                              onClick={() => setFormData({...formData, icon})}
                              className={`flex-1 rounded-xl border transition-all flex items-center justify-center ${formData.icon === icon ? 'bg-[var(--brand)]/20 border-[var(--brand)] text-[var(--brand)] shadow-lg' : 'bg-black/40 border-[var(--glass-border)] text-[var(--muted)]'}`}
                            >
                              {icon === 'Cpu' ? <Cpu size={20} /> : icon === 'TrendingUp' ? <TrendingUp size={20} /> : <Zap size={20} />}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest ml-1">Identity Description</label>
                      <input 
                        type="text" 
                        placeholder="Brief summary of this persona's focus..."
                        value={formData.description || ''} 
                        onChange={e => setFormData({...formData, description: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-4 font-bold text-[var(--fs-sm)] outline-none focus:border-[var(--brand)] transition-all shadow-inner" 
                      />
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center ml-1">
                        <label className="text-[10px] font-black uppercase text-[var(--muted)] tracking-widest">Neural Strategy Prompt</label>
                        <span className="text-[9px] font-black text-[var(--brand)] bg-[var(--brand)]/10 px-2 py-0.5 rounded uppercase tracking-tighter">AI Logic Core</span>
                      </div>
                      <textarea 
                        required
                        placeholder="Enter the deep strategy instructions for this persona..."
                        value={formData.strategy_prompt || ''} 
                        onChange={e => setFormData({...formData, strategy_prompt: e.target.value})}
                        className="w-full bg-black/60 border border-[var(--glass-border)] rounded-2xl p-5 font-mono text-[12px] outline-none focus:border-[var(--brand)] resize-none transition-all shadow-inner leading-relaxed" 
                        rows={8} 
                      />
                    </div>
                    <div className="flex items-center gap-4 p-5 bg-[var(--brand)]/5 rounded-2xl border border-[var(--brand)]/10">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center cursor-pointer transition-all ${formData.active ? 'bg-[var(--success)]/20 text-[var(--success)] shadow-[0_0_15px_rgba(34,197,94,0.2)]' : 'bg-white/5 text-[var(--muted)]'}`} onClick={() => setFormData({...formData, active: !formData.active})}>
                        <ShieldCheck size={24} />
                      </div>
                      <div className="flex-1">
                        <p className="text-[var(--fs-xs)] font-black uppercase tracking-tighter">Persona Protocol Status</p>
                        <p className="text-[10px] text-[var(--muted)] font-medium mt-0.5">{formData.active ? 'This persona is currently authorized for outreach generation.' : 'This persona is currently offline and will not be used.'}</p>
                      </div>
                      <button 
                        type="button"
                        onClick={() => setFormData({...formData, active: !formData.active})}
                        className={`px-4 py-2 rounded-lg font-black text-[10px] uppercase tracking-widest transition-all ${formData.active ? 'bg-[var(--success)] text-white' : 'bg-white/10 text-[var(--muted)]'}`}
                      >
                        {formData.active ? 'Enabled' : 'Disabled'}
                      </button>
                    </div>
                  </>
                )}
              </div>
              <div className="p-8 border-t border-[var(--glass-border)] flex gap-4 bg-[var(--bg-alt)]">
                <button type="button" onClick={() => setEditingItem(null)} className="flex-1 glass-panel py-4 font-black uppercase text-[10px] tracking-widest hover:bg-white/5 transition-all">Cancel</button>
                <button 
                  type="submit"
                  className="flex-[2] btn-primary py-4 font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 shadow-xl shadow-[var(--brand-glow)]"
                >
                  <Save size={20}/>
                  Commit Protocol
                </button>
              </div>
            </motion.form>
          </div>
        )}
      </AnimatePresence>

      {/* Real-time Notifications */}
      <AnimatePresence>
        {notification && (
          <motion.div 
            initial={{ x: 100, opacity: 0 }} 
            animate={{ x: 0, opacity: 1 }} 
            exit={{ x: 100, opacity: 0 }} 
            className={`fixed bottom-10 right-10 z-[600] p-5 rounded-2xl border flex items-center gap-4 shadow-2xl backdrop-blur-xl ${notification.type === 'error' ? 'bg-[var(--error)]/10 border-[var(--error)]/20 text-[var(--error)] shadow-[0_0_30px_rgba(239,68,68,0.2)]' : 'bg-[var(--success)]/10 border-[var(--success)]/20 text-[var(--success)] shadow-[0_0_30px_rgba(34,197,94,0.2)]'}`}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${notification.type === 'error' ? 'bg-[var(--error)]/20' : 'bg-[var(--success)]/20'}`}>
              {notification.type === 'error' ? <AlertCircle size={24}/> : <CheckCircle2 size={24}/>}
            </div>
            <div>
              <p className="font-black text-sm uppercase tracking-tighter italic leading-none">{notification.type === 'error' ? 'System Error' : 'Success'}</p>
              <p className="text-[11px] font-bold uppercase opacity-80 mt-1">{notification.message}</p>
            </div>
            <button onClick={() => setNotification(null)} className="ml-4 opacity-40 hover:opacity-100 transition-opacity"><X size={16}/></button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdminPanel;
