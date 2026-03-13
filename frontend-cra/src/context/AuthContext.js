import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../lib/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [identity, setIdentity] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Always try to fetch user - cookies are sent automatically
    fetchUser();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
      
      // Also fetch identity
      try {
        const identityResponse = await api.get('/identity');
        setIdentity(identityResponse.data);
      } catch (e) {
        // No identity yet, that's okay
      }
    } catch (error) {
      // Don't clear localStorage here - let the interceptor handle it
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { user: userData, csrf_token } = response.data;
    
    setUser(userData);
    
    // Fetch identity after login
    try {
      const identityResponse = await api.get('/identity');
      setIdentity(identityResponse.data);
    } catch (e) {
      // No identity yet
    }
    
    return userData;
  };

  const register = async (email, password, name) => {
    const response = await api.post('/auth/register', { email, password, name });
    const { user: userData } = response.data;
    
    setUser(userData);
    
    return userData;
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Logout endpoint might fail, but we still clear local state
      console.error('Logout error:', error);
    }
    localStorage.removeItem('reach_token'); // Clear legacy token
    setUser(null);
    setIdentity(null);
  };

  const refreshIdentity = async () => {
    try {
      const response = await api.get('/identity');
      setIdentity(response.data);
      return response.data;
    } catch (e) {
      setIdentity(null);
      return null;
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      identity,
      loading,
      login,
      register,
      logout,
      refreshIdentity
    }}>
      {children}
    </AuthContext.Provider>
  );
};
