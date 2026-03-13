import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import { extractErrorMessage } from '../lib/error-utils';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(email, password);
      toast.success('Welcome back');
      navigate('/dashboard');
    } catch (error) {
      const message = extractErrorMessage(error) || 'Invalid credentials';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Form side */}
      <div className="flex-1 flex flex-col justify-center px-6 py-12 lg:px-20">
        <div className="max-w-sm w-full mx-auto lg:mx-0">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-sm text-secondary hover:text-primary transition-colors mb-12"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>

          <h1 className="text-3xl font-serif mb-3">Welcome back</h1>
          <p className="text-secondary mb-10">
            Sign in to your Reach identity.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="rounded-none h-12"
                data-testid="login-email"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="rounded-none h-12"
                data-testid="login-password"
              />
            </div>

            <Button
              type="submit"
              className="w-full rounded-none h-12 text-base"
              disabled={loading}
              data-testid="login-submit"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <p className="mt-8 text-sm text-secondary">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary hover:opacity-70 transition-opacity">
              Create one
            </Link>
          </p>
        </div>
      </div>

      {/* Decoration side */}
      <div className="hidden lg:flex flex-1 items-center justify-center surface-2 border-l border-border">
        <div className="text-center">
          <span className="text-8xl font-serif text-tertiary/20">R</span>
        </div>
      </div>
    </div>
  );
}
