import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * AdminRoute — wraps a route so only users with is_admin=true can access it.
 * Non-admins are redirected to /dashboard with a 403-style redirect.
 */
export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-bg">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <Navigate to="/signin" replace />;
  if (!user.is_admin) return <Navigate to="/dashboard" replace />;

  return children;
}
