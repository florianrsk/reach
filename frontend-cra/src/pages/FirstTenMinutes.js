import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowRight, Check } from 'lucide-react';

export default function FirstTenMinutes() {
  const steps = [
    {
      number: '01',
      title: 'Create your identity',
      description: 'Pick a handle. This becomes your reach URL.',
      detail: 'reach.me/yourname',
      done: false
    },
    {
      number: '02',
      title: 'Your first slot is ready',
      description: 'A default "open" slot is created. It queues everything for your review.',
      detail: 'reach.me/yourname/open',
      done: false
    },
    {
      number: '03',
      title: 'Copy your link',
      description: 'Go to your dashboard. Copy your public reach URL.',
      detail: null,
      done: false
    },
    {
      number: '04',
      title: 'Replace your email somewhere',
      description: 'Pick one place. Your website, Twitter bio, GitHub profile. Remove the email. Paste the reach link.',
      detail: null,
      done: false,
      highlight: true
    },
  ];

  const optional = [
    'Create more slots (/business, /press)',
    'Add payment requirements',
    'Customize your rules',
    'Replace more emails'
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
        <div className="editorial-container mb-20 stagger">
          <p className="tag mb-6">Get Started</p>
          <h1 className="mb-8">
            First 10 minutes.
          </h1>
          <p className="text-secondary max-w-md">
            This is not documentation. This is a ritual.
          </p>
        </div>

        {/* The goal */}
        <section className="mb-20">
          <div className="wide-container">
            <div className="card-emphasis p-8 md:p-12 max-w-2xl">
              <p className="tag mb-4">The goal</p>
              <p className="text-2xl md:text-3xl font-serif">
                Remove your public email address.
              </p>
              <p className="text-secondary mt-6">
                Everything else is optional. If this happens, adoption sticks. If it doesn't, nothing else matters.
              </p>
            </div>
          </div>
        </section>

        {/* Steps */}
        <section className="mb-20">
          <div className="wide-container">
            <div className="space-y-6">
              {steps.map((step, index) => (
                <div 
                  key={index}
                  className={`p-6 md:p-8 ${step.highlight ? 'card-emphasis' : 'card-subtle'}`}
                >
                  <div className="flex gap-6 md:gap-8">
                    <div className="flex-shrink-0">
                      <span className="step-number text-3xl md:text-4xl">{step.number}</span>
                    </div>
                    <div className="flex-1 pt-1">
                      <h3 className="text-lg mb-2">{step.title}</h3>
                      <p className="text-secondary mb-3">{step.description}</p>
                      {step.detail && (
                        <p className="mono text-sm">{step.detail}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Done state */}
              <div className="p-6 md:p-8 card-subtle bg-surface-2">
                <div className="flex gap-6 md:gap-8">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 md:w-12 md:h-12 bg-foreground text-background flex items-center justify-center">
                      <Check className="w-5 h-5 md:w-6 md:h-6" />
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg mb-2">Done.</h3>
                    <p className="text-secondary">
                      You've created an irreversible moment. The next person who tries to contact you 
                      through that channel will go through Reach instead.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Why this matters */}
        <section className="section-gap border-t border-border">
          <div className="editorial-container">
            <h2 className="mb-8">Why this matters</h2>
            <div className="prose-block space-y-6 text-secondary">
              <p>
                The moment you remove your email from somewhere public, you've made a choice 
                that's hard to undo.
              </p>
              <p>
                The next person who tries to reach you through that channel will encounter 
                something different. They'll have to state their intent. They'll be evaluated. 
                They might not reach you at all.
              </p>
              <p className="text-primary">
                That's not a feature. That's the entire point.
              </p>
            </div>
          </div>
        </section>

        {/* What comes next */}
        <section className="section-gap border-t border-border surface-2">
          <div className="wide-container">
            <div className="editorial-container mb-12 px-0">
              <h2 className="mb-4">What comes next</h2>
              <p className="text-secondary">
                All optional. Do them when you're ready.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 gap-4 max-w-2xl">
              {optional.map((item, index) => (
                <div key={index} className="p-5 card-subtle bg-background">
                  <p className="text-sm">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="section-gap border-t border-border">
          <div className="editorial-container text-center">
            <p className="statement text-secondary mb-12">
              Ready to start?
            </p>
            <Link to="/register">
              <Button size="lg" className="rounded-none gap-3 text-base px-8 py-6">
                Create your identity
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
            <Link to="/replace-email" className="hover:text-primary transition-colors">Replace Email</Link>
            <Link to="/first-10-minutes" className="text-primary">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
