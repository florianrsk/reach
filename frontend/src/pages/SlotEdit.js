import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import { ArrowLeft, Save, ExternalLink } from 'lucide-react';

export default function SlotEdit() {
  const { slotId } = useParams();
  const { identity } = useAuth();
  const navigate = useNavigate();
  const [slot, setSlot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    description: '',
    visibility: 'public',
    requirePayment: false,
    paymentAmount: '',
    defaultAction: 'queue'
  });

  useEffect(() => {
    fetchSlot();
  }, [slotId]);

  const fetchSlot = async () => {
    try {
      const response = await api.get(`/slots/${slotId}`);
      const data = response.data;
      setSlot(data);
      setForm({
        description: data.description,
        visibility: data.visibility,
        requirePayment: !!data.reach_policy?.payment_amount,
        paymentAmount: data.reach_policy?.payment_amount?.toString() || '',
        defaultAction: data.reach_policy?.actions?.default || 'queue'
      });
    } catch (error) {
      toast.error('Slot not found');
      navigate('/slots');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Update slot details
      await api.put(`/slots/${slotId}`, {
        description: form.description,
        visibility: form.visibility
      });

      // Update policy
      await api.put(`/slots/${slotId}/policy`, {
        conditions: [],
        actions: { default: form.defaultAction },
        fallback: 'queue',
        payment_amount: form.requirePayment ? parseFloat(form.paymentAmount) : null
      });

      toast.success('Slot updated');
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to save';
      toast.error(message);
    } finally {
      setSaving(false);
    }
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
      <div className="max-w-2xl animate-in">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/slots')}
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-serif flex items-center gap-2">
              <span className="mono text-muted-foreground">/</span>
              {slot?.name}
            </h1>
            {slot?.visibility === 'public' && (
              <a
                href={`/r/${identity?.handle}/${slot?.name}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mt-1"
              >
                <span className="mono">/r/{identity?.handle}/{slot?.name}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        <div className="space-y-8">
          {/* Basic Settings */}
          <div className="form-section">
            <h2 className="text-lg font-serif mb-4">Settings</h2>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={form.description}
                  onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this slot is for..."
                  className="rounded-none resize-none"
                  rows={3}
                  data-testid="slot-description"
                />
                <p className="text-xs text-muted-foreground">
                  This is shown to senders before they submit a reach attempt.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="visibility">Visibility</Label>
                <Select
                  value={form.visibility}
                  onValueChange={(value) => setForm(prev => ({ ...prev, visibility: value }))}
                >
                  <SelectTrigger className="rounded-none" data-testid="slot-visibility">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">Public</SelectItem>
                    <SelectItem value="link-only">Link-only</SelectItem>
                    <SelectItem value="private">Private</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Current Policy Rules Display */}
          <div className="form-section">
            <h2 className="text-lg font-serif mb-4">Current Policy Rules</h2>
            
            <div className="border border-border p-4 mb-6">
              <div className="space-y-3">
                {/* Default Rule */}
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2 bg-foreground rounded-full"></div>
                  <div>
                    <p className="text-sm">
                      <span className="font-medium">Default rule:</span> All requests are set to "
                      <span className="font-medium">{form.defaultAction.replace(/_/g, ' ')}</span>"
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Applies when no specific rules match
                    </p>
                  </div>
                </div>
                
                {/* Payment Rule */}
                {form.requirePayment && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 mt-2 bg-foreground rounded-full"></div>
                    <div>
                      <p className="text-sm">
                        <span className="font-medium">Payment required:</span> Senders must pay $
                        <span className="font-medium">{form.paymentAmount || '0.00'}</span> to reach you
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Payment acts as a filter for serious requests
                      </p>
                    </div>
                  </div>
                )}
                
                {/* Example Rules (static for now) */}
                <div className="flex items-start gap-3 opacity-60">
                  <div className="w-2 h-2 mt-2 bg-muted rounded-full"></div>
                  <div>
                    <p className="text-sm">
                      <span className="font-medium">Example rule:</span> If intent is "spam" → Reject automatically
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Custom rules can be added to automate decisions
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 opacity-60">
                  <div className="w-2 h-2 mt-2 bg-muted rounded-full"></div>
                  <div>
                    <p className="text-sm">
                      <span className="font-medium">Example rule:</span> If sender has paid → Deliver to human
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Paid requests bypass the queue
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Policy Settings */}
          <div className="form-section">
            <h2 className="text-lg font-serif mb-4">Policy Configuration</h2>
            
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="defaultAction">Default Action</Label>
                <Select
                  value={form.defaultAction}
                  onValueChange={(value) => setForm(prev => ({ ...prev, defaultAction: value }))}
                >
                  <SelectTrigger className="rounded-none" data-testid="default-action">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="queue">Queue for review</SelectItem>
                    <SelectItem value="deliver_to_human">Deliver to human</SelectItem>
                    <SelectItem value="reject">Reject</SelectItem>
                    <SelectItem value="auto_respond">Auto-respond</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  What happens when AI can't make a clear decision.
                </p>
              </div>

              <div className="flex items-center justify-between p-4 border border-border">
                <div>
                  <Label className="text-base">Require Payment</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Senders must pay to reach you through this slot.
                  </p>
                </div>
                <Switch
                  checked={form.requirePayment}
                  onCheckedChange={(checked) => setForm(prev => ({ ...prev, requirePayment: checked }))}
                  data-testid="require-payment-switch"
                />
              </div>

              {form.requirePayment && (
                <div className="space-y-2">
                  <Label htmlFor="paymentAmount">Payment Amount (USD)</Label>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">$</span>
                    <Input
                      id="paymentAmount"
                      type="number"
                      min="1"
                      step="0.01"
                      value={form.paymentAmount}
                      onChange={(e) => setForm(prev => ({ ...prev, paymentAmount: e.target.value }))}
                      placeholder="25.00"
                      className="rounded-none"
                      data-testid="payment-amount"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Payment is a filter, not revenue extraction.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Save Button */}
          <Button
            onClick={handleSave}
            className="w-full rounded-none gap-2"
            disabled={saving}
            data-testid="save-slot-btn"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </Layout>
  );
}
