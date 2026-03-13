# Reach - AI-Powered Reachability Platform

## Overview
Reach is a reachability-as-logic platform that replaces email addresses, contact forms, and DMs with logic-based access. Users don't receive messages by default - all incoming attempts are evaluated by AI and rules.

## Original Problem Statement
Create a new internet default for human reachability. Users own their reach identity, set rules for who can reach them, and AI evaluates every incoming attempt. Most attempts never reach a human. Identity owners never pay - senders may pay to cross boundaries.

## User Personas

### Identity Owner (Free, always)
- Individuals, creators, founders who want to control their reachability
- People who receive too many cold emails/DMs
- Those who value their attention as finite

### Sender (Occasional)
- Anyone trying to reach an identity
- May be anonymous or verified
- Pays only if required by rules

## Architecture

### Backend (FastAPI + MongoDB)
- **Auth Service**: JWT-based authentication
- **Identity Service**: Handle creation, management
- **Slot Manager**: Reach surfaces (/open, /business, /press)
- **Reach Engine**: Evaluates attempts against policies
- **AI Orchestrator**: OpenAI GPT-5.2 for intent classification
- **Payment Service**: Stripe integration for paid reaches

### Frontend (React)
- Dark mode, minimal UI with Instrument Serif + Manrope typography
- Signal Amber (#F59E0B) accent color
- Shadcn/UI components

### Database Collections
- `users` - Authentication
- `identities` - Handle, type, bio
- `slots` - Reach surfaces with policies
- `reach_attempts` - Event log with AI classification
- `reach_policies` - Declarative rules
- `payment_transactions` - Stripe payments

## Core Requirements (Static)

### Must Have
- [x] Identity creation with unique handle
- [x] Slot management (CRUD)
- [x] Public reach pages (/r/{handle}/{slot})
- [x] AI-powered intent classification
- [x] Policy engine with configurable rules
- [x] Payment requirement support
- [x] Dashboard with stats
- [x] Reach attempts management

### Belief Pages (Adoption Critical)
- [x] /why - Philosophy and moral clarity
- [x] /replace-email - Concrete replacement guide
- [x] /first-10-minutes - The ritual for adoption

## What's Been Implemented (January 2026)

### Backend APIs
- Auth: register, login, get current user
- Identity: create, get, get by handle
- Slots: CRUD, policy updates
- Public Reach: get identity, get slot, submit attempt
- Reach Attempts: list, view, update decision
- Payments: checkout, status, webhook
- Stats: aggregated metrics
- Email notifications (Resend integration - requires API key)

### Frontend Pages
- Landing page with hero and features
- Auth (Login, Register)
- Dashboard with stats, copy link button, and identity setup
- In-app onboarding flow (3-step ritual)
- Slots management with improved empty states
- Slot editor with policy builder
- Attempts list with decision overrides
- Settings
- Public reach pages with identity context
- Public slot with decision transparency
- Payment flow
- Belief pages (/why, /replace-email, /first-10-minutes)
- Mobile-responsive layout with hamburger menu

### AI Integration
- OpenAI GPT-5.2 via Emergent LLM key
- Intent classification (business, personal, spam, urgent, unknown)
- Confidence scoring
- Rationale generation

### Payments
- Stripe integration for paid reaches
- Checkout session creation
- Payment status polling
- Webhook handling

### UX Improvements (Latest)
- Empty states with meaningful copy and illustrations
- In-app onboarding ritual after identity creation
- Public pages show identity bio/context
- Decision transparency for senders
- Copy link button prominently on dashboard
- Mobile-responsive hamburger menu
- Email notifications (owner + sender confirmation)

## Prioritized Backlog

### P0 (Critical)
- [x] Email notifications for delivered reaches (implemented, needs API key)
- [ ] Webhook triggers for integrations

### P1 (High)
- [ ] Calendar integration for scheduling
- [ ] Auto-response templates
- [ ] Domain verification for trusted senders

### P2 (Medium)
- [ ] Public API for integrators
- [ ] Analytics dashboard
- [ ] Bulk slot management

## Next Tasks
1. Add email notifications (Resend/SendGrid)
2. Create webhook system for external integrations
3. Add calendar scheduling (Google Calendar)
4. Build developer API docs
5. Add domain verification for trusted domains

## Success Metrics
- % of reach attempts blocked before human
- % of users removing public email addresses
- Paid reach conversion rate
- Policy execution accuracy

## Technical Notes
- Backend: FastAPI on port 8001
- Frontend: React on port 3000  
- Database: MongoDB
- AI: OpenAI GPT-5.2 (Emergent LLM key)
- Payments: Stripe (test key)
