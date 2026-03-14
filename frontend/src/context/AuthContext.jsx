import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../lib/api';
import websocketClient from '../lib/websocket';

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
  const [websocketConnected, setWebsocketConnected] = useState(false);

  useEffect(() => {
    // Always try to fetch user - cookies are sent automatically
    fetchUser();
  }, []);

  // Connect WebSocket when user is authenticated
  useEffect(() => {
    if (user?.id) {
      connectWebSocket();
    } else {
      // Disconnect WebSocket if user logs out
      websocketClient.disconnect();
      setWebsocketConnected(false);
    }

    // Cleanup on unmount
    return () => {
      websocketClient.disconnect();
    };
  }, [user?.id]);

  const connectWebSocket = () => {
    if (!user?.id) return;

    // Get access token from cookies
    const getAccessToken = () => {
      const match = document.cookie.match(new RegExp('(^| )access_token=([^;]+)'));
      return match ? match[2] : null;
    };

    const accessToken = getAccessToken();
    if (!accessToken) {
      console.warn('No access token found for WebSocket connection');
      return;
    }

    // Connect WebSocket
    websocketClient.connect(accessToken, user.id);

    // Listen for connection status changes
    websocketClient.addConnectionHandler((connected) => {
      setWebsocketConnected(connected);
    });

    // Listen for new attempts to update badge counts
    websocketClient.addMessageHandler((data) => {
      if (data.type === 'new_attempt') {
        // Dispatch event for badge updates
        window.dispatchEvent(new CustomEvent('new-attempt-notification', { detail: data }));
      }
    });
  };

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
    websocketClient.disconnect();
    setWebsocketConnected(false);
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
      websocketConnected,
      login,
      register,
      logout,
      refreshIdentity
    }}>
      {children}
    </AuthContext.Provider>
  );
};
