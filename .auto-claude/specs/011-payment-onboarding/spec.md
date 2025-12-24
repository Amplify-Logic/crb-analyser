# Payment & Onboarding - Friction Reduction

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

The payment and onboarding flow converts quiz completers to paying customers. Every friction point costs conversions.

## Objective
Minimize friction in the payment and onboarding flow while setting clear expectations and building trust.

## Current State
- Stripe integration configured
- Checkout and CheckoutSuccess pages
- €147 AI Report and €497 Human Audit tiers
- Terms and Privacy pages exist

## Deliverables

### 1. Value Reinforcement at Checkout
- Recap what they'll receive
- Compare to consulting alternative (€5,000+)
- Show sample report preview
- Social proof/testimonials

### 2. Friction Reduction
- Minimal form fields
- Clear pricing (no hidden fees)
- Multiple payment methods
- Trust signals (secure checkout, money-back guarantee)

### 3. Post-Payment Onboarding
- Clear next step immediately after payment
- Set expectations (90-min interview → report in X hours)
- Calendar booking for interview if applicable
- Welcome email with clear instructions

### 4. Account Creation
- Simple signup flow
- SSO options if valuable
- Magic link alternative to password
- Proper session handling

### 5. Recovery Flows
- Abandoned checkout recovery
- Failed payment handling
- Invoice/receipt delivery
- Support contact if issues

## Acceptance Criteria
- [ ] Checkout completes in < 2 minutes
- [ ] No surprises in payment flow
- [ ] Post-payment next step is crystal clear
- [ ] Welcome email sent immediately
- [ ] Failed payment has clear recovery path
- [ ] Mobile checkout works flawlessly

## Files to Modify
- `frontend/src/pages/Checkout.tsx`
- `frontend/src/pages/CheckoutSuccess.tsx`
- `frontend/src/pages/Login.tsx` / `Signup.tsx`
- `backend/src/routes/payments.py`
- `backend/src/services/email/` for welcome emails

## Metrics
- Checkout completion rate
- Time from quiz to payment
- Failed payment rate
- Support tickets related to payment
