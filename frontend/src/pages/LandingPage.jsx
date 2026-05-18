import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Brain, Target, Compass, Briefcase, ChevronRight, BarChart3, 
  Database, Code2, Rocket, Shield, Zap, Globe, Sparkles,
  Activity, ArrowUpRight, CheckCircle2, Star, Cpu, Fingerprint
} from 'lucide-react';

export default function LandingPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard');
    }
  }, [user, loading, navigate]);

  if (loading) return null;

  return (
    <div className="min-h-screen bg-main flex flex-col selection:bg-primary/30 font-inter">
      {/* Dynamic Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-primary/10 blur-[150px] animate-pulse duration-[5000ms]" />
        <div className="absolute bottom-[0%] left-[-10%] w-[50%] h-[50%] rounded-full bg-secondary/10 blur-[150px] animate-pulse duration-[7000ms]" />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-[100] bg-main/70 backdrop-blur-2xl border-b border-base/50">
        <div className="max-w-7xl mx-auto px-8 h-24 flex items-center justify-between">
          <div className="flex items-center gap-4 group cursor-pointer">
            <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center shadow-2xl group-hover:rotate-12 transition-transform overflow-hidden border border-base">
              <img src="/logo.png" alt="NextStep Logo" className="w-9 h-9 object-contain" />
            </div>
            <span className="font-outfit font-black text-3xl tracking-tighter text-main">NextStep</span>
          </div>
          
          <div className="hidden lg:flex items-center gap-12">
            {['Features', 'How it Works', 'Success Stories', 'Pricing'].map(item => (
              <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} className="text-sm font-black uppercase tracking-widest text-muted hover:text-primary transition-all relative group">
                {item}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full" />
              </a>
            ))}
          </div>

          <div className="flex items-center gap-6">
            <Link to="/signin" className="hidden sm:block text-sm font-black uppercase tracking-widest text-muted hover:text-main transition-colors">Sign In</Link>
            <Link to="/signup" className="btn-primary h-14 px-10 text-sm shadow-2xl shadow-primary/20">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="relative z-10 pt-32 pb-48 px-8 overflow-hidden">
        <div className="max-w-6xl mx-auto text-center space-y-12 relative">
          <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full bg-primary/5 border-2 border-primary/20 text-primary text-[10px] font-black uppercase tracking-[0.3em] animate-in-fade shadow-xl shadow-primary/5">
            <Activity className="w-4 h-4 animate-pulse" />
            Live Market Updates Active
          </div>
          
          <div className="space-y-6">
            <h1 className="text-7xl md:text-9xl font-black font-outfit text-main leading-[0.9] animate-in-slide tracking-tighter">
              Build Your <br />
              <span className="gradient-text">Dream Career</span>
            </h1>
            <p className="text-2xl md:text-3xl text-muted max-w-4xl mx-auto leading-relaxed animate-in-slide font-medium" style={{ animationDelay: '100ms' }}>
              The smartest way to find your next job. <br className="hidden md:block" /> 
              We help you learn the right skills and get hired faster.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-8 pt-10 animate-in-slide" style={{ animationDelay: '200ms' }}>
            <Link to="/signup" className="btn-primary h-20 px-16 text-xl shadow-2xl shadow-primary/30 group">
              Start Free Today
              <ArrowUpRight className="w-6 h-6 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </Link>
            <Link to="/signin" className="btn-secondary h-20 px-16 text-xl">
              See How it Works
            </Link>
          </div>

          {/* Trust Indicators */}
          <div className="pt-24 flex flex-wrap justify-center items-center gap-16 opacity-40 grayscale hover:grayscale-0 transition-all duration-700">
             <div className="flex items-center gap-3 font-black text-2xl font-outfit uppercase tracking-tighter"><Cpu className="w-8 h-8" /> Tech Jobs</div>
             <div className="flex items-center gap-3 font-black text-2xl font-outfit uppercase tracking-tighter"><Globe className="w-8 h-8" /> Remote Work</div>
             <div className="flex items-center gap-3 font-black text-2xl font-outfit uppercase tracking-tighter"><Database className="w-8 h-8" /> Data Skills</div>
             <div className="flex items-center gap-3 font-black text-2xl font-outfit uppercase tracking-tighter"><Shield className="w-8 h-8" /> Career Growth</div>
          </div>
        </div>
      </header>

      {/* Main Features */}
      <section id="features" className="relative z-10 py-48 bg-subtle/40 border-y-2 border-base">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-12 mb-32">
            <div className="space-y-6 max-w-2xl">
               <div className="flex items-center gap-3 text-secondary font-black uppercase tracking-[0.3em] text-xs">
                  <Sparkles className="w-5 h-5" />
                  Your Career Assistant
               </div>
               <h2 className="text-5xl md:text-6xl font-black font-outfit text-main leading-tight tracking-tighter">Everything you need to grow</h2>
            </div>
            <p className="text-muted text-xl font-medium max-w-lg leading-relaxed">
               NextStep uses smart analysis to show you exactly what skills you need to learn to get the job you want.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="surface-card p-12 space-y-10 group hover:scale-[1.02] transition-all cursor-default">
              <div className="w-20 h-20 rounded-[2rem] bg-primary/10 border-2 border-primary/20 flex items-center justify-center text-primary group-hover:rotate-12 transition-all shadow-xl shadow-primary/5">
                <BarChart3 className="w-10 h-10" />
              </div>
              <div className="space-y-4">
                <h3 className="text-3xl font-black font-outfit text-main tracking-tight">Market Trends</h3>
                <p className="text-muted text-lg leading-relaxed font-medium">
                  We track thousands of jobs daily to show you which skills are in high demand right now.
                </p>
              </div>
            </div>

            <div className="surface-card p-12 space-y-10 group hover:scale-[1.02] transition-all cursor-default">
              <div className="w-20 h-20 rounded-[2rem] bg-secondary/10 border-2 border-secondary/20 flex items-center justify-center text-secondary group-hover:rotate-12 transition-all shadow-xl shadow-secondary/5">
                <Target className="w-10 h-10" />
              </div>
              <div className="space-y-4">
                <h3 className="text-3xl font-black font-outfit text-main tracking-tight">Personalized Goals</h3>
                <p className="text-muted text-lg leading-relaxed font-medium">
                  Tell us your dream job, and we'll find exactly what's missing in your current profile to get you there.
                </p>
              </div>
            </div>

            <div className="surface-card p-12 space-y-10 group hover:scale-[1.02] transition-all cursor-default">
              <div className="w-20 h-20 rounded-[2rem] bg-success/10 border-2 border-success/20 flex items-center justify-center text-success group-hover:rotate-12 transition-all shadow-xl shadow-success/5">
                <Zap className="w-10 h-10" />
              </div>
              <div className="space-y-4">
                <h3 className="text-3xl font-black font-outfit text-main tracking-tight">Quick Learning</h3>
                <p className="text-muted text-lg leading-relaxed font-medium">
                  Take quick quizzes to test your knowledge and get a personalized learning plan to fill your gaps.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-48 relative z-10">
        <div className="max-w-7xl mx-auto px-8 grid grid-cols-2 md:grid-cols-4 gap-20">
          <div className="space-y-3 group cursor-default">
            <p className="text-7xl font-black font-outfit text-main group-hover:text-primary transition-colors tracking-tighter">98<span className="text-primary">%</span></p>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-muted">Better Job Matches</p>
          </div>
          <div className="space-y-3 group cursor-default">
            <p className="text-7xl font-black font-outfit text-main group-hover:text-secondary transition-colors tracking-tighter">1.2<span className="text-secondary">M</span></p>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-muted">Jobs Analyzed Weekly</p>
          </div>
          <div className="space-y-3 group cursor-default">
            <p className="text-7xl font-black font-outfit text-main group-hover:text-success transition-colors tracking-tighter">24<span className="text-success">/</span>7</p>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-muted">Real-time Updates</p>
          </div>
          <div className="space-y-3 group cursor-default">
            <p className="text-7xl font-black font-outfit text-main group-hover:text-primary transition-colors tracking-tighter">5<span className="text-primary">.</span>0</p>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-muted">User Rating</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-48 relative z-10 px-8">
        <div className="max-w-6xl mx-auto surface-card bg-primary p-16 md:p-32 text-center space-y-12 rounded-[4rem] shadow-2xl shadow-primary/30 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-white/10 blur-[120px] -mr-64 -mt-64 rounded-full group-hover:scale-110 transition-transform duration-1000" />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-black/10 blur-[100px] -ml-48 -mb-48 rounded-full" />
          
          <div className="relative z-10 space-y-8">
            <h2 className="text-6xl md:text-8xl font-black font-outfit text-white leading-none tracking-tighter">
              Ready to <br /> Get Started?
            </h2>
            <p className="text-white/80 text-2xl max-w-2xl mx-auto font-medium leading-relaxed">
              Join thousands of professionals who are using NextStep to land their dream jobs.
            </p>
            <div className="pt-10 flex flex-col sm:flex-row items-center justify-center gap-8">
              <Link to="/signup" className="btn-secondary h-24 px-20 text-2xl shadow-2xl shadow-black/20 hover:scale-105 transition-all">
                Create Free Account
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t-2 border-base py-24 bg-subtle/60 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-8 flex flex-col md:flex-row items-center justify-between gap-16">
          <div className="flex items-center gap-4 group cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-white border-2 border-base flex items-center justify-center group-hover:border-primary transition-all overflow-hidden">
              <img src="/logo.png" alt="NextStep Logo" className="w-7 h-7 object-contain" />
            </div>
            <span className="font-outfit font-black text-2xl tracking-tighter">NextStep</span>
          </div>
          
          <div className="flex flex-col items-center md:items-end gap-6">
            <div className="flex gap-12">
               {['Help Center', 'Privacy', 'Terms', 'Status'].map(item => (
                 <a key={item} href="#" className="text-sm font-black uppercase tracking-widest text-muted hover:text-primary transition-colors">{item}</a>
               ))}
            </div>
            <p className="text-muted text-sm font-black uppercase tracking-[0.2em] opacity-40">
              &copy; {new Date().getFullYear()} NextStep. All Systems Operational.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

