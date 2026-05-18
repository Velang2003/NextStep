import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { 
  Briefcase, ExternalLink, Trash2, StickyNote, 
  ChevronDown, ChevronUp, GripVertical, CheckCircle2, 
  Clock, XCircle, Star, Target, Loader2, Save, MapPin
} from 'lucide-react';

const COLUMNS = [
  { key: 'saved', label: 'Saved', icon: <Star />, color: 'text-muted', border: 'border-base', bg: 'bg-subtle' },
  { key: 'applied', label: 'Applied', icon: <Clock />, color: 'text-primary', border: 'border-primary/20', bg: 'bg-primary/5' },
  { key: 'interviewing', label: 'Interviewing', icon: <Target />, color: 'text-secondary', border: 'border-secondary/20', bg: 'bg-secondary/5' },
  { key: 'offered', label: 'Offered', icon: <CheckCircle2 />, color: 'text-success', border: 'border-success/20', bg: 'bg-success/5' },
  { key: 'rejected', label: 'Rejected', icon: <XCircle />, color: 'text-error', border: 'border-error/20', bg: 'bg-error/5' },
];

export default function Applications() {
  const [apps, setApps] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedNotes, setExpandedNotes] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [dragItem, setDragItem] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [appsRes, statsRes] = await Promise.all([
        api.get('/applications/'),
        api.get('/applications/stats'),
      ]);
      setApps(appsRes.data || []);
      setStats(statsRes.data || {});
    } catch {}
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const updateStatus = async (appId, newStatus) => {
    try {
      await api.put(`/applications/${appId}/status`, { status: newStatus });
      setApps(prev => prev.map(a =>
        a.id === appId ? { ...a, status: newStatus } : a
      ));
      api.get('/applications/stats').then(r => setStats(r.data || {}));
    } catch {}
  };

  const deleteApp = async (appId) => {
    if (!window.confirm('Remove this tracked application?')) return;
    try {
      await api.delete(`/applications/${appId}`);
      setApps(prev => prev.filter(a => a.id !== appId));
      api.get('/applications/stats').then(r => setStats(r.data || {}));
    } catch {}
  };

  const saveNotes = async (appId) => {
    try {
      await api.put(`/applications/${appId}/notes`, { notes: noteText });
      setApps(prev => prev.map(a =>
        a.id === appId ? { ...a, notes: noteText } : a
      ));
      setExpandedNotes(null);
    } catch {}
  };

  const handleDragStart = (e, appId) => {
    setDragItem(appId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, newStatus) => {
    e.preventDefault();
    if (dragItem) {
      updateStatus(dragItem, newStatus);
      setDragItem(null);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-10 max-w-screen-2xl mx-auto">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.2em]">
              <Target className="w-3.5 h-3.5" />
              Pipeline Tracking
            </div>
            <h1 className="text-4xl font-black font-outfit text-main">Applications Tracker</h1>
            <p className="text-muted text-lg font-medium">Manage your professional pipeline with precision.</p>
          </div>
        </header>

        {/* Dynamic Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {COLUMNS.map(col => (
            <div key={col.key} className="surface-card p-6 flex flex-col items-center justify-center text-center space-y-2 group transition-all hover:border-primary/30">
              <span className={`text-2xl font-black font-outfit text-main group-hover:text-primary transition-colors`}>{stats[col.key] || 0}</span>
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${col.color.replace('text-', 'bg-')}`} />
                <span className="text-[10px] font-black uppercase tracking-widest text-muted">{col.label}</span>
              </div>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 space-y-4 surface-card">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <p className="text-muted font-bold uppercase tracking-widest text-xs">Loading Pipeline Data...</p>
          </div>
        ) : apps.length === 0 ? (
          <div className="surface-card p-20 text-center space-y-6">
            <div className="w-24 h-24 bg-subtle rounded-3xl flex items-center justify-center mx-auto">
              <Briefcase className="w-10 h-10 text-muted" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold font-outfit text-main">Pipeline Empty</h2>
              <p className="text-muted max-w-sm mx-auto font-medium">Save jobs or start applications from the Job Browser to populate your tracker.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6 items-start overflow-x-auto pb-8 no-scrollbar">
            {COLUMNS.map(col => {
              const colApps = apps.filter(a => a.status === col.key);
              return (
                <div key={col.key}
                  className={`flex flex-col min-w-[320px] max-w-full rounded-[2rem] border transition-all duration-300 p-2 min-h-[600px]
                    ${col.border} ${col.bg}`}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, col.key)}
                >
                  {/* Column Header */}
                  <div className="p-4 mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-xl bg-surface border border-base ${col.color}`}>
                        {col.icon}
                      </div>
                      <h3 className="font-bold font-outfit text-main">{col.label}</h3>
                    </div>
                    <span className="text-xs font-black text-muted bg-surface/80 border border-base px-2.5 py-1 rounded-lg">
                      {colApps.length}
                    </span>
                  </div>

                  {/* Cards Area */}
                  <div className="flex-1 space-y-4 px-2 overflow-y-auto no-scrollbar">
                    {colApps.map(app => (
                      <div key={app.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, app.id)}
                        className={`surface-card p-6 cursor-grab active:cursor-grabbing hover:shadow-xl transition-all duration-300 group relative
                                    ${dragItem === app.id ? 'opacity-50 grayscale' : ''}`}
                      >
                        <div className="flex items-start gap-4">
                          <GripVertical className="w-4 h-4 text-muted/30 mt-1 shrink-0 group-hover:text-primary transition-colors" />
                          <div className="flex-1 min-w-0 space-y-1">
                            <h4 className="text-sm font-bold text-main truncate leading-tight group-hover:text-primary transition-colors">{app.job?.title}</h4>
                            <p className="text-xs font-bold text-muted truncate">{app.job?.company}</p>
                          </div>
                        </div>

                        <div className="mt-4 pt-4 border-t border-base space-y-4">
                          {app.job?.location && (
                            <div className="flex items-center gap-2 text-muted">
                              <MapPin className="w-3 h-3" />
                              <span className="text-[10px] font-bold truncate">{app.job.location}</span>
                            </div>
                          )}

                          {/* Notes Preview */}
                          {expandedNotes === app.id ? (
                            <div className="space-y-3 animate-in-fade">
                              <textarea 
                                value={noteText}
                                onChange={e => setNoteText(e.target.value)}
                                className="input-field text-xs min-h-[80px] py-3 leading-relaxed"
                                placeholder="Strategy notes..." 
                              />
                              <div className="flex gap-2">
                                <button onClick={() => saveNotes(app.id)} className="btn-primary h-8 px-4 text-[10px]">
                                  <Save className="w-3 h-3" /> Save
                                </button>
                                <button onClick={() => setExpandedNotes(null)} className="btn-secondary h-8 px-4 text-[10px]">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            app.notes && (
                              <div className="p-3 rounded-xl bg-subtle border border-base group/note">
                                <p className="text-[10px] text-muted font-medium italic line-clamp-2 leading-relaxed">{app.notes}</p>
                              </div>
                            )
                          )}

                          {/* Interactive Footer */}
                          <div className="flex items-center justify-between pt-2">
                            <div className="flex items-center gap-1">
                              {app.job?.url && (
                                <a 
                                  href={app.job.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="p-2 rounded-lg text-muted hover:text-primary hover:bg-primary/10 transition-all"
                                  title="View Original Listing"
                                >
                                  <ExternalLink className="w-3.5 h-3.5" />
                                </a>
                              )}
                              <button 
                                onClick={() => { setExpandedNotes(app.id); setNoteText(app.notes || ''); }}
                                className="p-2 rounded-lg text-muted hover:text-primary hover:bg-primary/10 transition-all"
                                title="Edit Notes"
                              >
                                <StickyNote className="w-3.5 h-3.5" />
                              </button>
                            </div>
                            <button 
                              onClick={() => deleteApp(app.id)}
                              className="p-2 rounded-lg text-muted hover:text-error hover:bg-error/10 transition-all"
                              title="Archive Application"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                    {colApps.length === 0 && (
                      <div className="h-24 rounded-3xl border border-dashed border-base flex items-center justify-center text-[10px] font-black uppercase tracking-widest text-muted opacity-40">
                        Drop Here
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppLayout>
  );
}

