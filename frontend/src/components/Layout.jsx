import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { LayoutDashboard, Inbox, Settings, LogOut, ExternalLink, Menu, X } from 'lucide-react';
import { useState, useEffect } from 'react';

export const Layout = ({ children }) => {
  const { user, identity, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [newAttemptsCount, setNewAttemptsCount] = useState(0);

  // Listen for new attempt notifications
  useEffect(() => {
    const handleNewAttempt = (event) => {
      setNewAttemptsCount(prev => prev + 1);
    };

    window.addEventListener('new-attempt-notification', handleNewAttempt);

    // Reset count when user visits attempts page
    if (location.pathname === '/attempts') {
      setNewAttemptsCount(0);
    }

    return () => {
      window.removeEventListener('new-attempt-notification', handleNewAttempt);
    };
  }, [location.pathname]);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { 
      path: '/attempts', 
      label: 'Attempts', 
      icon: Inbox,
      badge: newAttemptsCount > 0 ? newAttemptsCount : null
    },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="wide-container h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="text-lg font-serif">
              Reach
            </Link>
            
            <nav className="hidden md:flex items-center gap-6">
              {navItems.map(({ path, label, badge }) => (
                <div key={path} className="relative">
                  <Link
                    to={path}
                    className={`text-sm transition-colors ${
                      isActive(path) 
                        ? 'text-primary' 
                        : 'text-secondary hover:text-primary'
                    }`}
                    data-testid={`nav-${label.toLowerCase()}`}
                  >
                    {label}
                  </Link>
                  {badge && (
                    <span className="absolute -top-2 -right-3 bg-primary text-background text-xs font-medium rounded-full w-5 h-5 flex items-center justify-center">
                      {badge > 9 ? '9+' : badge}
                    </span>
                  )}
                </div>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {identity && (
              <Link
                to={`/r/${identity.handle}`}
                target="_blank"
                className="hidden sm:flex items-center gap-1 text-sm text-secondary hover:text-primary transition-colors"
                data-testid="public-link"
              >
                <span className="mono text-xs">/{identity.handle}</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            )}
            
            <div className="hidden sm:flex items-center gap-4 pl-4 border-l border-border">
              <span className="text-sm text-secondary">{user?.name}</span>
              <button
                onClick={logout}
                className="text-secondary hover:text-primary transition-colors"
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden text-secondary hover:text-primary"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border bg-background">
            <nav className="wide-container py-4 space-y-1">
              {navItems.map(({ path, label, icon: Icon, badge }) => (
                <div key={path} className="relative">
                  <Link
                    to={path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-3 text-sm transition-colors ${
                      isActive(path) 
                        ? 'text-primary bg-surface-2' 
                        : 'text-secondary hover:text-primary'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </Link>
                  {badge && (
                    <span className="absolute top-2 right-3 bg-primary text-background text-xs font-medium rounded-full w-5 h-5 flex items-center justify-center">
                      {badge > 9 ? '9+' : badge}
                    </span>
                  )}
                </div>
              ))}
              
              <div className="pt-3 mt-3 border-t border-border space-y-1">
                {identity && (
                  <Link
                    to={`/r/${identity.handle}`}
                    target="_blank"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3 py-3 text-sm text-secondary"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View public page
                  </Link>
                )}
                <button
                  onClick={() => { logout(); setMobileMenuOpen(false); }}
                  className="flex items-center gap-3 px-3 py-3 text-sm text-secondary w-full text-left"
                >
                  <LogOut className="w-4 h-4" />
                  Log out
                </button>
              </div>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-12">
        <div className="wide-container">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
