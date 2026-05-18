import { useState, useEffect, useCallback, useRef } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { 
  ShieldCheck, CheckCircle, XCircle, Trash2, Users, Database, Briefcase, 
  TrendingUp, RefreshCw, ChevronDown, ChevronUp, Edit2, Save, X,
  Activity, Layout, Lock, Settings, AlertCircle, Search, Info, Plus, Award,
  Loader2, Terminal
} from 'lucide-react';

// ── high-fidelity badge ──────────────────────────────────────
const Badge = ({ color, children }) => {
  const colors = {
    green:  'bg-success/5 text-success border-success/20',
    red:    'bg-error/5 text-error border-error/20',
    yellow: 'bg-warning/5 text-warning border-warning/20',
    blue:   'bg-primary/5 text-primary border-primary/20',
    violet: 'bg-secondary/5 text-secondary border-secondary/20',
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border-2 ${colors[color] || colors.blue}`}>
      {children}
    </span>
  );
};

// ── high-fidelity stat card ──────────────────────────────────
const StatCard = ({ label, value, icon: Icon, color = 'blue' }) => {
  const colors = { 
    blue: 'text-primary bg-primary/10 border-primary/20', 
    green: 'text-success bg-success/10 border-success/20', 
    amber: 'text-warning bg-warning/10 border-warning/20', 
    violet: 'text-secondary bg-secondary/10 border-secondary/20' 
  };
  return (
    <div className="surface-card p-6 flex flex-col gap-6 shadow-lg group hover:scale-[1.02] transition-all">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-2xl border-2 ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <Activity className="w-4 h-4 text-muted opacity-20 group-hover:opacity-100 transition-opacity" />
      </div>
      <div>
        <p className="text-3xl font-black font-outfit text-main mb-1">{value ?? '—'}</p>
        <p className="text-[10px] font-black text-muted uppercase tracking-widest leading-none">{label}</p>
      </div>
    </div>
  );
};

// ── professional section header ─────────────────────────────
const Section = ({ title, icon: Icon, children }) => (
  <div className="surface-card p-10 space-y-8 shadow-xl">
    <div className="flex items-center justify-between border-b border-base pb-6">
      <h2 className="text-2xl font-black font-outfit text-main flex items-center gap-4">
        {Icon && <Icon className="w-6 h-6 text-primary" />}
        {title}
      </h2>
      <div className="flex gap-2">
        <div className="w-2 h-2 rounded-full bg-primary" />
        <div className="w-2 h-2 rounded-full bg-base" />
        <div className="w-2 h-2 rounded-full bg-base" />
      </div>
    </div>
    <div className="animate-in-fade">{children}</div>
  </div>
);

export default function AdminPanel() {
  const [stats, setStats]               = useState(null);
  const [pending, setPending]           = useState([]);
  const [pendingRoles, setPendingRoles] = useState([]);
  const [roles, setRoles]               = useState([]);
  const [skills, setSkills]             = useState([]);
  const [users, setUsers]               = useState([]);
  const [tab, setTab]                   = useState('pending');     // pending | pending-roles | roles | skills | users
  const [loading, setLoading]           = useState(false);
  const [editingRole, setEditingRole]   = useState(null);          // {id, title, seniority, aliases: ""}
  const [isCreatingRole, setIsCreatingRole] = useState(false);
  const [newRole, setNewRole]           = useState({ title: '', seniority: '' });
  const [editingSkill, setEditingSkill] = useState(null);
  const [isCreatingSkill, setIsCreatingSkill] = useState(false);
  const [newSkill, setNewSkill]         = useState({ canonical_name: '', category: 'Tool' });
  const [msg, setMsg]                   = useState('');
  const [pendingFilter, setPendingFilter] = useState('pending');

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 4000); };

  // ── fetchers ──────────────────────────────────────────────────
  const fetchStats = useCallback(async () => {
    try { const r = await api.get('/admin/stats'); setStats(r.data); } catch {}
  }, []);

  const fetchPending = useCallback(async () => {
    try {
      const r = await api.get(`/admin/pending-skills?status=${pendingFilter}`);
      setPending(r.data.pending_skills || []);
    } catch {}
  }, [pendingFilter]);

  const fetchPendingRoles = useCallback(async () => {
    try {
      const r = await api.get(`/admin/pending-roles?status=${pendingFilter}`);
      setPendingRoles(r.data.pending_roles || []);
    } catch {}
  }, [pendingFilter]);

  const fetchRoles = useCallback(async () => {
    try { const r = await api.get('/admin/taxonomy/roles'); setRoles(r.data.roles || []); } catch {}
  }, []);

  const fetchSkills = useCallback(async () => {
    try { const r = await api.get('/admin/taxonomy/skills?per_page=100'); setSkills(r.data.skills || []); } catch {}
  }, []);

  const fetchUsers = useCallback(async () => {
    try { const r = await api.get('/admin/users'); setUsers(r.data.users || []); } catch {}
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);
  useEffect(() => { if (tab === 'pending') fetchPending(); }, [tab, fetchPending]);
  useEffect(() => { if (tab === 'pending-roles') fetchPendingRoles(); }, [tab, fetchPendingRoles]);
  useEffect(() => { if (tab === 'roles')   fetchRoles();   }, [tab, fetchRoles]);
  useEffect(() => { if (tab === 'skills')  fetchSkills();  }, [tab, fetchSkills]);
  useEffect(() => { if (tab === 'users')   fetchUsers();   }, [tab, fetchUsers]);

  // ── pending skill actions ─────────────────────────────────────
  const approve = async (id) => {
    try { await api.post(`/admin/pending-skills/${id}/approve`); flash('✅ Logic branch integrated.'); fetchPending(); fetchStats(); }
    catch { flash('❌ System error during integration.'); }
  };
  const reject = async (id) => {
    try { await api.post(`/admin/pending-skills/${id}/reject`, { note: 'Rejected by admin.' }); flash('🚫 Node discarded.'); fetchPending(); }
    catch { flash('❌ System error during discard.'); }
  };

  // ── pending role actions ──────────────────────────────────────
  const approveRole = async (id) => {
    try { await api.post(`/admin/pending-roles/${id}/approve`); flash('✅ Role identity validated.'); fetchPendingRoles(); fetchStats(); }
    catch { flash('❌ Role validation failed.'); }
  };
  const rejectRole = async (id) => {
    try { await api.post(`/admin/pending-roles/${id}/reject`, { note: 'Rejected by admin.' }); flash('🚫 Identity discarded.'); fetchPendingRoles(); }
    catch { flash('❌ Role discard failed.'); }
  };

  // ── role edit save ────────────────────────────────────────────
  const saveRole = async () => {
    if (!editingRole) return;
    const aliases = editingRole.aliases.split(',').map(s => s.trim()).filter(Boolean);
    try {
      await api.put(`/admin/taxonomy/roles/${editingRole.id}`, {
        title: editingRole.title,
        seniority: editingRole.seniority,
        aliases,
      });
      flash('✅ Taxonomy entry updated.');
      setEditingRole(null);
      fetchRoles();
    } catch (e) {
      flash('❌ Taxonomy update failure.');
    }
  };

  const createRole = async () => {
    if (!newRole.title) return;
    try {
      await api.post('/admin/taxonomy/roles', newRole);
      flash('✅ New role added to taxonomy.');
      setIsCreatingRole(false);
      setNewRole({ title: '', seniority: '' });
      fetchRoles();
      fetchStats();
    } catch (e) {
      flash('❌ Failed to create role.');
    }
  };

  // ── skill edit save ────────────────────────────────────────────
  const saveSkill = async () => {
    if (!editingSkill) return;
    const aliases = editingSkill.aliases.split(',').map(s => s.trim()).filter(Boolean);
    try {
      await api.put(`/admin/taxonomy/skills/${editingSkill.id}`, {
        canonical_name: editingSkill.canonical_name,
        category: editingSkill.category,
        aliases,
      });
      flash('✅ Skill entry updated.');
      setEditingSkill(null);
      fetchSkills();
    } catch (e) {
      flash('❌ Skill update failure.');
    }
  };

  const createSkill = async () => {
    if (!newSkill.canonical_name) return;
    try {
      await api.post('/admin/taxonomy/skills', newSkill);
      flash('✅ New skill added to taxonomy.');
      setIsCreatingSkill(false);
      setNewSkill({ canonical_name: '', category: 'Tool' });
      fetchSkills();
      fetchStats();
    } catch (e) {
      flash('❌ Failed to create skill.');
    }
  };

  // ── toggle admin ──────────────────────────────────────────────
  const toggleAdmin = async (userId) => {
    try { await api.patch(`/admin/users/${userId}/toggle-admin`); flash('✅ Privileges recalculated.'); fetchUsers(); }
    catch { flash('❌ Privilege error.'); }
  };

  // ── pipeline trigger + live status ─────────────────────────
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const pollRef = useRef(null);

  const pollPipelineStatus = useCallback(async () => {
    try {
      const r = await api.get('/admin/pipeline/status');
      setPipelineStatus(r.data);
      if (!r.data.is_running && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch {}
  }, []);

  const triggerPipeline = async () => {
    try { 
      flash('⏳ Initializing pipeline...');
      await api.post('/admin/pipeline/trigger');
      flash('✅ Pipeline started.'); 
      // Start polling
      pollPipelineStatus();
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(pollPipelineStatus, 2000);
    }
    catch { flash('❌ Pipeline initialization failed.'); }
  };

  // Check status on mount to pick up any running pipeline
  useEffect(() => {
    pollPipelineStatus();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [pollPipelineStatus]);

  const TABS = [
    { id: 'pending',       label: 'Pending Skills', icon: ShieldCheck },
    { id: 'pending-roles', label: 'Pending Roles',  icon: Users },
    { id: 'roles',         label: 'Roles & Aliases', icon: Database },
    { id: 'skills',        label: 'Skills & Aliases', icon: Award },
    { id: 'users',         label: 'Global Users',   icon: Lock },
  ];

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-10">
          <div className="flex items-start gap-6">
            <div className="p-5 rounded-[2rem] bg-secondary/10 border-2 border-secondary/20 shadow-xl shadow-secondary/5">
              <ShieldCheck className="w-10 h-10 text-secondary" />
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-secondary font-black uppercase tracking-[0.3em] text-xs">
                <Lock className="w-4 h-4" />
                Administrative Authority
              </div>
              <h1 className="text-5xl font-black font-outfit text-main tracking-tight">Intelligence Control</h1>
              <p className="text-muted text-xl font-medium">Global taxonomy governance and user matrix orchestration.</p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <button 
              onClick={triggerPipeline}
              disabled={pipelineStatus?.is_running}
              className="btn-primary h-16 px-10 text-base shadow-2xl shadow-primary/30 group w-full sm:w-auto disabled:opacity-50"
            >
              {pipelineStatus?.is_running 
                ? <Loader2 className="w-5 h-5 animate-spin" />
                : <Database className="w-5 h-5 group-hover:scale-110 transition-transform" />
              }
              {pipelineStatus?.is_running ? 'Pipeline Running...' : 'Trigger Pipeline'}
            </button>
            <button 
              onClick={() => { fetchStats(); fetchPending(); fetchPendingRoles(); fetchRoles(); fetchSkills(); fetchUsers(); }}
              className="btn-secondary h-16 px-8 text-base group w-full sm:w-auto"
            >
              <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-1000" />
              Sync State
            </button>
          </div>
        </header>

        {/* Live Pipeline Status Panel */}
        {pipelineStatus && (pipelineStatus.is_running || (pipelineStatus.logs && pipelineStatus.logs.length > 0)) && (
          <div className="surface-card p-8 space-y-6 border-2 border-primary/10 animate-in-slide">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-2xl ${pipelineStatus.is_running ? 'bg-primary/10 animate-pulse' : 'bg-success/10'}`}>
                  {pipelineStatus.is_running 
                    ? <Loader2 className="w-6 h-6 text-primary animate-spin" />
                    : <CheckCircle className="w-6 h-6 text-success" />
                  }
                </div>
                <div>
                  <h3 className="text-lg font-bold font-outfit text-main">{pipelineStatus.step || 'Idle'}</h3>
                  <p className="text-xs font-bold text-muted uppercase tracking-widest">
                    {pipelineStatus.is_running ? 'In Progress' : `Last run: ${pipelineStatus.last_run || 'Never'}`}
                  </p>
                </div>
              </div>
              {pipelineStatus.progress > 0 && pipelineStatus.total > 0 && (
                <span className="text-2xl font-black font-outfit text-primary">
                  {pipelineStatus.progress}/{pipelineStatus.total}
                </span>
              )}
            </div>

            {/* Progress Bar */}
            {pipelineStatus.is_running && pipelineStatus.total > 0 && (
              <div className="h-3 bg-subtle rounded-full overflow-hidden border border-base">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${Math.round((pipelineStatus.progress / pipelineStatus.total) * 100)}%` }}
                />
              </div>
            )}

            {/* Log Output */}
            {pipelineStatus.logs && pipelineStatus.logs.length > 0 && (
              <div className="bg-slate-950 rounded-2xl p-5 max-h-48 overflow-y-auto font-mono text-xs space-y-1 border border-slate-800">
                <div className="flex items-center gap-2 text-slate-500 mb-3 pb-2 border-b border-slate-800">
                  <Terminal className="w-3.5 h-3.5" />
                  <span className="text-[10px] font-black uppercase tracking-widest">Pipeline Log</span>
                </div>
                {pipelineStatus.logs.map((line, i) => (
                  <div key={i} className={`leading-relaxed ${
                    line.includes('✓') ? 'text-emerald-400' :
                    line.includes('✗') || line.includes('ERROR') ? 'text-red-400' :
                    line.includes('⏱') ? 'text-amber-400' :
                    'text-slate-300'
                  }`}>
                    {line}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {msg && (
          <div className="p-6 rounded-[2rem] bg-primary/5 border-2 border-primary/10 flex items-center gap-4 animate-in-fade backdrop-blur-xl">
             <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                <Info className="w-5 h-5" />
             </div>
             <p className="text-sm font-black text-primary uppercase tracking-widest">{msg}</p>
          </div>
        )}

        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <StatCard label={`Active Market Nodes`} value={stats.total_jobs} icon={Briefcase} color="blue" />
            <StatCard label="Skill Validation Backlog" value={stats.pending_skills} icon={ShieldCheck} color="amber" />
            <StatCard label="Role Identity Backlog"  value={stats.pending_roles}  icon={ShieldCheck} color="violet" />
            <StatCard label="Verified Taxonomy Roles" value={stats.total_roles}    icon={TrendingUp}   color="green" />
          </div>
        )}

        {/* Navigation Matrix */}
        <div className="flex flex-wrap gap-4 pb-4 border-b border-base overflow-x-auto no-scrollbar">
          {TABS.map(t => {
            const Icon = t.icon;
            return (
              <button 
                key={t.id} 
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-3 px-8 py-4 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border-2
                  ${tab === t.id 
                    ? 'bg-primary border-primary text-white shadow-xl shadow-primary/20' 
                    : 'bg-surface border-base text-muted hover:border-primary/40 hover:bg-subtle'}`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        <div className="space-y-12 animate-in-slide">
          {tab === 'pending' && (
            <Section title="Skill Validation Queue" icon={ShieldCheck}>
              <div className="flex gap-3 mb-8">
                {['pending','approved','rejected','all'].map(f => (
                  <button key={f} onClick={() => setPendingFilter(f)}
                    className={`px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border-2
                      ${pendingFilter === f ? 'bg-primary border-primary text-white' : 'bg-surface border-base text-muted hover:bg-subtle'}`}>
                    {f}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {pending.map(p => (
                  <div key={p.id} className="surface-card p-6 flex items-center justify-between gap-6 hover:border-primary/30 group transition-all">
                    <div className="space-y-1 min-w-0">
                      <p className="text-lg font-black font-outfit text-main truncate">{p.name}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-black text-muted uppercase tracking-widest">{p.source}</span>
                        <div className="w-1 h-1 rounded-full bg-base" />
                        <span className="text-[10px] font-bold text-primary truncate max-w-[150px]">{p.source_detail}</span>
                      </div>
                    </div>
                    {p.status === 'pending' && (
                      <div className="flex gap-2">
                        <button onClick={() => approve(p.id)} className="p-3 rounded-xl bg-success/5 text-success border border-success/10 hover:bg-success hover:text-white transition-all">
                          <CheckCircle className="w-5 h-5" />
                        </button>
                        <button onClick={() => reject(p.id)} className="p-3 rounded-xl bg-error/5 text-error border border-error/10 hover:bg-error hover:text-white transition-all">
                          <XCircle className="w-5 h-5" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {tab === 'pending-roles' && (
            <Section title="Role Identity Queue" icon={Users}>
              <div className="flex gap-3 mb-8">
                {['pending','approved','rejected','all'].map(f => (
                  <button key={f} onClick={() => setPendingFilter(f)}
                    className={`px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border-2
                      ${pendingFilter === f ? 'bg-primary border-primary text-white' : 'bg-surface border-base text-muted hover:bg-subtle'}`}>
                    {f}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {pendingRoles.map(r => (
                  <div key={r.id} className="surface-card p-6 flex items-center justify-between gap-6 hover:border-primary/30 group transition-all">
                    <div className="space-y-1 min-w-0">
                      <p className="text-lg font-black font-outfit text-main truncate">{r.title}</p>
                      <div className="flex items-center gap-3">
                        <Badge color="violet">{r.suggested_sector}</Badge>
                        <span className="text-[10px] font-black text-muted uppercase tracking-widest">Source: {r.source}</span>
                      </div>
                    </div>
                    {r.status === 'pending' && (
                      <div className="flex gap-2">
                        <button onClick={() => approveRole(r.id)} className="p-3 rounded-xl bg-success/5 text-success border border-success/10 hover:bg-success hover:text-white transition-all">
                          <CheckCircle className="w-5 h-5" />
                        </button>
                        <button onClick={() => rejectRole(r.id)} className="p-3 rounded-xl bg-error/5 text-error border border-error/10 hover:bg-error hover:text-white transition-all">
                          <XCircle className="w-5 h-5" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {tab === 'roles' && (
            <Section title={`Verified Taxonomy Ecosystem (${roles.length})`} icon={Database}>
              <div className="flex justify-end mb-6">
                <button onClick={() => setIsCreatingRole(!isCreatingRole)} className="btn-primary h-12 px-6">
                  {isCreatingRole ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                  {isCreatingRole ? 'Cancel' : 'Add New Role'}
                </button>
              </div>

              {isCreatingRole && (
                <div className="surface-card p-8 mb-6 border-2 border-primary/20 space-y-6 animate-in-slide">
                  <h3 className="text-xl font-bold font-outfit text-main">Create New Role</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Identity Title</label>
                      <input 
                        value={newRole.title} 
                        onChange={e => setNewRole(p => ({ ...p, title: e.target.value }))} 
                        className="input-field" 
                        placeholder="e.g. Data Scientist"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Seniority</label>
                      <input 
                        value={newRole.seniority} 
                        onChange={e => setNewRole(p => ({ ...p, seniority: e.target.value }))} 
                        className="input-field" 
                        placeholder="e.g. Mid, Senior"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <button onClick={createRole} className="btn-primary h-12 px-8">Save Role</button>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 gap-6">
                {roles.map(role => {
                  const isEditing = editingRole?.id === role.id;
                  return (
                    <div key={role.id} className={`surface-card overflow-hidden transition-all duration-500
                      ${isEditing ? 'border-primary ring-4 ring-primary/5' : 'hover:border-primary/20'}`}>
                      <div className="flex items-center justify-between gap-8 p-6">
                        <div className="flex-1 min-w-0 flex items-center gap-6">
                          <div className="w-12 h-12 rounded-2xl bg-subtle flex items-center justify-center text-xl shadow-inner font-black text-muted">
                            {role.title.charAt(0)}
                          </div>
                          <div className="space-y-1">
                            <p className="text-xl font-black font-outfit text-main leading-tight">{role.title}</p>
                            <div className="flex items-center gap-4">
                              {role.sector && <Badge color="blue">{role.sector}</Badge>}
                              <span className="text-[10px] font-black text-muted uppercase tracking-[0.2em]">{role.skill_count} Competency Nodes</span>
                            </div>
                          </div>
                        </div>
                        <button 
                          onClick={() => setEditingRole(isEditing ? null : { id: role.id, title: role.title, seniority: role.seniority || '', aliases: (role.aliases || []).join(', ') })}
                          className={`p-4 rounded-2xl transition-all ${isEditing ? 'bg-primary text-white shadow-lg' : 'bg-subtle text-muted hover:text-primary hover:bg-primary/10'}`}
                        >
                          {isEditing ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
                        </button>
                      </div>
                      
                      {isEditing && (
                        <div className="p-8 bg-subtle/30 border-t border-base space-y-8 animate-in-slide">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-2">
                              <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Identity Title</label>
                              <input 
                                value={editingRole.title} 
                                onChange={e => setEditingRole(p => ({ ...p, title: e.target.value }))} 
                                className="input-field py-4" 
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Alternative Aliases (Comma Separated)</label>
                              <textarea 
                                rows={2} 
                                value={editingRole.aliases} 
                                onChange={e => setEditingRole(p => ({ ...p, aliases: e.target.value }))} 
                                className="input-field py-4 resize-none" 
                                placeholder="Alias A, Alias B..." 
                              />
                            </div>
                          </div>
                          <div className="flex justify-end">
                            <button onClick={saveRole} className="btn-primary h-14 px-10 shadow-xl shadow-primary/20">
                              <Save className="w-5 h-5" />
                              Save Intelligence Delta
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Section>
          )}

          {tab === 'skills' && (
            <Section title={`Verified Taxonomy Skills`} icon={Award}>
              <div className="flex justify-end mb-6">
                <button onClick={() => setIsCreatingSkill(!isCreatingSkill)} className="btn-primary h-12 px-6">
                  {isCreatingSkill ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                  {isCreatingSkill ? 'Cancel' : 'Add New Skill'}
                </button>
              </div>

              {isCreatingSkill && (
                <div className="surface-card p-8 mb-6 border-2 border-primary/20 space-y-6 animate-in-slide">
                  <h3 className="text-xl font-bold font-outfit text-main">Create New Skill</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Canonical Name</label>
                      <input 
                        value={newSkill.canonical_name} 
                        onChange={e => setNewSkill(p => ({ ...p, canonical_name: e.target.value }))} 
                        className="input-field" 
                        placeholder="e.g. React.js"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Category</label>
                      <select 
                        value={newSkill.category} 
                        onChange={e => setNewSkill(p => ({ ...p, category: e.target.value }))} 
                        className="input-field bg-surface text-main" 
                      >
                        <option value="Language">Language</option>
                        <option value="Framework">Framework</option>
                        <option value="Tool">Tool</option>
                        <option value="Cloud">Cloud</option>
                        <option value="Database">Database</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <button onClick={createSkill} className="btn-primary h-12 px-8">Save Skill</button>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 gap-6">
                {skills.map(skill => {
                  const isEditing = editingSkill?.id === skill.id;
                  return (
                    <div key={skill.id} className={`surface-card overflow-hidden transition-all duration-500
                      ${isEditing ? 'border-primary ring-4 ring-primary/5' : 'hover:border-primary/20'}`}>
                      <div className="flex items-center justify-between gap-8 p-6">
                        <div className="flex-1 min-w-0 flex items-center gap-6">
                          <div className="w-12 h-12 rounded-2xl bg-subtle flex items-center justify-center text-xl shadow-inner font-black text-muted">
                            {skill.name.charAt(0)}
                          </div>
                          <div className="space-y-1">
                            <p className="text-xl font-black font-outfit text-main leading-tight">{skill.name}</p>
                            <div className="flex items-center gap-4">
                              <Badge color="violet">{skill.category}</Badge>
                            </div>
                          </div>
                        </div>
                        <button 
                          onClick={() => setEditingSkill(isEditing ? null : { id: skill.id, canonical_name: skill.name, category: skill.category || 'Tool', aliases: (skill.aliases || []).join(', ') })}
                          className={`p-4 rounded-2xl transition-all ${isEditing ? 'bg-primary text-white shadow-lg' : 'bg-subtle text-muted hover:text-primary hover:bg-primary/10'}`}
                        >
                          {isEditing ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
                        </button>
                      </div>
                      
                      {isEditing && (
                        <div className="p-8 bg-subtle/30 border-t border-base space-y-8 animate-in-slide">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-2">
                              <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Canonical Name</label>
                              <input 
                                value={editingSkill.canonical_name} 
                                onChange={e => setEditingSkill(p => ({ ...p, canonical_name: e.target.value }))} 
                                className="input-field py-4" 
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="text-[10px] font-black text-muted uppercase tracking-widest ml-1">Alternative Aliases (Comma Separated)</label>
                              <textarea 
                                rows={2} 
                                value={editingSkill.aliases} 
                                onChange={e => setEditingSkill(p => ({ ...p, aliases: e.target.value }))} 
                                className="input-field py-4 resize-none" 
                                placeholder="Alias A, Alias B..." 
                              />
                            </div>
                          </div>
                          <div className="flex justify-end">
                            <button onClick={saveSkill} className="btn-primary h-14 px-10 shadow-xl shadow-primary/20">
                              <Save className="w-5 h-5" />
                              Save Intelligence Delta
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Section>
          )}

          {tab === 'users' && (
            <Section title={`Global User Matrix (${users.length})`} icon={Lock}>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {users.map(u => (
                  <div key={u.id} className="surface-card p-6 flex items-center justify-between gap-6 hover:border-primary/30 group transition-all">
                    <div className="flex items-center gap-5 min-w-0">
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 border border-base flex items-center justify-center font-black text-primary font-outfit text-xl">
                        {u.email.charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="text-lg font-black font-outfit text-main truncate leading-tight">{u.email}</p>
                        <p className="text-[10px] font-black text-muted uppercase tracking-widest mt-1">Matrix ID: {u.id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 shrink-0">
                      {u.is_admin && <Badge color="violet">Root Admin</Badge>}
                      <button 
                        onClick={() => toggleAdmin(u.id)} 
                        className={`h-10 px-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border-2
                          ${u.is_admin ? 'bg-error/5 border-error/20 text-error hover:bg-error hover:text-white' : 'bg-primary/5 border-primary/20 text-primary hover:bg-primary hover:text-white'}`}
                      >
                        {u.is_admin ? 'Revoke Root' : 'Elevate to Root'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
