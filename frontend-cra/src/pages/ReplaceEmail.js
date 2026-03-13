import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowRight, Globe, MessageSquare, Briefcase, Users, Newspaper, Code } from 'lucide-react';

export default function ReplaceEmail() {
  const replacements = [
    {
      icon: Globe,
      location: 'Your website',
      before: 'Contact: hello@yourname.com',
      after: 'reach.me/yourname',
    },
    {
      icon: MessageSquare,
      location: 'Twitter / X bio',
      before: 'DMs open · email in bio',
      after: 'reach.me/yourname',
    },
    {
      icon: Code,
      location: 'GitHub profile',
      before: 'dev@yourname.com',
      after: 'reach.me/yourname/open',
    },
    {
      icon: Briefcase,
      location: 'LinkedIn',
      before: '"Open to opportunities"',
      after: 'reach.me/yourname/business',
    },
    {
      icon: Users,
      location: 'Creator sponsorship page',
      before: 'business@yourname.com',
      after: 'reach.me/yourname/business',
    },
    {
      icon: Newspaper,
      location: 'Press page',
      before: 'press@company.com',
      after: 'reach.me/company/press',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="wide-container h-16 flex items-center justify-between">
          <Link to="/" className="text-lg font-serif">Reach</Link>
          <Link to="/register">
            <Button variant="ghost" size="sm" className="text-sm">Get Started</Button>
          </Link>
        </div>
      </header>

      <main className="pt-32 pb-24">
        {/* Hero */}
        <div className="editorial-container mb-24 stagger">
          <p className="tag mb-6">The Ritual</p>
          <h1 className="mb-8">
            Replace your email.
          </h1>
          <p className="statement text-secondary max-w-lg">
            Every place you've shared it is an open door to interruption. 
            Close those doors. Open a gate.
          </p>
        </div>

        {/* The core comparison */}
        <section className="section-gap-sm border-y border-border surface-2">
          <div className="wide-container">
            <div className="grid md:grid-cols-2 gap-12 md:gap-20">
              {/* Email */}
              <div>
                <p className="tag mb-8">How email works</p>
                <div className="space-y-6 text-secondary">
                  <p>Anyone with your address can reach you.</p>
                  <p>You sort through everything manually.</p>
                  <p>No cost to sender, all cost to you.</p>
                  <p>Inbox zero is a full-time job.</p>
                </div>
              </div>
              
              {/* Reach */}
              <div>
                <p className="tag mb-8">How Reach works</p>
                <div className="space-y-6">
                  <p>Senders state their intent first.</p>
                  <p>AI + your rules decide who gets through.</p>
                  <p>Payment filters for serious intent.</p>
                  <p>You see decisions, not messages.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Replace this - the ceremony */}
        <section className="section-gap">
          <div className="wide-container">
            <div className="editorial-container mb-16 px-0">
              <h2 className="mb-4">Pick one. Replace it.</h2>
              <p className="text-secondary">
                Remove your email. Paste your reach link. That's it.
              </p>
            </div>

            <div className="space-y-4">
              {replacements.map((item, index) => (
                <div 
                  key={index}
                  className="card-subtle p-6 md:p-8 hover-lift"
                >
                  <div className="flex items-start gap-6">
                    <div className="w-10 h-10 flex items-center justify-center bg-surface-2 flex-shrink-0">
                      <item.icon className="w-5 h-5 text-secondary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium mb-4">{item.location}</p>
                      <div className="before-after">
                        <div>
                          <p className="tag mb-2">Before</p>
                          <p className="mono text-sm text-tertiary line-through">{item.before}</p>
                        </div>
                        <div>
                          <p className="tag mb-2">After</p>
                          <p className="mono text-sm">{item.after}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* The flow */}
        <section className="section-gap border-t border-border">
          <div className="wide-container">
            <div className="editorial-container mb-20 px-0">
              <h2 className="mb-4">What happens next</h2>
              <p className="text-secondary">
                When someone clicks your reach link.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-16">
              <div>
                <p className="step-number mb-4">1</p>
                <h3 className="mb-4">They explain themselves</h3>
                <p className="text-secondary text-sm">
                  Intent. Reason. Who they are. Structured input that AI can evaluate.
                </p>
              </div>
              <div>
                <p className="step-number mb-4">2</p>
                <h3 className="mb-4">Your rules decide</h3>
                <p className="text-secondary text-sm">
                  AI classifies intent. Your policy executes. Deliver, reject, queue, or require payment.
                </p>
              </div>
              <div>
                <p className="step-number mb-4">3</p>
                <h3 className="mb-4">You see what matters</h3>
                <p className="text-secondary text-sm">
                  No inbox. No unread count. A dashboard of decisions already made.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Example policy */}
        <section className="section-gap border-t border-border surface-2">
          <div className="wide-container">
            <div className="editorial-container mb-12 px-0">
              <h2 className="mb-4">A simple policy</h2>
              <p className="text-secondary">
                You don't write code. You set rules once and forget.
              </p>
            </div>

            <div className="code-block max-w-xl">
              <div className="space-y-2 text-sm">
                <p><span className="text-tertiary">IF</span> intent = spam</p>
                <p className="pl-6"><span className="text-tertiary">→</span> reject</p>
                <p className="mt-4"><span className="text-tertiary">IF</span> intent = business <span className="text-tertiary">AND</span> sender unknown</p>
                <p className="pl-6"><span className="text-tertiary">→</span> request payment ($25)</p>
                <p className="mt-4"><span className="text-tertiary">ELSE</span></p>
                <p className="pl-6"><span className="text-tertiary">→</span> queue for review</p>
              </div>
            </div>
            
            <p className="text-sm text-secondary mt-6 max-w-xl">
              The $25 isn't revenue. It's a filter. Anyone willing to pay is probably worth your time.
            </p>
          </div>
        </section>

        {/* Closing statement */}
        <section className="section-gap border-t border-border">
          <div className="editorial-container text-center">
            <p className="pullquote mb-16">
              You're not filtering your inbox.<br />
              You're replacing the entire model.
            </p>
            
            <Link to="/first-10-minutes">
              <Button size="lg" className="rounded-none gap-3 text-base px-8 py-6">
                Start in 10 minutes
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-12 border-t border-border">
        <div className="wide-container flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <span className="font-serif">Reach</span>
          <div className="flex gap-8 text-sm text-secondary">
            <Link to="/why" className="hover:text-primary transition-colors">Why</Link>
            <Link to="/replace-email" className="text-primary">Replace Email</Link>
            <Link to="/first-10-minutes" className="hover:text-primary transition-colors">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
