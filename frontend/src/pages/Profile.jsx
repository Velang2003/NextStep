import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  User, Briefcase, MapPin, Zap, ChevronDown, 
  Search, CheckCircle2, Sparkles, Target, Loader2, Save, Globe,
  Activity, Info, AlertCircle, ArrowRight, Fingerprint, Award
} from 'lucide-react';

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const [saved, setSaved]     = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [skills, setSkills]   = useState(user?.profile?.skills || []);
  const [allRoles, setAllRoles] = useState([]);
  const [suggestedSkills, setSuggestedSkills] = useState([]);

  useEffect(() => {
    api.get('/taxonomy/roles').then(r => {
      setAllRoles(r.data || []);
    });
  }, []);

  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    defaultValues: {
      first_name:       user?.profile?.first_name || '',
      last_name:        user?.profile?.last_name  || '',
      target_role:      user?.profile?.target_role  || '',
      location:         user?.profile?.location || '',
      experience_years: user?.profile?.experience_years || 0,
    }
  });

  const targetRole = watch('target_role');

  useEffect(() => {
    setSuggestedSkills([]);
    if (targetRole && targetRole.length > 2) {
      const timer = setTimeout(() => {
        api.get(`/jobs/trends/role-skills?role=${encodeURIComponent(targetRole)}`)
          .then(res => setSuggestedSkills((res.data || []).slice(0, 12)))
          .catch(() => setSuggestedSkills([]));
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [targetRole]);

  const onSubmit = async (data) => {
    setLoading(true); setError(''); setSaved(false);
    try {
      await api.put('/profile/', { ...data });
      setSaved(true);
      await refreshUser();
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save profile changes.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto space-y-12 pb-20">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-10">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.3em]">
              <Fingerprint className="w-4 h-4" />
              Profile Setup
            </div>
            <h1 className="text-5xl font-black font-outfit text-main tracking-tight">Your Profile</h1>
            <p className="text-muted text-xl font-medium max-w-2xl">
              Update your details to get better job matches and a clearer career plan.
            </p>
          </div>
          
          {saved && (
            <div className="flex items-center gap-3 px-6 py-3 rounded-2xl bg-success/5 border-2 border-success/20 text-success animate-in-slide shadow-lg shadow-success/5">
              <CheckCircle2 className="w-5 h-5" />
              <span className="text-xs font-black uppercase tracking-widest">Profile Updated</span>
            </div>
          )}
        </header>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            {/* Personal Canvas */}
            <div className="lg:col-span-5 surface-card p-10 space-y-10 shadow-xl">
              <div className="flex items-center gap-4 border-b border-base pb-6">
                <div className="p-4 rounded-2xl bg-primary/10 border-2 border-primary/20 text-primary shadow-lg shadow-primary/5">
                  <User className="w-6 h-6" />
                </div>
                <div className="space-y-0.5">
                  <h2 className="text-2xl font-black font-outfit text-main leading-tight">Personal Details</h2>
                  <p className="text-[10px] font-black text-muted uppercase tracking-widest">Basic Information</p>
                </div>
              </div>
              
              <div className="space-y-8">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <label className="text-[10px] font-black text-muted uppercase tracking-[0.2em] ml-1">First Name</label>
                    <input 
                      id="profile-first-name" 
                      className="input-field py-4" 
                      placeholder="Alex"
                      {...register('first_name')} 
                    />
                  </div>
                  <div className="space-y-3">
                    <label className="text-[10px] font-black text-muted uppercase tracking-[0.2em] ml-1">Last Name</label>
                    <input 
                      id="profile-last-name" 
                      className="input-field py-4" 
                      placeholder="Chen"
                      {...register('last_name')} 
                    />
                  </div>
                </div>
                
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-muted uppercase tracking-[0.2em] ml-1">Geographic Location</label>
                  <div className="relative group">
                    <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted group-focus-within:text-primary transition-colors" />
                    <input 
                      id="profile-location" 
                      className="input-field pl-12 py-4" 
                      placeholder="e.g. London, UK"
                      {...register('location')} 
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Professional Context Canvas */}
            <div className="lg:col-span-7 surface-card p-10 space-y-10 shadow-xl">
              <div className="flex items-center gap-4 border-b border-base pb-6">
                <div className="p-4 rounded-2xl bg-secondary/10 border-2 border-secondary/20 text-secondary shadow-lg shadow-secondary/5">
                  <Briefcase className="w-6 h-6" />
                </div>
                <div className="space-y-0.5">
                  <h2 className="text-2xl font-black font-outfit text-main leading-tight">Job Details</h2>
                  <p className="text-[10px] font-black text-muted uppercase tracking-widest">Job Goals</p>
                </div>
              </div>
              
              <div className="space-y-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-muted uppercase tracking-[0.2em] ml-1">Job You Want</label>
                  <div className="relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted group-focus-within:text-primary transition-colors" />
                    <input 
                      id="profile-target-role" 
                      list="roles-list" 
                      className={`input-field pl-12 py-4 ${errors.target_role ? 'border-error' : ''}`}
                      placeholder="Search and select jobs..."
                      {...register('target_role', { required: 'Please enter a target job.' })} 
                      autoComplete="off" 
                    />
                    <datalist id="roles-list">
                      {allRoles.map(r => <option key={r.id} value={r.title} />)}
                    </datalist>
                  </div>
                  {errors.target_role && (
                    <p className="text-[10px] font-black text-error uppercase tracking-widest ml-1 animate-in-fade flex items-center gap-2">
                      <AlertCircle className="w-3.5 h-3.5" />
                      {errors.target_role.message}
                    </p>
                  )}
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-black text-muted uppercase tracking-[0.2em] ml-1">Years of Experience</label>
                  <div className="relative group">
                    <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted group-focus-within:text-primary transition-colors" />
                    <select 
                      id="profile-experience" 
                      className="input-field pl-12 py-4 appearance-none cursor-pointer pr-12"
                      {...register('experience_years')}
                    >
                      {[0,1,2,3,4,5,6,7,8,9,10].map(y => (
                        <option key={y} value={y}>
                          {y === 0 ? 'Less than 1 Year' : `${y}+ Years`}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted pointer-events-none group-hover:translate-y-0.5 transition-transform" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Strategic Skill Roadmap */}
          {targetRole && suggestedSkills.length > 0 && (
            <div className="surface-card p-12 lg:p-16 space-y-12 animate-in-slide shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 blur-[100px] -mr-48 -mt-48 rounded-full" />
              
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-10 relative z-10 border-b border-base pb-8">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-primary font-black uppercase tracking-[0.3em] text-xs">
                    <Sparkles className="w-5 h-5" />
                    Recommended Skills
                  </div>
                  <h2 className="text-4xl font-black font-outfit text-main tracking-tight leading-tight">
                    Skills for Your New Role
                  </h2>
                  <p className="text-muted text-lg font-medium">These skills are most in demand for <span className="text-primary font-bold">{targetRole}</span> roles.</p>
                </div>
                <div className="flex items-center gap-4 bg-primary/10 border-2 border-primary/20 px-6 py-3 rounded-2xl shadow-xl shadow-primary/5">
                  <Zap className="w-5 h-5 text-primary fill-current" />
                  <span className="text-xs font-black text-primary uppercase tracking-widest">Recommended for You</span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative z-10">
                {suggestedSkills.map((skill, idx) => {
                  const isLearned = skills.includes(skill);
                  return (
                    <div 
                      key={skill} 
                      className={`p-8 rounded-[2.5rem] border-2 transition-all duration-500 flex flex-col gap-6 group relative overflow-hidden
                        ${isLearned 
                          ? 'bg-success/5 border-success/20 shadow-xl shadow-success/5' 
                          : 'bg-surface border-base hover:border-primary/40 hover:shadow-2xl hover:scale-[1.02]'}`}
                    >
                      {isLearned && (
                        <div className="absolute top-4 right-4 text-success/40">
                           <Award className="w-8 h-8 rotate-12" />
                        </div>
                      )}
                      
                      <div className="flex items-center gap-5">
                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-sm font-black shadow-lg transition-transform group-hover:rotate-12
                          ${isLearned ? 'bg-success text-white' : 'bg-subtle text-muted border-2 border-base'}`}>
                          {isLearned ? <CheckCircle2 className="w-6 h-6" /> : (idx + 1).toString().padStart(2, '0')}
                        </div>
                        <div className="space-y-1 min-w-0">
                           <span className={`text-xl font-black font-outfit truncate block ${isLearned ? 'text-success' : 'text-main'}`}>{skill}</span>
                           <span className="text-[10px] font-black uppercase tracking-widest text-muted opacity-60">
                             {isLearned ? 'Learned' : 'Need to Learn'}
                           </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between pt-4 border-t border-base/40">
                        <div className="flex gap-1">
                           {[1,2,3].map(i => (
                             <div key={i} className={`w-4 h-1.5 rounded-full ${isLearned ? 'bg-success/40' : i <= (3 - idx % 3) ? 'bg-primary/40' : 'bg-base'}`} />
                           ))}
                        </div>
                        {!isLearned && (
                           <div className="text-[10px] font-black text-primary uppercase tracking-widest flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                             Add Skill
                             <ArrowRight className="w-3.5 h-3.5" />
                           </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {error && (
            <div className="p-6 rounded-[2rem] bg-error/5 border-2 border-error/20 text-error flex items-center gap-4 animate-in-fade shadow-xl shadow-error/5">
              <div className="p-3 rounded-2xl bg-error/10">
                 <AlertCircle className="w-6 h-6" />
              </div>
              <p className="text-sm font-black uppercase tracking-widest leading-relaxed">{error}</p>
            </div>
          )}

          <div className="flex justify-end pt-6">
            <button 
              id="profile-save" 
              type="submit" 
              disabled={loading} 
              className="btn-primary h-20 px-16 text-xl shadow-2xl shadow-primary/30 group relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
              <div className="relative z-10 flex items-center gap-4">
                {loading ? (
                  <Loader2 className="w-7 h-7 animate-spin" />
                ) : saved ? (
                  <CheckCircle2 className="w-7 h-7" />
                ) : (
                  <Save className="w-7 h-7 group-hover:scale-110 transition-transform" />
                )}
                <span className="font-black font-outfit tracking-tight">
                  {loading ? 'Saving...' : saved ? 'Profile Saved' : 'Save Profile'}
                </span>
              </div>
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}

