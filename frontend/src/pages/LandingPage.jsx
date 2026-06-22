import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Brain, Target, Compass, Briefcase, ChevronRight, BarChart3, 
  Database, Code2, Rocket, Shield, Zap, Globe, Sparkles,
  Activity, ArrowUpRight, CheckCircle2, Star, Cpu, Fingerprint, HelpCircle
} from 'lucide-react';

export default function LandingPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [faqOpen, setFaqOpen] = useState(null);
  const [statusToast, setStatusToast] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard');
    }
  }, [user, loading, navigate]);

  const triggerStatus = (e) => {
    e.preventDefault();
    setStatusToast(true);
    setTimeout(() => {
      setStatusToast(false);
    }, 6000);
  };

  if (loading) return null;

  const faqs = [
    {
      q: "How is the job market trend data updated?",
      a: "Our background ingestion pipeline sweeps and indexes open positions daily at 2:00 AM IST across 9 major platforms (including Greenhouse, Lever, Jooble, and Adzuna), ensuring real-time relevance."
    },
    {
      q: "What language models power the skill assessments?",
      a: "Quizzes are generated dynamically in less than a second using Llama 3 8B models hosted via high-throughput Nvidia NIM and Groq API endpoints."
    },
    {
      q: "How does the skill verification system work?",
      a: "Select any skill on your dashboard to start a 10-question conceptual or code-debugging quiz. Scoring 70% or above marks the skill as 'Verified' on your profile, highlighting your mastery to potential employers."
    },
    {
      q: "Is NextStep completely free to use?",
      a: "Yes! Our Basic plan is free forever and includes full job searching, trend tracking, and 3 assessments/month. Upgrade to Pro for unlimited AI evaluations and premium geospatial analytics."
    }
  ];

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
          <div className="flex items-center gap-4 group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
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
            <a href="#how-it-works" className="btn-secondary h-20 px-16 text-xl flex items-center justify-center">
              See How it Works
            </a>
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

      {/* How It Works */}
      <section id="how-it-works" className="relative z-10 py-48">
        <div className="max-w-7xl mx-auto px-8">
          <div className="text-center space-y-6 mb-32">
            <div className="inline-flex items-center gap-3 px-6 py-2 rounded-full bg-secondary/5 border border-secondary/20 text-secondary text-[10px] font-black uppercase tracking-[0.3em]">
              <Compass className="w-4 h-4" />
              3 Simple Steps
            </div>
            <h2 className="text-5xl md:text-6xl font-black font-outfit text-main tracking-tighter">How NextStep Works</h2>
            <p className="text-muted text-xl font-medium max-w-xl mx-auto">
              Your structural path to career enhancement, engineered for clarity and speed.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-16 relative">
            {/* Connection line for desktop */}
            <div className="hidden lg:block absolute top-1/2 left-20 right-20 h-0.5 bg-gradient-to-r from-primary/10 via-secondary/10 to-success/10 -translate-y-20 z-0" />

            {[
              {
                step: '01',
                title: 'Sync Your Profile',
                desc: 'Input your core technology competencies and select your target industry career path.',
                icon: Fingerprint,
                color: 'text-primary bg-primary/5 border-primary/20'
              },
              {
                step: '02',
                title: 'Identify Gaps',
                desc: 'Our engine contrasts your verified profile against thousands of scraped job metrics to output skill-gaps.',
                icon: Target,
                color: 'text-secondary bg-secondary/5 border-secondary/20'
              },
              {
                step: '03',
                title: 'Verify & Up-level',
                desc: 'Complete adaptive, AI-generated multiple choice questions to confirm masteries and apply immediately.',
                icon: Brain,
                color: 'text-success bg-success/5 border-success/20'
              }
            ].map(({ step, title, desc, icon: Icon, color }) => (
              <div key={step} className="surface-card p-12 space-y-8 relative z-10 hover:border-primary/20 group">
                <div className="flex justify-between items-center">
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center border-2 ${color} group-hover:rotate-12 transition-transform`}>
                    <Icon className="w-8 h-8" />
                  </div>
                  <span className="text-6xl font-black font-outfit opacity-10 group-hover:opacity-30 transition-opacity tracking-tight">{step}</span>
                </div>
                <div className="space-y-4">
                  <h3 className="text-2xl font-black font-outfit text-main">{title}</h3>
                  <p className="text-muted text-base leading-relaxed font-medium">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Success Stories */}
      <section id="success-stories" className="relative z-10 py-48 bg-subtle/30 border-y-2 border-base">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-12 mb-32">
            <div className="space-y-6">
              <div className="flex items-center gap-3 text-success font-black uppercase tracking-[0.3em] text-xs">
                <Star className="w-5 h-5 fill-success" />
                Community Stories
              </div>
              <h2 className="text-5xl md:text-6xl font-black font-outfit text-main tracking-tighter">Approved by Developers</h2>
            </div>
            <p className="text-muted text-xl font-medium max-w-md leading-relaxed">
              Read how developers in the community leverage NextStep analytics to fast-track their hiring loops.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {[
              {
                name: 'Velan',
                role: 'Frontend Developer & Tester',
                avatar: 'V',
                text: "Implementing and testing the React UI has been a fantastic experience. NextStep's real-time skill-gap recommendations made expanding my portfolio incredibly easy."
              },
              {
                name: 'Chethankumar',
                role: 'Backend & Ingestion Engineer',
                avatar: 'C',
                text: "Building the concurrent pipeline and resetting sequence alignment was complex, but NextStep's analytics make it all worth it. The data distribution mapping works perfectly."
              },
              {
                name: 'Arjun Mehta',
                role: 'DevOps Specialist at CloudCorp',
                avatar: 'A',
                text: "The Docker configurations and AI validation tests run cleanly. NextStep helps us find qualified candidates with verified skills, reducing hiring time by 40%."
              }
            ].map(({ name, role, avatar, text }) => (
              <div key={name} className="surface-card p-12 space-y-8 flex flex-col justify-between hover:scale-[1.01] transition-transform">
                <div className="space-y-6">
                  <div className="flex gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 text-success fill-success" />
                    ))}
                  </div>
                  <p className="text-muted text-base leading-relaxed italic font-medium">"{text}"</p>
                </div>
                <div className="flex items-center gap-4 pt-6 border-t border-base">
                  <div className="w-12 h-12 rounded-xl bg-primary text-white flex items-center justify-center font-black font-outfit text-lg">
                    {avatar}
                  </div>
                  <div className="flex flex-col">
                    <span className="font-bold text-main text-sm">{name}</span>
                    <span className="text-[10px] text-muted font-black uppercase tracking-widest">{role}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="relative z-10 py-48">
        <div className="max-w-7xl mx-auto px-8">
          <div className="text-center space-y-6 mb-32">
            <div className="inline-flex items-center gap-3 px-6 py-2 rounded-full bg-primary/5 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-[0.3em]">
              <Zap className="w-4 h-4" />
              SaaS Subscriptions
            </div>
            <h2 className="text-5xl md:text-6xl font-black font-outfit text-main tracking-tighter">Simple, Transparent Pricing</h2>
            <p className="text-muted text-xl font-medium max-w-xl mx-auto">
              Choose the roadmap that matches your career pace. No hidden hooks.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-5xl mx-auto">
            {/* Free Plan */}
            <div className="surface-card p-16 space-y-12 relative overflow-hidden group hover:border-base/80">
              <div className="space-y-4">
                <h3 className="text-3xl font-black font-outfit text-main">Basic Tracker</h3>
                <p className="text-muted text-sm font-medium">Essential analytics to catalog your career trajectory.</p>
                <div className="pt-6">
                  <span className="text-6xl font-black font-outfit text-main">$0</span>
                  <span className="text-muted font-bold text-sm ml-2">/ Free Forever</span>
                </div>
              </div>
              
              <ul className="space-y-5 border-y border-base py-8">
                {[
                  'Real-time job listings feed',
                  'Standard skill-gap analyzer dashboard',
                  '3 Llama 3 AI assessments per month',
                  'Lightweight dark/light mode UI context'
                ].map(feat => (
                  <li key={feat} className="flex items-center gap-3 text-muted text-sm font-medium">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    {feat}
                  </li>
                ))}
              </ul>

              <Link to="/signup" className="btn-secondary w-full h-16 text-base font-bold shadow-lg shadow-base/10">
                Start Free
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="surface-card p-16 space-y-12 relative overflow-hidden border-primary/30 shadow-xl shadow-primary/5 group">
              <div className="absolute top-0 right-0 bg-primary text-white text-[9px] font-black uppercase tracking-widest px-6 py-2 rounded-bl-2xl">
                Best Choice
              </div>
              
              <div className="space-y-4">
                <h3 className="text-3xl font-black font-outfit text-main">Dream Pathfinder</h3>
                <p className="text-muted text-sm font-medium">Deep intelligence suite for aggressive career upskilling.</p>
                <div className="pt-6">
                  <span className="text-6xl font-black font-outfit text-main">$15</span>
                  <span className="text-muted font-bold text-sm ml-2">/ month</span>
                </div>
              </div>
              
              <ul className="space-y-5 border-y border-base py-8">
                {[
                  'Everything in Basic Tracker',
                  'Unlimited Llama 3 AI Assessments',
                  'Global geographic distribution analytics',
                  'Automatic DB sequence syncer access',
                  'Priority administrative support channels'
                ].map(feat => (
                  <li key={feat} className="flex items-center gap-3 text-main text-sm font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-primary fill-primary/10" />
                    {feat}
                  </li>
                ))}
              </ul>

              <Link to="/signup" className="btn-primary w-full h-16 text-base font-bold shadow-2xl shadow-primary/20 hover:scale-[1.01]">
                Get Pro Access
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-48 relative z-10 bg-subtle/20 border-y-2 border-base">
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

      {/* FAQ & Help Center */}
      <section id="help-center" className="relative z-10 py-48">
        <div className="max-w-4xl mx-auto px-8">
          <div className="text-center space-y-6 mb-24">
            <div className="inline-flex items-center gap-3 px-6 py-2 rounded-full bg-success/5 border border-success/20 text-success text-[10px] font-black uppercase tracking-[0.3em]">
              <HelpCircle className="w-4 h-4" />
              FAQ Database
            </div>
            <h2 className="text-5xl md:text-6xl font-black font-outfit text-main tracking-tighter">Help Center</h2>
            <p className="text-muted text-xl font-medium max-w-xl mx-auto">
              Find answers to core operational and product questions.
            </p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, idx) => {
              const isOpen = faqOpen === idx;
              return (
                <div key={idx} className="surface-card overflow-hidden">
                  <button 
                    onClick={() => setFaqOpen(isOpen ? null : idx)}
                    className="w-full p-8 flex items-center justify-between text-left hover:bg-subtle/30 transition-colors"
                  >
                    <span className="font-outfit font-black text-lg md:text-xl text-main pr-8">{faq.q}</span>
                    <span className={`text-2xl font-black font-outfit text-muted transition-transform duration-200 ${isOpen ? 'rotate-45 text-primary' : ''}`}>+</span>
                  </button>
                  {isOpen && (
                    <div className="p-8 pt-2 border-t border-base bg-subtle/10 animate-in-fade">
                      <p className="text-muted text-base leading-relaxed font-medium">{faq.a}</p>
                    </div>
                  )}
                </div>
              );
            })}
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
          <div className="flex items-center gap-4 group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-10 h-10 rounded-xl bg-white border-2 border-base flex items-center justify-center group-hover:border-primary transition-all overflow-hidden">
              <img src="/logo.png" alt="NextStep Logo" className="w-7 h-7 object-contain" />
            </div>
            <span className="font-outfit font-black text-2xl tracking-tighter">NextStep</span>
          </div>
          
          <div className="flex flex-col items-center md:items-end gap-6">
            <div className="flex gap-12 items-center flex-wrap justify-center">
              <a href="#help-center" className="text-sm font-black uppercase tracking-widest text-muted hover:text-primary transition-colors">Help Center</a>
              <Link to="/privacy" className="text-sm font-black uppercase tracking-widest text-muted hover:text-primary transition-colors">Privacy</Link>
              <Link to="/terms" className="text-sm font-black uppercase tracking-widest text-muted hover:text-primary transition-colors">Terms</Link>
              <a href="#status" onClick={triggerStatus} className="text-sm font-black uppercase tracking-widest text-muted hover:text-primary transition-colors">Status</a>
            </div>
            <p className="text-muted text-sm font-black uppercase tracking-[0.2em] opacity-40">
              &copy; {new Date().getFullYear()} NextStep. All Systems Operational.
            </p>
          </div>
        </div>
      </footer>

      {/* Glassmorphic Systems Status Toast */}
      {statusToast && (
        <div className="fixed bottom-8 right-8 z-[1000] surface-card p-6 border-success/30 shadow-2xl bg-surface/90 backdrop-blur-xl rounded-2xl w-[320px] animate-in-slide space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-success animate-ping" />
            <div className="w-3 h-3 rounded-full bg-success absolute" />
            <span className="font-outfit font-black text-main text-base uppercase tracking-wider ml-1">Systems Status</span>
          </div>
          <div className="space-y-2 text-xs text-muted font-bold">
            <div className="flex justify-between">
              <span>Ingestion Pipeline:</span>
              <span className="text-success">100% ONLINE</span>
            </div>
            <div className="flex justify-between">
              <span>Groq/Nvidia AI Endpoints:</span>
              <span className="text-success">100% ONLINE</span>
            </div>
            <div className="flex justify-between">
              <span>PostgreSQL Database:</span>
              <span className="text-success">100% ONLINE</span>
            </div>
            <div className="flex justify-between">
              <span>Authentication Services:</span>
              <span className="text-success">100% ONLINE</span>
            </div>
          </div>
          <button onClick={() => setStatusToast(false)} className="text-[10px] font-black uppercase text-muted hover:text-main w-full text-center pt-2 border-t border-base">
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
