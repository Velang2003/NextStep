import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';

// Lazily load all page components to split vendor/UI chunks
const LandingPage  = lazy(() => import('./pages/LandingPage'));
const SignIn     = lazy(() => import('./pages/SignIn'));
const SignUp     = lazy(() => import('./pages/SignUp'));
const Dashboard  = lazy(() => import('./pages/Dashboard'));
const Profile    = lazy(() => import('./pages/Profile'));
const MarketTrends = lazy(() => import('./pages/MarketTrends'));
const SkillGap   = lazy(() => import('./pages/SkillGap'));
const CareerPath = lazy(() => import('./pages/CareerPath'));
const Jobs       = lazy(() => import('./pages/Jobs'));
const SkillAssessment = lazy(() => import('./pages/SkillAssessment'));
const RoleTrends = lazy(() => import('./pages/RoleTrends'));
const GeoMap     = lazy(() => import('./pages/GeoMap'));
const Applications = lazy(() => import('./pages/Applications'));
const AdminPanel = lazy(() => import('./pages/AdminPanel'));
const Terms      = lazy(() => import('./pages/Terms'));
const Privacy    = lazy(() => import('./pages/Privacy'));

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
          <Suspense fallback={
            <div className="min-h-screen bg-[#0B0F19] flex flex-col items-center justify-center space-y-4">
              <div className="w-10 h-10 border-4 border-[#3B82F6] border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-400 text-xs font-bold uppercase tracking-[0.2em]">Loading Page...</p>
            </div>
          }>
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
          </Suspense>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
