import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { extractErrorMessage } from '../lib/error-utils';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { ArrowLeft, Link as LinkIcon, Image } from 'lucide-react';

export default function FaceSetup() {
  const { refreshIdentity } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    handle: '',
    display_name: '',
    headline: '',
    current_focus: '',
    availability_signal: '',
    prompt: '',
    photo_url: '',
    links: [{ label: '', url: '' }, { label: '', url: '' }]
  });

  const promptExamples = [
    "What are you working on and why did you think of me?",
    "Tell me what you need and how I can help.",
    "What's the one thing you want me to know?"
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLinkChange = (index, field, value) => {
    const newLinks = [...formData.links];
    newLinks[index] = { ...newLinks[index], [field]: value };
    setFormData(prev => ({ ...prev, links: newLinks }));
  };

  const addLink = () => {
    if (formData.links.length < 2) {
      setFormData(prev => ({ 
        ...prev, 
        links: [...prev.links, { label: '', url: '' }] 
      }));
    }
  };

  const removeLink = (index) => {
    if (formData.links.length > 0) {
      const newLinks = formData.links.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, links: newLinks }));
    }
  };

  const setExamplePrompt = (example) => {
    setFormData(prev => ({ ...prev, prompt: example }));
  };

  const validateForm = () => {
    if (!formData.handle || formData.handle.length < 3) {
      toast.error('Handle must be at least 3 characters');
      return false;
    }

    if (!/^[a-z0-9_-]+$/.test(formData.handle.toLowerCase())) {
      toast.error('Handle can only contain letters, numbers, underscores, and hyphens');
      return false;
    }

    if (!formData.display_name || formData.display_name.length < 2) {
      toast.error('Display name must be at least 2 characters');
      return false;
    }

    if (!formData.headline || formData.headline.length < 10 || formData.headline.length > 100) {
      toast.error('Headline must be 10-100 characters');
      return false;
    }

    if (!formData.current_focus || formData.current_focus.length < 20 || formData.current_focus.length > 300) {
      toast.error('Current focus must be 20-300 characters');
      return false;
    }

    if (!formData.availability_signal || formData.availability_signal.length < 10 || formData.availability_signal.length > 200) {
      toast.error('Availability signal must be 10-200 characters');
      return false;
    }

    if (!formData.prompt || formData.prompt.length < 10 || formData.prompt.length > 200) {
      toast.error('Prompt must be 10-200 characters');
      return false;
    }

    if (formData.photo_url && !formData.photo_url.startsWith('http')) {
      toast.error('Photo URL must start with http:// or https://');
      return false;
    }

    for (const link of formData.links) {
      if (link.label && !link.url) {
        toast.error('Link URL is required if label is provided');
        return false;
      }
      if (link.url && !link.url.startsWith('http')) {
        toast.error('Link URL must start with http:// or https://');
        return false;
      }
      if (link.label && link.label.length > 30) {
        toast.error('Link label must be at most 30 characters');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const links = formData.links.filter(link => link.label && link.url);
      
      await api.post('/identity', {
        handle: formData.handle.toLowerCase(),
        display_name: formData.display_name,
        headline: formData.headline,
        current_focus: formData.current_focus,
        availability_signal: formData.availability_signal,
        prompt: formData.prompt,
        photo_url: formData.photo_url || null,
        links: links.length > 0 ? links : null
      });

      await refreshIdentity();
      toast.success('Face created successfully');
      navigate('/dashboard');
    } catch (error) {
      const message = extractErrorMessage(error) || 'Failed to create Face';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-12 animate-in">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm text-secondary hover:text-primary transition-colors mb-12"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <h1 className="text-3xl font-serif mb-3">Create your Face</h1>
        <p className="text-secondary mb-10">
          This is how people will see and reach you. Complete all fields to make your handle live.
        </p>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Handle */}
          <div className="space-y-3">
            <Label htmlFor="handle" className="text-sm">Handle</Label>
            <div className="flex items-center gap-2">
              <span className="text-secondary mono text-sm">/r/</span>
              <Input
                id="handle"
                name="handle"
                value={formData.handle}
                onChange={handleChange}
                placeholder="yourname"
                className="rounded-none h-12 mono"
                required
                data-testid="face-handle"
              />
            </div>
            <p className="text-xs text-tertiary">
              Lowercase letters, numbers, underscores, and hyphens only
            </p>
          </div>

          {/* Display Name */}
          <div className="space-y-3">
            <Label htmlFor="display_name" className="text-sm">Display Name</Label>
            <Input
              id="display_name"
              name="display_name"
              value={formData.display_name}
              onChange={handleChange}
              placeholder="How you want to be known"
              className="rounded-none h-12"
              required
              data-testid="face-display-name"
            />
            <p className="text-xs text-tertiary">
              Your public name (2-50 characters)
            </p>
          </div>

          {/* Headline */}
          <div className="space-y-3">
            <Label htmlFor="headline" className="text-sm">Headline</Label>
            <Input
              id="headline"
              name="headline"
              value={formData.headline}
              onChange={handleChange}
              placeholder="What you do or what this handle is for"
              className="rounded-none h-12"
              required
              data-testid="face-headline"
            />
            <p className="text-xs text-tertiary">
              One sentence about you (10-100 characters)
            </p>
          </div>

          {/* Current Focus */}
          <div className="space-y-3">
            <Label htmlFor="current_focus" className="text-sm">Current Focus</Label>
            <Textarea
              id="current_focus"
              name="current_focus"
              value={formData.current_focus}
              onChange={handleChange}
              placeholder="What you're working on right now (1-2 sentences)"
              className="rounded-none resize-none min-h-[100px]"
              required
              data-testid="face-current-focus"
            />
            <p className="text-xs text-tertiary">
              20-300 characters
            </p>
          </div>

          {/* Availability Signal */}
          <div className="space-y-3">
            <Label htmlFor="availability_signal" className="text-sm">Availability Signal</Label>
            <Input
              id="availability_signal"
              name="availability_signal"
              value={formData.availability_signal}
              onChange={handleChange}
              placeholder="I check this weekly / I respond to everyone here"
              className="rounded-none h-12"
              required
              data-testid="face-availability"
            />
            <p className="text-xs text-tertiary">
              When and how you'll respond (10-200 characters)
            </p>
          </div>

          {/* Photo URL */}
          <div className="space-y-3">
            <Label htmlFor="photo_url" className="text-sm flex items-center gap-2">
              <Image className="w-4 h-4" />
              Photo URL (optional)
            </Label>
            <Input
              id="photo_url"
              name="photo_url"
              value={formData.photo_url}
              onChange={handleChange}
              placeholder="https://example.com/photo.jpg"
              className="rounded-none h-12"
              data-testid="face-photo-url"
            />
            <p className="text-xs text-tertiary">
              Link to your profile picture
            </p>
          </div>

          {/* Prompt */}
          <div className="space-y-3">
            <Label htmlFor="prompt" className="text-sm">Your Prompt</Label>
            <Textarea
              id="prompt"
              name="prompt"
              value={formData.prompt}
              onChange={handleChange}
              placeholder="The question or invitation senders will respond to"
              className="rounded-none resize-none min-h-[100px]"
              required
              data-testid="face-prompt"
            />
            <p className="text-xs text-tertiary">
              This replaces every form field on the sender side. 10-200 characters.
            </p>
            
            {/* Prompt Examples */}
            <div className="mt-4">
              <p className="text-sm text-secondary mb-2">Example prompts:</p>
              <div className="space-y-2">
                {promptExamples.map((example, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setExamplePrompt(example)}
                    className="text-sm text-tertiary hover:text-primary transition-colors block w-full text-left p-2 border border-border hover:border-primary/20 rounded-none"
                    data-testid={`face-prompt-example-${index}`}
                  >
                    "{example}"
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Links */}
          <div className="space-y-4">
            <Label className="text-sm flex items-center gap-2">
              <LinkIcon className="w-4 h-4" />
              Links (optional, max 2)
            </Label>
            
            {formData.links.map((link, index) => (
              <div key={index} className="grid grid-cols-12 gap-3">
                <div className="col-span-5">
                  <Input
                    placeholder="Label (e.g., My work)"
                    value={link.label}
                    onChange={(e) => handleLinkChange(index, 'label', e.target.value)}
                    className="rounded-none h-10"
                    data-testid={`face-link-label-${index}`}
                  />
                </div>
                <div className="col-span-6">
                  <Input
                    placeholder="https://example.com"
                    value={link.url}
                    onChange={(e) => handleLinkChange(index, 'url', e.target.value)}
                    className="rounded-none h-10"
                    data-testid={`face-link-url-${index}`}
                  />
                </div>
                <div className="col-span-1">
                  {formData.links.length > 0 && (
                    <button
                      type="button"
                      onClick={() => removeLink(index)}
                      className="w-10 h-10 flex items-center justify-center text-secondary hover:text-primary transition-colors"
                      data-testid={`face-link-remove-${index}`}
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            ))}

            {formData.links.length < 2 && (
              <button
                type="button"
                onClick={addLink}
                className="text-sm text-secondary hover:text-primary transition-colors"
                data-testid="face-link-add"
              >
                + Add another link
              </button>
            )}
            
            <p className="text-xs text-tertiary">
              Maximum 2 links to your work or projects
            </p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full rounded-none h-12 mt-8"
            disabled={loading}
            data-testid="face-submit"
          >
            {loading ? 'Creating...' : 'Create Face & Go Live'}
          </Button>
        </form>
      </div>
    </Layout>
  );
}