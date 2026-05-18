import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  signInWithPopup
} from 'firebase/auth';
import { auth, googleProvider } from '../firebase';
import api from '../services/api';

const AuthContext = createContext(null);

/**
 * Fetches the full user profile from our backend and merges it with the
 * Firebase user object so we have `is_admin`, `profile`, etc. available.
 */
async function fetchBackendProfile(firebaseUser) {
  const token = await firebaseUser.getIdToken(/* forceRefresh= */ true);
  localStorage.setItem('access_token', token);
  const res = await api.get('/auth/me');
  return { ...firebaseUser, ...res.data.user };
}

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  // Track whether we're in the middle of a manual login/signup to avoid
  // the onAuthStateChanged handler double-fetching the profile.
  const manualAuthInProgress = useRef(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      // If a manual login is ongoing, skip — that flow will call setUser itself.
      if (manualAuthInProgress.current) return;

      if (firebaseUser) {
        try {
          const fullUser = await fetchBackendProfile(firebaseUser);
          setUser(fullUser);
        } catch (err) {
          console.error('[Auth] Backend profile fetch failed:', err);
          // Still let the user in with basic Firebase info
          setUser(firebaseUser);
        }
      } else {
        localStorage.removeItem('access_token');
        setUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []); // Run ONCE on mount — no [user] dependency to avoid infinite loops

  const login = useCallback(async (email, password) => {
    manualAuthInProgress.current = true;
    try {
      setLoading(true);
      const result = await signInWithEmailAndPassword(auth, email, password);
      const fullUser = await fetchBackendProfile(result.user);
      setUser(fullUser);
      return fullUser;
    } finally {
      manualAuthInProgress.current = false;
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (email, password) => {
    manualAuthInProgress.current = true;
    try {
      setLoading(true);
      const result = await createUserWithEmailAndPassword(auth, email, password);
      const fullUser = await fetchBackendProfile(result.user);
      setUser(fullUser);
      return fullUser;
    } finally {
      manualAuthInProgress.current = false;
      setLoading(false);
    }
  }, []);

  const googleLogin = useCallback(async () => {
    manualAuthInProgress.current = true;
    try {
      setLoading(true);
      const result = await signInWithPopup(auth, googleProvider);
      const fullUser = await fetchBackendProfile(result.user);
      setUser(fullUser);
      return fullUser;
    } finally {
      manualAuthInProgress.current = false;
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      setLoading(true);
      await signOut(auth);
      localStorage.removeItem('access_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const resetPassword = useCallback(async (email) => {
    try {
      const { sendPasswordResetEmail } = await import('firebase/auth');
      await sendPasswordResetEmail(auth, email);
    } catch (err) {
      console.error('[Auth] Password reset failed:', err);
      throw err;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    try {
      const fullUser = await fetchBackendProfile(currentUser);
      setUser(prev => ({ ...prev, ...fullUser }));
    } catch (err) {
      console.error('[Auth] Refresh failed:', err);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, googleLogin, logout, refreshUser, resetPassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
