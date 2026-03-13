import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowRight } from 'lucide-react';

export default function Why() {
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

      {/* Essay content */}
      <article className="pt-32 pb-24">
        <div className="editorial-container">
          {/* Title */}
          <header className="mb-20 stagger">
            <p className="tag mb-6">Philosophy</p>
            <h1 className="mb-6">
              Email is an accident.<br />
              Reach is a choice.
            </h1>
          </header>

          {/* Essay body */}
          <div className="prose-block space-y-8 text-secondary animate-in" style={{ animationDelay: '200ms' }}>
            <p>
              Somewhere along the way, we accepted that anyone with our email address 
              could interrupt our day.
            </p>

            <p>
              Cold pitches. Newsletters we never signed up for. "Quick syncs" from strangers. 
              Recruiters who didn't read our profile. PR blasts. Follow-ups to follow-ups.
            </p>

            <p>
              We called this "being reachable."
            </p>

            <p className="text-primary text-lg">
              It's not reachability. It's surrender.
            </p>
          </div>

          {/* Section break */}
          <div className="my-20 divider" />

          {/* The Problem */}
          <section className="mb-20">
            <h2 className="mb-8">The inbox is broken by design</h2>
            <div className="prose-block space-y-6 text-secondary">
              <p>
                Email was designed for one thing: delivery. It optimizes for the sender. 
                If they know your address, they can reach you. Period.
              </p>
              <p>
                There's no gate. No filter. No cost. No consequence.
              </p>
              <p>
                The burden is on you—the receiver—to sort, delete, ignore, unsubscribe, 
                and maintain the endless wall against noise.
              </p>
              <p className="text-primary">
                This is backwards.
              </p>
            </div>
          </section>

          {/* Pull quote */}
          <blockquote className="my-20 py-12 border-y border-border">
            <p className="pullquote text-center max-w-xl mx-auto">
              Being reachable is a right.<br />
              Being interruptive is not.
            </p>
          </blockquote>

          {/* The Shift */}
          <section className="mb-20">
            <h2 className="mb-8">What if reaching someone required intention?</h2>
            <div className="prose-block space-y-6 text-secondary">
              <p>
                Not a password. Not a paywall. Just intention.
              </p>
              <p>
                What if every attempt to reach you was evaluated? Not by you—you're 
                too busy for that—but by logic you defined once and forgot about.
              </p>
              <p>
                What if most attempts never reached you at all?
              </p>
              <p>
                What if the few that did were pre-qualified, categorized, and 
                summarized before you ever saw them?
              </p>
              <p className="text-primary">
                This isn't filtering email. This is replacing the entire model.
              </p>
            </div>
          </section>

          {/* Section break */}
          <div className="my-20 divider" />

          {/* What Changes */}
          <section className="mb-20">
            <h2 className="mb-12">What changes</h2>
            <div className="space-y-12">
              <div>
                <h3 className="text-primary mb-3">You stop publishing your email.</h3>
                <p className="text-secondary">
                  On your website, your bio, your profile—everywhere you've been 
                  inviting interruption. You replace it with a reach link.
                </p>
              </div>
              <div>
                <h3 className="text-primary mb-3">Senders explain themselves.</h3>
                <p className="text-secondary">
                  Not in a long message. In structured intent. Why are they reaching out? 
                  What do they want? Are they willing to pay for your attention?
                </p>
              </div>
              <div>
                <h3 className="text-primary mb-3">Rules decide, not you.</h3>
                <p className="text-secondary">
                  You set the logic once. Business inquiry from a verified domain? 
                  Let it through. Cold sales pitch? Reject. Unknown intent but willing 
                  to pay $25? Maybe worth a look.
                </p>
              </div>
              <div>
                <h3 className="text-primary mb-3">You see decisions, not noise.</h3>
                <p className="text-secondary">
                  No inbox to manage. No unread count. Just a feed of what made it 
                  through, with AI summaries and rationales.
                </p>
              </div>
            </div>
          </section>

          {/* Section break */}
          <div className="my-20 divider" />

          {/* Who This Is For */}
          <section className="mb-20">
            <h2 className="mb-8">Who this is for</h2>
            <div className="prose-block space-y-6 text-secondary">
              <p>
                People who create. People who build. People whose attention has value.
              </p>
              <p>
                People who are tired of being the last line of defense against 
                the entire internet.
              </p>
              <p>
                People who believe they should be reachable—but on their terms.
              </p>
            </div>
          </section>

          {/* Who This Is Not For */}
          <section className="mb-20">
            <h2 className="mb-8">Who this is not for</h2>
            <div className="prose-block space-y-6 text-secondary">
              <p>
                People who want more engagement, more inbound, more "opportunities."
              </p>
              <p>
                People who measure success by how many people contact them.
              </p>
              <p>
                People who haven't yet realized that attention is finite.
              </p>
            </div>
          </section>

          {/* Closing */}
          <section className="my-20 py-12 border-y border-border">
            <div className="prose-block">
              <p className="text-secondary mb-4">
                We didn't set out to fix email.
              </p>
              <p className="statement text-primary">
                We set out to make being reachable intentional again.
              </p>
            </div>
          </section>

          {/* CTA - only at the end */}
          <div className="pt-8">
            <Link to="/register">
              <Button size="lg" className="rounded-none gap-3 text-base px-8 py-6">
                Create your reach link
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </article>

      {/* Footer */}
      <footer className="py-12 border-t border-border">
        <div className="wide-container flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <span className="font-serif">Reach</span>
          <div className="flex gap-8 text-sm text-secondary">
            <Link to="/why" className="text-primary">Why</Link>
            <Link to="/replace-email" className="hover:text-primary transition-colors">Replace Email</Link>
            <Link to="/first-10-minutes" className="hover:text-primary transition-colors">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
