import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Users, 
  Mail, 
  TrendingUp, 
  Settings, 
  Bell, 
  Search, 
  ChevronRight,
  Zap,
  Filter,
  RefreshCcw,
  LogOut,
  Target,
  BarChart3,
  Menu,
  X,
  MessageSquare,
  Shield,
  Cpu,
  Bot,
  ArrowUp,
  Terminal,
  CheckCircle2,
  AlertCircle,
  Info,
  Layout,
  Play,
  Sun,
  Moon
} from 'lucide-react';
import { motion, AnimatePresence, useScroll, useSpring, useTransform } from 'framer-motion';
import NotificationCenter from './components/NotificationCenter';
import LeadDetailsModal from './components/LeadDetailsModal';
import LeadScraper from './components/LeadScraper';
import PersonaModal from './components/PersonaModal';
import AdminPanel from './components/AdminPanel';
import { trackDashboardView } from './firebase';

import OverviewDashboard from './components/OverviewDashboard';
import LeadsTable from './components/LeadsTable';
import HarvesterPanel from './components/HarvesterPanel';
import CampaignsPanel from './components/CampaignsPanel';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import AuthPage from './components/AuthPage';
import SettingsPage from './components/SettingsPage';
import SystemMonitor from './components/SystemMonitor';

const App = () => {
  const [theme, setTheme] = useState(() => localStorage.getItem('dashboard-theme') || 'dark');
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('nn-api-key'));
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('nn-api-key') || '');
  const [loginError, setLoginError] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [bulkSelection, setBulkSelection] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [activeFilter, setActiveFilter] = useState('All Niches');
  const [searchQuery, setSearchQuery] = useState('');
  const [logs, setLogs] = useState([]);
  const [socket, setSocket] = useState(null);
  const [systemStats, setSystemStats] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [editingPersona, setEditingPersona] = useState(null);
  const [maintenanceRunning, setMaintenanceRunning] = useState({});
  const [isScrapeModalOpen, setIsScrapeModalOpen] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const { scrollYProgress } = useScroll();
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  const headerOpacity = useTransform(smoothProgress, [0, 0.05], [1, 0.9]);
  const headerScale = useTransform(smoothProgress, [0, 0.05], [1, 0.99]);
  const sidebarX = useTransform(smoothProgress, [0, 0.05], [0, -5]);
  const contentY = useTransform(smoothProgress, [0, 0.05], [0, -10]);

  const showFeedback = (message, type = 'success') => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  const handleLogin = async (key) => {
    setLoading(true);
    setLoginError('');
    try {
      const response = await fetch('/api/v2/system/stats', {
        headers: { 'X-API-Key': key }
      });
      if (response.ok) {
        localStorage.setItem('nn-api-key', key);
        setApiKey(key);
        setIsAuthenticated(true);
        showFeedback('Neural link established successfully');
      } else {
        setLoginError('Neural handshake failed. Verify access key.');
      }
    } catch (err) {
      setLoginError('Neural uplink connection timeout.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (settings) => {
    setLoading(true);
    try {
      const res = await fetch('/api/bot/config', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        await fetchData();
        showFeedback('System protocols updated successfully');
      }
    } catch (err) {
      console.error('Settings update failed', err);
      showFeedback('Protocol update failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = () => {
    if (window.confirm('Disconnect from Neural Command Center?')) {
      localStorage.removeItem('nn-api-key');
      setIsAuthenticated(false);
      setApiKey('');
      setData(null);
      window.location.reload();
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const fetchData = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const response = await fetch('/api/dashboard', {
        headers: { 'X-API-Key': apiKey }
      });
      const payload = await response.json();
      setData(payload);
      setError(null);
    } catch (err) {
      setError('Failed to sync with neural command center');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, apiKey]);

  const handleBulkAction = async (action) => {
    if (bulkSelection.length === 0) return;
    try {
      const response = await fetch('/api/leads/bulk-update', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({ ids: bulkSelection, action })
      });
      if (response.ok) {
        setBulkSelection([]);
        await fetchData();
        showFeedback(`Bulk ${action} completed`);
      }
    } catch (err) {
      console.error('Bulk action failed:', err);
      showFeedback('Bulk action failed', 'error');
    }
  };

  const handleBotAction = async (action, payload = {}) => {
    try {
      let endpoint = '';
      let method = 'POST';
      switch (action) {
        case 'start': endpoint = '/api/bot/run-now'; break;
        case 'pause': endpoint = '/api/bot/pause'; break;
        case 'stop': endpoint = '/api/bot/stop'; break;
        case 'refresh': await fetchData(); return;
        case 'config': endpoint = '/api/bot/config'; break;
        default: return;
      }
      
      const response = await fetch(endpoint, { 
        method,
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: Object.keys(payload).length > 0 ? JSON.stringify(payload) : undefined
      });
      if (response.ok) {
        await fetchData();
        showFeedback(`Bot protocol: ${action} initiated`);
      }
    } catch (err) {
      console.error('Bot action failed:', err);
      showFeedback('Neural node communication failed', 'error');
    }
  };

  const fetchLogs = useCallback(async () => {
    try {
      const response = await fetch('/api/logs?lines=100', {
        headers: { 'X-API-Key': apiKey }
      });
      const payload = await response.json();
      if (payload.logs) setLogs(payload.logs);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    }
  }, [apiKey]);

  const fetchSystemStats = useCallback(async () => {
    try {
      const response = await fetch('/api/v2/system/stats', {
        headers: { 'X-API-Key': apiKey }
      });
      const payload = await response.json();
      setSystemStats(payload);
    } catch (err) {
      console.error('Failed to fetch system stats:', err);
    }
  }, [apiKey]);

  const runMaintenance = async (task) => {
    setMaintenanceRunning(prev => ({ ...prev, [task]: true }));
    try {
      await fetch('/api/v2/system/maintenance/run', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({ task })
      });
      await fetchSystemStats();
      showFeedback(`${task.replace('_', ' ')} completed`);
    } catch (err) {
      console.error('Maintenance failed:', err);
      showFeedback('Maintenance protocol failed', 'error');
    } finally {
      setMaintenanceRunning(prev => ({ ...prev, [task]: false }));
    }
  };

  const fetchPersonas = useCallback(async () => {
    try {
      const response = await fetch('/api/personas', {
        headers: { 'X-API-Key': apiKey }
      });
      const payload = await response.json();
      setPersonas(payload);
    } catch (err) {
      console.error('Failed to fetch personas:', err);
    }
  }, [apiKey]);

  useEffect(() => {
    trackDashboardView();
    fetchData();
    fetchPersonas();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData, fetchPersonas]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('dashboard-theme', theme);
  }, [theme]);

  useEffect(() => {
    if (activeTab === 'system') {
      fetchSystemStats();
      const interval = setInterval(fetchSystemStats, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab, fetchSystemStats]);

  useEffect(() => {
    if (activeTab === 'logs' && !socket) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        setLogs(prev => [event.data, ...prev].slice(0, 100));
      };

      ws.onclose = () => setSocket(null);
      setSocket(ws);
      return () => ws.close();
    }
  }, [activeTab, socket]);

  useEffect(() => {
    const handleScroll = () => setShowScrollTop(window.scrollY > 400);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (loading && !data && isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] text-[var(--ink)]">
        <div className="flex flex-col items-center gap-4">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
            className="w-16 h-16 rounded-full border-4 border-[var(--brand)]/20 border-t-[var(--brand)]"
          />
          <p className="text-[var(--fs-sm)] font-medium animate-pulse uppercase tracking-widest">Initializing Neural Interface...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <AuthPage 
        onLogin={handleLogin} 
        loading={loading} 
        loginError={loginError} 
      />
    );
  }

  const kpis = [
    { 
      label: 'Total Leads', 
      value: data?.overview?.total_leads || '0', 
      change: `+${data?.overview?.new_leads_24h || 0}`, 
      icon: Users, 
      color: 'var(--brand)',
      trend: 'up'
    },
    { 
      label: 'Emails Sent', 
      value: data?.overview?.emails_sent || '0', 
      change: `${data?.overview?.daily_actions || 0} today`, 
      icon: Mail, 
      color: 'var(--purple)',
      trend: 'neutral'
    },
    { 
      label: 'Replies', 
      value: data?.health?.reply_total || '0', 
      change: `${data?.health?.reply_rate || 0}% rate`, 
      icon: MessageSquare, 
      color: 'var(--success)',
      trend: 'up'
    },
    { 
      label: 'Conversions', 
      value: data?.health?.conversion_total || '0', 
      change: `${data?.health?.conversion_rate || 0}% rate`, 
      icon: Target, 
      color: 'var(--accent)',
      trend: 'up'
    }, 
  ];

  return (
    <div className="min-h-screen flex bg-[var(--bg)] selection:bg-[var(--brand)] selection:text-white">
      {/* Page Progress Bar */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-1 bg-[var(--brand)] z-[1000] origin-left"
        style={{ scaleX: smoothProgress }}
      />

      {/* Feedback Toast */}
      <AnimatePresence>
        {feedback && (
          <motion.div
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 20, x: '-50%' }}
            className={`fixed bottom-10 left-1/2 z-[1000] px-6 py-3 rounded-full clay-card flex items-center gap-3 border ${feedback.type === 'error' ? 'border-[var(--error)] text-[var(--error)] bg-[var(--error)]/10' : 'border-[var(--success)] text-[var(--success)] bg-[var(--success)]/10'}`}
          >
            {feedback.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
            <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest">{feedback.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Global Error Banner */}
      <AnimatePresence>
        {error && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="fixed top-0 left-0 right-0 z-[2000] bg-[var(--error)] text-white p-[var(--s-2)] flex items-center justify-center gap-4 shadow-2xl"
          >
            <AlertCircle size={16} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">{error}</span>
            <button onClick={() => setError(null)} className="p-1 hover:bg-white/10 rounded-full transition-all"><X size={14}/></button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside 
        style={{ x: sidebarX }}
        className={`
          fixed lg:relative z-50 h-[calc(100vh-var(--s-4))] m-[var(--s-2)]
          ${sidebarOpen ? 'w-[18rem]' : 'w-[var(--s-12)]'} 
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-[calc(100%+var(--s-4))] lg:translate-x-0'}
          clay-card flex flex-col transition-all duration-500 ease-[var(--ease)] overflow-hidden
        `}
      >
        <div className="p-[var(--s-8)] flex items-center justify-between">
          <div className="flex items-center gap-[var(--s-4)] overflow-hidden">
            <div className="w-[var(--s-12)] h-[var(--s-12)] bg-gradient-to-br from-[var(--brand)] to-[var(--brand-glow)] rounded-[var(--r-md)] flex items-center justify-center shrink-0 shadow-[0_8px_32px_-8px_var(--brand-glow)] hover:rotate-12 transition-transform duration-500 border border-[var(--line)]">
              <Zap className="text-white drop-shadow-lg" size={28} />
            </div>
            {sidebarOpen && (
              <div className="flex flex-col">
                <span className="font-black text-[var(--fs-xl)] tracking-tighter leading-none bg-gradient-to-r from-[var(--ink)] to-[var(--muted)] bg-clip-text text-transparent uppercase">Neural</span>
                <span className="text-[var(--fs-xs)] text-[var(--brand)] font-black tracking-[0.3em] mt-1 uppercase">Ops Console</span>
              </div>
            )}
          </div>
          <button 
            onClick={() => setMobileMenuOpen(false)}
            className="lg:hidden p-[var(--s-2)] hover:bg-[var(--glass-hover)] rounded-[var(--r-sm)] text-[var(--muted)]"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 px-[var(--s-4)] space-y-[var(--s-2)] mt-[var(--s-4)] custom-scrollbar overflow-y-auto">
          {[
            { id: 'overview', icon: Layout, label: 'Overview' },
            { id: 'leads', icon: Users, label: 'Leads' },
            { id: 'harvester', icon: Target, label: 'Harvester' },
            { id: 'campaigns', icon: Mail, label: 'Campaigns' },
            { id: 'analytics', icon: BarChart3, label: 'Analytics' },
            { id: 'system', icon: Cpu, label: 'System Health' },
            { id: 'admin', icon: Shield, label: 'Admin Panel' },
            { id: 'logs', icon: Activity, label: 'Live Logs' },
            { id: 'settings', icon: Settings, label: 'Settings' },
          ].map((item) => (
            <button 
              key={item.id} 
              onClick={() => setActiveTab(item.id)}
              aria-current={activeTab === item.id ? 'page' : undefined}
              className={`w-full flex items-center gap-[var(--s-4)] p-[var(--s-4)] rounded-[var(--r-md)] transition-all relative group ${activeTab === item.id ? 'text-white' : 'text-[var(--muted)] hover:bg-[var(--glass-hover)] hover:text-[var(--ink)]'}`}
            >
              {activeTab === item.id && (
                <motion.div 
                  layoutId="activeNav"
                  className="absolute inset-0 bg-gradient-to-r from-[var(--brand)] to-[var(--success)] rounded-[var(--r-md)] shadow-[0_8px_24px_-8px_var(--brand-glow)] z-0"
                />
              )}
              <item.icon size={22} className={`relative z-10 transition-all duration-300 ${activeTab === item.id ? 'scale-110 drop-shadow-md' : 'group-hover:scale-110 group-hover:text-[var(--brand)]'}`} />
              {sidebarOpen && <span className="relative z-10 font-bold tracking-tight text-[var(--fs-sm)] uppercase">{item.label}</span>}
              {activeTab === item.id && sidebarOpen && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="absolute right-[var(--s-4)] w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_white] z-10"
                />
              )}
            </button>
          ))}
        </nav>

        <div className="p-[var(--s-6)] mt-auto border-t border-[var(--line)] bg-[var(--bg-alt)]/30">
          <button 
            onClick={handleDisconnect}
            className="w-full flex items-center gap-[var(--s-4)] p-[var(--s-4)] rounded-[var(--r-md)] text-[var(--error)] hover:bg-[var(--error)]/10 transition-all group font-black text-[var(--fs-xs)] uppercase tracking-widest"
          >
            <LogOut size={20} className="group-hover:-translate-x-1 transition-transform" />
            {sidebarOpen && <span>Secure Exit</span>}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <motion.main 
        style={{ y: contentY }}
        className="flex-1 flex flex-col p-[var(--s-2)] md:p-[var(--s-3)] lg:pl-0 overflow-hidden relative"
      >
        <div className="absolute top-[-100px] left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[var(--brand)] opacity-10 blur-[120px] pointer-events-none" />

        <motion.header 
          style={{ opacity: headerOpacity, scale: headerScale }}
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-[var(--s-6)] mb-[var(--s-10)] relative z-20 px-[var(--s-4)]"
        >
          <div className="flex items-center gap-[var(--s-4)] w-full sm:w-auto">
            <button 
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden w-[var(--s-12)] h-[var(--s-12)] glass-panel flex items-center justify-center rounded-[var(--r-md)] hover:scale-110 active:scale-95 transition-all shadow-xl"
            >
              <Menu size={20} />
            </button>
            <div>
              <div className="flex items-center gap-[var(--s-2)] mb-[var(--s-2)]">
                <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--muted)] opacity-50">Neural Console</span>
                <ChevronRight size={10} className="text-[var(--muted)] opacity-30" />
                <span className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--brand)]">{activeTab}</span>
              </div>
              <h1 className="text-[var(--fs-xl)] md:text-[var(--fs-2xl)] font-black tracking-tighter text-[var(--ink)] leading-[var(--lh-tight)]">Neural Console <span className="text-[var(--brand)]">v6.0</span></h1>
              <p className="text-[var(--fs-xs)] text-[var(--muted)] font-black uppercase tracking-[0.2em] mt-[var(--s-1)] flex items-center gap-[var(--s-2)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] shadow-[0_0_8px_var(--success)] animate-pulse" />
                Neural Node: <span className="text-[var(--success)]">Operational</span> • Syncing {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-[var(--s-4)] w-full sm:w-auto flex-1 justify-end">
            <div className="hidden xl:flex items-center bg-[var(--bg-alt)]/50 border border-[var(--glass-border)] rounded-[var(--r-md)] px-[var(--s-4)] py-[var(--s-3)] focus-within:border-[var(--brand)] transition-all group flex-1 max-w-md shadow-inner">
              <Search size={18} className="text-[var(--muted)] group-focus-within:text-[var(--brand)] transition-colors" />
              <input 
                type="text" 
                placeholder="Query neural database..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent border-none outline-none text-[var(--fs-sm)] w-full ml-[var(--s-3)] font-bold text-[var(--ink)] placeholder:text-[var(--muted)]/50" 
              />
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-[var(--s-3)] w-full sm:w-auto ml-auto">
              <div className="flex gap-[var(--s-1)] p-[var(--s-1)] bg-[var(--bg-alt)]/80 border border-[var(--glass-border)] rounded-[var(--r-md)] items-center justify-center min-h-[56px] shadow-2xl backdrop-blur-xl group order-last lg:order-none">
                <button 
                  onClick={toggleTheme} 
                  className="w-11 h-11 flex items-center justify-center rounded-[var(--r-sm)] hover:bg-[var(--glass-hover)] transition-all text-[var(--ink)] opacity-60 hover:opacity-100"
                >
                  {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
                <div className="w-px h-5 bg-[var(--line)] mx-[var(--s-1)]" />
                <button 
                  onClick={() => setNotificationsOpen(true)} 
                  className="w-11 h-11 flex items-center justify-center rounded-[var(--r-sm)] relative hover:bg-[var(--glass-hover)] transition-all text-[var(--ink)] opacity-60 hover:opacity-100"
                >
                  <Bell size={20} />
                  {data?.notifications?.length > 0 && (
                    <span className="absolute top-3 right-3 w-2.5 h-2.5 bg-[var(--error)] rounded-full border-2 border-[var(--bg-alt)] shadow-[0_0_12px_var(--error)] animate-bounce"></span>
                  )}
                </button>
              </div>

              <button 
                onClick={() => handleBotAction('start')} 
                className="flex items-center justify-center gap-[var(--s-3)] px-[var(--s-6)] min-h-[56px] rounded-[var(--r-md)] bg-[var(--success)] text-white hover:brightness-110 transition-all font-black text-[var(--fs-xs)] uppercase tracking-widest shadow-[0_12px_24px_-8px_var(--success)] hover:scale-[1.05] active:scale-[0.98]"
              >
                <Play size={18} className="fill-white" />
                <span>Execute</span>
              </button>

              <button 
                onClick={() => setIsScrapeModalOpen(true)} 
                className="flex items-center justify-center gap-[var(--s-3)] px-[var(--s-6)] min-h-[56px] rounded-[var(--r-md)] bg-[var(--brand)] text-white hover:brightness-110 transition-all font-black text-[var(--fs-xs)] uppercase tracking-widest shadow-[0_12px_24px_-8px_var(--brand)] hover:scale-[1.05] active:scale-[0.98]"
              >
                <Search size={18} strokeWidth={3} />
                <span>Harvest</span>
              </button>

              <button 
                onClick={() => handleBotAction('pause')} 
                className="flex items-center justify-center gap-[var(--s-3)] px-[var(--s-6)] min-h-[56px] rounded-[var(--r-md)] bg-[var(--bg-alt)]/80 border border-[var(--glass-border)] text-[var(--ink)] hover:bg-[var(--glass-hover)] transition-all font-black text-[var(--fs-xs)] uppercase tracking-widest shadow-xl hover:scale-[1.05] active:scale-[0.98]"
              >
                <div className="flex gap-1.5">
                  <div className="w-1.5 h-4 bg-[var(--ink)] opacity-40 rounded-full" />
                  <div className="w-1.5 h-4 bg-[var(--ink)] opacity-40 rounded-full" />
                </div>
                <span>Halt</span>
              </button>
            </div>
          </div>
        </motion.header>

        <div className="flex-1 overflow-y-auto pr-2 space-y-[var(--s-4)] custom-scrollbar pb-10">
          {activeTab === 'overview' ? (
            <OverviewDashboard 
              data={data} 
              kpis={kpis} 
              onBotAction={handleBotAction} 
              setIsScrapeModalOpen={setIsScrapeModalOpen} 
            />
          ) : activeTab === 'harvester' ? (
            <HarvesterPanel data={data} fetchData={fetchData} />
          ) : activeTab === 'leads' ? (
            <LeadsTable 
              data={data} 
              bulkSelection={bulkSelection} 
              setBulkSelection={setBulkSelection} 
              handleBulkAction={handleBulkAction} 
              searchQuery={searchQuery} 
              activeFilter={activeFilter} 
              setSelectedLead={setSelectedLead} 
            />
          ) : activeTab === 'campaigns' ? (
            <CampaignsPanel 
              data={data} 
              personas={personas} 
              setEditingPersona={setEditingPersona} 
              handleBotAction={handleBotAction} 
            />
          ) : activeTab === 'analytics' ? (
            <AnalyticsDashboard data={data} />
          ) : activeTab === 'logs' ? (
            <div className="clay-card p-[var(--s-8)] h-[600px] flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-[var(--fs-lg)] font-black tracking-tight flex items-center gap-2 uppercase">
                  <Terminal size={20} className="text-[var(--brand)]" />
                  Neural Execution Log
                </h3>
                <div className="flex gap-2">
                  <button onClick={fetchLogs} className="p-2 hover:bg-white/5 rounded-xl transition-all text-[var(--brand)]"><RefreshCcw size={18} /></button>
                </div>
              </div>
              <div className="flex-1 bg-black/40 rounded-[var(--r-md)] border border-white/5 p-4 font-mono text-[var(--fs-xs)] overflow-y-auto custom-scrollbar shadow-inner">
                {logs.length > 0 ? logs.map((log, i) => (
                  <div key={i} className="mb-2 flex gap-4 opacity-80 hover:opacity-100 transition-opacity">
                    <span className="text-[var(--muted)] opacity-40">[{log.timestamp || 'SYNC'}]</span>
                    <span className={`font-black ${log.level === 'ERROR' ? 'text-[var(--error)]' : log.level === 'WARNING' ? 'text-[var(--accent)]' : 'text-[var(--brand)]'}`}>
                      {log.level || 'INFO'}
                    </span>
                    <span className="text-[var(--ink)]">{log.message || log}</span>
                  </div>
                )) : (
                  <div className="h-full flex items-center justify-center opacity-20 italic">
                    <p>Listening for neural signals...</p>
                  </div>
                )}
              </div>
            </div>
          ) : activeTab === 'system' ? (
            <SystemMonitor 
              stats={systemStats} 
              onRefresh={fetchSystemStats} 
              runMaintenance={runMaintenance}
              maintenanceRunning={maintenanceRunning}
            />
          ) : activeTab === 'admin' ? (
            <AdminPanel />
          ) : activeTab === 'settings' ? (
            <SettingsPage 
              data={data} 
              personas={personas} 
              onSave={handleSaveSettings} 
              onBotAction={handleBotAction} 
            />
          ) : (
            <div className="h-full flex items-center justify-center glass-panel p-10 text-center">
              <div>
                <Bot size={48} className="mx-auto mb-4 text-[var(--muted)] opacity-20" />
                <h2 className="text-[var(--fs-xl)] font-bold mb-2">Module Offline</h2>
                <p className="text-[var(--muted)]">The {activeTab} control module is currently in development.</p>
              </div>
            </div>
          )}
        </div>

        <button 
          onClick={scrollToTop}
          className={`fixed bottom-6 right-6 p-4 rounded-full bg-[var(--brand)] text-white shadow-2xl transition-all duration-300 z-[100] ${showScrollTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10 pointer-events-none'}`}
          aria-label="Scroll to top"
        >
          <ArrowUp size={20} />
        </button>
      </motion.main>

      <NotificationCenter 
        isOpen={notificationsOpen} 
        onClose={() => setNotificationsOpen(false)} 
        notifications={data?.notifications || []}
      />

      <LeadDetailsModal 
        lead={selectedLead} 
        onClose={() => setSelectedLead(null)} 
      />

      <PersonaModal 
        persona={editingPersona} 
        onClose={() => setEditingPersona(null)} 
        onSave={async (p) => {
          await fetch('/api/personas', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'X-API-Key': apiKey
            },
            body: JSON.stringify(p)
          });
          fetchPersonas();
          setEditingPersona(null);
          showFeedback('Persona protocol updated');
        }}
      />

      <AnimatePresence>
        {isScrapeModalOpen && (
          <div className="fixed inset-0 z-[500] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsScrapeModalOpen(false)}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-2xl glass-panel overflow-hidden shadow-2xl border-[var(--brand)]/20"
            >
              <div className="p-6 border-b border-[var(--glass-border)] flex justify-between items-center bg-[var(--brand)]/5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--brand)]/10 flex items-center justify-center text-[var(--brand)]">
                    <Zap size={20} />
                  </div>
                  <h2 className="text-[var(--fs-lg)] font-black tracking-tighter uppercase italic">Neural Harvester Deployment</h2>
                </div>
                <button onClick={() => setIsScrapeModalOpen(false)} className="p-2 hover:bg-white/5 rounded-xl transition-all text-[var(--muted)] hover:text-[var(--ink)]"><X size={20} /></button>
              </div>
              <div className="p-4 bg-black/20">
                <LeadScraper onStarted={() => { setIsScrapeModalOpen(false); fetchData(); showFeedback('Harvester deployed'); }} />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { 
          background: var(--glass-border); 
          border-radius: 10px; 
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--muted); }
      `}} />
    </div>
  );
};

export default App;
