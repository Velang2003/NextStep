import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { 
  Map, Zap, Star, CheckSquare, AlertCircle, 
  TrendingUp, Compass, Rocket, Award, Loader2, 
  ArrowRight, ShieldCheck, Target, Sparkles, Globe
} from 'lucide-react';
import { Link } from 'react-router-dom';

const TIER_CONFIG = {
  critical:     { label: 'Must Learn',     color: 'text-error', border: 'border-error/20', bg: 'bg-error/5', icon: <AlertCircle className="w-5 h-5" /> },
  important:    { label: 'Recommended',    color: 'text-warning', border: 'border-warning/20', bg: 'bg-warning/5', icon: <Target className="w-5 h-5" /> },
  nice_to_have: { label: 'Bonus Skills',   color: 'text-success', border: 'border-success/20', bg: 'bg-success/5', icon: <Sparkles className="w-5 h-5" /> },
};

export default function CareerPath() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [recommendedRoles, setRecommendedRoles] = useState([]);

  useEffect(() => {
    api.get('/profile/career-path')
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.error || 'Failed to load career path.'))
      .finally(() => setLoading(false));
    
    api.get('/profile/recommended-roles')
      .then(r => setRecommendedRoles(r.data?.recommended_roles || []))
      .catch(() => {});
  }, []);

  const totalMissing = data
    ? Object.values(data.learning_path || {}).reduce((acc, arr) => acc + arr.length, 0)
    : 0;
  
  const strong = data?.strong_skills || [];
  const improve = data?.improvement_skills || [];

  return (
    <AppLayout>
      <div className="space-y-12 max-w-7xl mx-auto pb-20">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.2em]">
              <Compass className="w-3.5 h-3.5" />
              Your Career Plan
            </div>
            <h1 className="text-4xl font-black font-outfit text-main">Career Roadmap</h1>
            <p className="text-muted text-lg font-medium">
              A personalized guide to becoming an expert in {data?.target_role ? <span className="text-primary font-black">{data.target_role}</span> : 'your field'}.
            </p>
          </div>
        </header>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 space-y-4 surface-card">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <p className="text-muted font-bold uppercase tracking-widest text-xs">Creating your roadmap...</p>
          </div>
        ) : error ? (
          <div className="surface-card p-20 text-center space-y-8 max-w-3xl mx-auto border-error/10">
            <div className="w-24 h-24 bg-error/10 rounded-3xl flex items-center justify-center mx-auto">
              <AlertCircle className="w-12 h-12 text-error" />
            </div>
            <div className="space-y-3">
              <h2 className="text-3xl font-black font-outfit text-main">Something went wrong</h2>
              <p className="text-muted text-lg font-medium">We couldn't load your roadmap. Please try again.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Link to="/profile" className="btn-primary px-8">Setup Profile</Link>
              <Link to="/market" className="btn-secondary px-8">Explore Market Data</Link>
            </div>
          </div>
        ) : (
          <div className="space-y-16 animate-in-slide">
            {/* Executive Summary */}
            <div className="surface-card p-10 bg-gradient-to-br from-primary/5 via-secondary/5 to-transparent border-primary/10 relative overflow-hidden">
               <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 blur-[100px] -mr-48 -mt-48 rounded-full" />
               <div className="relative z-10 flex flex-col lg:flex-row items-center gap-10">
                <div className="w-24 h-24 rounded-[2.5rem] bg-primary flex items-center justify-center shrink-0 shadow-2xl shadow-primary/40">
                  <Map className="w-12 h-12 text-white" />
                </div>
                <div className="space-y-3 text-center lg:text-left">
                  <h2 className="text-4xl font-black font-outfit text-main">
                    {totalMissing} steps to your goal
                  </h2>
                  <p className="text-muted text-lg max-w-4xl leading-relaxed font-medium">
                    We've looked at <span className="text-primary font-black">{data.jobs_analyzed}</span> job listings to find the best path for you. 
                    Focusing on the <span className="text-error font-black uppercase tracking-wider">Must Learn</span> skills will help you get hired faster.
                  </p>
                </div>
              </div>
            </div>

            {/* Recommended Vectors */}
            {recommendedRoles.length > 0 && (
              <div className="space-y-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-black font-outfit text-main flex items-center gap-3">
                    <TrendingUp className="w-6 h-6 text-primary" /> 
                    Suggested Careers
                  </h2>
                  <span className="text-[10px] font-black uppercase tracking-widest text-muted">Jobs that match your skills</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  {recommendedRoles.filter(r => !r.is_current_target).slice(0, 3).map((role, idx) => (
                    <div key={idx} className="surface-card p-8 surface-card-hover group flex flex-col justify-between h-full space-y-6">
                      <div className="flex justify-between items-start">
                        <div className="w-12 h-12 bg-subtle rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">🚀</div>
                        <div className="flex flex-col items-end">
                          <span className="text-2xl font-black font-outfit text-primary">{role.match_percentage}%</span>
                          <span className="text-[10px] font-black uppercase tracking-widest text-muted">Skill Match</span>
                        </div>
                      </div>
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold font-outfit text-main group-hover:text-primary transition-colors leading-tight">{role.role}</h3>
                        <div className="flex items-center gap-2 text-xs font-black text-success">
                          <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                          {role.live_jobs} OPEN JOBS
                        </div>
                        {role.matched_skills?.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-4 border-t border-base">
                            {role.matched_skills.map(s => (
                              <span key={s} className="text-[9px] px-2.5 py-1 rounded-lg bg-success/10 text-success font-black border border-success/20 uppercase tracking-wider">✓ {s}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Competency Inventory */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              {/* Verified Strengths */}
              <div className="surface-card p-10 border-success/10 bg-success/[0.01] space-y-8">
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-black font-outfit text-main flex items-center gap-3">
                    <ShieldCheck className="w-7 h-7 text-success" /> Your Strengths
                  </h3>
                  <span className="text-[10px] font-black uppercase tracking-widest text-muted">Core Skills</span>
                </div>
                {strong.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4">
                    {strong.map(s => (
                      <div key={s.skill} className="bg-surface border border-base p-5 rounded-2xl flex justify-between items-center group hover:border-success/30 transition-all shadow-sm">
                        <span className="font-bold text-main">{s.skill}</span>
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-1.5 bg-subtle rounded-full overflow-hidden">
                            <div className="h-full bg-success rounded-full" style={{ width: `${s.score}%` }} />
                          </div>
                          <span className="text-xs font-black text-success bg-success/10 px-3 py-1 rounded-full border border-success/20">{s.score}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-10 text-center">
                    <p className="text-muted font-medium italic">Take a test to see your strengths here.</p>
                  </div>
                )}
              </div>

              {/* Optimization Targets */}
              <div className="surface-card p-10 border-warning/10 bg-warning/[0.01] space-y-8">
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-black font-outfit text-main flex items-center gap-3">
                    <Rocket className="w-7 h-7 text-warning" /> Skills to Improve
                  </h3>
                  <span className="text-[10px] font-black uppercase tracking-widest text-muted">Needs Focus</span>
                </div>
                {improve.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4">
                    {improve.map(s => (
                      <div key={s.skill} className="bg-surface border border-base p-5 rounded-2xl flex justify-between items-center group hover:border-warning/30 transition-all shadow-sm">
                        <span className="font-bold text-main">{s.skill}</span>
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-1.5 bg-subtle rounded-full overflow-hidden">
                            <div className="h-full bg-warning rounded-full" style={{ width: `${s.score}%` }} />
                          </div>
                          <span className="text-xs font-black text-warning bg-warning/10 px-3 py-1 rounded-full border border-warning/20">{s.score}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-10 text-center">
                    <p className="text-muted font-medium italic">Your skills are already at a great level!</p>
                  </div>
                )}
              </div>
            </div>

            {/* Strategic Roadmap Canvas */}
            <div className="space-y-10">
              <h2 className="text-3xl font-black font-outfit text-main">Your Learning Order</h2>
              
              <div className="space-y-8">
                {Object.entries(TIER_CONFIG).map(([tier, cfg]) => {
                  const items = data.learning_path?.[tier] || [];
                  if (items.length === 0) return null;
                  return (
                    <div key={tier} className={`surface-card p-12 border-2 ${cfg.border} ${cfg.bg} relative overflow-hidden group`}>
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
                        <div className="flex items-center gap-4">
                          <div className={`p-4 rounded-2xl bg-surface border border-base shadow-sm ${cfg.color}`}>
                            {cfg.icon}
                          </div>
                          <div>
                            <h4 className="text-3xl font-black font-outfit text-main uppercase tracking-tight">{cfg.label}</h4>
                            <p className="text-muted font-bold text-xs uppercase tracking-widest mt-1">Priority Level</p>
                          </div>
                        </div>
                        <div className={`px-6 py-3 rounded-2xl bg-surface border border-base shadow-sm flex items-center gap-4`}>
                          <span className="text-2xl font-black font-outfit text-main">{items.length}</span>
                          <span className="text-[10px] font-black uppercase tracking-widest text-muted">Pending Targets</span>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        {items.map(item => (
                          <div key={item.skill} className="space-y-4">
                            <div className="flex justify-between items-end">
                              <div className="space-y-1">
                                <span className="text-xl font-black text-main block group-hover:text-primary transition-colors">{item.skill}</span>
                                <span className="text-[10px] text-muted uppercase tracking-[0.2em] font-black">
                                  {item.market_count > 0 ? `${item.market_count?.toLocaleString()} Listings Required` : 'Baseline Standard'}
                                </span>
                              </div>
                              <div className="text-right">
                                <span className={`text-3xl font-black font-outfit ${cfg.color}`}>{item.demand_pct}%</span>
                                <span className="block text-[10px] text-muted font-black uppercase tracking-widest">Relative Demand</span>
                              </div>
                            </div>
                            <div className="h-3 bg-subtle rounded-full overflow-hidden border border-base">
                              <div 
                                className={`h-full rounded-full transition-all duration-1000 ease-out shadow-lg ${cfg.color.replace('text-', 'bg-')}`}
                                style={{ width: `${item.demand_pct}%` }} 
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Integrated Navigation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-12 border-t border-base">
              <Link to="/assessment" className="surface-card p-10 flex items-center gap-8 surface-card-hover group">
                <div className="w-20 h-20 bg-primary/10 rounded-[2rem] flex items-center justify-center text-4xl group-hover:scale-110 transition-transform">🎯</div>
                <div className="space-y-2">
                  <h4 className="text-2xl font-black font-outfit text-main group-hover:text-primary transition-colors">Test Your Skills</h4>
                  <p className="text-muted font-medium text-lg">Take a quick quiz to update your roadmap.</p>
                </div>
              </Link>
              <Link to="/market" className="surface-card p-10 flex items-center gap-8 surface-card-hover group">
                <div className="w-20 h-20 bg-secondary/10 rounded-[2rem] flex items-center justify-center text-4xl group-hover:scale-110 transition-transform">📊</div>
                <div className="space-y-2">
                  <h4 className="text-2xl font-black font-outfit text-main group-hover:text-secondary transition-colors">Job Trends</h4>
                  <p className="text-muted font-medium text-lg">See which skills are most in demand right now.</p>
                </div>
              </Link>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

