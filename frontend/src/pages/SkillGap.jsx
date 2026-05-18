import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { 
  RadarChart, Radar, PolarGrid, PolarAngleAxis, 
  ResponsiveContainer, Tooltip, PolarRadiusAxis 
} from 'recharts';
import { 
  Target, CheckCircle2, AlertCircle, Zap, Brain, 
  Sparkles, Award, Loader2, ChevronRight, BarChart3,
  Cpu, Activity, TrendingUp, Info, ArrowUpRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function SkillGap() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/profile/skill-gap')
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.error || 'Could not load analysis.'))
      .finally(() => setLoading(false));
  }, []);

  const radarData = data?.missing_skills?.slice(0, 8).map(skill => ({
    skill,
    demand: data.demand_frequencies?.[skill] || 0,
  })) || [];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="surface-card p-4 shadow-2xl border-primary/20 animate-in-fade backdrop-blur-xl">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted mb-2 border-b border-base pb-2">{payload[0].payload.skill}</p>
          <div className="flex items-center gap-3">
             <div className="w-1.5 h-8 rounded-full bg-primary" />
             <div className="flex flex-col">
                <span className="text-xl font-black font-outfit text-main">{payload[0].value}%</span>
                <span className="text-[10px] font-bold text-muted uppercase tracking-widest">Job Demand</span>
             </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <AppLayout>
      <div className="space-y-12 max-w-7xl mx-auto pb-20">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.3em]">
              <Brain className="w-4 h-4" />
              What's Missing?
            </div>
            <h1 className="text-5xl font-black font-outfit text-main tracking-tight">Skill Analysis</h1>
            <p className="text-muted text-xl font-medium max-w-2xl leading-relaxed">
              We compare your current skills to 
              {data?.target_role ? (
                <span className="text-primary font-bold"> {data.target_role} </span>
              ) : (
                ' the jobs '
              )}
              you're looking for.
            </p>
          </div>
          
          <div className="flex gap-4">
            <Link to="/profile" className="btn-secondary h-16 px-10 text-base group">
              Update Profile
              <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </header>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-48 space-y-8 surface-card">
            <div className="relative">
              <Loader2 className="w-16 h-16 text-primary animate-spin" />
              <Cpu className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-primary animate-pulse" />
            </div>
            <div className="text-center space-y-2">
              <p className="text-muted font-black uppercase tracking-[0.3em] text-xs">Analyzing Your Profile...</p>
              <p className="text-[10px] font-bold text-muted/60 uppercase">Checking job requirements</p>
            </div>
          </div>
        ) : error ? (
          <div className="surface-card p-20 text-center space-y-10 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/5 blur-[100px] -mt-48 rounded-full" />
            <div className="relative z-10 space-y-8">
              <div className="w-28 h-28 bg-surface rounded-[2.5rem] flex items-center justify-center mx-auto shadow-2xl border border-base">
                <Target className="w-12 h-12 text-primary animate-pulse" />
              </div>
              <div className="space-y-3">
                <h2 className="text-3xl font-black font-outfit text-main">Tell us about your goals</h2>
                <p className="text-muted max-w-lg mx-auto font-medium text-lg leading-relaxed">
                  We need to know your target job and current skills to show you what you should learn next.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row justify-center gap-6 pt-4">
                <Link to="/profile" id="skill-gap-setup-profile" className="btn-primary h-16 px-12 text-lg shadow-2xl shadow-primary/30">
                  Setup Profile
                </Link>
                <Link to="/market" id="skill-gap-sync-data" className="btn-secondary h-16 px-12 text-lg">
                  See Job Trends
                </Link>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-12 animate-in-slide">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
              {/* Match Score */}
              <div className="lg:col-span-5 surface-card p-12 bg-primary text-white flex flex-col items-center justify-center text-center space-y-8 shadow-2xl shadow-primary/30 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-80 h-80 bg-white/10 blur-[100px] -mr-40 -mt-40 rounded-full" />
                <div className="absolute bottom-0 left-0 w-80 h-80 bg-black/10 blur-[100px] -ml-40 -mb-40 rounded-full" />
                
                <div className="relative z-10 w-full flex flex-col items-center">
                  <div className="relative w-56 h-56">
                    <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90 filter drop-shadow-2xl">
                      <circle cx="50" cy="50" r="44" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="8" />
                      <circle cx="50" cy="50" r="44" fill="none"
                        stroke="white" strokeWidth="8" strokeLinecap="round"
                        className="transition-all duration-[2000ms] ease-out"
                        strokeDasharray={`${data.match_percentage * 2.764} 276.4`} />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center space-y-1">
                      <span className="text-6xl font-black font-outfit tracking-tighter">{data.match_percentage}%</span>
                      <span className="text-[10px] font-black uppercase tracking-[0.3em] opacity-80">Job Match Score</span>
                    </div>
                  </div>
                  <div className="mt-10 space-y-3">
                    <h2 className="text-3xl font-black font-outfit tracking-tight">Market Demand</h2>
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 text-xs font-bold uppercase tracking-widest">
                      <Activity className="w-4 h-4" />
                      {data.jobs_analyzed?.toLocaleString() || 0} Jobs Analyzed
                    </div>
                  </div>
                </div>
              </div>

              {/* Insights Panel */}
              <div className="lg:col-span-7 surface-card p-12 flex flex-col justify-center space-y-10 shadow-xl">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 text-primary font-black uppercase tracking-[0.2em] text-xs">
                    <Sparkles className="w-5 h-5" />
                    How to Improve
                  </div>
                  <h3 className="text-3xl font-black font-outfit text-main leading-tight">
                    Your Skill Summary
                  </h3>
                  <p className="text-muted text-xl font-medium leading-relaxed">
                    You already have good experience with <span className="text-primary font-bold"> {data.owned_skills?.[0] || 'your core skills'} </span>. 
                    By learning <span className="text-error font-bold">{data.missing_skills?.length} more skills</span>, you'll be ready for many more job openings.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 pt-10 border-t border-base">
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-muted uppercase tracking-[0.2em]">Skills You Have</p>
                    <div className="flex items-center gap-3">
                      <p className="text-5xl font-black font-outfit text-success">{data.owned_skills?.length}</p>
                      <div className="p-2 rounded-xl bg-success/10 text-success">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-muted uppercase tracking-[0.2em]">Skills to Learn</p>
                    <div className="flex items-center gap-3">
                      <p className="text-5xl font-black font-outfit text-error">{data.missing_skills?.length}</p>
                      <div className="p-2 rounded-xl bg-error/10 text-error">
                        <AlertCircle className="w-5 h-5" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              {/* Missing Skills */}
              <div className="surface-card p-10 space-y-10 shadow-xl">
                <div className="flex items-center justify-between border-b border-base pb-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-2xl bg-error/10">
                      <AlertCircle className="w-6 h-6 text-error" />
                    </div>
                    <h3 className="text-2xl font-black font-outfit text-main">What's Missing</h3>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-black text-muted uppercase tracking-widest">
                    <Activity className="w-3.5 h-3.5" />
                    Market Demand
                  </div>
                </div>
                
                <div className="space-y-8">
                  {data.missing_skills?.slice(0, 8).map((skill, i) => {
                    const freq = data.demand_frequencies?.[skill] || 0;
                    const max  = Math.max(...Object.values(data.demand_frequencies || {}), 1);
                    const pct  = Math.round(freq / max * 100);
                    return (
                      <div key={skill} className="space-y-3 group cursor-default">
                        <div className="flex justify-between items-end">
                          <span className="text-sm font-black text-main group-hover:text-error transition-colors">{skill}</span>
                          <span className="text-xs font-black text-muted tracking-widest">{freq}% DEMAND</span>
                        </div>
                        <div className="h-3 bg-subtle rounded-full overflow-hidden border border-base p-0.5">
                          <div className="h-full bg-error rounded-full transition-all duration-1000 ease-out shadow-lg"
                            style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Skills You Have */}
              <div className="surface-card p-10 space-y-10 shadow-xl">
                <div className="flex items-center justify-between border-b border-base pb-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-2xl bg-success/10">
                      <CheckCircle2 className="w-6 h-6 text-success" />
                    </div>
                    <h3 className="text-2xl font-black font-outfit text-main">Skills You Have</h3>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-black text-muted uppercase tracking-widest">
                    <Award className="w-3.5 h-3.5" />
                    Verified Skills
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {data.owned_skills?.map(skill => (
                    <div key={skill} className="group flex items-center justify-between px-6 py-4 rounded-2xl bg-surface border-2 border-base hover:border-success/40 transition-all cursor-default">
                      <span className="font-black text-main text-sm truncate">{skill}</span>
                      <CheckCircle2 className="w-5 h-5 text-success/40 group-hover:text-success transition-colors shrink-0" />
                    </div>
                  ))}
                  {(!data.owned_skills || data.owned_skills.length === 0) && (
                    <div className="col-span-2 py-16 text-center bg-subtle/30 rounded-[2.5rem] border-2 border-dashed border-base space-y-4">
                      <div className="w-16 h-16 bg-surface rounded-2xl flex items-center justify-center mx-auto shadow-inner">
                        <Award className="w-8 h-8 text-muted opacity-30" />
                      </div>
                      <p className="text-muted font-bold text-sm uppercase tracking-widest">No verified skills yet</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Skill Chart */}
            {radarData.length > 0 && (
              <div className="surface-card p-12 lg:p-16 flex flex-col items-center space-y-12 shadow-2xl relative overflow-hidden">
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-primary/5 blur-[100px] -mr-48 -mb-48 rounded-full" />
                
                <div className="w-full text-center space-y-3 relative z-10">
                  <div className="flex items-center justify-center gap-3 text-primary font-black uppercase tracking-[0.3em] text-xs">
                    <Activity className="w-5 h-5" />
                    Market Overview
                  </div>
                  <h3 className="text-4xl font-black font-outfit text-main tracking-tight">Skill Chart</h3>
                  <p className="text-muted text-lg font-medium max-w-xl mx-auto">This chart shows which missing skills are most important for your career.</p>
                </div>

                <div className="h-[500px] w-full relative z-10">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="var(--color-base)" strokeWidth={1} />
                      <PolarAngleAxis 
                        dataKey="skill" 
                        tick={{ fill: 'var(--color-muted)', fontSize: 11, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '1px' }} 
                      />
                      <PolarRadiusAxis angle={30} domain={[0, 'auto']} axisLine={false} tick={false} />
                      <Radar
                        name="Demand"
                        dataKey="demand"
                        stroke="var(--color-primary)"
                        fill="var(--color-primary)"
                        fillOpacity={0.15}
                        strokeWidth={3}
                        animationDuration={2000}
                        animationEasing="ease-out"
                      />
                      <Tooltip content={<CustomTooltip />} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Next Steps */}
            <div className="surface-card p-12 bg-subtle/30 border-2 border-dashed border-base flex flex-col md:flex-row items-center justify-between gap-10">
              <div className="space-y-3 max-w-2xl text-center md:text-left">
                <div className="flex items-center justify-center md:justify-start gap-3 text-primary font-black uppercase tracking-[0.2em] text-xs">
                  <TrendingUp className="w-5 h-5" />
                  Next Steps
                </div>
                <h4 className="text-3xl font-black font-outfit text-main">Ready to start learning?</h4>
                <p className="text-muted text-lg font-medium leading-relaxed">
                  We've created a personalized plan to help you learn these skills quickly.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-6 w-full md:w-auto">
                <Link to="/career-path" id="view-career-path-btn" className="btn-primary h-16 px-12 text-lg shadow-2xl shadow-primary/30 group">
                  <Zap className="w-6 h-6 group-hover:scale-110 transition-transform fill-current" />
                  See My Plan
                </Link>
                <Link to="/assessment" className="btn-secondary h-16 px-12 text-lg">
                  Take a Test
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

