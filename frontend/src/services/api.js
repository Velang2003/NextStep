import axios from 'axios';
import { auth } from '../firebase';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach a FRESH Firebase ID token to every request.
// getIdToken() transparently refreshes if the token has expired (1-hour TTL).
api.interceptors.request.use(async (config) => {
  try {
    const currentUser = auth.currentUser;
    if (currentUser) {
      const token = await currentUser.getIdToken();
      localStorage.setItem('access_token', token);
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      const stored = localStorage.getItem('access_token');
      if (stored) config.headers.Authorization = `Bearer ${stored}`;
    }
  } catch {
    const stored = localStorage.getItem('access_token');
    if (stored) config.headers.Authorization = `Bearer ${stored}`;
  }
  return config;
});

// Handle 401 errors.
// IMPORTANT: Only redirect to sign-in when Firebase ALSO has no current user.
// If Firebase still has a session, the 401 is a transient backend error during
// auth initialization — do NOT force-redirect (that causes the login-refresh loop).
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      const hasFirebaseSession = !!auth.currentUser;

      if (hasFirebaseSession) {
        console.warn('[API] 401 detected with active session. Retrying with fresh token...');
        originalRequest._retry = true;
        
        // Force refresh the token
        const newToken = await auth.currentUser.getIdToken(true);
        localStorage.setItem('access_token', newToken);
        
        // Update header and retry
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } else {
        // Truly unauthenticated — clear stale token and redirect to sign-in
        console.warn('[API] Unauthorized and no active Firebase session — redirecting.');
        localStorage.removeItem('access_token');
        if (!window.location.pathname.startsWith('/sign')) {
          window.location.href = '/signin';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
