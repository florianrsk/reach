import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { extractErrorMessage } from '../lib/error-utils';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { RefreshCw, Inbox, Clock, CheckCircle, XCircle, MessageSquare, Shield } from 'lucide-react';

export default function DecisionSurface() {
  const { identity } = useAuth();
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending'); // Default view is Pending
  const [stats, setStats] = useState({ total: 0, approved: 0, rejected: 0 });
  const [expandedMessageId, setExpandedMessageId] = useState(null);

  useEffect(() => {
    fetchAttempts();
  }, []);

  const fetchAttempts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/attempts');
      setAttempts(response.data);
      calculateStats(response.data);
    } catch (error) {
      console.error('Failed to fetch attempts:', error);
      toast.error('Failed to load submissions');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (attemptsList) => {
    const total = attemptsList.length;
    const approved = attemptsList.filter(a => a.decision === 'deliver_to_human').length;
    const rejected = attemptsList.filter(a => a.decision === 'reject').length;
    setStats({ total, approved, rejected });
  };

  const handleDecision = async (attemptId, decision) => {
    try {
      await api.put(`/attempts/${attemptId}/decision?decision=${decision}`);
      toast.success('Decision updated');
      fetchAttempts();
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to update decision';
      toast.error(message);
    }
  };

  const handleBlock = async (attemptId) => {
    try {
      // TODO: Implement block endpoint
      await api.post(`/attempts/${attemptId}/block`);
      toast.success('Sender blocked');
      fetchAttempts();
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to block sender';
      toast.error(message);
    }
  };

  const handleAsk = async (attemptId) => {
    try {
      // TODO: Implement ask endpoint
      await api.post(`/attempts/${attemptId}/ask`);
      toast.success('Follow-up question sent');
      fetchAttempts();
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to send question';
      toast.error(message);
    }
  };

  const filteredAttempts = attempts.filter(a => {
    if (filter === 'all') return true;
    if (filter === 'pending') return a.decision === 'queued' || a.decision === 'request_more_context';
    if (filter === 'approved') return a.decision === 'deliver_to_human';
    if (filter === 'rejected') return a.decision === 'reject';
    return true;
  });

  const autoDecidedAttempts = attempts.filter(a => 
    a.ai_classification?.rules_evaluated && 
    !a.manual_override &&
    (a.ai_classification?.final_decision === 'auto_approve' || 
     a.ai_classification?.final_decision === 'auto_reject')
  );

  const pendingAttempts = filteredAttempts.filter(a => a.decision === 'queued' || a.decision === 'request_more_context');

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const truncateMessage = (message, maxLength = 120) => {
    if (!message) return '';
    if (message.length <= maxLength) return message;
    return message.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 animate-in max-w-6xl mx-auto">
        {/* Three numbers at the top - always visible */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Total attempts</p>
                <p className="text-3xl font-serif">{stats.total}</p>
              </div>
              <Inbox className="w-8 h-8 text-muted-foreground/50" />
            </div>
          </div>
          
          <div className="border border-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Approved</p>
                <p className="text-3xl font-serif">{stats.approved}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-muted-foreground/50" />
            </div>
          </div>
          
          <div className="border border-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Rejected</p>
                <p className="text-3xl font-serif">{stats.rejected}</p>
              </div>
              <XCircle className="w-8 h-8 text-muted-foreground/50" />
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex space-x-1 border border-border p-1 w-fit">
            {['all', 'pending', 'approved', 'rejected'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 text-sm transition-colors ${
                  filter === f 
                    ? 'bg-foreground text-background' 
                    : 'hover:bg-muted'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                {f === 'pending' && pendingAttempts.length > 0 && (
                  <span className="ml-2 bg-foreground/20 text-foreground px-1.5 py-0.5 text-xs">
                    {pendingAttempts.length}
                  </span>
                )}
              </button>
            ))}
          </div>
          
          <Button
            variant="outline"
            onClick={fetchAttempts}
            className="rounded-none border-border"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Auto-decided section (if any) */}
        {autoDecidedAttempts.length > 0 && filter === 'all' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-muted-foreground" />
              <h2 className="font-serif text-lg">Auto-decided by rules</h2>
              <span className="text-sm text-muted-foreground ml-2">
                ({autoDecidedAttempts.length})
              </span>
            </div>
            <div className="space-y-4">
              {autoDecidedAttempts.map((attempt) => (
                <SubmissionCard
                  key={attempt.id}
                  attempt={attempt}
                  expandedMessageId={expandedMessageId}
                  setExpandedMessageId={setExpandedMessageId}
                  handleDecision={handleDecision}
                  handleBlock={handleBlock}
                  handleAsk={handleAsk}
                  formatTimeAgo={formatTimeAgo}
                  truncateMessage={truncateMessage}
                  isAutoDecided={true}
                />
              ))}
            </div>
          </div>
        )}

        {/* Main submissions list */}
        <div className="space-y-4">
          {filteredAttempts.length === 0 ? (
            <EmptyState filter={filter} identity={identity} />
          ) : (
            filteredAttempts.map((attempt) => (
              <SubmissionCard
                key={attempt.id}
                attempt={attempt}
                expandedMessageId={expandedMessageId}
                setExpandedMessageId={setExpandedMessageId}
                handleDecision={handleDecision}
                handleBlock={handleBlock}
                handleAsk={handleAsk}
                formatTimeAgo={formatTimeAgo}
                truncateMessage={truncateMessage}
                isAutoDecided={false}
              />
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}

function SubmissionCard({ 
  attempt, 
  expandedMessageId, 
  setExpandedMessageId, 
  handleDecision, 
  handleBlock, 
  handleAsk,
  formatTimeAgo,
  truncateMessage,
  isAutoDecided 
}) {
  const isExpanded = expandedMessageId === attempt.id;
  const message = attempt.payload?.intent || attempt.payload?.reason || '';
  const aiData = attempt.ai_classification || {};
  
  return (
    <div className={`border border-border p-6 space-y-4 ${isAutoDecided ? 'bg-muted/20' : ''}`}>
      {/* Message section */}
      <div>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm mb-2">
              {isExpanded ? message : truncateMessage(message)}
            </p>
            {message.length > 120 && (
              <button
                onClick={() => setExpandedMessageId(isExpanded ? null : attempt.id)}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                {isExpanded ? 'Show less' : 'Read full message'}
              </button>
            )}
          </div>
          <div className="text-sm text-muted-foreground ml-4">
            {formatTimeAgo(attempt.created_at)}
          </div>
        </div>
      </div>

      {/* Metadata chips */}
      <div className="flex flex-wrap gap-2">
        {/* Intent category */}
        {attempt.payload?.intent_category && (
          <span className="text-xs px-2 py-1 border border-border">
            {attempt.payload.intent_category}
          </span>
        )}
        
        {/* Time requirement */}
        {attempt.payload?.time_requirement && (
          <span className="text-xs px-2 py-1 border border-border">
            {attempt.payload.time_requirement === 'conversation' ? 'Wants a conversation' : 
             attempt.payload.time_requirement === 'read' ? 'Just a read' : 
             'Wants a reply'}
          </span>
        )}
        
        {/* Deposit status */}
        {attempt.payment_status === 'completed' && (
          <span className="text-xs px-2 py-1 border border-border">
            Paid ${attempt.payment_amount}
          </span>
        )}
        {attempt.payment_status === 'pending' && (
          <span className="text-xs px-2 py-1 border border-border">
            Payment pending
          </span>
        )}
        
        {/* Auto-decided badge */}
        {isAutoDecided && (
          <span className="text-xs px-2 py-1 border border-border bg-muted">
            Auto-{aiData.final_decision?.replace('auto_', '')}d by rules
          </span>
        )}
      </div>

      {/* Rules that triggered */}
      {aiData.triggered_rules && aiData.triggered_rules.length > 0 && (
        <div className="text-sm">
          <p className="text-muted-foreground mb-1">Rules matched:</p>
          <div className="space-y-1">
            {aiData.triggered_rules.map((rule, index) => (
              <div key={index} className="text-sm">
                • {rule.rule} → suggested {rule.action}
              </div>
            ))}
          </div>
        </div>
      )}
      {aiData.rules_evaluated && (!aiData.triggered_rules || aiData.triggered_rules.length === 0) && (
        <div className="text-sm text-muted-foreground">
          No rules triggered → queued for review
        </div>
      )}

      {/* AI reasoning */}
      {aiData.reasoning_summary && (
        <div className="text-sm text-muted-foreground border-t border-border pt-3">
          {aiData.reasoning_summary}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 pt-3 border-t border-border">
        <Button
          onClick={() => handleDecision(attempt.id, 'deliver_to_human')}
          variant="outline"
          className="rounded-none border-border"
          disabled={attempt.decision === 'deliver_to_human'}
        >
          Let through
        </Button>
        
        <Button
          onClick={() => handleDecision(attempt.id, 'reject')}
          variant="outline"
          className="rounded-none border-border"
          disabled={attempt.decision === 'reject'}
        >
          Pass
        </Button>
        
        <Button
          onClick={() => handleAsk(attempt.id)}
          variant="outline"
          className="rounded-none border-border"
        >
          <MessageSquare className="w-4 h-4 mr-2" />
          Ask
        </Button>
        
        <Button
          onClick={() => handleBlock(attempt.id)}
          variant="outline"
          className="rounded-none border-border"
        >
          <Shield className="w-4 h-4 mr-2" />
          Block
        </Button>
      </div>
    </div>
  );
}

function EmptyState({ filter, identity }) {
  const reachLink = identity ? `/${identity.handle}` : '/your-handle';
  const fullReachLink = identity ? `${window.location.origin}/r/${identity.handle}` : '';
  
  const copyLink = () => {
    if (fullReachLink) {
      navigator.clipboard.writeText(fullReachLink);
      toast.success('Link copied');
    }
  };
  
  return (
    <div className="border border-border p-12 text-center">
      <Inbox className="w-12 h-12 mx-auto mb-4 text-muted-foreground/30" />
      {filter === 'pending' ? (
        <>
          <h3 className="font-serif text-lg mb-2">Nothing waiting. You're clear.</h3>
          <p className="text-muted-foreground mb-6">
            When someone tries to reach you, they'll appear here for your decision.
          </p>
          <div className="flex items-center justify-center gap-2 max-w-md mx-auto">
            <code className="text-sm bg-background border border-border px-3 py-2 flex-1 text-left truncate">
              {reachLink}
            </code>
            {fullReachLink && (
              <Button
                variant="outline"
                onClick={copyLink}
                className="rounded-none border-border"
                size="sm"
              >
                Copy
              </Button>
            )}
          </div>
        </>
      ) : filter === 'approved' ? (
        <>
          <h3 className="font-serif text-lg mb-2">No approved requests yet</h3>
          <p className="text-muted-foreground mb-6">
            Approved requests will appear here once you let them through.
          </p>
          <div className="border border-dashed border-border p-5 mb-6 opacity-60 max-w-md mx-auto">
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
          <p className="text-sm text-tertiary">
            This is what an approved request looks like
          </p>
        </>
      ) : filter === 'all' ? (
        <>
          <h3 className="font-serif text-lg mb-2">No submissions yet</h3>
          <p className="text-muted-foreground mb-6">
            Share your reach link to start receiving requests.
          </p>
          <div className="flex items-center justify-center gap-2 max-w-md mx-auto">
            <code className="text-sm bg-background border border-border px-3 py-2 flex-1 text-left truncate">
              {reachLink}
            </code>
            {fullReachLink && (
              <Button
                variant="outline"
                onClick={copyLink}
                className="rounded-none border-border"
                size="sm"
              >
                Copy
              </Button>
            )}
          </div>
        </>
      ) : (
        <>
          <h3 className="font-serif text-lg mb-2">No {filter} submissions</h3>
          <p className="text-muted-foreground">Try changing the filter to see other submissions.</p>
        </>
      )}
    </div>
  );
}