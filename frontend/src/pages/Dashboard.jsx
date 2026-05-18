import { useAuth } from '../context/AuthContext';
import AppLayout from '../components/AppLayout';
import { TrendingUp, Target, Map, Zap, FileDown, Briefcase, Award, ArrowUpRight, Sparkles, Clock, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useState, useEffect } from 'react';

const QUICK_ACTIONS = [
  { to: '/profile',     label: 'Update Profile', desc: 'Add your skills and the job you want',       icon: <Sparkles />, color: 'text-primary bg-primary/10' },
  { to: '/market',      label: 'Job Trends',     desc: 'See which skills are in high demand',       icon: <TrendingUp />, color: 'text-secondary bg-secondary/10' },
  { to: '/skill-gap',   label: 'What\'s Missing?', desc: 'See which skills you should learn next',     icon: <Target />, color: 'text-error bg-error/10' },
  { to: '/assessment',  label: 'Skill Tests',    desc: 'Take quick quizzes to test your knowledge',  icon: <Award />, color: 'text-success bg-success/10' },
  { to: '/career-path', label: 'Career Plan',    desc: 'See your personalized learning roadmap',      icon: <Map />, color: 'text-indigo-500 bg-indigo-500/10' },
  { to: '/geo-map',     label: 'Job Map',        desc: 'See where the jobs are located',             icon: <Globe />, color: 'text-cyan-500 bg-cyan-500/10' },
];

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.profile?.first_name || user?.email?.split('@')[0] || 'Member';
  const [downloading, setDownloading] = useState(false);
  const [stats, setStats] = useState({
    skill_match: 0,
    jobs_tracked: 0,
    skills_gap: 0,
    assessment_score: 0,
    applications: 0,
  });

  useEffect(() => {
    api.get('/jobs/dashboard-stats')
      .then(r => setStats(r.data))
      .catch(() => {});
  }, []);

  const STAT_CARDS = [
    { label: 'Skill Match',    value: `${stats.skill_match}%`,        icon: Target,     trend: 'Real-time', color: 'text-primary' },
    { label: 'Jobs Tracked',   value: stats.jobs_tracked.toLocaleString(), icon: TrendingUp, trend: 'Live Data',  color: 'text-secondary' },
    { label: 'Skills Gap',     value: stats.skills_gap,               icon: Zap,        trend: 'Critical',  color: 'text-error' },
    { label: 'Assessment',     value: `${stats.assessment_score}%`,  icon: Award,      trend: 'Personal',  color: 'text-success' },
  ];

  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      const res = await api.get('/reports/download', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `NextStep_Intelligence_Report_${firstName}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('[Download Error]', err);
      alert('Failed to generate report. Please make sure your profile is complete.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-10 max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.2em]">
              <Clock className="w-3.5 h-3.5" />
              Activity • {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}
            </div>
            <h1 className="text-4xl md:text-5xl font-black font-outfit text-main">
              Welcome, <span className="gradient-text">{firstName}</span>.
            </h1>
            <p className="text-muted text-lg font-medium">We are checking your career progress.</p>
          </div>
          
          <button 
            id="download-report-btn" 
            onClick={handleDownloadReport} 
            disabled={downloading}
            className="btn-primary h-14 px-8 shadow-lg shadow-primary/25 group"
          >
            <FileDown className={`w-5 h-5 ${downloading ? 'animate-bounce' : 'group-hover:scale-110 transition-transform'}`} />
            {downloading ? 'Preparing...' : 'Download My Report'}
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {STAT_CARDS.map(({ label, value, icon: Icon, trend, color }) => (
            <div key={label} className="surface-card p-8 space-y-6">
              <div className="flex items-center justify-between">
                <div className={`p-3 rounded-xl bg-subtle border border-base ${color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-subtle border border-base text-[10px] font-bold text-muted">
                  {trend}
                  <ArrowUpRight className="w-3 h-3 opacity-50" />
                </div>
              </div>
              <div>
                <p className="text-sm font-bold text-muted uppercase tracking-widest mb-1">{label}</p>
                <p className="text-4xl font-black font-outfit text-main">{value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Critical Onboarding / Profile Notice */}
        {!user?.profile?.target_role && (
          <div className="surface-card bg-primary p-1 md:p-1.5 overflow-hidden">
            <div className="bg-surface rounded-[1.25rem] p-8 md:p-12 flex flex-col lg:flex-row items-center gap-10">
              <div className="w-24 h-24 rounded-3xl bg-primary/5 flex items-center justify-center text-5xl animate-pulse">🎯</div>
              <div className="flex-1 text-center lg:text-left space-y-3">
                <h2 className="text-3xl font-black font-outfit text-main">Set Your Goal</h2>
                <p className="text-muted text-lg max-w-2xl font-medium">
                  Tell us the job you want and your current skills so we can help you grow. 
                  Land your dream job by completing your profile.
                </p>
              </div>
              <Link to="/profile" id="dashboard-setup-profile" className="btn-primary h-14 px-10 text-lg">
                Complete Setup
              </Link>
            </div>
          </div>
        )}

        {/* Intelligence Hub Grid */}
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-base" />
            <h2 className="text-xs font-black uppercase tracking-[0.3em] text-muted whitespace-nowrap">Explore Features</h2>
            <div className="h-px flex-1 bg-base" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {QUICK_ACTIONS.map(({ to, label, desc, icon, color }) => (
              <Link key={to} to={to} className="surface-card surface-card-hover p-8 group flex items-start gap-6">
                <div className={`shrink-0 w-16 h-16 rounded-2xl flex items-center justify-center text-3xl transition-transform duration-500 group-hover:scale-110 ${color}`}>
                  {icon}
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-main group-hover:text-primary transition-colors">{label}</h3>
                  <p className="text-muted font-medium text-sm leading-relaxed">{desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

