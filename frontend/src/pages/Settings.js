import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import { Copy, ExternalLink, Eye, Save, Edit } from 'lucide-react';

export default function Settings() {
  const { user, identity, refreshIdentity } = useAuth();
  const [saving, setSaving] = useState(false);
  const [modulesConfig, setModulesConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load modules configuration
  useEffect(() => {
    loadModulesConfig();
  }, [identity]);

  const loadModulesConfig = async () => {
    if (!identity) return;
    
    try {
      const response = await api.get('/modules');
      setModulesConfig(response.data);
    } catch (error) {
      console.error('Failed to load modules config:', error);
      toast.error('Failed to load module configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveModulesConfig = async () => {
    if (!identity || !modulesConfig) return;
    
    setSaving(true);
    try {
      await api.put('/modules', modulesConfig);
      toast.success('Module configuration saved');
      refreshIdentity();
    } catch (error) {
      console.error('Failed to save modules config:', error);
      toast.error('Failed to save module configuration');
    } finally {
      setSaving(false);
    }
  };

  const updateModuleConfig = (moduleName, updates) => {
    setModulesConfig(prev => ({
      ...prev,
      [moduleName]: {
        ...prev[moduleName],
        ...updates
      }
    }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const publicUrl = identity ? `${window.location.origin}/r/${identity.handle}` : '';
  const previewUrl = identity ? `/r/${identity.handle}?preview=true` : '';

  if (loading) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-4">
              {[1, 2, 3, 4, 5, 6, 7].map(i => (
                <div key={i} className="h-32 bg-gray-100 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8 animate-in">
        {/* Header with Preview button */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-serif mb-1">Settings</h1>
            <p className="text-muted-foreground">
              Configure how people reach you
            </p>
          </div>
          <div className="flex gap-2">
            <a href={previewUrl} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="rounded-none gap-2">
                <Eye className="w-4 h-4" />
                Preview your page
              </Button>
            </a>
            <Button 
              onClick={saveModulesConfig} 
              disabled={saving}
              className="rounded-none gap-2"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save all'}
            </Button>
          </div>
        </div>

        {/* Face Summary */}
        {identity && (
          <div className="form-section">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-serif">Your Face</h2>
              <a href="/face-setup">
                <Button variant="outline" size="sm" className="rounded-none gap-2">
                  <Edit className="w-3 h-3" />
                  Edit Face
                </Button>
              </a>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-muted-foreground">Name</div>
                <div className="text-lg font-serif">{identity.display_name || identity.handle}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Headline</div>
                <div>{identity.headline || 'No headline set'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Prompt</div>
                <div className="italic">"{identity.prompt || 'No prompt set'}"</div>
              </div>
            </div>
          </div>
        )}

        {/* Public Link */}
        {identity && (
          <div className="form-section">
            <h2 className="text-lg font-serif mb-4">Public Link</h2>
            <div className="flex items-center gap-2">
              <Input
                value={publicUrl}
                readOnly
                className="rounded-none mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(publicUrl)}
                className="rounded-none flex-shrink-0"
              >
                <Copy className="w-4 h-4" />
              </Button>
              <a href={publicUrl} target="_blank" rel="noopener noreferrer">
                <Button
                  variant="outline"
                  size="icon"
                  className="rounded-none flex-shrink-0"
                >
                  <ExternalLink className="w-4 h-4" />
                </Button>
              </a>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Share this link to let people reach you.
            </p>
          </div>
        )}

        {/* Module 1: Intent Categories */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Intent Categories</h3>
              <p className="text-sm text-muted-foreground">
                Suggest categories to help senders clarify their intent
              </p>
            </div>
            <Switch
              checked={modulesConfig?.intent_categories?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('intent_categories', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.intent_categories?.enabled && (
            <div className="space-y-4 mt-4 animate-in">
              <div>
                <Label htmlFor="categories">Categories (comma separated, max 8)</Label>
                <Input
                  id="categories"
                  value={modulesConfig.intent_categories.categories?.join(', ') || ''}
                  onChange={(e) => updateModuleConfig('intent_categories', { 
                    categories: e.target.value.split(',').map(c => c.trim()).filter(c => c)
                  })}
                  placeholder="Collaboration, Feedback, Press, Investment, Question"
                  className="rounded-none"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Senders will see these as soft chip suggestions below the prompt
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Module 2: Time Signal */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Time Signal</h3>
              <p className="text-sm text-muted-foreground">
                Ask senders how much time they need
              </p>
            </div>
            <Switch
              checked={modulesConfig?.time_signal?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('time_signal', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.time_signal?.enabled && (
            <div className="mt-4 animate-in">
              <p className="text-sm">
                After the sender writes their message, a simple question appears: 
                <span className="font-medium"> "How much time do you need?"</span>
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Three options only: "Just a read" / "A reply" / "A conversation". 2 seconds to answer.
              </p>
            </div>
          )}
        </div>

        {/* Module 3: Challenge Question */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Challenge Question</h3>
              <p className="text-sm text-muted-foreground">
                Add a question to filter lazy senders
              </p>
            </div>
            <Switch
              checked={modulesConfig?.challenge_question?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('challenge_question', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.challenge_question?.enabled && (
            <div className="space-y-4 mt-4 animate-in">
              <div>
                <Label htmlFor="challenge-question">Your question</Label>
                <Input
                  id="challenge-question"
                  value={modulesConfig.challenge_question.question || ''}
                  onChange={(e) => updateModuleConfig('challenge_question', { question: e.target.value })}
                  placeholder="What motivated you to reach out today?"
                  className="rounded-none"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Appears before the prompt unlocks — framed as curiosity, not a gate
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Module 4: Waiting Period */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Waiting Period</h3>
              <p className="text-sm text-muted-foreground">
                Hide the text box for a short duration
              </p>
            </div>
            <Switch
              checked={modulesConfig?.waiting_period?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('waiting_period', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.waiting_period?.enabled && (
            <div className="space-y-4 mt-4 animate-in">
              <div>
                <Label htmlFor="waiting-seconds">Wait time (seconds)</Label>
                <div className="flex gap-2">
                  {[30, 60, 90].map((seconds) => (
                    <Button
                      key={seconds}
                      type="button"
                      variant={modulesConfig.waiting_period.seconds === seconds ? "default" : "outline"}
                      onClick={() => updateModuleConfig('waiting_period', { seconds })}
                      className="rounded-none"
                    >
                      {seconds}s
                    </Button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  The prompt text box is hidden for this duration. Drive-by senders leave. Genuine senders stay.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Module 5: Deposit */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Deposit</h3>
              <p className="text-sm text-muted-foreground">
                Hold a small deposit until you respond
              </p>
            </div>
            <Switch
              checked={modulesConfig?.deposit?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('deposit', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.deposit?.enabled && (
            <div className="space-y-4 mt-4 animate-in">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="deposit-amount">Amount (USD)</Label>
                  <Input
                    id="deposit-amount"
                    type="number"
                    min="1"
                    step="0.01"
                    value={modulesConfig.deposit.amount_usd || 5}
                    onChange={(e) => updateModuleConfig('deposit', { 
                      amount_usd: parseFloat(e.target.value) || 5 
                    })}
                    className="rounded-none"
                  />
                </div>
                <div>
                  <Label htmlFor="response-days">Response commitment (days)</Label>
                  <Input
                    id="response-days"
                    type="number"
                    min="1"
                    max="30"
                    value={modulesConfig.deposit.response_days || 7}
                    onChange={(e) => updateModuleConfig('deposit', { 
                      response_days: parseInt(e.target.value) || 7 
                    })}
                    className="rounded-none"
                  />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Sender sees: "{identity?.display_name || 'I'} commits to responding within {modulesConfig.deposit.response_days || 7} days. 
                A small deposit of ${modulesConfig.deposit.amount_usd || 5} is held until they respond — fully returned when they do."
              </p>
              <p className="text-xs text-muted-foreground">
                Note: Payment processing will be implemented in a later phase
              </p>
            </div>
          )}
        </div>

        {/* Module 6: Rules Engine */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Rules Engine</h3>
              <p className="text-sm text-muted-foreground">
                Write plain language rules for AI to execute
              </p>
            </div>
            <Switch
              checked={modulesConfig?.rules_engine?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('rules_engine', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.rules_engine?.enabled && (
            <div className="space-y-4 mt-4 animate-in">
              <div>
                <Label htmlFor="rules">Rules (one per line)</Label>
                <Textarea
                  id="rules"
                  value={modulesConfig.rules_engine.rules?.join('\n') || ''}
                  onChange={(e) => updateModuleConfig('rules_engine', { 
                    rules: e.target.value.split('\n').filter(r => r.trim())
                  })}
                  placeholder="If message mentions sales or agency — reject automatically&#10;If message is under 30 words — ask for more context&#10;If time requirement is a conversation — require deposit&#10;After 5 approved requests this month — pause this handle"
                  className="rounded-none resize-none min-h-[120px] font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  AI reads these rules and executes them when a submission arrives. 
                  Every decision shows which rule triggered and why. You can override any decision.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Module 7: Capacity Controls */}
        <div className="form-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-serif">Capacity Controls</h3>
              <p className="text-sm text-muted-foreground">
                Set limits to manage your availability
              </p>
            </div>
            <Switch
              checked={modulesConfig?.capacity_controls?.enabled || false}
              onCheckedChange={(checked) => updateModuleConfig('capacity_controls', { enabled: checked })}
            />
          </div>
          
          {modulesConfig?.capacity_controls?.enabled && (
            <div className="space-y-4 mt-4 animate-in">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="max-approved-week">Max approved per week</Label>
                  <Input
                    id="max-approved-week"
                    type="number"
                    min="1"
                    value={modulesConfig.capacity_controls.max_approved_per_week || ''}
                    onChange={(e) => updateModuleConfig('capacity_controls', { 
                      max_approved_per_week: e.target.value ? parseInt(e.target.value) : null 
                    })}
                    placeholder="Unlimited"
                    className="rounded-none"
                  />
                </div>
                <div>
                  <Label htmlFor="sender-cooldown">Sender cooldown (days)</Label>
                  <Input
                    id="sender-cooldown"
                    type="number"
                    min="1"
                    value={modulesConfig.capacity_controls.sender_cooldown_days || ''}
                    onChange={(e) => updateModuleConfig('capacity_controls', { 
                      sender_cooldown_days: e.target.value ? parseInt(e.target.value) : null 
                    })}
                    placeholder="No cooldown"
                    className="rounded-none"
                  />
                </div>
                <div>
                  <Label htmlFor="daily-cap">Daily submission cap</Label>
                  <Input
                    id="daily-cap"
                    type="number"
                    min="1"
                    value={modulesConfig.capacity_controls.daily_submission_cap || ''}
                    onChange={(e) => updateModuleConfig('capacity_controls', { 
                      daily_submission_cap: e.target.value ? parseInt(e.target.value) : null 
                    })}
                    placeholder="Unlimited"
                    className="rounded-none"
                  />
                </div>
                <div>
                  <Label htmlFor="expiry-date">Handle expiry date</Label>
                  <Input
                    id="expiry-date"
                    type="date"
                    value={modulesConfig.capacity_controls.handle_expiry_date || ''}
                    onChange={(e) => updateModuleConfig('capacity_controls', { 
                      handle_expiry_date: e.target.value || null 
                    })}
                    className="rounded-none"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Sender cooldown is tracked by IP + browser fingerprint (no email required)
              </p>
            </div>
          )}
        </div>

        {/* Save button at bottom */}
        <div className="sticky bottom-0 bg-background py-4 border-t">
          <div className="flex justify-end">
            <Button 
              onClick={saveModulesConfig} 
              disabled={saving}
              className="rounded-none gap-2"
              size="lg"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save all changes'}
            </Button>
          </div>
        </div>
      </div>
    </Layout>
  );
}