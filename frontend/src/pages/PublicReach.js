import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import { toast } from 'sonner';
import { Send, User, Link as LinkIcon, Clock, CheckCircle, Lock, DollarSign, Eye } from 'lucide-react';

export default function PublicReach() {
  const { handle } = useParams();
  const [searchParams] = useSearchParams();
  const isPreview = searchParams.get('preview') === 'true';
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  
  // Module states
  const [showChallenge, setShowChallenge] = useState(false);
  const [challengeAnswer, setChallengeAnswer] = useState('');
  const [showTimeSignal, setShowTimeSignal] = useState(false);
  const [timeRequirement, setTimeRequirement] = useState('');
  const [waitingPeriodActive, setWaitingPeriodActive] = useState(false);
  const [waitingTimeLeft, setWaitingTimeLeft] = useState(0);
  const [selectedIntent, setSelectedIntent] = useState('');

  useEffect(() => {
    fetchData();
  }, [handle]);

  useEffect(() => {
    // Handle waiting period
    if (data?.modules?.waiting_period?.enabled && !isPreview) {
      const seconds = data.modules.waiting_period.seconds || 30;
      setWaitingPeriodActive(true);
      setWaitingTimeLeft(seconds);
      
      const timer = setInterval(() => {
        setWaitingTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            setWaitingPeriodActive(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [data, isPreview]);

  const fetchData = async () => {
    try {
      const response = await api.get(`/reach/${handle}`);
      setData(response.data);
      
      // Check if challenge question should be shown
      if (response.data.modules?.challenge_question?.enabled && !isPreview) {
        setShowChallenge(true);
      }
    } catch (error) {
      const errorMsg = extractErrorMessage(error);
      setError(errorMsg || 'This reach link doesn\'t exist yet.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check challenge question
    if (showChallenge && !challengeAnswer.trim()) {
      toast.error('Please answer the question');
      return;
    }

    if (!message.trim()) {
      toast.error('Please write a message');
      return;
    }

    if (message.length < 10) {
      toast.error('Message must be at least 10 characters');
      return;
    }

    // Check time signal
    if (data?.modules?.time_signal?.enabled && !timeRequirement && !isPreview) {
      setShowTimeSignal(true);
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        message: message.trim(),
        ...(challengeAnswer && { challenge_answer: challengeAnswer.trim() }),
        ...(timeRequirement && { time_requirement: timeRequirement }),
        ...(selectedIntent && { intent_category: selectedIntent })
      };

      const response = await api.post(`/reach/${handle}/message`, payload);
      
      setSubmitted(true);
      toast.success(response.data.message || 'Message sent');
    } catch (error) {
      const errorMsg = extractErrorMessage(error) || 'Failed to send message';
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTimeSignalSelect = (requirement) => {
    setTimeRequirement(requirement);
    setShowTimeSignal(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <h1 className="text-3xl font-serif mb-4">This reach link doesn't exist yet.</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <div className="text-sm text-tertiary">
            Powered by <span className="text-secondary">Reach</span>
          </div>
        </div>
      </div>
    );
  }

  const identity = data?.identity;
  const modules = data?.modules || {};

  if (submitted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-foreground text-background flex items-center justify-center mx-auto mb-6 rounded-none">
            <Send className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-serif mb-4">Your message reached {identity.display_name}.</h1>
          <p className="text-lg text-secondary mb-8">
            {identity.availability_signal.includes('check') 
              ? identity.availability_signal.replace('I check', 'They check').replace('check this', 'check their reach')
              : identity.availability_signal.replace('I', 'They')} and will respond if it's a fit.
          </p>
          <div className="text-sm text-tertiary">
            Powered by <span className="text-secondary">Reach</span>
          </div>
        </div>
      </div>
    );
  }

  // Show time signal modal
  if (showTimeSignal) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <Clock className="w-12 h-12 mx-auto mb-6 text-secondary" />
          <h1 className="text-2xl font-serif mb-4">How much time do you need?</h1>
          <p className="text-muted-foreground mb-8">This helps {identity.display_name} prioritize their queue.</p>
          
          <div className="space-y-3">
            {['Just a read', 'A reply', 'A conversation'].map((option) => (
              <button
                key={option}
                onClick={() => handleTimeSignalSelect(option)}
                className="w-full p-4 border text-left hover:bg-muted transition-colors rounded-none"
              >
                {option}
              </button>
            ))}
          </div>
          
          <p className="text-xs text-muted-foreground mt-6">
            Choose within 2 seconds for best experience
          </p>
        </div>
      </div>
    );
  }

  // Show challenge question
  if (showChallenge) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <Lock className="w-12 h-12 mx-auto mb-6 text-secondary" />
          <h1 className="text-2xl font-serif mb-4">Before we begin...</h1>
          <p className="text-lg mb-8">{modules.challenge_question.question}</p>
          
          <textarea
            value={challengeAnswer}
            onChange={(e) => setChallengeAnswer(e.target.value)}
            placeholder="Type your answer here..."
            className="w-full p-4 border rounded-none resize-none min-h-[120px] mb-6"
            autoFocus
          />
          
          <button
            onClick={() => {
              if (challengeAnswer.trim()) {
                setShowChallenge(false);
              } else {
                toast.error('Please answer the question');
              }
            }}
            className="w-full p-4 bg-foreground text-background font-medium rounded-none hover:opacity-90 transition-opacity"
          >
            Continue to message
          </button>
          
          <p className="text-xs text-muted-foreground mt-6">
            This helps ensure genuine connections
          </p>
        </div>
      </div>
    );
  }

  // Show deposit notice if enabled
  const showDepositNotice = modules.deposit?.enabled && !isPreview;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto">
        {/* Preview notice */}
        {isPreview && (
          <div className="mb-6 p-4 border border-yellow-200 bg-yellow-50 text-yellow-800 rounded-none">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              <span className="font-medium">Preview Mode</span>
            </div>
            <p className="text-sm mt-1">You're viewing how your page appears to senders.</p>
          </div>
        )}

        {/* Waiting period notice */}
        {waitingPeriodActive && (
          <div className="mb-6 p-4 border border-blue-200 bg-blue-50 text-blue-800 rounded-none text-center">
            <Clock className="w-4 h-4 inline-block mr-2" />
            <span>Please take a moment to read {identity.display_name}'s page. The message box will appear in {waitingTimeLeft} seconds.</span>
          </div>
        )}

        {/* Header with photo */}
        <div className="flex flex-col md:flex-row gap-6 mb-8">
          {identity.photo_url && (
            <img
              src={identity.photo_url}
              alt={identity.display_name}
              className="w-24 h-24 md:w-32 md:h-32 object-cover rounded-none flex-shrink-0"
            />
          )}
          <div>
            <h1 className="text-4xl md:text-5xl font-serif mb-2">{identity.display_name}</h1>
            <p className="text-xl text-secondary mb-4">{identity.headline}</p>
            {identity.current_focus && (
              <p className="text-muted-foreground mb-2">{identity.current_focus}</p>
            )}
            {identity.availability_signal && (
              <p className="text-sm text-tertiary flex items-center gap-2">
                <Clock className="w-3 h-3" />
                {identity.availability_signal}
              </p>
            )}
          </div>
        </div>

        {/* Links */}
        {identity.links && identity.links.length > 0 && (
          <div className="flex flex-wrap gap-3 mb-8">
            {identity.links.map((link, index) => (
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

        {/* Deposit notice */}
        {showDepositNotice && (
          <div className="mb-8 p-6 border rounded-none bg-muted/30">
            <div className="flex items-start gap-3">
              <DollarSign className="w-5 h-5 text-secondary mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-serif text-lg mb-2">Response commitment</h3>
                <p className="text-muted-foreground">
                  {identity.display_name} commits to responding within {modules.deposit.response_days} days. 
                  A small deposit of ${modules.deposit.amount_usd} is held until they respond — fully returned when they do.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Prompt */}
        <div className="mb-8">
          <h2 className="text-2xl font-serif mb-4">{identity.prompt}</h2>
          
          {/* Intent categories */}
          {modules.intent_categories?.enabled && modules.intent_categories.categories?.length > 0 && (
            <div className="mb-6">
              <p className="text-sm text-muted-foreground mb-3">Suggested categories (optional):</p>
              <div className="flex flex-wrap gap-2">
                {modules.intent_categories.categories.slice(0, 8).map((category, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedIntent(category)}
                    className={`px-3 py-1.5 text-sm border rounded-none transition-colors ${
                      selectedIntent === category 
                        ? 'bg-foreground text-background border-foreground' 
                        : 'hover:bg-muted'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message form */}
          {!waitingPeriodActive && (
            <form onSubmit={handleSubmit}>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Write your message here..."
                className="w-full p-6 border rounded-none resize-none min-h-[200px] mb-6 text-lg"
                disabled={submitting}
                autoFocus={!showChallenge}
              />
              
              <div className="flex justify-between items-center">
                <div className="text-sm text-muted-foreground">
                  {message.length < 10 ? (
                    <span>At least {10 - message.length} more characters needed</span>
                  ) : (
                    <span>{message.length} characters</span>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={submitting || message.length < 10}
                  className="px-8 py-3 bg-foreground text-background font-medium rounded-none hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {submitting ? (
                    <>Sending...</>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send message
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="pt-8 border-t text-center text-sm text-tertiary">
          Powered by <span className="text-secondary">Reach</span>
          {isPreview && (
            <div className="mt-2">
              <a href="/settings" className="text-secondary hover:underline">
                Return to settings
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}