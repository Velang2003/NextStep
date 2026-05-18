import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  Cell, PieChart, Pie, Legend 
} from 'recharts';
import { 
  TrendingUp, RefreshCw, AlertCircle, Search, BarChart3, 
  Clock, Zap, ArrowUpRight, ArrowDownRight, Globe, Layers, Loader2, 
  Activity, Database, Cpu, PieChart as PieIcon, MapPin
} from 'lucide-react';
import { Link } from 'react-router-dom';

const COLORS = [
  '#2563eb', // primary
  '#7c3aed', // secondary
  '#059669', // success
  '#ea580c', // warning
  '#dc2626', // error
  '#0891b2', 
  '#4f46e5', 
  '#db2777'
];

export default function MarketTrends() {
  const { user } = useAuth();
  const [skills, setSkills] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [sectorList, setSectorList] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sector, setSector] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/taxonomy/sectors').then(r => {
      setSectorList((r.data || []).filter(s => s.name !== 'Other'));
    });
  }, []);

  const loadData = async () => {
    setLoading(true); setError('');
    try {
      const [sk, sec, loc] = await Promise.all([
        api.get(`/jobs/trends/skills${sector ? `?sector=${encodeURIComponent(sector)}` : ''}`),
        api.get('/jobs/trends/sectors'),
        api.get('/jobs/trends/locations'),
      ]);
      setSkills(sk.data);
      setSectors(sec.data);
      setLocations(loc.data);
    } catch (e) {
      setError('Job data is currently unavailable. Please refresh the trends.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [sector]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="surface-card p-4 shadow-2xl border-primary/20 animate-in-fade backdrop-blur-xl">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted mb-2 border-b border-base pb-2">{label || payload[0]?.name}</p>
          <div className="flex items-center gap-3">
            <div className="w-2 h-10 rounded-full bg-primary" />
            <div className="flex flex-col">
              <span className="text-2xl font-black font-outfit text-main leading-none">{payload[0].value.toLocaleString()}</span>
              <span className="text-[10px] font-bold text-muted uppercase tracking-widest mt-1">Live Listings</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <AppLayout>
      <div className="space-y-12 max-w-screen-2xl mx-auto pb-20">
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.3em]">
              <Activity className="w-4 h-4" />
              Market Overview • {new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
            </div>
            <h1 className="text-5xl font-black font-outfit text-main tracking-tight">Job Trends</h1>
            <p className="text-muted text-xl font-medium max-w-3xl">
              See which skills are currently in demand by employers worldwide.
            </p>
          </div>
          
          <div className="flex items-center gap-3 px-6 py-3 rounded-2xl bg-subtle border border-base">
              <Clock className="w-4 h-4 text-muted" />
              <span className="text-xs font-black text-muted uppercase tracking-widest">Auto-updated daily at 2 AM</span>
            </div>
        </header>

        {error && (
          <div className="p-6 rounded-[2rem] bg-error/5 border border-error/10 text-error font-bold flex items-center gap-4 animate-in-fade">
            <div className="p-2 rounded-xl bg-error/10">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-black uppercase tracking-widest">Could not load data</h4>
              <p className="text-xs opacity-80">{error}</p>
            </div>
          </div>
        )}

        {/* Intelligence Filters */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-black text-muted uppercase tracking-[0.2em] flex items-center gap-2">
              <Database className="w-4 h-4" />
              Filter by Industry
            </h3>
            <span className="text-[10px] font-bold text-primary bg-primary/10 px-3 py-1 rounded-full border border-primary/20">
              {sectorList.length + 1} Industries Tracked
            </span>
          </div>
          <div className="flex gap-3 pb-4 overflow-x-auto no-scrollbar whitespace-nowrap">
            <button
              onClick={() => setSector('')}
              className={`px-8 py-3 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border-2
                ${sector === '' 
                  ? 'bg-primary border-primary text-white shadow-xl shadow-primary/20' 
                  : 'bg-surface border-base text-muted hover:border-primary/40 hover:bg-subtle'}`}
            >
              All Industries
            </button>
            {sectorList.map(s => (
              <button key={s.name}
                onClick={() => setSector(s.name)}
                className={`px-8 py-3 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border-2
                  ${sector === s.name 
                    ? 'bg-primary border-primary text-white shadow-xl shadow-primary/20' 
                    : 'bg-surface border-base text-muted hover:border-primary/40 hover:bg-subtle'}`}
              >
                {s.name}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-48 space-y-8 surface-card">
            <div className="relative">
              <Loader2 className="w-16 h-16 text-primary animate-spin" />
              <Cpu className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-primary animate-pulse" />
            </div>
            <div className="text-center space-y-2">
              <p className="text-muted font-black uppercase tracking-[0.3em] text-xs">Updating job data...</p>
              <p className="text-[10px] font-bold text-muted/60 uppercase">Fetching latest job listings</p>
            </div>
          </div>
        ) : (
          <div className="space-y-12 animate-in-slide">
            {/* Primary Skill Demand Canvas */}
            <div className="surface-card p-10 lg:p-14 space-y-12 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 blur-[100px] -mr-48 -mt-48 rounded-full" />
              
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 relative z-10">
                <div className="space-y-2">
                  <h2 className="text-3xl font-black font-outfit text-main flex items-center gap-4">
                    <div className="p-3 rounded-[1.25rem] bg-primary/10 border border-primary/20">
                      <TrendingUp className="w-8 h-8 text-primary" />
                    </div>
                    Skill Demand
                  </h2>
                  <p className="text-muted font-medium text-lg">Most requested skills in the current job market.</p>
                </div>
                <div className="flex gap-4">
                   <div className="surface-card px-8 py-4 bg-subtle/50 border-base text-center">
                    <p className="text-[10px] font-black text-muted uppercase tracking-widest">Active Skills</p>
                    <p className="text-3xl font-black font-outfit text-primary">{skills.length}</p>
                   </div>
                   <div className="surface-card px-8 py-4 bg-subtle/50 border-base text-center">
                    <p className="text-[10px] font-black text-muted uppercase tracking-widest">Total Demand</p>
                    <p className="text-3xl font-black font-outfit text-main">{skills.reduce((a, b) => a + b.count, 0).toLocaleString()}</p>
                   </div>
                </div>
              </div>

              {skills.length === 0 ? (
                <div className="text-center py-32 bg-subtle/30 rounded-[3rem] border-2 border-dashed border-base space-y-8">
                  <div className="w-24 h-24 bg-surface rounded-[2rem] flex items-center justify-center mx-auto shadow-inner">
                    <PieIcon className="w-10 h-10 text-muted opacity-40" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-2xl font-bold font-outfit text-main">No data found</h3>
                    <p className="text-muted font-medium max-w-md mx-auto leading-relaxed">We couldn't find any job data for this industry yet.</p>
                  </div>
                  <p className="text-xs font-bold text-muted uppercase tracking-widest">Data is refreshed automatically every day at 2:00 AM</p>
                </div>
              ) : (
                <div className="h-[500px] w-full relative z-10 overflow-x-auto no-scrollbar">
                  <div style={{ width: Math.max(skills.length * 60, 600), minWidth: '100%', height: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={skills} margin={{ top: 20, right: 30, left: 0, bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-base)" vertical={false} />
                        <XAxis 
                          dataKey="skill" 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fill: 'var(--color-muted)', fontSize: 11, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '1px' }}
                          angle={-45} 
                          textAnchor="end" 
                          interval={0}
                          dy={20}
                        />
                        <YAxis 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fill: 'var(--color-muted)', fontSize: 11, fontWeight: 800 }}
                        />
                        <Tooltip 
                          content={<CustomTooltip />} 
                          cursor={{ fill: 'var(--color-primary)', opacity: 0.05, radius: 10 }} 
                        />
                        <Bar 
                          dataKey="count" 
                          radius={[10, 10, 0, 0]} 
                          barSize={40}
                          animationDuration={1500}
                          animationEasing="ease-out"
                        >
                          {skills.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

            {/* Dimensional Breakdowns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              {/* Sector Distribution */}
              <div className="surface-card p-10 space-y-10 shadow-xl border-indigo-500/10">
                <div className="flex items-center justify-between border-b border-base pb-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-2xl bg-indigo-500/10">
                      <Layers className="w-6 h-6 text-indigo-500" />
                    </div>
                    <h3 className="text-2xl font-black font-outfit text-main">Industry Trends</h3>
                  </div>
                  <Link to="/role-trends" className="btn-secondary h-10 px-4 text-[10px] gap-2">
                    JOB ROLES <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
                
                <div className="space-y-8">
                  {sectors.slice(0, 6).map((sec, i) => {
                    const max = sectors[0]?.total_jobs || sectors[0]?.count || 1;
                    const count = sec.total_jobs || sec.count || 0;
                    const pct = Math.round(count / max * 100);
                    const growth = sec.growth_pct || 0;
                    return (
                      <div key={sec.sector} className="space-y-3 group cursor-default">
                        <div className="flex justify-between items-end">
                          <span className="text-sm font-black text-main group-hover:text-primary transition-colors">{sec.sector}</span>
                          <div className="flex items-center gap-4">
                            <span className="text-xs font-black text-muted tracking-widest">{count.toLocaleString()} ROLES</span>
                            {growth !== 0 && (
                              <div className={`flex items-center gap-1 text-[10px] font-black px-2 py-1 rounded-lg border shadow-sm ${growth > 0 ? 'bg-success/5 text-success border-success/20' : 'bg-error/5 text-error border-error/20'}`}>
                                {growth > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                                {Math.abs(growth)}%
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="h-3 bg-subtle rounded-full overflow-hidden border border-base p-0.5">
                          <div className="h-full rounded-full transition-all duration-1000 ease-out shadow-lg"
                            style={{ width: `${pct}%`, backgroundColor: COLORS[i % COLORS.length] }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Geographical Density */}
              <div className="surface-card p-10 space-y-10 shadow-xl border-success-500/10">
                <div className="flex items-center justify-between border-b border-base pb-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-2xl bg-success/10">
                      <Globe className="w-6 h-6 text-success" />
                    </div>
                    <h3 className="text-2xl font-black font-outfit text-main">Jobs by Location</h3>
                  </div>
                  <Link to="/geo-map" className="btn-secondary h-10 px-4 text-[10px] gap-2">
                    SEE MAP <MapPin className="w-3.5 h-3.5" />
                  </Link>
                </div>
                
                <div className="space-y-8">
                  {locations.slice(0, 6).map((loc, i) => {
                    const max = locations[0]?.count || 1;
                    const pct = Math.round(loc.count / max * 100);
                    return (
                      <div key={loc.country} className="space-y-3 group cursor-default">
                        <div className="flex justify-between items-end">
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[(i + 4) % COLORS.length] }} />
                            <span className="text-sm font-black text-main group-hover:text-success transition-colors">{loc.country || 'Global/Remote'}</span>
                          </div>
                          <span className="text-xs font-black text-muted tracking-widest">{loc.count.toLocaleString()} LIVE NODES</span>
                        </div>
                        <div className="h-3 bg-subtle rounded-full overflow-hidden border border-base p-0.5">
                          <div className="h-full rounded-full transition-all duration-1000 ease-out shadow-lg"
                            style={{ width: `${pct}%`, backgroundColor: COLORS[(i + 4) % COLORS.length] }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

