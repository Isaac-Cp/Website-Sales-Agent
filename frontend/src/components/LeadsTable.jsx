import React from 'react';
import { motion } from 'framer-motion';
import { 
  Users, 
  Mail, 
  Target, 
  LogOut, 
  X, 
  ChevronRight 
} from 'lucide-react';

const LeadsTable = ({ 
  data, 
  bulkSelection, 
  setBulkSelection, 
  handleBulkAction, 
  searchQuery, 
  activeFilter, 
  setSelectedLead 
}) => {
  const filteredLeads = (data?.lead_feed || [])
    .filter(lead => {
      const matchesSearch = !searchQuery || 
        lead.business_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lead.email?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesFilter = activeFilter === 'All Niches' || lead.niche === activeFilter;
      return matchesSearch && matchesFilter;
    });

  return (
    <div className="space-y-[var(--s-6)]">
      <div className="clay-card p-[var(--s-6)] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-[var(--fs-sm)] font-black uppercase tracking-[0.2em] text-[var(--ink)]">Intelligence Database</h2>
          {bulkSelection.length > 0 && (
            <div className="flex items-center gap-2 animate-in slide-in-from-left-2 duration-300">
              <span className="text-[10px] font-black uppercase text-[var(--brand)] px-3 py-1 bg-[var(--brand)]/10 rounded-full border border-[var(--brand)]/20 shadow-sm">
                {bulkSelection.length} Selected
              </span>
              <div className="h-4 w-px bg-[var(--line)] mx-1" />
              <button 
                onClick={() => handleBulkAction('mark_contacted')}
                className="p-2 hover:bg-black/20 rounded-full text-[var(--success)] transition-all hover:scale-110 active:scale-90"
                title="Mark as Contacted"
              >
                <Mail size={16} />
              </button>
              <button 
                onClick={() => handleBulkAction('high_value')}
                className="p-2 hover:bg-black/20 rounded-full text-[var(--accent)] transition-all hover:scale-110 active:scale-90"
                title="Mark as High Value"
              >
                <Target size={16} />
              </button>
              <button 
                onClick={() => handleBulkAction('archive')}
                className="p-2 hover:bg-black/20 rounded-full text-[var(--muted)] hover:text-[var(--ink)] transition-all hover:scale-110 active:scale-90"
                title="Archive Selected"
              >
                <LogOut size={16} />
              </button>
              <button 
                onClick={() => handleBulkAction('delete')}
                className="p-2 hover:bg-black/20 rounded-full text-[var(--error)] transition-all hover:scale-110 active:scale-90"
                title="Delete Selected"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 rounded-full bg-black/20 border border-white/5 text-[10px] font-black uppercase tracking-widest text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
            Nodes: {data?.overview?.total_leads}
          </button>
          <button className="px-4 py-2 rounded-full bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20 text-[10px] font-black uppercase tracking-widest shadow-[0_4px_12px_var(--success)]/10">
            Active: {data?.health?.sent_total}
          </button>
        </div>
      </div>
      <div className="clay-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[var(--fs-sm)] border-collapse">
            <thead className="bg-black/20 border-b border-[var(--line)]">
              <tr>
                <th className="p-4 w-12">
                  <div className="relative flex items-center">
                    <input 
                      type="checkbox" 
                      className="appearance-none w-5 h-5 rounded-[6px] border border-[var(--line)] bg-black/20 checked:bg-[var(--brand)] transition-all cursor-pointer shadow-inner"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setBulkSelection(data?.lead_feed?.map(l => l.id) || []);
                        } else {
                          setBulkSelection([]);
                        }
                      }}
                    />
                    {bulkSelection.length === data?.lead_feed?.length && data?.lead_feed?.length > 0 && (
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none text-white">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7"></path></svg>
                      </div>
                    )}
                  </div>
                </th>
                <th className="p-4 font-black uppercase tracking-[0.2em] text-[10px] text-[var(--muted)]">Core Entity</th>
                <th className="p-4 font-black uppercase tracking-[0.2em] text-[10px] text-[var(--muted)]">Status Node</th>
                <th className="p-4 font-black uppercase tracking-[0.2em] text-[10px] text-[var(--muted)]">Neural Link</th>
                <th className="p-4 font-black uppercase tracking-[0.2em] text-[10px] text-[var(--muted)]">Vector</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--line)]">
              {filteredLeads.map((lead, i) => (
                <motion.tr 
                  key={lead.id} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className={`hover:bg-white/5 transition-all group cursor-pointer ${bulkSelection.includes(lead.id) ? 'bg-[var(--brand)]/5' : ''}`}
                >
                  <td className="p-4" onClick={(e) => e.stopPropagation()}>
                    <div className="relative flex items-center">
                      <input 
                        type="checkbox" 
                        checked={bulkSelection.includes(lead.id)}
                        onChange={() => {
                          setBulkSelection(prev => 
                            prev.includes(lead.id) 
                              ? prev.filter(id => id !== lead.id) 
                              : [...prev, lead.id]
                          );
                        }}
                        className="appearance-none w-5 h-5 rounded-[6px] border border-[var(--line)] bg-black/20 checked:bg-[var(--brand)] transition-all cursor-pointer shadow-inner"
                      />
                      {bulkSelection.includes(lead.id) && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none text-white">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7"></path></svg>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="p-4" onClick={() => setSelectedLead(lead)}>
                    <p className="font-black text-[var(--ink)] tracking-tight">{lead.business_name}</p>
                    <p className="text-[10px] text-[var(--muted)] font-bold uppercase tracking-widest">{lead.city}</p>
                  </td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-[0.1em] border ${
                      lead.status === 'contacted' 
                        ? 'bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20' 
                        : 'bg-black/20 text-[var(--muted)] border-white/5'
                    }`}>
                      {lead.status}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-[10px] font-bold text-[var(--brand)] opacity-80 group-hover:opacity-100 transition-opacity">
                    {lead.email || <span className="opacity-30 italic">No neural link</span>}
                  </td>
                  <td className="p-4">
                    <span className="text-[10px] font-black text-[var(--muted)] uppercase tracking-widest bg-black/20 px-2 py-1 rounded-[4px]">{lead.niche}</span>
                  </td>
                  <td className="p-4 text-right">
                    <button className="p-2 hover:bg-white/10 rounded-full opacity-0 group-hover:opacity-100 transition-all text-[var(--brand)]">
                      <ChevronRight size={16} />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LeadsTable;
