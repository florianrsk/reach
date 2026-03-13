import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowRight } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm">
        <div className="wide-container h-16 flex items-center justify-between">
          <Link to="/" className="text-lg font-serif">Reach</Link>
          <div className="flex items-center gap-6">
            <Link to="/login" className="text-sm text-secondary hover:text-primary transition-colors">
              Log in
            </Link>
            <Link to="/register">
              <Button size="sm" className="rounded-none text-sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero - Statement, not explanation */}
      <section className="min-h-[85vh] flex items-center">
        <div className="editorial-container pt-24 stagger">
          <h1 className="mb-8">
            Stop sharing<br />your email.
          </h1>
          <p className="statement text-secondary max-w-lg mb-12">
            Share a reach link instead.
          </p>
          <Link to="/register">
            <Button size="lg" className="rounded-none gap-3 text-base px-8 py-6">
              Create your reach link
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Single clarifying section */}
      <section className="section-gap border-t border-border">
        <div className="editorial-container">
          <p className="statement text-secondary mb-16">
            Senders explain their intent.<br />
            AI and your rules decide who gets through.<br />
            You see decisions, not messages.
          </p>
          
          <Link 
            to="/replace-email" 
            className="inline-flex items-center gap-2 text-sm border-b border-foreground pb-1 hover:opacity-70 transition-opacity"
          >
            See how it works
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-border">
        <div className="wide-container flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <span className="font-serif">Reach</span>
          <div className="flex gap-8 text-sm text-secondary">
            <Link to="/why" className="hover:text-primary transition-colors">Why</Link>
            <Link to="/replace-email" className="hover:text-primary transition-colors">Replace Email</Link>
            <Link to="/first-10-minutes" className="hover:text-primary transition-colors">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
