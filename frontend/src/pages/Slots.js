import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Settings, Trash2, Globe, Lock, Link as LinkIcon, Layers } from 'lucide-react';

export default function Slots() {
  const { identity } = useAuth();
  const navigate = useNavigate();
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: '',
    description: '',
    visibility: 'public'
  });

  useEffect(() => {
    fetchSlots();
  }, []);

  const fetchSlots = async () => {
    try {
      const response = await api.get('/slots');
      setSlots(response.data);
    } catch (error) {
      console.error('Failed to fetch slots:', error);
    } finally {
      setLoading(false);
    }
  };

  const createSlot = async (e) => {
    e.preventDefault();
    
    if (!form.name || form.name.length < 2) {
      toast.error('Name must be at least 2 characters');
      return;
    }

    if (!/^[a-z0-9_]+$/.test(form.name.toLowerCase())) {
      toast.error('Name can only contain letters, numbers, and underscores');
      return;
    }

    setCreating(true);
    try {
      await api.post('/slots', {
        name: form.name.toLowerCase(),
        description: form.description,
        visibility: form.visibility
      });
      toast.success('Slot created');
      setShowCreate(false);
      setForm({ name: '', description: '', visibility: 'public' });
      fetchSlots();
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to create slot';
      toast.error(message);
    } finally {
      setCreating(false);
    }
  };

  const deleteSlot = async (slotId, slotName) => {
    if (slotName === 'open') {
      toast.error('Cannot delete the default "open" slot');
      return;
    }

    if (!confirm('Are you sure you want to delete this slot?')) return;

    try {
      await api.delete(`/slots/${slotId}`);
      toast.success('Slot deleted');
      fetchSlots();
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to delete slot';
      toast.error(message);
    }
  };

  const getVisibilityIcon = (visibility) => {
    switch (visibility) {
      case 'public': return <Globe className="w-4 h-4" />;
      case 'private': return <Lock className="w-4 h-4" />;
      default: return <LinkIcon className="w-4 h-4" />;
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
      <div className="space-y-8 animate-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-serif mb-1">Slots</h1>
            <p className="text-muted-foreground">
              Your reach surfaces. Each slot can have its own rules.
            </p>
          </div>
          
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="rounded-none gap-2" data-testid="create-slot-btn">
                <Plus className="w-4 h-4" />
                Create Slot
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-none">
              <DialogHeader>
                <DialogTitle className="font-serif text-xl">Create Slot</DialogTitle>
              </DialogHeader>
              <form onSubmit={createSlot} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground mono">/{identity?.handle}/</span>
                    <Input
                      id="name"
                      value={form.name}
                      onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value.toLowerCase() }))}
                      placeholder="business"
                      className="rounded-none mono"
                      required
                      data-testid="slot-name-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={form.description}
                    onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Business inquiries and partnership opportunities"
                    className="rounded-none resize-none"
                    rows={3}
                    required
                    data-testid="slot-description-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="visibility">Visibility</Label>
                  <Select
                    value={form.visibility}
                    onValueChange={(value) => setForm(prev => ({ ...prev, visibility: value }))}
                  >
                    <SelectTrigger className="rounded-none" data-testid="slot-visibility-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">Public - Anyone can find</SelectItem>
                      <SelectItem value="link-only">Link-only - Hidden from public page</SelectItem>
                      <SelectItem value="private">Private - Disabled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1 rounded-none"
                    onClick={() => setShowCreate(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1 rounded-none"
                    disabled={creating}
                    data-testid="slot-submit-btn"
                  >
                    {creating ? 'Creating...' : 'Create'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Slots Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {slots.map((slot) => (
            <div
              key={slot.id}
              className={`border p-6 ${slot.name === 'open' ? 'border-foreground bg-foreground text-background' : 'border-border card-hover'}`}
              data-testid={`slot-${slot.name}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  {getVisibilityIcon(slot.visibility)}
                  <span className={`mono text-sm ${slot.name === 'open' ? 'text-background/80' : 'text-muted-foreground'}`}>/{slot.name}</span>
                  {slot.name === 'open' && (
                    <span className="text-xs px-2 py-0.5 bg-background text-foreground">Default</span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant={slot.name === 'open' ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => navigate(`/slots/${slot.id}`)}
                    data-testid={`edit-slot-${slot.name}`}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                  {slot.name !== 'open' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteSlot(slot.id, slot.name)}
                      className="text-destructive hover:text-destructive"
                      data-testid={`delete-slot-${slot.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              <p className={`text-sm mb-2 line-clamp-2 ${slot.name === 'open' ? 'text-background/90' : 'text-foreground'}`}>
                {slot.description || (slot.name === 'open' ? 'Your default reach slot for all incoming requests' : slot.description)}
              </p>

              {/* Policy Summary */}
              <div className="mb-4">
                <div className={`text-xs ${slot.name === 'open' ? 'text-background/70' : 'text-muted-foreground'} mb-2`}>
                  Policy rules:
                </div>
                <div className="space-y-1">
                  {slot.reach_policy?.conditions?.length > 0 ? (
                    slot.reach_policy.conditions.map((condition, idx) => (
                      <div key={idx} className={`text-xs ${slot.name === 'open' ? 'text-background/90' : 'text-foreground/70'}`}>
                        If {condition.field} {condition.operator} "{condition.value}" → {condition.action}
                      </div>
                    ))
                  ) : (
                    <div className={`text-xs ${slot.name === 'open' ? 'text-background/70' : 'text-muted-foreground'}`}>
                      Default: {slot.reach_policy?.actions?.default || 'queue'} all requests
                    </div>
                  )}
                  {slot.reach_policy?.payment_amount && (
                    <div className={`text-xs ${slot.name === 'open' ? 'text-background/90' : 'text-primary'}`}>
                      ${slot.reach_policy.payment_amount} payment required
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs">
                  <span className={`capitalize ${slot.name === 'open' ? 'text-background/70' : 'text-muted-foreground'}`}>
                    {slot.visibility}
                  </span>
                  {slot.reach_policy?.payment_amount && (
                    <span className={slot.name === 'open' ? 'text-background/90' : 'text-primary'}>
                      ${slot.reach_policy.payment_amount}
                    </span>
                  )}
                </div>
                
                {/* Status Badge */}
                <div className={`text-xs px-2 py-0.5 ${slot.name === 'open' ? 'bg-background text-foreground' : 'bg-muted text-muted-foreground'}`}>
                  {slot.name === 'open' ? 'Active' : 'Configured'}
                </div>
              </div>

              {slot.visibility === 'public' && (
                <a
                  href={`/r/${identity?.handle}/${slot.name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block mt-4 text-xs mono truncate ${slot.name === 'open' ? 'text-background/70 hover:text-background' : 'text-muted-foreground hover:text-foreground'}`}
                >
                  /r/{identity?.handle}/{slot.name}
                </a>
              )}
            </div>
          ))}
        </div>

        {slots.length === 0 && (
          <div className="border border-border p-8 sm:p-12 text-center">
            <div className="max-w-sm mx-auto">
              <Layers className="w-12 h-12 mx-auto mb-4 text-muted-foreground/30" />
              <h3 className="font-serif text-lg mb-2">No custom slots yet</h3>
              <p className="text-sm text-muted-foreground mb-6">
                You have a default "open" slot. Create additional slots for different types of reach—business, press, collaboration.
              </p>
              <Button 
                onClick={() => setShowCreate(true)}
                className="rounded-none gap-2"
              >
                <Plus className="w-4 h-4" />
                Create Your First Slot
              </Button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
