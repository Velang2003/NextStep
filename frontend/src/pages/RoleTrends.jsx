import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { 
  Briefcase, TrendingUp, BarChart2, Filter, 
  ChevronRight, Loader2, Award, Sparkles, Globe
} from 'lucide-react';

const COLORS = ['#6366f1','#8b5cf6','#a78bfa','#60a5fa','#34d399','#f59e0b','#f472b6','#fb923c','#38bdf8','#4ade80'];

export default function RoleTrends() {
  const [roles, setRoles] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [selectedSector, setSelectedSector] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/taxonomy/sectors').then(r => {
      setSectors(r.data || []);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = selectedSector ? `?sector=${encodeURIComponent(selectedSector)}&limit=20` : '?limit=20';
    api.get(`/jobs/trends/roles${params}`)
      .then(r => setRoles(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedSector]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="surface-card p-4 shadow-xl border-primary/20 animate-in-fade">
          <p className="text-xs font-black text-muted uppercase tracking-[0.2em] mb-1">
            {payload[0].payload.sector}
          </p>
          <p className="text-sm font-bold text-main mb-2">{payload[0].payload.role}</p>
          <div className="h-px bg-base mb-2" />
          <p className="text-lg font-black text-primary">{payload[0].value} <span className="text-xs font-bold text-muted">Listings</span></p>
        </div>
      );
    }
    return null;
  };

  return (
    <AppLayout>
      <div className="space-y-10 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-secondary font-bold text-xs uppercase tracking-[0.2em]">
              <BarChart2 className="w-3.5 h-3.5" />
              Market Dominance
            </div>
            <h1 className="text-4xl font-black font-outfit text-main">Role Trends</h1>
            <p className="text-muted text-lg font-medium">Most in-demand professional roles across global sectors.</p>
          </div>
        </header>

        {/* Sector Filter Bar */}
        <div className="surface-card p-2 flex flex-wrap items-center gap-2 overflow-x-auto no-scrollbar">
          <div className="px-4 py-2 flex items-center gap-2 border-r border-base mr-2">
            <Filter className="w-4 h-4 text-muted" />
            <span className="text-xs font-black uppercase tracking-widest text-muted">Sector</span>
          </div>
          <button
            id="role-sector-all"
            onClick={() => setSelectedSector('')}
            className={`px-5 py-2 rounded-xl text-xs font-bold transition-all
              ${!selectedSector 
                ? 'bg-secondary text-white shadow-lg shadow-secondary/20' 
                : 'text-muted hover:text-main hover:bg-subtle'}`}
          >
            All Sectors
          </button>
          {sectors.filter(s => s.name !== 'Other').map(s => (
            <button
              key={s.name}
              id={`role-sector-${s.name}`}
              onClick={() => setSelectedSector(s.name)}
              className={`px-5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap
                ${selectedSector === s.name 
                  ? 'bg-secondary text-white shadow-lg shadow-secondary/20' 
                  : 'text-muted hover:text-main hover:bg-subtle'}`}
            >
              {s.name}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 space-y-4 surface-card">
            <Loader2 className="w-10 h-10 text-secondary animate-spin" />
            <p className="text-muted font-bold uppercase tracking-widest text-xs">Aggregating Global Data...</p>
          </div>
        ) : roles.length === 0 ? (
          <div className="surface-card p-20 text-center space-y-6">
            <div className="w-24 h-24 bg-subtle rounded-3xl flex items-center justify-center mx-auto">
              <Briefcase className="w-10 h-10 text-muted" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold font-outfit text-main">No Trend Data Detected</h2>
              <p className="text-muted max-w-sm mx-auto font-medium">Please synchronize your market intelligence engine to view role dominance.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-10 animate-in-slide">
            {/* Chart Surface */}
            <div className="surface-card p-8 lg:p-12 space-y-8">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <h3 className="text-2xl font-bold font-outfit text-main flex items-center gap-3">
                    <TrendingUp className="w-6 h-6 text-primary" />
                    Demand Distribution
                  </h3>
                  <p className="text-sm font-medium text-muted">Relative hiring volume for top {roles.length} roles</p>
                </div>
                <div className="hidden sm:flex items-center gap-4 text-[10px] font-black uppercase tracking-widest text-muted">
                  <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-primary" /> Volume</span>
                  <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-secondary" /> Growth</span>
                </div>
              </div>

              <div className="h-[500px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={roles} layout="vertical" margin={{ top: 0, right: 40, left: 20, bottom: 0 }}>
                    <CartesianGrid stroke="var(--color-base)" strokeDasharray="4 4" horizontal={false} />
                    <XAxis type="number" hide />
                    <YAxis 
                      dataKey="role" 
                      type="category" 
                      tick={{ fill: 'var(--color-main)', fontSize: 13, fontWeight: 700 }}
                      width={180}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--color-subtle)', opacity: 0.4 }} />
                    <Bar dataKey="count" radius={[0, 8, 8, 0]} barSize={24}>
                      {roles.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {roles.slice(0, 9).map((role, i) => (
                <div key={role.role} className="surface-card p-8 surface-card-hover group flex flex-col justify-between h-full space-y-6">
                  <div className="flex items-start justify-between">
                    <div 
                      className="w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-black text-white shadow-lg transition-transform duration-500 group-hover:scale-110"
                      style={{ background: COLORS[i % COLORS.length] }}
                    >
                      {i + 1}
                    </div>
                    <span className="px-3 py-1 rounded-full bg-subtle border border-base text-[10px] font-black uppercase tracking-widest text-muted group-hover:border-primary/30 transition-colors">
                      {role.sector}
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    <h3 className="text-xl font-bold text-main leading-tight group-hover:text-primary transition-colors">{role.role}</h3>
                    <div className="flex items-center justify-between pt-4 border-t border-base">
                      <p className="text-2xl font-black font-outfit text-main">{role.count}</p>
                      <p className="text-[10px] font-black uppercase tracking-widest text-muted">Active Listings</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-10 border-t border-base">
              <div className="flex items-center gap-4 text-muted">
                <Globe className="w-5 h-5 opacity-50" />
                <span className="text-sm font-medium">Data aggregated from over 12 global career networks</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

