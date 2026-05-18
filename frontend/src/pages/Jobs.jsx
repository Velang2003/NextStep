import { useState, useEffect, useCallback } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { Search, Globe, Briefcase, ExternalLink, Bookmark, BookmarkCheck, Filter, MapPin, Building2, Calendar, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [inputSearch, setInputSearch] = useState('');
  const [country, setCountry] = useState('');
  const [remote, setRemote] = useState('');
  const [sector, setSector] = useState('');
  const [sectors, setSectors] = useState([]);
  const [savedJobs, setSavedJobs] = useState(new Set());

  useEffect(() => {
    api.get('/taxonomy/sectors').then(r => {
      setSectors((r.data || []).filter(s => s.name !== 'Other'));
    });
    api.get('/applications/').then(r => {
      const ids = new Set((r.data || []).map(a => a.job_id));
      setSavedJobs(ids);
    }).catch(() => {});
  }, []);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: 15 });
      if (searchText) params.append('search', searchText);
      if (country) params.append('country', country);
      if (remote) params.append('remote', remote);
      if (sector) params.append('sector', sector);
      const res = await api.get(`/jobs/?${params}`);
      setJobs(res.data.jobs);
      setTotal(res.data.total);
      setPages(res.data.pages);
    } catch { /* no-op */ }
    finally { setLoading(false); }
  }, [page, searchText, country, remote, sector]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchText(inputSearch.trim());
    setPage(1);
  };

  const handleSave = async (jobId) => {
    try {
      await api.post('/applications/save', { job_id: jobId });
      setSavedJobs(prev => new Set([...prev, jobId]));
    } catch {}
  };

  const handleApply = async (job) => {
    try {
      await api.post('/applications/apply', { job_id: job.id });
      setSavedJobs(prev => new Set([...prev, job.id]));
      if (job.url) window.open(job.url, '_blank');
    } catch {}
  };

  const SOURCE_BADGE = {
    greenhouse: 'bg-green-500/10 text-green-600 border-green-500/20',
    lever:      'bg-blue-500/10  text-blue-600  border-blue-500/20',
    ashby:      'bg-purple-500/10 text-purple-600 border-purple-500/20',
  };

  return (
    <AppLayout>
      <div className="space-y-8 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-black font-outfit text-main">Job Browser</h1>
            <p className="text-muted text-lg font-medium">
              {total > 0 ? (
                <>Found <span className="text-primary font-bold">{total.toLocaleString()}</span> jobs that match your goals.</>
              ) : (
                'Search for jobs from top tech companies.'
              )}
            </p>
          </div>
        </header>

        {/* Search & Filters */}
        <div className="surface-card p-6 space-y-6 shadow-md">
          <form onSubmit={handleSearch} className="flex flex-col lg:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
              <input 
                id="job-search" 
                type="text" 
                placeholder="Search by title, company, or tech stack..."
                value={inputSearch}
                onChange={e => setInputSearch(e.target.value)}
                className="input-field pl-11 h-12" 
              />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <select 
                id="filter-sector" 
                value={sector} 
                onChange={e => { setSector(e.target.value); setPage(1); }}
                className="input-field h-12 text-xs font-bold"
              >
                <option value="">All Sectors</option>
                {sectors.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
              </select>

              <select 
                id="filter-country" 
                value={country} 
                onChange={e => { setCountry(e.target.value); setPage(1); }}
                className="input-field h-12 text-xs font-bold"
              >
                <option value="">All Regions</option>
                {['United States','United Kingdom','Canada','India','Germany','Australia','France','Netherlands','Singapore'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select 
                id="filter-remote" 
                value={remote} 
                onChange={e => { setRemote(e.target.value); setPage(1); }}
                className="input-field h-12 text-xs font-bold"
              >
                <option value="">Work Type</option>
                <option value="true">Remote</option>
                <option value="false">On-site</option>
              </select>

              <button type="submit" className="btn-primary h-12 shadow-lg shadow-primary/20">
                Filter Results
              </button>
            </div>
          </form>

          {(searchText || country || remote || sector) && (
            <div className="flex items-center gap-3 pt-4 border-t border-base">
              <span className="text-xs font-bold uppercase tracking-widest text-muted">Active Filters:</span>
              <div className="flex flex-wrap gap-2">
                {searchText && <span className="badge bg-primary/10 text-primary">{searchText}</span>}
                {sector && <span className="badge bg-secondary/10 text-secondary">{sector}</span>}
                {country && <span className="badge bg-indigo-500/10 text-indigo-500">{country}</span>}
                {remote && <span className="badge bg-success/10 text-success">{remote === 'true' ? 'Remote' : 'On-site'}</span>}
                <button 
                  onClick={() => { setSearchText(''); setInputSearch(''); setCountry(''); setRemote(''); setSector(''); setPage(1); }}
                  className="text-xs font-bold text-error hover:underline ml-2"
                >
                  Clear All
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Job Listings */}
        <div className="space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 space-y-4 surface-card">
              <Loader2 className="w-10 h-10 text-primary animate-spin" />
              <p className="text-muted font-bold uppercase tracking-widest text-xs">Loading jobs...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="surface-card p-20 text-center space-y-4">
              <div className="w-20 h-20 bg-subtle rounded-3xl flex items-center justify-center mx-auto">
                <Briefcase className="w-10 h-10 text-muted" />
              </div>
              <h3 className="text-2xl font-bold text-main">No jobs found</h3>
              <p className="text-muted max-w-md mx-auto">Adjust your filters or try a different search term to find what you're looking for.</p>
              <button 
                onClick={() => { setSearchText(''); setInputSearch(''); setCountry(''); setRemote(''); setSector(''); setPage(1); }}
                className="btn-secondary"
              >
                Reset Search
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4">
                {jobs.map(job => (
                  <div key={job.id} className="surface-card p-6 flex flex-col md:flex-row items-start md:items-center gap-6 group hover:border-primary/40 transition-all shadow-sm">
                    <div className="flex-1 space-y-4">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-xl font-bold text-main group-hover:text-primary transition-colors">{job.title}</h3>
                        <div className="flex gap-2">
                          {job.remote && <span className="badge bg-success/10 text-success">Remote</span>}
                          <span className={`badge ${SOURCE_BADGE[job.source] || 'bg-subtle text-muted'}`}>{job.source}</span>
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm font-medium text-muted">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4" />
                          {job.company}
                        </div>
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4" />
                          {job.location || 'Distributed'}
                        </div>
                        {job.employment_type && (
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4" />
                            {job.employment_type}
                          </div>
                        )}
                      </div>

                      {job.skills?.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {job.skills.slice(0, 5).map(s => (
                            <span key={s} className="px-2.5 py-1 rounded-lg bg-subtle border border-base text-[10px] font-bold text-muted uppercase tracking-wider">{s}</span>
                          ))}
                          {job.skills.length > 5 && (
                            <span className="text-[10px] font-bold text-muted/50 self-center">+{job.skills.length - 5} more</span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto shrink-0 pt-4 md:pt-0 border-t md:border-t-0 border-base">
                      <button 
                        onClick={() => handleSave(job.id)}
                        className={`p-3 rounded-xl border transition-all ${savedJobs.has(job.id)
                          ? 'border-warning/30 bg-warning/10 text-warning shadow-md shadow-warning/10'
                          : 'border-base bg-surface text-muted hover:text-main hover:border-primary/30'}`}
                        aria-label="Save job"
                      >
                        {savedJobs.has(job.id) ? <BookmarkCheck className="w-5 h-5" /> : <Bookmark className="w-5 h-5" />}
                      </button>
                      <button 
                        onClick={() => handleApply(job)}
                        className="btn-primary flex-1 md:flex-none h-12 px-6 shadow-md shadow-primary/20"
                      >
                        <ExternalLink className="w-4 h-4" /> 
                        Quick Apply
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {pages > 1 && (
                <div className="flex items-center justify-between pt-8 border-t border-base">
                  <p className="text-sm font-bold text-muted">
                    Showing Page <span className="text-main">{page}</span> of <span className="text-main">{pages}</span>
                  </p>
                  <div className="flex items-center gap-2">
                    <button 
                      disabled={page === 1} 
                      onClick={() => setPage(p => p - 1)}
                      className="btn-secondary h-10 w-10 p-0"
                      aria-label="Previous page"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <button 
                      disabled={page === pages} 
                      onClick={() => setPage(p => p + 1)}
                      className="btn-secondary h-10 w-10 p-0"
                      aria-label="Next page"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

