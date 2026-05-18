import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  LayoutDashboard, TrendingUp, Target, Map, User, LogOut, ChevronRight,
  Briefcase, ClipboardList, Globe, Award, Menu, X, Sun, Moon, BarChart2, Search, ShieldCheck,
  Settings
} from 'lucide-react';
import { useState, useEffect } from 'react';

const NAV = [
  { to: '/dashboard',    icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/market',       icon: TrendingUp,      label: 'Market Trends' },
  { to: '/role-trends',  icon: BarChart2,       label: 'Role Trends' },
  { to: '/jobs',         icon: Search,          label: 'Job Browser' },
  { to: '/geo-map',      icon: Globe,           label: 'Geo Analysis' },
  { to: '/skill-gap',    icon: Target,          label: 'Skill Gap' },
  { to: '/assessment',   icon: Award,           label: 'Assessment' },
  { to: '/career-path',  icon: Map,             label: 'Career Path' },
  { to: '/applications', icon: ClipboardList,   label: 'Applications' },
];

const ADMIN_NAV = { to: '/admin', icon: ShieldCheck, label: 'Admin Panel' };

export default function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = () => { logout(); navigate('/signin'); };

  return (
    <div className="flex min-h-screen bg-main transition-colors duration-300">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden animate-in-fade" 
          onClick={() => setSidebarOpen(false)} 
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:sticky top-0 left-0 h-screen z-50
        w-72 shrink-0 flex flex-col bg-surface border-r border-base
        transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Sidebar Header */}
        <div className="p-6 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl overflow-hidden flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform bg-white">
              <img src="/logo.png" alt="NextStep Logo" className="w-8 h-8 object-contain" />
            </div>
            <span className="text-xl font-bold font-outfit tracking-tight text-main">NextStep</span>
          </NavLink>
          <button 
            onClick={() => setSidebarOpen(false)} 
            className="lg:hidden p-2 text-muted hover:text-main hover:bg-subtle rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto custom-scrollbar">
          <p className="px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-muted/60">Main Menu</p>
          {[...NAV, ...(user?.is_admin ? [ADMIN_NAV] : [])].map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group
                ${isActive 
                  ? 'bg-primary text-white shadow-md shadow-primary/20' 
                  : 'text-muted hover:text-main hover:bg-subtle'}
              `}
            >
              <Icon className={`w-5 h-5 shrink-0 ${location.pathname === to ? 'text-white' : 'group-hover:text-primary transition-colors'}`} />
              {label}
              <ChevronRight className={`w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-all ${location.pathname === to ? 'hidden' : 'translate-x-[-4px] group-hover:translate-x-0'}`} />
            </NavLink>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 mt-auto border-t border-base bg-subtle/30">
          <div className="flex items-center gap-3 p-3 rounded-2xl bg-surface border border-base mb-4 shadow-sm">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-sm font-bold text-white shadow-inner">
              {(user?.email?.[0] || 'U').toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-main truncate leading-tight">{user?.profile?.first_name || 'User'}</p>
              <p className="text-xs text-muted truncate">{user?.email}</p>
            </div>
            <NavLink to="/profile" className="p-2 text-muted hover:text-primary transition-colors" title="Settings">
              <Settings className="w-4 h-4" />
            </NavLink>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={toggleTheme}
              className="flex items-center justify-center gap-2 p-2.5 rounded-xl border border-base bg-surface text-muted hover:text-main hover:bg-subtle transition-all"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-warning" /> : <Moon className="w-4 h-4 text-indigo-500" />}
              <span className="text-xs font-semibold">{isDark ? 'Light' : 'Dark'}</span>
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center justify-center gap-2 p-2.5 rounded-xl border border-base bg-surface text-muted hover:text-error hover:bg-error/5 transition-all"
            >
              <LogOut className="w-4 h-4" />
              <span className="text-xs font-semibold">Exit</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className={`
          sticky top-0 z-30 px-4 sm:px-8 py-4 flex items-center justify-between
          transition-all duration-200 bg-main/80 backdrop-blur-md
          ${scrolled ? 'border-b border-base py-3' : 'py-5'}
        `}>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(true)} 
              className="lg:hidden p-2 text-muted hover:text-main hover:bg-surface border border-base rounded-xl transition-all shadow-sm"
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:block">
              <h2 className="text-lg font-bold text-main">
                {NAV.find(n => n.to === location.pathname)?.label || 'Overview'}
              </h2>
              <div className="flex items-center gap-2 text-xs text-muted font-medium">
                <span>NextStep</span>
                <ChevronRight className="w-3 h-3 opacity-30" />
                <span className="text-primary capitalize">{location.pathname.replace('/', '') || 'Dashboard'}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <NavLink to="/profile" className="flex items-center gap-3 p-1 pl-3 rounded-xl border border-base bg-surface hover:border-primary/50 transition-all shadow-sm group">
              <span className="text-sm font-bold text-main group-hover:text-primary transition-colors">Profile</span>
              <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center overflow-hidden border border-primary/20">
                <User className="w-5 h-5" />
              </div>
            </NavLink>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-4 sm:p-8 max-w-screen-2xl mx-auto w-full animate-in-slide">
          {children}
        </div>

        {/* Mobile Bottom Navigation (optional, kept if user likes it, but cleaned up) */}
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface/90 backdrop-blur-lg border-t border-base
                        flex items-center justify-around py-3 px-2 shadow-lg">
          {[
            { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
            { to: '/jobs',      icon: Briefcase,       label: 'Jobs' },
            { to: '/assessment', icon: Award,           label: 'Assess' },
            { to: '/profile',   icon: User,            label: 'User' }
          ].map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `
              flex flex-col items-center gap-1 px-4 py-1 rounded-xl transition-all
              ${isActive ? 'text-primary bg-primary/5 scale-110' : 'text-muted hover:text-main'}
            `}>
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-bold uppercase tracking-tighter">{label}</span>
            </NavLink>
          ))}
        </nav>
      </main>
    </div>
  );
}

