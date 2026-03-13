import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import { extractErrorMessage } from '../lib/error-utils';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      await register(email, password, name);
      toast.success('Account created');
      navigate('/dashboard');
    } catch (error) {
      const message = extractErrorMessage(error) || 'Registration failed';
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

          <h1 className="text-3xl font-serif mb-3">Create your identity</h1>
          <p className="text-secondary mb-10">
            Free forever. Senders pay, you don't.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm">Name</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                required
                className="rounded-none h-12"
                data-testid="register-name"
              />
            </div>

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
                data-testid="register-email"
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
                minLength={6}
                className="rounded-none h-12"
                data-testid="register-password"
              />
              <p className="text-xs text-tertiary">Minimum 6 characters</p>
            </div>

            <Button
              type="submit"
              className="w-full rounded-none h-12 text-base"
              disabled={loading}
              data-testid="register-submit"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          <p className="mt-8 text-sm text-secondary">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:opacity-70 transition-opacity">
              Sign in
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
