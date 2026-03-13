import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important: Send cookies with requests
});

// Get CSRF token from cookie
const getCsrfToken = () => {
  const match = document.cookie.match(new RegExp('(^| )csrf_token=([^;]+)'));
  return match ? match[2] : null;
};

// Add CSRF token to requests
api.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken();
  if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase())) {
    config.headers['x-csrf-token'] = csrfToken;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear any legacy localStorage token
      localStorage.removeItem('reach_token');
      // Only redirect if not already on auth pages
      if (!window.location.pathname.startsWith('/login') && 
          !window.location.pathname.startsWith('/register') &&
          !window.location.pathname.startsWith('/r/')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
