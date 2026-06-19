import { useState, useEffect, useRef } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { 
  Target, Play, CheckCircle, XCircle, Clock, 
  ArrowRight, Trophy, RotateCcw, Search, Filter, 
  Loader2, Award, Sparkles, BookOpen, ChevronLeft, 
  Code, Info, ChevronRight, BarChart
} from 'lucide-react';

const DIFFICULTIES = [
  { key: 'easy', label: 'Beginner', color: 'text-success', border: 'border-success/20', bg: 'bg-success/5' },
  { key: 'medium', label: 'Intermediate', color: 'text-warning', border: 'border-warning/20', bg: 'bg-warning/5' },
  { key: 'hard', label: 'Advanced', color: 'text-error', border: 'border-error/20', bg: 'bg-error/5' },
];

export default function SkillAssessment() {
  const [skills, setSkills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [difficulty, setDifficulty] = useState('medium');
  const [phase, setPhase] = useState('select'); // select | quiz | results
  const [assessment, setAssessment] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [profileSkills, setProfileSkills] = useState([]);
  const [targetRole, setTargetRole] = useState(null);
  const [roleSkills, setRoleSkills] = useState([]);
  const [timer, setTimer] = useState(0);
  const [totalExpected, setTotalExpected] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    api.get('/taxonomy/skills/categories').then(r => {
      setCategories(r.data || []);
    });
    api.get('/assessment/history').then(r => {
      setHistory(r.data || []);
    });
    api.get('/auth/me').then(r => {
      const profile = r.data?.user?.profile;
      if (profile?.skills) {
        const pSkills = typeof profile.skills === 'string'
          ? profile.skills.split(',').map(s => s.trim()).filter(Boolean)
          : Array.isArray(profile.skills) ? profile.skills : [];
        setProfileSkills(pSkills);
      }
      if (profile?.target_role) {
        const tr = profile.target_role;
        setTargetRole(tr);
        api.get(`/jobs/trends/role-skills?role=${encodeURIComponent(tr)}`).then(res => {
          const fetchedRoleSkills = res.data || [];
          setRoleSkills(fetchedRoleSkills);
          if (fetchedRoleSkills.length > 0) {
            setSkills(fetchedRoleSkills.map(s => ({ name: s })));
          } else {
            api.get('/taxonomy/skills?per_page=0').then(r => {
              setSkills((r.data?.skills || []).map(s => ({ name: s.name, category: s.category })));
            });
          }
        });
      } else {
        api.get('/taxonomy/skills?per_page=0').then(r => {
          setSkills((r.data?.skills || []).map(s => ({ name: s.name, category: s.category })));
        });
      }
    }).catch(() => {
      api.get('/taxonomy/skills?per_page=0').then(r => {
        setSkills((r.data?.skills || []).map(s => ({ name: s.name, category: s.category })));
      });
    });
  }, []);

  const minRequired = 3;

  const filteredSkills = skills.filter(s => {
    const matchCat = !selectedCategory || s.category === selectedCategory;
    const matchSearch = !searchTerm || s.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchCat && matchSearch;
  });

  const toggleSkill = (skillName) => {
    setSelectedSkills(prev => 
      prev.includes(skillName) 
        ? prev.filter(s => s !== skillName)
        : prev.length < 3 ? [...prev, skillName] : prev
    );
  };

  const startQuiz = async () => {
    if (selectedSkills.length < minRequired) return;
    setLoading(true);
    try {
      const res = await api.post('/assessment/start', {
        skills: selectedSkills,
        count: 10,
        difficulty,
      });
      setAssessment(res.data);
      setTotalExpected(res.data.total_questions || 30);
      setQuestions([]);
      setCurrentQ(0);
      setAnswers({});
      setPhase('quiz');
      setTimer(0);
      timerRef.current = setInterval(() => setTimer(t => t + 1), 1000);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to start test.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let pollInterval;
    let lastCount = 0;
    let settledTicks = 0;

    if (phase === 'quiz' && assessment?.assessment_ids) {
      pollInterval = setInterval(async () => {
        try {
          const ids = assessment.assessment_ids.join(',');
          const res = await api.get(`/assessment/questions?ids=${ids}`);
          if (res.data?.questions) {
            const incoming = res.data.questions;
            setQuestions(incoming);

            // Stop if we have all expected questions
            if (incoming.length >= totalExpected) {
              clearInterval(pollInterval);
              return;
            }

            // Stop if question count hasn't changed for 2 polls (settled state)
            if (incoming.length === lastCount) {
              settledTicks += 1;
              if (settledTicks >= 2 && incoming.length > 0) {
                // Update total so UI shows correct count, then stop polling
                setTotalExpected(incoming.length);
                clearInterval(pollInterval);
                return;
              }
            } else {
              settledTicks = 0;
            }
            lastCount = incoming.length;
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);
    }
    return () => clearInterval(pollInterval);
  }, [phase, assessment, totalExpected]);

  const selectAnswer = (qId, letter) => {
    setAnswers(prev => ({ ...prev, [qId]: letter }));
  };

  const submitQuiz = async () => {
    setLoading(true);
    clearInterval(timerRef.current);
    try {
      const res = await api.post('/assessment/submit', {
        answers,
      });
      setResults(res.data);
      setPhase('results');
      api.get('/assessment/history').then(r => setHistory(r.data || []));
    } catch (err) {
      alert('Failed to submit. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetQuiz = () => {
    setPhase('select');
    setAssessment(null);
    setQuestions([]);
    setResults(null);
    setAnswers({});
    setCurrentQ(0);
    clearInterval(timerRef.current);
  };

  const formatTime = (s) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-10">
        {phase === 'select' && (
          <div className="space-y-10 animate-in-slide">
            <header className="text-center space-y-4 max-w-3xl mx-auto">
              <div className="flex items-center justify-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.2em]">
                <Target className="w-4 h-4" />
                Skill Check
              </div>
              <h1 className="text-5xl font-black font-outfit text-main">Test Your Knowledge</h1>
              <p className="text-muted text-lg font-medium leading-relaxed">
                Take a quick test to see how well you know your skills. 
                Pick 3 skills to get started.
              </p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
              <div className="lg:col-span-2 space-y-6">
                <div className="surface-card p-10 space-y-8">
                  <div className="flex items-center justify-between border-b border-base pb-6">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-black font-outfit text-main">Choose Skills</h2>
                      <p className="text-xs font-bold text-muted uppercase tracking-widest">Select 3 topics to test</p>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className={`text-2xl font-black font-outfit ${selectedSkills.length === 3 ? 'text-success' : 'text-primary'}`}>
                        {selectedSkills.length} / {minRequired}
                      </span>
                      <span className="text-[10px] font-black text-muted uppercase tracking-widest">Selected</span>
                    </div>
                  </div>

                  {!targetRole && (
                    <div className="p-4 rounded-2xl bg-error/5 border border-error/10 flex items-start gap-4">
                      <Info className="w-5 h-5 text-error mt-0.5" />
                      <p className="text-xs font-bold text-error leading-relaxed">Please set your target job in your profile to see relevant skills here.</p>
                    </div>
                  )}

                  <div className="relative">
                    <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
                    <input 
                      type="text" 
                      placeholder="Search skills..."
                      value={searchTerm} 
                      onChange={e => setSearchTerm(e.target.value)}
                      className="input-field pl-14 py-4 text-base font-medium shadow-sm" 
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 max-h-[500px] overflow-y-auto pr-2 no-scrollbar">
                    {filteredSkills.map(s => {
                      const isMastered = profileSkills.includes(s.name);
                      const isSelected = selectedSkills.includes(s.name);
                      return (
                        <button 
                          key={s.name} 
                          id={`assess-${s.name}`}
                          onClick={() => toggleSkill(s.name)}
                          disabled={selectedSkills.length === 3 && !isSelected}
                          className={`group relative p-5 rounded-[1.5rem] border-2 text-left transition-all duration-300
                            ${isSelected
                              ? 'bg-primary border-primary text-white shadow-xl shadow-primary/20 scale-[1.02]'
                              : isMastered 
                                ? 'bg-success/5 border-success/10 text-success opacity-70 hover:opacity-100' 
                                : 'bg-surface border-base text-main hover:border-primary/40 hover:bg-subtle'}`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors
                              ${isSelected ? 'bg-white/20' : 'bg-subtle group-hover:bg-primary/10'}`}>
                              <BookOpen className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-primary'}`} />
                            </div>
                            {isMastered && !isSelected && <CheckCircle className="w-4 h-4 text-success" />}
                          </div>
                          <span className="text-sm font-black uppercase tracking-tight leading-tight block">{s.name}</span>
                          {isMastered && <span className="text-[9px] font-black uppercase tracking-widest mt-1 block opacity-60">Verified</span>}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="space-y-8">
                <div className="surface-card p-10 space-y-10">
                  <div className="space-y-6">
                    <h3 className="text-xl font-black font-outfit text-main flex items-center gap-3">
                      <Filter className="w-5 h-5 text-primary" />
                      Difficulty
                    </h3>
                    <div className="space-y-3">
                      {DIFFICULTIES.map(d => (
                        <button 
                          key={d.key} 
                          onClick={() => setDifficulty(d.key)}
                          className={`w-full p-5 rounded-2xl border-2 text-left transition-all duration-300 flex items-center justify-between group
                            ${difficulty === d.key
                              ? `${d.border} ${d.bg} ${d.color} shadow-lg`
                              : 'border-base bg-surface text-muted hover:border-base/60'}`}
                        >
                          <div className="flex flex-col">
                            <span className="text-sm font-black uppercase tracking-widest">{d.label}</span>
                          </div>
                          <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all
                            ${difficulty === d.key ? 'bg-current border-current' : 'border-base group-hover:border-primary/40'}`}>
                            {difficulty === d.key && <CheckCircle className="w-4 h-4 text-white" />}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="pt-6 border-t border-base space-y-6">
                    <button 
                      id="start-quiz-btn" 
                      onClick={startQuiz}
                      disabled={selectedSkills.length < minRequired || loading}
                      className="btn-primary w-full h-16 text-base shadow-2xl shadow-primary/30"
                    >
                      {loading ? (
                        <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                      ) : (
                        <div className="flex items-center justify-center gap-3">
                          <Play className="w-5 h-5 fill-current" />
                          Start Test
                        </div>
                      )}
                    </button>
                    <p className="text-[10px] font-black text-muted text-center uppercase tracking-widest leading-relaxed">
                      30 Questions total. <br />Takes about 15 minutes.
                    </p>
                  </div>
                </div>

                {history.length > 0 && (
                  <div className="surface-card p-10 space-y-6">
                    <h3 className="text-xl font-black font-outfit text-main flex items-center gap-3">
                      <Trophy className="w-5 h-5 text-warning" />
                      Past Results
                    </h3>
                    <div className="space-y-6">
                      {history.slice(0, 5).map(h => (
                        <div key={h.id} className="flex items-center justify-between group cursor-default">
                          <div className="space-y-1">
                            <span className="text-sm font-bold text-main group-hover:text-primary transition-colors">{h.skill_name}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-[9px] font-black uppercase tracking-[0.2em] text-muted">{h.difficulty}</span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end">
                            <span className={`text-xl font-black font-outfit ${h.passed ? 'text-success' : 'text-error'}`}>
                              {h.percentage}%
                            </span>
                            <span className="text-[9px] font-black uppercase tracking-widest text-muted">{h.passed ? 'Passed' : 'Try Again'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {phase === 'quiz' && (
          <div className="max-w-4xl mx-auto py-10 space-y-10 animate-in-fade">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-8">
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-primary font-black uppercase tracking-[0.3em] text-xs">
                  <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  Testing: {questions[currentQ]?.skill || 'Generating questions...'}
                </div>
                <h1 className="text-4xl font-black font-outfit text-main">
                  Question {currentQ + 1} <span className="text-muted/40 font-medium">/ {totalExpected}</span>
                </h1>
              </div>
              <div className="surface-card px-8 py-4 flex items-center gap-4 text-2xl font-black font-outfit text-primary shadow-xl">
                <Clock className="w-6 h-6" /> 
                {formatTime(timer)}
              </div>
            </header>

            <div className="h-3 bg-subtle rounded-full overflow-hidden border border-base p-0.5">
              <div 
                className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-1000 ease-out shadow-lg shadow-primary/20"
                style={{ width: `${((currentQ + 1) / totalExpected) * 100}%` }} 
              />
            </div>

            {!questions[currentQ] ? (
              <div className="surface-card p-20 flex flex-col items-center justify-center min-h-[400px] space-y-8">
                <div className="relative">
                  <div className="w-20 h-20 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                  <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 text-primary animate-pulse" />
                </div>
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-black font-outfit text-main uppercase tracking-tight">Preparing your questions...</h3>
                  <p className="text-muted font-medium">Our AI is picking the best questions for you.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-10 animate-in-slide">
                <div className="surface-card p-12 space-y-10">
                  <div className="text-2xl font-bold text-slate-900 dark:text-white leading-relaxed tracking-tight">
                    {questions[currentQ].question}
                  </div>

                  {questions[currentQ].code_snippet && (
                    <div className="rounded-[2rem] overflow-hidden border border-base shadow-2xl">
                      <div className="flex items-center justify-between px-6 py-4 bg-[#1e1e2e] border-b border-white/5">
                        <div className="flex gap-2">
                          <div className="w-3 h-3 rounded-full bg-error/80" />
                          <div className="w-3 h-3 rounded-full bg-warning/80" />
                          <div className="w-3 h-3 rounded-full bg-success/80" />
                        </div>
                        <div className="flex items-center gap-2">
                          <Code className="w-3 h-3 text-white/40" />
                          <span className="text-[10px] text-white/40 font-black uppercase tracking-[0.2em]">Code Preview</span>
                        </div>
                      </div>
                      <pre className="bg-[#0f0f1a] text-secondary font-mono text-sm leading-relaxed p-8 overflow-x-auto no-scrollbar">
                        <code>{questions[currentQ].code_snippet}</code>
                      </pre>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {Object.entries(questions[currentQ].options || {}).map(([letter, text]) => {
                      const isSelected = answers[String(questions[currentQ].id)] === letter;
                      return (
                        <button 
                          key={letter}
                          id={`option-${letter}`}
                          onClick={() => selectAnswer(String(questions[currentQ].id), letter)}
                          className={`group relative p-8 rounded-[2rem] border-2 text-left transition-all duration-500 flex items-center gap-6
                            ${isSelected
                              ? 'border-primary bg-primary/5 shadow-2xl shadow-primary/10 scale-[1.02]'
                              : 'border-base bg-surface hover:border-primary/30 hover:bg-subtle'}`}
                        >
                          <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl font-black transition-all duration-500 shrink-0
                            ${isSelected
                              ? 'bg-primary text-white shadow-lg rotate-6'
                              : 'bg-subtle text-muted group-hover:bg-primary/10 group-hover:text-primary group-hover:-rotate-3'}`}>
                            {letter.toUpperCase()}
                          </div>
                          <span className="text-base font-bold text-slate-900 dark:text-white leading-tight">
                            {text}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <footer className="flex items-center justify-between">
                  <button 
                    onClick={() => setCurrentQ(c => Math.max(0, c - 1))}
                    disabled={currentQ === 0}
                    className="btn-secondary h-14 px-8 flex items-center gap-3 disabled:opacity-0"
                  >
                    <ChevronLeft className="w-5 h-5" /> Previous
                  </button>
                  
                  <div className="hidden md:flex gap-2">
                    {Array.from({ length: totalExpected }).map((_, i) => (
                      <div key={i} className={`w-2 h-2 rounded-full transition-all duration-500
                        ${i === currentQ ? 'bg-primary w-6' : i < questions.length ? 'bg-primary/30' : 'bg-base'}`} 
                      />
                    ))}
                  </div>

                  {currentQ < totalExpected - 1 ? (
                    <button 
                      id="next-q" 
                      onClick={() => setCurrentQ(c => c + 1)}
                      disabled={!questions[currentQ]}
                      className="btn-primary h-14 px-10 group"
                    >
                      Next Question <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  ) : (
                    <button 
                      id="submit-quiz" 
                      onClick={submitQuiz} 
                      disabled={loading || !questions[currentQ]}
                      className="btn-primary bg-success hover:bg-success/90 h-14 px-10 shadow-xl shadow-success/20"
                    >
                      {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : 'Finish Test'}
                    </button>
                  )}
                </footer>
              </div>
            )}
          </div>
        )}

        {phase === 'results' && results && (
          <div className="max-w-6xl mx-auto space-y-12 animate-in-slide pb-20">
            <header className="text-center space-y-6">
              <div className="w-24 h-24 rounded-[2.5rem] bg-gradient-to-br from-primary to-secondary flex items-center justify-center mx-auto shadow-2xl shadow-primary/30">
                <Trophy className="w-12 h-12 text-white" />
              </div>
              <div className="space-y-2">
                <h1 className="text-5xl font-black font-outfit text-main">Test Completed</h1>
                <p className="text-muted text-lg font-medium">We've updated your profile with your results.</p>
              </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { title: 'Your Strengths', items: results.summary?.filter(s => s.percentage > 70) || [], color: 'text-success', bg: 'bg-success/5', border: 'border-success/10' },
                { title: 'Needs Practice', items: results.summary?.filter(s => s.percentage <= 70) || [], color: 'text-warning', bg: 'bg-warning/5', border: 'border-warning/10' },
                { title: 'New Skills to Learn', items: roleSkills.filter(s => !profileSkills.includes(s) && !results.summary?.find(rs => rs.skill === s)).map(s => ({ skill: s, unassessed: true })), color: 'text-error', bg: 'bg-error/5', border: 'border-error/10' },
              ].map(cat => (
                <div key={cat.title} className={`surface-card p-8 border-2 ${cat.border} ${cat.bg} space-y-6 flex flex-col`}>
                  <div className="flex items-center justify-between border-b border-base pb-4">
                    <h3 className={`text-lg font-black font-outfit uppercase tracking-wider ${cat.color}`}>{cat.title}</h3>
                    <BarChart className={`w-4 h-4 ${cat.color}`} />
                  </div>
                  <div className="flex-1 space-y-4">
                    {cat.items.length === 0 ? (
                      <p className="text-muted text-xs italic opacity-60 py-4">No data yet.</p>
                    ) : cat.items.map((res, idx) => (
                      <div key={idx} className="bg-surface border border-base p-4 rounded-2xl flex items-center justify-between shadow-sm group hover:border-primary/30 transition-all">
                        {res.unassessed ? (
                          <>
                            <span className="font-bold text-main text-sm">{res.skill}</span>
                            <span className="text-[9px] font-black uppercase tracking-widest text-error/80 px-2 py-0.5 rounded-md bg-error/5 border border-error/10">New</span>
                          </>
                        ) : (
                          <>
                            <div className="space-y-0.5">
                              <h4 className="font-black text-main text-sm truncate max-w-[120px]">{res.skill}</h4>
                              <span className="text-[10px] font-black text-muted uppercase tracking-widest">{res.score} / {res.total} Score</span>
                            </div>
                            <div className={`text-xl font-black font-outfit ${res.percentage > 70 ? 'text-success' : 'text-warning'}`}>
                              {res.percentage}%
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="surface-card p-10 space-y-10">
              <div className="flex items-center justify-between border-b border-base pb-6">
                <h3 className="text-3xl font-black font-outfit text-main">Review Answers</h3>
                <div className="flex gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-success" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-muted">Correct</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-error" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-muted">Wrong</span>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                {results.questions?.map((q, i) => (
                  <div key={q.id} className={`p-8 rounded-[2rem] border-2 transition-all duration-500
                    ${q.is_correct ? 'border-success/10 bg-success/[0.01]' : 'border-error/10 bg-error/[0.01]'}`}>
                    <div className="flex items-start gap-6">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-lg transition-transform hover:scale-110
                        ${q.is_correct ? 'bg-success text-white' : 'bg-error text-white'}`}>
                        {q.is_correct ? <CheckCircle className="w-6 h-6" /> : <XCircle className="w-6 h-6" />}
                      </div>
                      <div className="flex-1 space-y-6 overflow-hidden">
                        <div className="text-xl font-bold text-slate-900 dark:text-white leading-relaxed">
                          {q.question}
                        </div>
                        
                        {q.code_snippet && (
                          <div className="rounded-2xl overflow-hidden border border-base shadow-inner bg-[#0f0f1a]">
                            <pre className="text-secondary font-mono text-xs leading-relaxed p-6 overflow-x-auto no-scrollbar">
                              <code>{q.code_snippet}</code>
                            </pre>
                          </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className={`p-5 rounded-2xl border-2 flex flex-col gap-2 ${q.is_correct ? 'border-success/20 bg-success/5' : 'border-error/20 bg-error/5'}`}>
                            <span className="font-black uppercase text-[10px] tracking-widest opacity-60">Your Answer</span>
                            <span className="text-sm font-bold text-slate-900 dark:text-white">
                              {q.options[q.user_answer] || 'Not answered'}
                            </span>
                          </div>
                          {!q.is_correct && (
                            <div className="p-5 rounded-2xl border-2 border-success/20 bg-success/5 flex flex-col gap-2">
                              <span className="font-black uppercase text-[10px] tracking-widest opacity-60">Correct Answer</span>
                              <span className="text-sm font-bold text-slate-900 dark:text-white">
                                {q.options[q.correct_answer]}
                              </span>
                            </div>
                          )}
                        </div>

                        {q.explanation && (
                          <div className="p-5 rounded-2xl bg-primary/5 border border-primary/10 flex gap-4">
                            <Info className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                            <div className="space-y-1">
                              <span className="font-black uppercase text-[10px] tracking-widest text-primary">Expert Tip</span>
                              <p className="text-sm font-medium text-main leading-relaxed">{q.explanation}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <footer className="flex flex-col sm:flex-row gap-6 justify-center items-center py-10 border-t border-base">
              <button onClick={resetQuiz} className="btn-primary h-16 px-12 text-lg shadow-xl shadow-primary/20 flex items-center gap-3">
                <RotateCcw className="w-5 h-5" /> Take Another Test
              </button>
              <button onClick={() => window.location.href = '/dashboard'} className="btn-secondary h-16 px-12 text-lg">
                Go to Dashboard
              </button>
            </footer>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

