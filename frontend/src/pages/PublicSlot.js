import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { ArrowLeft, DollarSign, CheckCircle, XCircle, Clock, Send, AlertCircle, User, Link as LinkIcon } from 'lucide-react';

export default function PublicSlot() {
  const { handle, slot: slotName } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({
    message: '',
    intent_category: '',
    time_requirement: '',
    challenge_answer: ''
  });
  const [showChallenge, setShowChallenge] = useState(false);
  const [showTimeSignal, setShowTimeSignal] = useState(false);

  useEffect(() => {
    // If a slot name is specified, redirect to Face page (slots are deprecated)
    if (slotName && slotName !== 'open') {
      navigate(`/r/${handle}`, { replace: true });
      return;
    }
    fetchData();
  }, [handle, slotName, navigate]);

  const fetchData = async () => {
    try {
      // Use Face-based endpoint instead of slot endpoint
      const response = await api.get(`/reach/${handle}`);
      setData(response.data);
    } catch (error) {
      setError(extractErrorMessage(error) || 'Reach page not found');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!form.message) {
      toast.error('Please write a message');
      return;
    }

    if (form.message.length < 10) {
      toast.error('Message must be at least 10 characters');
      return;
    }

    setSubmitting(true);
    try {
      // Use Face-based endpoint instead of slot endpoint
      const payload = {
        message: form.message.trim(),
        ...(form.intent && { intent_category: form.intent }),
        ...(form.reason && { time_requirement: form.reason }),
        ...(form.sender_email && { sender_email: form.sender_email.trim() }),
        ...(form.sender_name && { sender_name: form.sender_name.trim() })
      };
      
      const response = await api.post(`/reach/${handle}/message`, payload);
      setResult(response.data);
      toast.success('Message sent successfully');
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to send message';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const initiatePayment = async () => {
    if (!result?.id) return;
    
    try {
      const response = await api.post('/payments/checkout', {
        reach_attempt_id: result.id,
        origin_url: window.location.origin
      });
      
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      toast.error('Failed to initiate payment');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center">
          <h1 className="text-4xl font-serif mb-2">404</h1>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Link to={`/r/${handle}`} className="text-foreground hover:underline">
            View all slots
          </Link>
        </div>
      </div>
    );
  }

  // Result view with decision transparency
  if (result) {
    const getResultIcon = () => {
      switch (result.decision) {
        case 'deliver_to_human':
          return <CheckCircle className="w-12 h-12" />;
        case 'reject':
          return <XCircle className="w-12 h-12" />;
        case 'request_payment':
          return <DollarSign className="w-12 h-12" />;
        default:
          return <Clock className="w-12 h-12" />;
      }
    };

    const getResultTitle = () => {
      switch (result.decision) {
        case 'deliver_to_human':
          return 'Delivered';
        case 'reject':
          return 'Not Accepted';
        case 'request_payment':
          return 'Payment Required';
        case 'queue':
          return 'Queued for Review';
        case 'auto_respond':
          return 'Auto Response';
        default:
          return 'Processed';
      }
    };

    const getResultDescription = () => {
      switch (result.decision) {
        case 'deliver_to_human':
          return `Your request has been delivered to ${handle}. They will see your message.`;
        case 'reject':
          return `Based on the evaluation, this request was not accepted.`;
        case 'request_payment':
          return `${handle} requires payment for this type of reach. This filters for serious intent.`;
        case 'queue':
          return `Your request is queued for ${handle}'s review. They'll see it when they check their dashboard.`;
        default:
          return 'Your request has been processed.';
      }
    };

    return (
      <div className="min-h-screen bg-background">
        <header className="border-b border-border">
          <div className="max-w-[600px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
            <Link to="/" className="text-xl font-serif">Reach</Link>
            <span className="text-sm text-muted-foreground mono">
              /{handle}/{slotName}
            </span>
          </div>
        </header>

        <main className="max-w-[600px] mx-auto px-4 sm:px-6 py-8 sm:py-12">
          <div className="text-center py-8 sm:py-12" data-testid="result-view">
            <div className="text-muted-foreground mb-4">
              {getResultIcon()}
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif mt-6 mb-2" data-testid="result-title">
              {getResultTitle()}
            </h1>
            <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
              {getResultDescription()}
            </p>

            {/* Decision Transparency */}
            <div className="text-left border border-border p-4 sm:p-6 mb-6 bg-muted/30">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                How this was decided
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Your intent:</span>
                  <span className="capitalize">{form.intent}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">AI classification:</span>
                  <span className="capitalize">{result.ai_classification?.intent_type || 'unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Confidence:</span>
                  <span>{Math.round((result.ai_classification?.confidence || 0) * 100)}%</span>
                </div>
                <div className="pt-3 border-t border-border">
                  <span className="text-muted-foreground">Rationale:</span>
                  <p className="mt-1 text-foreground" data-testid="result-rationale">
                    {result.rationale}
                  </p>
                </div>
              </div>
            </div>

            {result.decision === 'request_payment' && result.payment_amount && (
              <div className="mb-8">
                <p className="text-lg mb-4">
                  Amount: <span className="font-medium">${result.payment_amount}</span>
                </p>
                <Button
                  onClick={initiatePayment}
                  className="rounded-none gap-2"
                  data-testid="pay-btn"
                >
                  <DollarSign className="w-4 h-4" />
                  Pay to Reach
                </Button>
              </div>
            )}

            {result.auto_response && (
              <div className="border border-border p-6 text-left mt-8">
                <p className="text-sm text-muted-foreground mb-2">Auto Response:</p>
                <p>{result.auto_response}</p>
              </div>
            )}

            <div className="mt-8">
              <Link
                to={`/r/${handle}`}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                ← Back to {handle}'s reach page
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-[600px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-serif">Reach</Link>
          <span className="text-sm text-muted-foreground mono">
            /{handle}/{slotName}
          </span>
        </div>
      </header>

      <main className="max-w-[600px] mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* Back link */}
        <Link
          to={`/r/${handle}`}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6 sm:mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to {handle}
        </Link>

        {/* Identity Header */}
        <div className="flex flex-col md:flex-row gap-6 mb-8">
          {data.identity.photo_url && (
            <img
              src={data.identity.photo_url}
              alt={data.identity.display_name}
              className="w-24 h-24 md:w-32 md:h-32 object-cover rounded-none flex-shrink-0"
            />
          )}
          <div>
            <h1 className="text-4xl md:text-5xl font-serif mb-2">{data.identity.display_name}</h1>
            <p className="text-xl text-secondary mb-4">{data.identity.headline}</p>
            {data.identity.current_focus && (
              <p className="text-muted-foreground mb-2">{data.identity.current_focus}</p>
            )}
            {data.identity.availability_signal && (
              <p className="text-sm text-tertiary flex items-center gap-2">
                <Clock className="w-3 h-3" />
                {data.identity.availability_signal}
              </p>
            )}
          </div>
        </div>

        {/* Links */}
        {data.identity.links && data.identity.links.length > 0 && (
          <div className="flex flex-wrap gap-3 mb-8">
            {data.identity.links.map((link, index) => (
              <a
                key={index}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 border hover:bg-muted transition-colors rounded-none text-sm"
              >
                <LinkIcon className="w-3 h-3" />
                {link.label}
              </a>
            ))}
          </div>
        )}

        {/* Prompt */}
        <div className="mb-8">
          <h2 className="text-2xl font-serif mb-4">{data.identity.prompt}</h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="intent">Intent *</Label>
            <Select
              value={form.intent}
              onValueChange={(value) => setForm(prev => ({ ...prev, intent: value }))}
            >
              <SelectTrigger className="rounded-none" data-testid="intent-select">
                <SelectValue placeholder="Select your intent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="business">Business Inquiry</SelectItem>
                <SelectItem value="personal">Personal</SelectItem>
                <SelectItem value="press">Press / Media</SelectItem>
                <SelectItem value="collaboration">Collaboration</SelectItem>
                <SelectItem value="support">Support / Help</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">Reason *</Label>
            <Input
              id="reason"
              value={form.reason}
              onChange={(e) => setForm(prev => ({ ...prev, reason: e.target.value }))}
              placeholder="Why are you reaching out?"
              className="rounded-none"
              required
              data-testid="reason-input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="message">Message (optional)</Label>
            <Textarea
              id="message"
              value={form.message}
              onChange={(e) => setForm(prev => ({ ...prev, message: e.target.value }))}
              placeholder="Additional details..."
              className="rounded-none resize-none"
              rows={4}
              data-testid="message-input"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sender_name">Your Name</Label>
              <Input
                id="sender_name"
                value={form.sender_name}
                onChange={(e) => setForm(prev => ({ ...prev, sender_name: e.target.value }))}
                placeholder="Optional"
                className="rounded-none"
                data-testid="sender-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sender_email">Your Email</Label>
              <Input
                id="sender_email"
                type="email"
                value={form.sender_email}
                onChange={(e) => setForm(prev => ({ ...prev, sender_email: e.target.value }))}
                placeholder="For confirmation"
                className="rounded-none"
                data-testid="sender-email-input"
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full rounded-none gap-2"
            disabled={submitting}
            data-testid="submit-reach-btn"
          >
            <Send className="w-4 h-4" />
            {submitting ? 'Submitting...' : 'Submit Request'}
          </Button>

          <p className="text-xs text-muted-foreground text-center">
            Your request will be evaluated by AI and rules. 
            The outcome will be displayed immediately.
          </p>
        </form>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 mt-8">
        <div className="max-w-[600px] mx-auto px-4 sm:px-6 text-center">
          <p className="text-sm text-muted-foreground">
            Powered by <Link to="/" className="hover:text-foreground">Reach</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}