import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Copy, Check, ArrowRight, ExternalLink } from 'lucide-react';

export default function Dashboard() {
  const { identity, refreshIdentity } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);

  useEffect(() => {
    if (identity) {
      // Check if Face is completed
      if (!identity.face_completed) {
        // Redirect to Face setup
        navigate('/face-setup');
        return;
      }
      fetchData();
      checkOnboardingStatus();
    } else {
      setLoading(false);
    }
  }, [identity, navigate]);

  const checkOnboardingStatus = async () => {
    const hasCompletedOnboarding = localStorage.getItem(`reach_onboarding_${identity?.id}`);
    if (!hasCompletedOnboarding) {
      setOnboardingStep(1);
    }
  };

  const completeOnboarding = () => {
    localStorage.setItem(`reach_onboarding_${identity?.id}`, 'true');
    setOnboardingStep(0);
  };

  const fetchData = async () => {
    try {
      const [statsRes, attemptsRes] = await Promise.all([
        api.get('/stats'),
        api.get('/attempts')
      ]);
      setStats(statsRes.data);
      setAttempts(attemptsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };



  const copyLink = () => {
    const url = `${window.location.origin}/r/${identity?.handle}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success('Link copied');
    setTimeout(() => setCopied(false), 2000);
  };

  const publicUrl = identity ? `${window.location.origin}/r/${identity.handle}` : '';

  // Loading state
  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <p className="text-secondary">Loading...</p>
        </div>
      </Layout>
    );
  }

  // No identity - should redirect to FaceSetup via useEffect
  if (!identity) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <p className="text-secondary">Redirecting to Face setup...</p>
        </div>
      </Layout>
    );
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <p className="text-secondary">Loading...</p>
        </div>
      </Layout>
    );
  }

  // Onboarding overlay
  if (onboardingStep > 0) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto py-12 animate-in">
          {/* Progress */}
          <div className="flex items-center justify-center gap-2 mb-12 text-sm text-secondary">
            <span className={onboardingStep >= 1 ? 'text-primary' : ''}>Create</span>
            <span>→</span>
            <span className={onboardingStep >= 2 ? 'text-primary' : ''}>Copy</span>
            <span>→</span>
            <span className={onboardingStep >= 3 ? 'text-primary' : ''}>Replace</span>
          </div>

          {onboardingStep === 1 && (
            <div className="text-center">
              <div className="w-16 h-16 bg-foreground text-background flex items-center justify-center mx-auto mb-8">
                <Check className="w-8 h-8" />
              </div>
              <h1 className="text-3xl font-serif mb-3">Identity created</h1>
              <p className="text-secondary mb-10">
                You're <span className="mono">/{identity?.handle}</span>
              </p>
              <Button 
                onClick={() => setOnboardingStep(2)} 
                className="rounded-none h-12 px-8 gap-2"
                data-testid="onboarding-next-1"
              >
                Continue
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          )}

          {onboardingStep === 2 && (
            <div className="text-center">
              <h1 className="text-3xl font-serif mb-3">Copy your link</h1>
              <p className="text-secondary mb-10">
                This replaces your email address.
              </p>
              
              <div className="flex items-center gap-2 max-w-md mx-auto mb-10">
                <Input
                  value={publicUrl}
                  readOnly
                  className="rounded-none h-12 mono text-sm"
                />
                <Button
                  variant={copied ? "default" : "outline"}
                  onClick={copyLink}
                  className="rounded-none h-12 px-6 gap-2"
                  data-testid="onboarding-copy"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              </div>

              <Button 
                onClick={() => setOnboardingStep(3)} 
                className="rounded-none h-12 px-8 gap-2"
                data-testid="onboarding-next-2"
              >
                I've copied it
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          )}

          {onboardingStep === 3 && (
            <div className="text-center">
              <h1 className="text-3xl font-serif mb-3">Replace your email</h1>
              <p className="text-secondary mb-10">
                Pick one place. Remove your email. Paste your reach link.
              </p>
              
              <div className="space-y-2 text-left max-w-sm mx-auto mb-10">
                {[
                  'Your website contact section',
                  'Twitter / X bio',
                  'GitHub profile',
                  'LinkedIn summary',
                ].map((place, i) => (
                  <div key={i} className="p-4 card-subtle text-sm text-secondary">
                    {place}
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <Button 
                  onClick={completeOnboarding} 
                  className="rounded-none h-12 px-8"
                  data-testid="onboarding-done"
                >
                  I've replaced my email
                </Button>
                <button 
                  onClick={completeOnboarding}
                  className="block mx-auto text-sm text-secondary hover:text-primary transition-colors"
                >
                  Skip for now
                </button>
              </div>
            </div>
          )}
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="animate-in">
        {/* Face Preview Section */}
        <div className="mb-12 border border-border p-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-serif mb-2">{identity.display_name}</h1>
              <p className="text-lg text-secondary mb-1">{identity.headline}</p>
              {identity.photo_url && (
                <div className="w-16 h-16 rounded-none overflow-hidden mb-4">
                  <img 
                    src={identity.photo_url} 
                    alt={identity.display_name}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 px-2 py-1 bg-foreground text-background text-xs font-medium">
              <Check className="w-3 h-3" />
              <span>Face Complete</span>
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <div>
              <h3 className="text-sm text-secondary mb-1">Current Focus</h3>
              <p className="text-foreground">{identity.current_focus}</p>
            </div>
            <div>
              <h3 className="text-sm text-secondary mb-1">Availability</h3>
              <p className="text-foreground">{identity.availability_signal}</p>
            </div>
            <div>
              <h3 className="text-sm text-secondary mb-1">Your Prompt</h3>
              <p className="text-foreground italic">"{identity.prompt}"</p>
            </div>
            
            {identity.links && identity.links.length > 0 && (
              <div>
                <h3 className="text-sm text-secondary mb-2">Links</h3>
                <div className="flex flex-wrap gap-3">
                  {identity.links.map((link, index) => (
                    <a
                      key={index}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline"
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Reach Link Section */}
          <div className="pt-6 border-t border-border">
            <h2 className="text-xl font-serif mb-4">Your reach link</h2>
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1 border border-border p-4 mono text-lg bg-background">
                {publicUrl}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={copied ? "default" : "outline"}
                  onClick={copyLink}
                  className="rounded-none h-12 px-6 gap-2"
                  data-testid="dashboard-copy-link"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied' : 'Copy'}
                </Button>
                <Button
                  variant="outline"
                  className="rounded-none h-12 px-6 gap-2"
                  onClick={() => {
                    copyLink();
                    toast.success('Link copied to clipboard. Share it anywhere!');
                  }}
                >
                  <ExternalLink className="w-4 h-4" />
                  Share
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Stat Cards - 3 cards as requested */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
          {[
            { label: 'Total Attempts', value: stats?.total_attempts || 0, description: 'All reach attempts' },
            { label: 'Approved', value: stats?.delivered || 0, description: 'Delivered to you' },
            { label: 'Blocked', value: stats?.blocked || 0, description: 'Automatically rejected' },
          ].map(({ label, value, description }) => (
            <div key={label} className="border border-border p-6" data-testid={`stat-${label.toLowerCase().replace(' ', '-')}`}>
              <p className="text-sm text-secondary mb-1">{label}</p>
              <p className="text-3xl font-serif mb-2">{value}</p>
              <p className="text-xs text-tertiary">{description}</p>
            </div>
          ))}
        </div>

        {/* Recent Attempts Preview */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-serif">Recent Attempts</h2>
            {attempts.length > 0 && (
              <button
                onClick={() => navigate('/attempts')}
                className="text-sm text-secondary hover:text-primary transition-colors"
                data-testid="view-all-attempts"
              >
                View all
              </button>
            )}
          </div>

          {attempts.length === 0 ? (
            <div className="border border-border p-8">
              <h3 className="font-serif text-lg mb-3">No attempts yet</h3>
              <p className="text-sm text-secondary mb-6">
                When someone tries to reach you, you'll see them here
              </p>
              
              {/* Visual preview of what an attempt card looks like */}
              <div className="border border-dashed border-border p-5 mb-6 opacity-60">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="tag bg-background text-secondary">collaboration</span>
                      <span className="tag bg-background text-primary">deliver to human</span>
                    </div>
                    <p className="text-sm truncate mb-1">Interested in collaborating on a new project</p>
                    <p className="text-xs text-tertiary">sender@example.com · Just now</p>
                  </div>
                </div>
              </div>
              
              <Button
                variant="outline"
                className="rounded-none gap-2"
                onClick={copyLink}
              >
                <Copy className="w-4 h-4" />
                Copy your reach link to get started
              </Button>
            </div>
          ) : (
            <div className="border border-border divide-y divide-border">
              {attempts.map((attempt) => (
                <div 
                  key={attempt.id} 
                  className="p-5 hover:bg-surface-2 transition-colors cursor-pointer"
                  onClick={() => navigate('/attempts')}
                  data-testid={`attempt-${attempt.id}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="tag">
                          {attempt.ai_classification?.intent_type || 'unknown'}
                        </span>
                        <span className={`tag ${
                          attempt.decision === 'deliver_to_human' ? 'text-primary' :
                          attempt.decision === 'reject' ? 'line-through' : ''
                        }`}>
                          {attempt.decision.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-sm truncate">
                        {attempt.payload?.reason || 'No reason provided'}
                      </p>
                      <p className="text-xs text-tertiary mt-1">
                        {attempt.sender_context?.email || 'Anonymous'} · {new Date(attempt.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex items-center justify-between pt-6 border-t border-border">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-primary" />
            <span className="text-sm text-secondary">Your reach is live</span>
          </div>
          <Button
            variant="outline"
            className="rounded-none gap-2"
            onClick={() => navigate('/slots')}
            data-testid="manage-slots-btn"
          >
            Manage slots
          </Button>
        </div>
      </div>
    </Layout>
  );
}
