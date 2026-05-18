import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import LandingPage  from './pages/LandingPage';
import SignIn     from './pages/SignIn';
import SignUp     from './pages/SignUp';
import Dashboard  from './pages/Dashboard';
import Profile    from './pages/Profile';
import MarketTrends from './pages/MarketTrends';
import SkillGap   from './pages/SkillGap';
import CareerPath from './pages/CareerPath';
import Jobs       from './pages/Jobs';
import SkillAssessment from './pages/SkillAssessment';
import RoleTrends from './pages/RoleTrends';
import GeoMap     from './pages/GeoMap';
import Applications from './pages/Applications';
import AdminPanel from './pages/AdminPanel';
import Terms      from './pages/Terms';
import Privacy    from './pages/Privacy';

// Smart redirect: authenticated users → /dashboard, guests → /signin
function AuthRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return <Navigate to={user ? '/dashboard' : '/signin'} replace />;
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/signin" element={<SignIn />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/privacy" element={<Privacy />} />

            {/* Protected */}
            <Route path="/dashboard"    element={<ProtectedRoute><Dashboard    /></ProtectedRoute>} />
            <Route path="/profile"      element={<ProtectedRoute><Profile      /></ProtectedRoute>} />
            <Route path="/market"       element={<ProtectedRoute><MarketTrends /></ProtectedRoute>} />
            <Route path="/jobs"         element={<ProtectedRoute><Jobs         /></ProtectedRoute>} />
            <Route path="/skill-gap"    element={<ProtectedRoute><SkillGap     /></ProtectedRoute>} />
            <Route path="/career-path"  element={<ProtectedRoute><CareerPath   /></ProtectedRoute>} />
            <Route path="/assessment"   element={<ProtectedRoute><SkillAssessment /></ProtectedRoute>} />
            <Route path="/role-trends"  element={<ProtectedRoute><RoleTrends   /></ProtectedRoute>} />
            <Route path="/geo-map"      element={<ProtectedRoute><GeoMap       /></ProtectedRoute>} />
            <Route path="/applications" element={<ProtectedRoute><Applications /></ProtectedRoute>} />
            <Route path="/admin"        element={<AdminRoute><AdminPanel /></AdminRoute>} />

            {/* Catch-all: smart redirect based on auth state */}
            <Route path="*" element={<AuthRedirect />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
