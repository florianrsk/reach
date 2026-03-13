import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { RefreshCw, Inbox, ChevronRight } from 'lucide-react';

export default function Attempts() {
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedAttempt, setSelectedAttempt] = useState(null);

  useEffect(() => {
    fetchAttempts();
  }, []);

  const fetchAttempts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/attempts');
      setAttempts(response.data);
    } catch (error) {
      console.error('Failed to fetch attempts:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateDecision = async (attemptId, decision) => {
    try {
      await api.put(`/attempts/${attemptId}/decision?decision=${decision}`);
      toast.success('Decision updated');
      fetchAttempts();
      setSelectedAttempt(null);
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to update';
      toast.error(message);
    }
  };

  const filteredAttempts = attempts.filter(a => {
    if (filter === 'all') return true;
    if (filter === 'pending') return ['queue', 'request_payment'].includes(a.decision);
    if (filter === 'delivered') return a.decision === 'deliver_to_human';
    if (filter === 'rejected') return a.decision === 'reject';
    return true;
  });

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
      <div className="space-y-6 animate-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-serif mb-1">Reach Attempts</h1>
            <p className="text-muted-foreground">
              {attempts.length} total attempts
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-40 rounded-none" data-testid="filter-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="delivered">Delivered</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
            
            <Button
              variant="outline"
              size="icon"
              onClick={fetchAttempts}
              className="rounded-none"
              data-testid="refresh-btn"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Attempts List */}
        {filteredAttempts.length === 0 ? (
          <div className="border border-border p-8">
            <div className="max-w-lg mx-auto">
              <Inbox className="w-12 h-12 mx-auto mb-4 text-muted-foreground/30" />
              <h3 className="font-serif text-lg mb-3 text-center">
                {filter === 'all' ? 'No reach attempts yet' : `No ${filter} attempts`}
              </h3>
              <p className="text-sm text-muted-foreground mb-6 text-center">
                {filter === 'all' 
                  ? "When someone tries to reach you, you'll see them here"
                  : "Try changing the filter to see other attempts."}
              </p>
              
              {/* Sample ghost attempt card for visual preview */}
              {filter === 'all' && (
                <div className="border border-dashed border-border p-5 mb-6 opacity-60">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <span className="text-xs px-2 py-0.5 bg-muted text-muted-foreground">
                          collaboration
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-foreground text-background">
                          deliver to human
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-muted text-muted-foreground">
                          92% confidence
                        </span>
                      </div>
                      <p className="text-sm truncate mb-1">Interested in collaborating on a new project</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span>sender@example.com</span>
                        <span>Just now</span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="border border-border divide-y divide-border">
            {filteredAttempts.map((attempt) => (
              <div
                key={attempt.id}
                className="p-4 hover:bg-muted/30 transition-colors cursor-pointer flex items-center justify-between gap-4"
                onClick={() => setSelectedAttempt(attempt)}
                data-testid={`attempt-row-${attempt.id}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-xs px-2 py-0.5 bg-muted text-muted-foreground">
                      {attempt.ai_classification?.intent_type || 'unknown'}
                    </span>
                    <span className={`text-xs px-2 py-0.5 ${
                      attempt.decision === 'deliver_to_human' ? 'bg-foreground text-background' :
                      attempt.decision === 'reject' ? 'bg-muted text-muted-foreground line-through' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      {attempt.decision.replace(/_/g, ' ')}
                    </span>
                    {attempt.payment_status === 'completed' && (
                      <span className="text-xs px-2 py-0.5 bg-foreground text-background">
                        Paid ${attempt.payment_amount}
                      </span>
                    )}
                  </div>
                  
                  <p className="font-medium mb-1 truncate">
                    {attempt.payload?.intent}
                  </p>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    {attempt.payload?.reason}
                  </p>
                  
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span>{attempt.sender_context?.email || 'Anonymous'}</span>
                    <span>{new Date(attempt.created_at).toLocaleString()}</span>
                  </div>
                </div>
                
                <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              </div>
            ))}
          </div>
        )}

        {/* Attempt Detail Dialog */}
        <Dialog open={!!selectedAttempt} onOpenChange={() => setSelectedAttempt(null)}>
          <DialogContent className="rounded-none max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-serif text-xl">Reach Attempt</DialogTitle>
            </DialogHeader>
            
            {selectedAttempt && (
              <div className="space-y-6 mt-4">
                {/* Status */}
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 bg-muted text-muted-foreground">
                    {selectedAttempt.ai_classification?.intent_type || 'unknown'}
                  </span>
                  <span className={`text-xs px-2 py-1 ${
                    selectedAttempt.decision === 'deliver_to_human' ? 'bg-foreground text-background' :
                    selectedAttempt.decision === 'reject' ? 'bg-muted text-muted-foreground' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {selectedAttempt.decision.replace(/_/g, ' ')}
                  </span>
                  {selectedAttempt.ai_classification?.confidence && (
                    <span className="text-xs px-2 py-1 bg-muted text-muted-foreground">
                      {Math.round(selectedAttempt.ai_classification.confidence * 100)}% confidence
                    </span>
                  )}
                </div>

                {/* Sender Info */}
                <div>
                  <h3 className="text-sm font-medium mb-2">Sender</h3>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <p>Email: {selectedAttempt.sender_context?.email || 'Anonymous'}</p>
                    <p>Name: {selectedAttempt.sender_context?.name || 'Unknown'}</p>
                  </div>
                </div>

                {/* Payload */}
                <div>
                  <h3 className="text-sm font-medium mb-2">Request</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-muted-foreground">Intent</span>
                      <p className="text-sm">{selectedAttempt.payload?.intent}</p>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">Reason</span>
                      <p className="text-sm">{selectedAttempt.payload?.reason}</p>
                    </div>
                    {selectedAttempt.payload?.message && (
                      <div>
                        <span className="text-xs text-muted-foreground">Message</span>
                        <p className="text-sm whitespace-pre-wrap">{selectedAttempt.payload.message}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* AI Rationale */}
                <div className="p-4 bg-muted/50 border border-border">
                  <h3 className="text-sm font-medium mb-2">AI Decision</h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedAttempt.rationale || 'No rationale provided.'}
                  </p>
                </div>

                {/* Actions */}
                {['queue', 'request_payment'].includes(selectedAttempt.decision) && (
                  <div className="flex gap-2 pt-4 border-t border-border">
                    <Button
                      variant="default"
                      className="flex-1 rounded-none"
                      onClick={() => updateDecision(selectedAttempt.id, 'deliver_to_human')}
                      data-testid="approve-btn"
                    >
                      Deliver
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1 rounded-none"
                      onClick={() => updateDecision(selectedAttempt.id, 'reject')}
                      data-testid="reject-btn"
                    >
                      Reject
                    </Button>
                  </div>
                )}

                {/* Timestamp */}
                <p className="text-xs text-muted-foreground">
                  Received: {new Date(selectedAttempt.created_at).toLocaleString()}
                </p>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
