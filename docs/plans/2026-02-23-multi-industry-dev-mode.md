# Multi-Industry Dev Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the CLI report generator to support dental, professional services, and e-commerce with rich workshop transcripts, so dev-mode reports match production quality.

**Architecture:** Generalize the existing e-commerce-only CLI (`generate_report.py` + `fabricator.py` + seeds) to be industry-aware. Add seed files for dental and professional-services with realistic company profiles and 15-20 message workshop transcripts. The fabricator becomes a dispatcher that builds industry-specific answer dicts. No changes to `report_service.py` — just richer input data.

**Tech Stack:** Python 3.12, asyncio, Supabase, existing `generate_report_streaming()` pipeline

---

## CRB Context
- Affected user journey stage: Report generation (dev testing only)
- Industries impacted: ecommerce, dental, professional-services
- Reference docs to load during execution: `.claude/reference/report-quality.md`

## Rollback Plan
If this fails, revert by: `git revert HEAD~N` — all changes are additive (new seed files, extended fabricator). No existing functionality is removed.

---

## Task 1: Create Dental Seed File

**Files:**
- Create: `backend/src/cli/seeds/dental.json`

**Step 1: Create the seed file with 2 dental practices**

Create `backend/src/cli/seeds/dental.json` with this exact structure (matching `ecommerce.json` format):

```json
{
  "industry": "dental",
  "description": "Dental practices for CRB report generation",
  "tiers": {
    "small": {
      "description": "Solo practitioner, 1-5 staff, single location",
      "defaults": {
        "budget": 300,
        "hourly_cost": 55,
        "pain_points": ["manual appointment scheduling", "paper intake forms", "patient no-shows"]
      }
    },
    "mid": {
      "description": "Group practice, 10-50 staff, 2-4 locations",
      "defaults": {
        "budget": 1500,
        "hourly_cost": 55,
        "pain_points": ["multi-location scheduling", "patient communication gaps", "insurance claim delays", "staff coordination"]
      }
    },
    "scaling": {
      "description": "DSO or large group, 50-200 staff, 5+ locations",
      "defaults": {
        "budget": 5000,
        "hourly_cost": 60,
        "pain_points": ["centralized reporting", "cross-location data silos", "standardizing clinical workflows", "provider credentialing"]
      }
    }
  },
  "seeds": [
    {
      "name": "Solo Tandarts Amsterdam",
      "website": "https://solotandarts-amsterdam.nl",
      "country": "NL",
      "profile": {
        "tier": "small",
        "industry": "dental",
        "staff_size": "1-10",
        "practice_type": "general_dentistry",
        "locations": 1,
        "patient_volume": 120,
        "insurance_mix": "70_public_30_private",
        "monthly_revenue": 28000,
        "hourly_rate": 55,
        "current_tools": ["Exquise", "Google Calendar", "paper forms"],
        "pain_points": ["manual appointment scheduling", "paper intake forms", "patient no-shows", "manual recall system"]
      },
      "workshop_transcript": [
        {"role": "assistant", "content": "Thanks for joining this workshop. Let's start with the basics — can you walk me through what a typical day looks like at your practice?"},
        {"role": "user", "content": "Sure. I'm a solo dentist with one dental hygienist and a receptionist. We open at 8am, first patient at 8:30. My receptionist manages the schedule in Exquise — that's our practice management system — but honestly most of the coordination is done with phone calls and a paper diary. Patients call to book, and if they don't answer when we call for reminders, they just don't show up."},
        {"role": "assistant", "content": "How big of a problem are no-shows for you?"},
        {"role": "user", "content": "Huge. I'd say we get 8-10 no-shows per week out of maybe 60 scheduled appointments. That's over 15%. Each missed appointment is about €120 in lost revenue. My receptionist spends probably 4-5 hours a week just calling people to confirm. Half the time she gets voicemail."},
        {"role": "assistant", "content": "That's significant — roughly €5,000/month in lost revenue from no-shows alone. What about new patient intake — how does that work currently?"},
        {"role": "user", "content": "Patients fill out paper forms when they arrive. Medical history, insurance details, contact info. Then my receptionist manually types everything into Exquise. It takes about 15 minutes per new patient, and we get maybe 15-20 new patients per month. Plus errors — wrong phone numbers, misspelled names. Last month we sent a recall letter to the wrong address because of a typo."},
        {"role": "assistant", "content": "And how do you handle patient recalls — like 6-month checkup reminders?"},
        {"role": "user", "content": "That's entirely manual. My receptionist runs a report from Exquise every Monday and sends recall letters by post. Yes, physical letters. We tried email but our system doesn't really support automated campaigns. I know we're losing patients because they just forget to come back. My hygienist thinks we lose about 20% of patients who should be coming in for their 6-month checkup."},
        {"role": "assistant", "content": "Let's talk about your technology more broadly. Besides Exquise, what other tools do you use?"},
        {"role": "user", "content": "Google Calendar for my personal schedule. My hygienist uses a separate paper schedule. We have a basic website — it's just a WordPress page with our address and phone number. No online booking. Patients can't see available slots. We use a shared Gmail inbox for the practice. For X-rays we have a Planmeca unit that stores images locally. No cloud backup."},
        {"role": "assistant", "content": "If you could wave a magic wand and fix one thing tomorrow, what would it be?"},
        {"role": "user", "content": "Online booking with automatic reminders. I lose so much revenue to no-shows, and my receptionist is drowning in phone calls. If patients could just book online and get SMS reminders automatically, that alone would probably save us €3,000-4,000 a month. But I've looked at some solutions and they all seem complicated to set up, or they don't integrate with Exquise."},
        {"role": "assistant", "content": "What's your budget situation for technology improvements?"},
        {"role": "user", "content": "I could spend maybe €200-300 per month on software. But it needs to actually save me time and money — I'm not going to pay for something that creates more work. I tried a patient portal two years ago and gave up after a month because it was too complicated for my older patients."},
        {"role": "assistant", "content": "That's a really important point about the patient demographic. What's the age distribution of your patients?"},
        {"role": "user", "content": "Mixed. Maybe 30% are over 60, and they're not very tech-savvy. But the younger patients — the 25-45 group, which is probably 40% — they expect online booking. I've had patients literally tell me they'd switch to a practice with online booking. So I'm losing new patients too, not just no-shows."},
        {"role": "assistant", "content": "Last question — are there any compliance or data concerns that keep you up at night?"},
        {"role": "user", "content": "GDPR, definitely. All our patient data is on a local server under my desk. If it crashes, I lose everything. We have no backup strategy. My accountant has been telling me to move to the cloud for a year now. Also, I'm not sure our paper forms comply with current GDPR consent requirements. I should probably get that sorted before someone complains."}
      ]
    },
    {
      "name": "Bright Smile Dental Group",
      "website": "https://brightsmile-dental.nl",
      "country": "NL",
      "profile": {
        "tier": "mid",
        "industry": "dental",
        "staff_size": "11-50",
        "practice_type": "group_practice",
        "locations": 3,
        "patient_volume": 800,
        "insurance_mix": "60_public_40_private",
        "monthly_revenue": 185000,
        "hourly_rate": 55,
        "current_tools": ["Dentally", "Google Workspace", "Instagram", "Mailchimp", "WhatsApp Business"],
        "pain_points": ["multi-location scheduling", "patient communication gaps", "insurance claim processing", "staff coordination across locations"]
      },
      "workshop_transcript": [
        {"role": "assistant", "content": "Thanks for joining. You're running 3 locations — can you give me an overview of how they're currently set up and managed?"},
        {"role": "user", "content": "We have Amsterdam Centrum, Amsterdam Zuid, and a new location in Haarlem that opened 6 months ago. Each has 2-3 dentists, 2 hygienists, and front desk staff. Total team is about 35 people. I'm the practice manager — I oversee all three but I'm physically at Centrum most days."},
        {"role": "assistant", "content": "How do the three locations coordinate? Is everything on Dentally?"},
        {"role": "user", "content": "Yes, Dentally is our PMS — it's cloud-based which is great, but each location was set up somewhat independently. The Haarlem location especially — when we onboarded them, we didn't migrate their old data well. So we have duplicate patient records across locations. I'd estimate maybe 15% of patients who visit multiple locations have duplicate entries. It causes billing errors and confusion."},
        {"role": "assistant", "content": "What about scheduling — can patients book at any location?"},
        {"role": "user", "content": "Technically yes, through Dentally. But in practice patients call the specific location. We don't have a centralized booking system that shows availability across all three. So if Centrum is full on Tuesday, the receptionist there doesn't always think to suggest Zuid. We lose maybe 10-15 appointments per week because of this — patients just say 'I'll call back later' and never do."},
        {"role": "assistant", "content": "Tell me about your insurance claim process. You mentioned that's a pain point."},
        {"role": "user", "content": "It's a nightmare. Dutch insurance claims require specific codes, and each insurer has slightly different rules. Our front desk staff spend about 2 hours per day per location on claims. That's 30 hours per week across the group. We reject or need to resubmit about 12% of claims because of coding errors. Each rejection delays payment by 4-6 weeks. At any given time we have €40,000-50,000 in outstanding claims."},
        {"role": "assistant", "content": "That's a lot of tied-up revenue. How about patient communication — you mentioned gaps there?"},
        {"role": "user", "content": "We use Mailchimp for newsletters — maybe send one every 2 months. WhatsApp Business for ad-hoc messages but it's not integrated with anything. Recall reminders are automated through Dentally but only via email. We don't have SMS reminders. Our no-show rate is about 10%, which is better than average but still costs us. We also can't easily reach patients who haven't visited in 12+ months — our reactivation campaigns are manual and sporadic."},
        {"role": "assistant", "content": "What's your biggest operational headache across the three locations?"},
        {"role": "user", "content": "Staff scheduling and coordination. I use a shared Google Sheet for shift planning, but it's constantly out of date. Dentists swap shifts and forget to update it. When someone calls in sick, I spend 45 minutes calling around to find coverage. We also have no good way to see performance metrics across locations — I manually pull numbers from Dentally every month to create a report. It takes me a full day."},
        {"role": "assistant", "content": "If you could solve one problem with technology, what would have the biggest impact?"},
        {"role": "user", "content": "Centralized scheduling with cross-location visibility and automated insurance claim submission. Those two things alone would probably save us 40+ hours per week of admin time and recover €15,000-20,000 per month in faster claim payments. I've been looking at tools like NexHealth or Doctify but I'm not sure what integrates with Dentally."},
        {"role": "assistant", "content": "What's your technology budget for improvements?"},
        {"role": "user", "content": "We can do €1,000-1,500 per month. The Haarlem expansion stretched us financially, but the inefficiencies are costing us more than the software would. I just need to be confident it'll actually work with our setup. We had a bad experience with an AI chatbot for the website last year — it gave patients wrong information about treatments and we had to pull it after two weeks."}
      ]
    }
  ]
}
```

**Step 2: Verify the file loads correctly**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && python -c "import json; d=json.load(open('src/cli/seeds/dental.json')); print(f'Loaded {len(d[\"seeds\"])} dental seeds, tiers: {list(d[\"tiers\"].keys())}')"`

Expected: `Loaded 2 dental seeds, tiers: ['small', 'mid', 'scaling']`

**Step 3: Commit**

```bash
git add backend/src/cli/seeds/dental.json
git commit -m "feat: add dental seed file with workshop transcripts for dev mode"
```

---

## Task 2: Create Professional Services Seed File

**Files:**
- Create: `backend/src/cli/seeds/professional-services.json`

**Step 1: Create the seed file with 2 professional services firms**

Create `backend/src/cli/seeds/professional-services.json`:

```json
{
  "industry": "professional-services",
  "description": "Professional services firms for CRB report generation",
  "tiers": {
    "small": {
      "description": "Solo/boutique firm, 1-10 staff, single specialization",
      "defaults": {
        "budget": 500,
        "hourly_cost": 65,
        "pain_points": ["manual time tracking", "document management chaos", "client onboarding friction"]
      }
    },
    "mid": {
      "description": "Mid-size firm, 10-50 staff, multiple service lines",
      "defaults": {
        "budget": 2000,
        "hourly_cost": 75,
        "pain_points": ["project visibility gaps", "resource allocation", "compliance overhead", "knowledge silos"]
      }
    },
    "scaling": {
      "description": "Large firm, 50-200 staff, multi-office/international",
      "defaults": {
        "budget": 5000,
        "hourly_cost": 85,
        "pain_points": ["cross-office collaboration", "talent management", "client reporting at scale", "M&A integration"]
      }
    }
  },
  "seeds": [
    {
      "name": "Catalyst Consulting",
      "website": "https://catalyst-consulting.nl",
      "country": "NL",
      "profile": {
        "tier": "small",
        "industry": "professional-services",
        "staff_size": "1-10",
        "service_type": "strategy_consulting",
        "billing_model": "project_based",
        "client_count": 12,
        "compliance_requirements": ["GDPR"],
        "monthly_revenue": 45000,
        "hourly_rate": 150,
        "current_tools": ["Google Workspace", "Notion", "Toggl", "Stripe", "LinkedIn"],
        "pain_points": ["manual proposal writing", "inconsistent project tracking", "knowledge lost between projects", "no CRM"]
      },
      "workshop_transcript": [
        {"role": "assistant", "content": "Let's start with an overview — what kind of consulting does Catalyst do, and who are your typical clients?"},
        {"role": "user", "content": "We're an 8-person strategy consulting firm. We help mid-size companies — usually €5M-50M revenue — with growth strategy, digital transformation, and operational improvement. Our sweet spot is companies that have outgrown their founder-led approach and need to professionalize. Typical engagement is 6-12 weeks, €15,000-40,000."},
        {"role": "assistant", "content": "Walk me through how a new client engagement works, from first contact to delivery."},
        {"role": "user", "content": "A lead comes in — usually through LinkedIn content or referrals. I have a 30-minute discovery call. If it's a fit, we write a proposal. Proposals are our biggest bottleneck — each one takes 3-5 hours to write, and we probably win 1 in 3. That's 10-15 hours per month on proposals that go nowhere. We use Google Docs for proposals, no templates, each consultant writes them differently."},
        {"role": "assistant", "content": "Once you win the project, how do you manage delivery?"},
        {"role": "user", "content": "We use Notion for project management. Each project gets a Notion workspace. But here's the problem — every consultant sets up their workspace differently. There's no standard structure. When I need to review a project or when a consultant leaves, I can't find anything. We also track time in Toggl, but compliance is maybe 60%. People forget to log hours, so our profitability data is unreliable."},
        {"role": "assistant", "content": "How do you handle knowledge management — learnings from past projects, reusable frameworks?"},
        {"role": "user", "content": "We don't, really. It's all in people's heads or scattered across Google Drives. We did a digital transformation project for a logistics company last year — brilliant work. Now we have a similar engagement coming up and I can't find half the deliverables. Every project we start from scratch. I know there's so much we could reuse — frameworks, benchmark data, presentation templates. We just have no system."},
        {"role": "assistant", "content": "What about client relationships and pipeline management?"},
        {"role": "user", "content": "I have a Google Sheet. Honestly, it's embarrassing for a consulting firm. No CRM, no pipeline tracking, no automated follow-ups. I keep relationships warm through personal LinkedIn messages. But I know we're leaving money on the table — past clients who'd buy more if we stayed in touch, warm leads that go cold because nobody followed up. My guess is we lose €10,000-15,000 per month in missed repeat business."},
        {"role": "assistant", "content": "How are you handling invoicing and financial management?"},
        {"role": "user", "content": "Stripe for payments, Xero for accounting. That part actually works okay. The problem is the gap between — I can't easily tell you which projects are profitable because time tracking is inconsistent. Some projects we've definitely undercharged on. I suspect our average effective hourly rate is closer to €100 when it should be €150, because of scope creep we don't track."},
        {"role": "assistant", "content": "If you could fix one thing about your operations, what would it be?"},
        {"role": "user", "content": "Proposal automation and a knowledge base. If we could cut proposal time from 5 hours to 1 hour using templates and AI, and if we could actually capture and reuse knowledge from past projects, it would fundamentally change our capacity. Right now I turn away work because we're at capacity — but half our time is spent on non-billable admin. Free that up and we could take on 2-3 more projects per quarter without hiring."},
        {"role": "assistant", "content": "What's your budget for technology improvements?"},
        {"role": "user", "content": "€400-600 per month. But honestly, if something could demonstrably save us 20+ hours per month of admin time, I'd go to €1,000. Our hourly rate is €150 — so 20 saved hours is €3,000 in recovered capacity. The ROI math is obvious, I just need to know what actually works and doesn't become another tool nobody uses."}
      ]
    },
    {
      "name": "Van Berg & Partners",
      "website": "https://vanberg-partners.nl",
      "country": "NL",
      "profile": {
        "tier": "mid",
        "industry": "professional-services",
        "staff_size": "11-50",
        "service_type": "accounting_advisory",
        "billing_model": "retainer_and_project",
        "client_count": 180,
        "compliance_requirements": ["GDPR", "Dutch_audit_standards", "NBA_regulations"],
        "monthly_revenue": 125000,
        "hourly_rate": 95,
        "current_tools": ["Exact Online", "Microsoft 365", "CaseWare", "Twinfield", "Teams"],
        "pain_points": ["annual audit bottleneck", "document collection from clients", "regulatory compliance tracking", "junior staff onboarding"]
      },
      "workshop_transcript": [
        {"role": "assistant", "content": "Thanks for making time. Let's start broad — tell me about Van Berg & Partners and how the firm operates today."},
        {"role": "user", "content": "We're a 22-person accounting and advisory firm in Rotterdam. Four partners, eight senior accountants, six juniors, and four admin staff. We do annual accounts, tax filing, audit, and business advisory for SMEs. About 180 active clients, mostly in the €1M-20M revenue range. We've been around for 15 years and we're growing steadily — added 25 new clients last year."},
        {"role": "assistant", "content": "What does your tech stack look like currently?"},
        {"role": "user", "content": "Exact Online for general ledger and client accounting. CaseWare for audit and compilation. Twinfield for some older clients we haven't migrated yet. Microsoft 365 for email, documents, Teams for internal chat. Everything is somewhat siloed — CaseWare doesn't talk to Exact, so our staff manually re-enter data during audit season. We also use a shared network drive for client documents, which is... a mess."},
        {"role": "assistant", "content": "Tell me about audit season. You mentioned that's a bottleneck?"},
        {"role": "user", "content": "January through April is brutal. We have about 60 clients that need annual accounts filed, and 20 that need full audits. The biggest time sink is document collection — chasing clients for bank statements, invoices, receipts. Our staff send an average of 15 follow-up emails per client. Some clients take 6-8 weeks to provide everything. Meanwhile our staff are idle on that engagement, waiting. Then everything comes in at once and we're overwhelmed."},
        {"role": "assistant", "content": "How much time would you estimate is spent on document collection and follow-up?"},
        {"role": "user", "content": "Conservatively? 800 hours per year across the firm. That's almost half an FTE just on follow-up emails and phone calls. We tried a client portal two years ago — Basecone — but adoption was terrible. Only about 30% of clients actually used it. The rest kept emailing PDFs or, worse, dropping off paper documents."},
        {"role": "assistant", "content": "What about compliance and regulatory changes — how do you stay on top of those?"},
        {"role": "user", "content": "That's a growing concern. Dutch accounting standards change regularly, and we need to ensure every engagement complies. Right now it's the partners' job to stay current and cascade changes to the team. But things slip through. Last year we had to redo three sets of annual accounts because of a reporting standard change we implemented late. That cost us probably €15,000 in unbilled time and significant client frustration."},
        {"role": "assistant", "content": "How do you onboard junior staff? You mentioned that as a pain point."},
        {"role": "user", "content": "It takes 6 months before a junior is truly productive. They learn by sitting with seniors, which pulls the seniors off billable work. We have no formal training system, no documented procedures. Every senior has their own way of doing things in CaseWare. When a senior leaves — which has happened twice in the past year — their clients' institutional knowledge walks out the door. We spent weeks trying to figure out how one departing senior had set up their CaseWare files."},
        {"role": "assistant", "content": "What would have the biggest impact on the firm if you could solve it?"},
        {"role": "user", "content": "Two things: automated document collection from clients, and standardized workflows in CaseWare with compliance checks built in. If clients could upload documents to a portal that actually worked — with AI that categorizes and matches documents to the right accounts — we'd save hundreds of hours. And if CaseWare had automated compliance checklists that updated with regulation changes, we'd eliminate those costly redo situations."},
        {"role": "assistant", "content": "Budget for technology improvements?"},
        {"role": "user", "content": "The partners have approved up to €1,500 per month for the right solution. But we need to see ROI within 6 months. We've been burned before — the Basecone implementation cost us €8,000 and we abandoned it. Whatever we do next needs a proper rollout plan with client training. Our clients are mostly small business owners, not tech people."}
      ]
    }
  ]
}
```

**Step 2: Verify the file loads correctly**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && python -c "import json; d=json.load(open('src/cli/seeds/professional-services.json')); print(f'Loaded {len(d[\"seeds\"])} professional-services seeds, tiers: {list(d[\"tiers\"].keys())}')"`

Expected: `Loaded 2 professional-services seeds, tiers: ['small', 'mid', 'scaling']`

**Step 3: Commit**

```bash
git add backend/src/cli/seeds/professional-services.json
git commit -m "feat: add professional services seed file with workshop transcripts"
```

---

## Task 3: Update E-commerce Seeds with Workshop Transcripts

**Files:**
- Modify: `backend/src/cli/seeds/ecommerce.json`

The existing e-commerce seeds have no `workshop_transcript` field. Add transcripts to 2 seeds — one small, one mid — so ecommerce has the same dev-mode fidelity as the new industries.

**Step 1: Add workshop transcript to BonBon Boutique (small tier)**

Add a `workshop_transcript` field to the first seed (BonBon Boutique, line 31). Insert after the `pain_points` array closing bracket (line 43) and before the closing brace of the seed object (line 44):

```json
"workshop_transcript": [
  {"role": "assistant", "content": "Let's start by understanding your business. What does BonBon Boutique sell and who are your customers?"},
  {"role": "user", "content": "We're a handmade jewelry brand based in Amsterdam. Everything is designed and made here — earrings, necklaces, bracelets. Our customers are mostly women 25-45, gift buyers, and tourists who find us on Instagram. We do about 250 orders a month through Shopify, average order is around €85."},
  {"role": "assistant", "content": "Walk me through what happens when an order comes in."},
  {"role": "user", "content": "An order hits Shopify, I get a notification. My assistant prints the packing slip, picks the items from our studio shelves, wraps them — we do premium gift wrapping for every order — and drops them at PostNL. For personalized items, which are about 30% of orders, I engrave them myself, which adds 1-2 days. The whole process is manual. I spend 2-3 hours daily on fulfillment instead of designing new pieces."},
  {"role": "assistant", "content": "What about customer questions and support?"},
  {"role": "user", "content": "I handle them myself through Shopify chat and Instagram DMs. Maybe 15-20 messages per day. Most are 'when will my order arrive' or 'do you have this in gold' or 'can I customize this.' Very repetitive. But I feel like I need to answer personally because our brand is about that personal touch. I'm just running out of hours in the day."},
  {"role": "assistant", "content": "Tell me about your marketing. You mentioned Instagram — how does that work?"},
  {"role": "user", "content": "Instagram is our main channel. I post 4-5 times a week, do stories daily. We have about 18,000 followers. I also run Meta ads — spending maybe €800/month — but I have no idea what's actually working. I just boost posts that get good organic engagement. No email marketing at all, which I know is a mistake. We collect emails at checkout but never send anything."},
  {"role": "assistant", "content": "You mentioned no email marketing — what's holding you back?"},
  {"role": "user", "content": "Time, mostly. I know I should set up abandoned cart emails and a welcome series. I looked at Klaviyo but it felt overwhelming. I'm not a marketer, I'm a jewelry designer. I tried Mailchimp once but the template looked terrible and I gave up. I have a list of 4,000 email addresses just sitting there doing nothing. My friend who runs a similar brand says email is 30% of her revenue."},
  {"role": "assistant", "content": "That's a big missed opportunity. What about product content — descriptions, photos?"},
  {"role": "user", "content": "I photograph everything myself with my iPhone. It actually looks pretty good for Instagram, but for the website product pages... I have 120 products and each one needs 4-5 photos, a description, materials, sizing. I'm about 40 products behind on proper descriptions. For new launches I spend a whole day just on content creation. I know AI could help with writing descriptions but I haven't tried it yet."},
  {"role": "assistant", "content": "What would make the biggest difference for your business right now?"},
  {"role": "user", "content": "Getting email marketing running and automating the repetitive customer questions. Those two things alone would probably add €3,000-5,000 per month in revenue and give me back 2 hours a day. I'd use that time to design new collections, which is what actually grows the business. I just need someone to tell me exactly what to set up and make it simple."}
]
```

**Step 2: Add workshop transcript to Filling Pieces (mid tier)**

Add a `workshop_transcript` field to the Filling Pieces seed (line 181). Insert after the `pain_points` array and before the closing brace:

```json
"workshop_transcript": [
  {"role": "assistant", "content": "Filling Pieces is a well-known brand. Can you describe the current state of operations?"},
  {"role": "user", "content": "We're a premium sneaker brand, about 30 people now. Direct-to-consumer through Shopify plus wholesale to about 150 retailers globally. Monthly we do around 3,000 DTC orders and manage wholesale separately through a B2B portal. Revenue is roughly €400K/month DTC and €200K wholesale. We're growing fast but our backend can't keep up."},
  {"role": "assistant", "content": "What does 'backend can't keep up' mean specifically?"},
  {"role": "user", "content": "Our inventory is a mess. We have one warehouse in Amsterdam and we dropship some products. But there's no real-time sync between Shopify, our wholesale orders, and actual warehouse stock. Last month we oversold 3 SKUs — had to cancel orders and refund customers. That's a brand killer for a premium product. We also carry about €200K in dead stock from poor demand planning."},
  {"role": "assistant", "content": "How are you managing wholesale alongside DTC?"},
  {"role": "user", "content": "Honestly, with spreadsheets and email. Retailers email orders, our wholesale team enters them into a Google Sheet, then someone manually reserves inventory. If a retailer orders 50 pairs of a popular style, we might already have sold 30 of those DTC by the time we process it. There's no integration between the two channels. Our wholesale coordinator spends 80% of her time on manual data entry."},
  {"role": "assistant", "content": "Tell me about your customer experience tech stack."},
  {"role": "user", "content": "Klaviyo for email — we're actually pretty good there, maybe 25% of revenue. Shopify for the storefront. Google Analytics for basic tracking. But we have no customer service platform — support goes to a shared inbox. We get maybe 200 tickets a month and it's chaos. Multiple people responding, no tracking, customers sometimes get two different answers. We looked at Gorgias but haven't pulled the trigger."},
  {"role": "assistant", "content": "What's the team's biggest frustration day-to-day?"},
  {"role": "user", "content": "Tool sprawl. We have 15+ different tools that don't talk to each other. Marketing uses different data than ops, finance has their own numbers. Nobody trusts the data. I spend Friday afternoons manually building a dashboard in Google Sheets that's already outdated by Monday. We need a single source of truth. An ERP maybe? But that feels like a massive project and we're already stretched thin."},
  {"role": "assistant", "content": "What's your priority for the next 6 months?"},
  {"role": "user", "content": "Fix inventory management and get wholesale integrated before it costs us a major retail partner. After that, customer service platform and better analytics. Budget is there — we could do €2,000-3,000/month in software. The problem isn't money, it's time and knowing what to pick. Every vendor says they're the solution. I need someone to cut through the noise and give me a clear roadmap."}
]
```

**Step 3: Verify transcripts load correctly**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && python -c "import json; d=json.load(open('src/cli/seeds/ecommerce.json')); seeds_with_ws=[s['name'] for s in d['seeds'] if s.get('workshop_transcript')]; print(f'Seeds with transcripts: {seeds_with_ws}')"`

Expected: `Seeds with transcripts: ['BonBon Boutique', 'Filling Pieces']`

**Step 4: Commit**

```bash
git add backend/src/cli/seeds/ecommerce.json
git commit -m "feat: add workshop transcripts to ecommerce seeds (BonBon, Filling Pieces)"
```

---

## Task 4: Generalize the Fabricator for Multi-Industry

**Files:**
- Modify: `backend/src/cli/fabricator.py` (entire file)
- Test: `cd backend && python -c "from src.cli.fabricator import fabricate_quiz_session; print('import ok')"`

**Step 1: Rewrite `fabricator.py` to support all three industries**

Replace the entire contents of `backend/src/cli/fabricator.py` with:

```python
"""
Quiz Answer Fabricator — Multi-Industry

Converts seed business profiles + optional scraped website data
into realistic quiz_session data for the report pipeline.
Supports: ecommerce, dental, professional-services.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.skills.base import COUNTRY_CURRENCY_MAP


# ============================================================================
# E-COMMERCE CONSTANTS
# ============================================================================

CATEGORY_AOV = {
    "fashion": 85,
    "electronics": 150,
    "health": 65,
    "beauty": 55,
    "home": 120,
    "food": 45,
    "sports": 95,
    "pets": 60,
    "jewelry": 200,
    "kids": 70,
    "general": 80,
}

# ============================================================================
# SHARED CONSTANTS
# ============================================================================

COUNTRY_HOURLY_COST = {
    "NL": 45, "DE": 45, "FR": 40, "BE": 42,
    "UK": 40, "GB": 40,
    "US": 55, "CA": 50,
    "AU": 50, "NZ": 45,
}


def fabricate_quiz_session(
    seed: Dict[str, Any],
    tier_defaults: Dict[str, Any],
    scraped_data: Optional[Dict[str, Any]] = None,
    report_tier: str = "quick",
) -> Dict[str, Any]:
    """
    Build a complete quiz_session dict from seed + scraped data.

    Dispatches to industry-specific answer builders based on
    seed["profile"]["industry"]. Falls back to ecommerce for
    backward compatibility with seeds that lack an industry field.
    """
    profile = seed["profile"]
    industry = profile.get("industry", "ecommerce")
    country = seed.get("country", "NL")
    currency = COUNTRY_CURRENCY_MAP.get(country, "EUR")
    hourly_cost = COUNTRY_HOURLY_COST.get(country, tier_defaults.get("hourly_cost", 40))

    pain_points = profile.get("pain_points") or tier_defaults.get("pain_points", [])

    # Build industry-specific answers
    answers = _build_answers(industry, profile, tier_defaults, pain_points, hourly_cost, currency)

    # Build company profile
    company_profile = _build_company_profile(seed, profile, industry, scraped_data)

    # Build interview data from workshop transcript
    interview_data = _build_interview_data(seed)

    now = datetime.now(timezone.utc).isoformat()

    return {
        "id": str(uuid.uuid4()),
        "email": f"cli-{uuid.uuid4().hex[:8]}@crb-analyser.local",
        "tier": report_tier,
        "status": "paid",
        "current_section": 0,
        "current_question": 0,
        "answers": answers,
        "results": {},
        "company_name": seed["name"],
        "company_website": seed.get("website", ""),
        "company_profile": company_profile,
        "existing_stack": _build_existing_stack(profile),
        "interview_data": interview_data,
        "created_at": now,
        "updated_at": now,
    }


def _build_answers(
    industry: str,
    profile: Dict[str, Any],
    tier_defaults: Dict[str, Any],
    pain_points: List[str],
    hourly_cost: int,
    currency: str,
) -> Dict[str, Any]:
    """Build the answers dict based on industry."""
    # Common fields across all industries
    base = {
        "industry": industry,
        "company_size": profile.get("staff_size", "1-10"),
        "current_tools": profile.get("current_tools", []),
        "pain_points": pain_points,
        "biggest_challenge": pain_points[0] if pain_points else "operational efficiency",
        "monthly_revenue": profile.get("monthly_revenue", 50000),
        "hourly_rate": profile.get("hourly_rate", hourly_cost),
        "budget": tier_defaults.get("budget", 1000),
        "currency": currency,
    }

    if industry == "ecommerce":
        category = profile.get("product_category", "general")
        aov = CATEGORY_AOV.get(category, CATEGORY_AOV["general"])
        monthly_orders = profile.get("monthly_orders", 300)
        base.update({
            "monthly_revenue": monthly_orders * aov,
            "platform": profile.get("platform", "shopify"),
            "has_erp": profile.get("has_erp", False),
            "product_category": category,
            "monthly_orders": monthly_orders,
        })

    elif industry == "dental":
        base.update({
            "practice_type": profile.get("practice_type", "general_dentistry"),
            "locations": profile.get("locations", 1),
            "patient_volume": profile.get("patient_volume", 200),
            "insurance_mix": profile.get("insurance_mix", "mixed"),
        })

    elif industry == "professional-services":
        base.update({
            "service_type": profile.get("service_type", "consulting"),
            "billing_model": profile.get("billing_model", "hourly"),
            "client_count": profile.get("client_count", 50),
            "compliance_requirements": profile.get("compliance_requirements", []),
        })

    return base


def _build_company_profile(
    seed: Dict[str, Any],
    profile: Dict[str, Any],
    industry: str,
    scraped_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the company_profile dict from scraped data or seed."""
    if scraped_data:
        return {
            "description": scraped_data.get("description", ""),
            "products": scraped_data.get("products", []),
            "visible_tech": scraped_data.get("visible_tech", []),
            "source": "cli_scraper",
            **{k: v for k, v in scraped_data.items()
               if k not in ("description", "products", "visible_tech")},
        }

    # Industry-specific descriptions
    if industry == "dental":
        locations = profile.get("locations", 1)
        loc_str = f"{locations} location{'s' if locations > 1 else ''}"
        desc = f"{seed['name']} — {profile.get('practice_type', 'general dentistry').replace('_', ' ')} with {loc_str}"
    elif industry == "professional-services":
        desc = f"{seed['name']} — {profile.get('service_type', 'consulting').replace('_', ' ')} firm"
    else:
        category = profile.get("product_category", "general")
        desc = f"{seed['name']} — {category} e-commerce store"

    return {
        "description": desc,
        "products": [],
        "visible_tech": profile.get("current_tools", []),
        "source": "seed_only",
    }


def _build_interview_data(seed: Dict[str, Any]) -> Dict[str, Any]:
    """Build interview_data from workshop transcript if available."""
    transcript = seed.get("workshop_transcript", [])
    if not transcript:
        return {"messages": [], "confidence": {}}

    return {
        "messages": transcript,
        "confidence": {
            "overall": 0.85,
            "tools": 0.9,
            "pain_points": 0.85,
            "budget": 0.8,
            "workflows": 0.85,
        },
    }


def _build_existing_stack(profile: Dict[str, Any]) -> list:
    """Build existing_stack list from seed tools."""
    tools = profile.get("current_tools", [])
    return [
        {"name": tool, "slug": tool.lower().replace(" ", "-"), "api_score": 3}
        for tool in tools
    ]
```

**Step 2: Verify the refactored fabricator imports and works**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && python -c "
from src.cli.fabricator import fabricate_quiz_session
import json

# Test with existing ecommerce seed format (backward compat)
seed = {'name': 'Test', 'country': 'NL', 'profile': {'tier': 'small', 'staff_size': '1-10', 'monthly_orders': 200, 'product_category': 'fashion', 'current_tools': ['shopify'], 'pain_points': ['manual work']}}
defaults = {'budget': 500, 'hourly_cost': 40, 'pain_points': ['test']}
result = fabricate_quiz_session(seed, defaults)
assert result['answers']['industry'] == 'ecommerce', 'Should default to ecommerce'
assert result['answers']['monthly_revenue'] == 200 * 85, 'AOV calc should work'
assert result['interview_data'] == {'messages': [], 'confidence': {}}, 'No transcript = empty'
print('Ecommerce backward compat: OK')

# Test with dental seed
seed2 = {'name': 'Test Dental', 'country': 'NL', 'profile': {'industry': 'dental', 'tier': 'small', 'staff_size': '1-10', 'practice_type': 'general_dentistry', 'locations': 1, 'patient_volume': 120, 'monthly_revenue': 28000, 'current_tools': ['Exquise'], 'pain_points': ['no-shows']}, 'workshop_transcript': [{'role': 'user', 'content': 'test'}]}
result2 = fabricate_quiz_session(seed2, defaults)
assert result2['answers']['industry'] == 'dental'
assert result2['answers']['practice_type'] == 'general_dentistry'
assert len(result2['interview_data']['messages']) == 1, 'Should include transcript'
print('Dental: OK')
print('All tests passed')
"`

Expected: All three assertions pass, output ends with `All tests passed`

**Step 3: Commit**

```bash
git add backend/src/cli/fabricator.py
git commit -m "refactor: generalize fabricator for multi-industry seed support"
```

---

## Task 5: Extend CLI with --industry and --all-industries Flags

**Files:**
- Modify: `backend/src/cli/generate_report.py` (entire file)

**Step 1: Rewrite `generate_report.py` to support multi-industry**

Replace the entire contents of `backend/src/cli/generate_report.py` with:

```python
"""
CRB Report Generator CLI

Generate full CRB reports for testing across industries.

Usage:
    # Single report by industry (random seed)
    python -m src.cli.generate_report --industry dental
    python -m src.cli.generate_report --industry ecommerce --tier mid
    python -m src.cli.generate_report --industry professional-services

    # Default: ecommerce (backward compatible)
    python -m src.cli.generate_report --tier small

    # Single report from URL (ecommerce only)
    python -m src.cli.generate_report --url https://store.com --country NL --staff 1-10

    # Batch: one per industry
    python -m src.cli.generate_report --batch --all-industries

    # Batch: multiple from one industry
    python -m src.cli.generate_report --batch --industry dental --count 3
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()  # Must be before src.* imports

from src.cli.fabricator import fabricate_quiz_session
from src.cli.scraper import scrape_ecommerce_site
from src.config.supabase_client import get_async_supabase
from src.services.report_service import generate_report_streaming

logger = logging.getLogger(__name__)

SEEDS_DIR = Path(__file__).parent / "seeds"

SUPPORTED_INDUSTRIES = ["ecommerce", "dental", "professional-services"]


def load_seeds(industry: str = "ecommerce") -> Dict[str, Any]:
    """Load seed list for a given industry."""
    seeds_file = SEEDS_DIR / f"{industry}.json"
    if not seeds_file.exists():
        print(f"No seed file found for industry '{industry}' at {seeds_file}")
        print(f"Available: {', '.join(list_available_industries())}")
        sys.exit(1)
    with open(seeds_file) as f:
        return json.load(f)


def list_available_industries() -> List[str]:
    """List industries that have seed files."""
    return [p.stem for p in sorted(SEEDS_DIR.glob("*.json"))]


def pick_seed(seeds_data: Dict[str, Any], tier: Optional[str] = None) -> Dict[str, Any]:
    """Pick a random seed, optionally filtered by tier."""
    all_seeds = seeds_data["seeds"]
    if tier:
        filtered = [s for s in all_seeds if s["profile"]["tier"] == tier]
        if not filtered:
            tiers = sorted(set(s["profile"]["tier"] for s in all_seeds))
            print(f"No seeds found for tier '{tier}'. Available tiers: {', '.join(tiers)}")
            sys.exit(1)
        return random.choice(filtered)
    return random.choice(all_seeds)


def print_header(name: str, url: str, tier: str, country: str, staff: str, industry: str) -> None:
    """Print report generation header."""
    print(f"\n{'=' * 60}")
    print(f"  CRB Report Generator")
    print(f"{'=' * 60}")
    print(f"  Target:    {name}")
    print(f"  Industry:  {industry}")
    print(f"  URL:       {url}")
    print(f"  Profile:   {tier} | {country} | {staff} staff")
    print(f"{'=' * 60}\n")


def print_progress(data: Dict[str, Any]) -> None:
    """Print a progress update line."""
    progress = data.get("progress", 0)
    step = data.get("step", "")

    bar_width = 20
    filled = int(bar_width * progress / 100)
    bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

    print(f"  [{bar}] {progress:3d}%  {step}", end="\r", flush=True)

    if data.get("phase_complete"):
        print()


async def generate_single_report(
    seed: Dict[str, Any],
    seeds_data: Dict[str, Any],
    report_tier: str = "quick",
    scrape: bool = True,
    skip_review: bool = False,
    use_playwright: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Generate a single report from a seed.

    Returns dict with report_id, findings_count, ai_readiness, etc.
    """
    profile = seed["profile"]
    tier = profile["tier"]
    industry = profile.get("industry", seeds_data.get("industry", "ecommerce"))
    tier_defaults = seeds_data["tiers"][tier]["defaults"]

    print_header(
        name=seed["name"],
        url=seed.get("website", "N/A"),
        tier=tier,
        country=seed.get("country", "?"),
        staff=profile.get("staff_size", "?"),
        industry=industry,
    )

    # Step 1: Scrape website (only for ecommerce with websites)
    scraped_data = None
    if scrape and seed.get("website") and industry == "ecommerce":
        print("  Scraping website...", end="", flush=True)
        if use_playwright:
            from src.skills.browser.enhanced_scraper import EnhancedScraperSkill
            from src.skills.base import SkillContext
            scraper = EnhancedScraperSkill()
            scrape_context = SkillContext(
                industry="ecommerce",
                metadata={"url": seed["website"]}
            )
            result = await scraper.run(scrape_context)
            if result.success:
                scraped_data = result.data
                tech = scraped_data.get("visible_tech", [])
                method = scraped_data.get("scrape_method", "unknown")
                print(f" done via {method} ({len(tech)} technologies detected)")
            else:
                print(f" failed, using seed data only")
                scraped_data = None
        else:
            scraped_data = await scrape_ecommerce_site(seed["website"])
            if scraped_data.get("success"):
                tech = scraped_data.get("visible_tech", [])
                print(f" done ({len(tech)} technologies detected)")
            else:
                print(f" failed ({scraped_data.get('error', 'unknown')}), using seed data only")
                scraped_data = None

    # Workshop transcript info
    transcript = seed.get("workshop_transcript", [])
    if transcript:
        print(f"  Workshop transcript: {len(transcript)} messages loaded")
    else:
        print(f"  Workshop transcript: none (report will have less context)")

    # Step 2: Fabricate quiz session
    session_data = fabricate_quiz_session(seed, tier_defaults, scraped_data, report_tier)
    session_id = session_data["id"]

    # Step 3: Insert into Supabase
    print("  Creating quiz session...", end="", flush=True)
    supabase = await get_async_supabase()
    await supabase.table("quiz_sessions").insert(session_data).execute()
    print(f" done (id: {session_id[:8]}...)")

    # Step 4: Generate report
    print("\n  Generating report:\n")
    start_time = time.time()
    report_id = None
    last_phase = None
    error = None

    async for event in generate_report_streaming(session_id, report_tier, skip_review=skip_review):
        if not event.startswith("data: "):
            continue

        try:
            data = json.loads(event[6:].strip())
        except json.JSONDecodeError:
            continue

        phase = data.get("phase", "")
        if phase != last_phase and last_phase is not None:
            print()
        last_phase = phase

        if data.get("report_id"):
            report_id = data["report_id"]

        if data.get("phase") == "error" or data.get("error"):
            error = data.get("error", "Unknown error")
            break

        print_progress(data)

    elapsed = time.time() - start_time
    print("\n")

    if error:
        print(f"  ERROR: {error}")
        return None

    print(f"{'=' * 60}")
    print(f"  Complete")
    print(f"{'=' * 60}")
    print(f"  Report ID:    {report_id}")
    print(f"  Session ID:   {session_id}")
    print(f"  Industry:     {industry}")
    print(f"  Transcript:   {len(transcript)} messages")
    print(f"  Total Time:   {elapsed:.1f}s")
    print(f"{'=' * 60}\n")

    return {
        "report_id": report_id,
        "session_id": session_id,
        "company": seed["name"],
        "industry": industry,
        "tier": tier,
        "elapsed": elapsed,
    }


async def generate_from_url(
    url: str,
    country: str = "NL",
    staff_size: str = "11-50",
    report_tier: str = "quick",
    skip_review: bool = False,
    use_playwright: bool = False,
) -> Optional[Dict[str, Any]]:
    """Generate a report from a custom URL (ecommerce only)."""
    seed = {
        "name": url.replace("https://", "").replace("http://", "").split("/")[0],
        "website": url,
        "country": country,
        "profile": {
            "tier": "mid",
            "industry": "ecommerce",
            "staff_size": staff_size,
            "monthly_orders": 500,
            "platform": "unknown",
            "product_category": "general",
            "has_erp": False,
            "current_tools": [],
            "pain_points": [],
        }
    }

    seeds_data = {
        "industry": "ecommerce",
        "tiers": {
            "mid": {"defaults": {"budget": 2000, "hourly_cost": 50,
                                 "pain_points": ["scaling operations", "customer service volume",
                                                 "manual processes"]}}
        }
    }

    return await generate_single_report(seed, seeds_data, report_tier, scrape=True, skip_review=skip_review, use_playwright=use_playwright)


async def cmd_single(args: argparse.Namespace) -> None:
    """Generate a single report."""
    if args.url:
        result = await generate_from_url(
            url=args.url,
            country=args.country,
            staff_size=args.staff,
            report_tier=args.report_tier,
            skip_review=args.no_review,
            use_playwright=args.playwright,
        )
    else:
        seeds_data = load_seeds(args.industry)
        seed = pick_seed(seeds_data, args.tier)
        result = await generate_single_report(
            seed, seeds_data, args.report_tier,
            skip_review=args.no_review, use_playwright=args.playwright,
        )

    if not result:
        sys.exit(1)


async def cmd_batch(args: argparse.Namespace) -> None:
    """Generate multiple reports."""
    if args.all_industries:
        industries = list_available_industries()
    else:
        industries = [args.industry]

    results = []
    total_count = 0

    for industry in industries:
        seeds_data = load_seeds(industry)
        count = 1 if args.all_industries else args.count

        for i in range(count):
            total_count += 1
            print(f"\n{'\u2500' * 60}")
            print(f"  Report {total_count} — {industry}")
            print(f"{'\u2500' * 60}")

            seed = pick_seed(seeds_data, args.tier)
            result = await generate_single_report(
                seed, seeds_data, args.report_tier,
                skip_review=args.no_review, use_playwright=args.playwright,
            )

            if result:
                results.append(result)
            else:
                print(f"  Skipping failed report, continuing batch...")

    # Print batch summary
    print(f"\n{'=' * 70}")
    print(f"  Batch Complete: {len(results)}/{total_count} reports generated")
    print(f"{'=' * 70}")
    print(f"  {'Company':30s}  {'Industry':22s}  {'Tier':8s}  {'Time':>6s}  {'Report ID'}")
    print(f"  {'-'*30}  {'-'*22}  {'-'*8}  {'-'*6}  {'-'*10}")
    for r in results:
        rid = r['report_id'][:8] if r['report_id'] else 'N/A'
        print(f"  {r['company']:30s}  {r['industry']:22s}  {r['tier']:8s}  {r['elapsed']:5.1f}s  {rid}...")
    total_time = sum(r["elapsed"] for r in results)
    print(f"\n  Total time: {total_time:.1f}s ({total_time / 60:.1f} min)")
    print(f"{'=' * 70}\n")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CRB Report Generator — generate full reports across industries"
    )

    # Mode selection
    parser.add_argument("--batch", action="store_true", help="Generate multiple reports")
    parser.add_argument("--count", type=int, default=5, help="Number of reports in batch mode (default: 5)")

    # Industry & seed selection
    parser.add_argument("--industry", default="ecommerce",
                        help=f"Industry to generate for (available: {', '.join(SUPPORTED_INDUSTRIES)})")
    parser.add_argument("--all-industries", action="store_true",
                        help="Generate one report per available industry (batch mode)")
    parser.add_argument("--tier", choices=["small", "mid", "scaling"], help="Business tier filter")

    # Custom URL mode (ecommerce only)
    parser.add_argument("--url", help="Custom website URL (ecommerce only, overrides seed list)")
    parser.add_argument("--country", default="NL", help="Country code for URL mode (default: NL)")
    parser.add_argument("--staff", default="11-50", help="Staff size for URL mode (default: 11-50)")

    # Report options
    parser.add_argument("--report-tier", choices=["quick", "full"], default="quick",
                        help="Report tier (default: quick)")
    parser.add_argument("--no-scrape", action="store_true", help="Skip website scraping")
    parser.add_argument("--no-review", action="store_true",
                        help="Skip review/validation phase for faster iteration")
    parser.add_argument("--playwright", action="store_true",
                        help="Use Playwright for JS-rendered scraping (ecommerce only)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    # Route to command
    if args.batch or args.all_industries:
        asyncio.run(cmd_batch(args))
    else:
        asyncio.run(cmd_single(args))


if __name__ == "__main__":
    main()
```

**Step 2: Verify CLI help works**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && python -m src.cli.generate_report --help`

Expected output should include `--industry`, `--all-industries`, and list supported industries.

**Step 3: Verify industry loading works**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && python -c "
from src.cli.generate_report import load_seeds, list_available_industries, pick_seed
print('Available industries:', list_available_industries())
for ind in ['ecommerce', 'dental', 'professional-services']:
    data = load_seeds(ind)
    seed = pick_seed(data)
    print(f'{ind}: picked {seed[\"name\"]} ({seed[\"profile\"][\"tier\"]})')
"`

Expected: Lists all three industries and picks a seed from each.

**Step 4: Commit**

```bash
git add backend/src/cli/generate_report.py
git commit -m "feat: extend CLI with --industry and --all-industries flags"
```

---

## Task 6: Add Makefile Targets

**Files:**
- Modify: `Makefile:1` (update .PHONY) and add new targets after line 26

**Step 1: Update .PHONY line**

On line 1 of `Makefile`, add `dev-report dev-report-all` to the .PHONY list.

Change:
```makefile
.PHONY: test test-backend test-frontend lint typecheck dev generate-report ui-test ui-test-headed playwright-install playwright-cli-install generate-report-playwright research-vendor test-all
```

To:
```makefile
.PHONY: test test-backend test-frontend lint typecheck dev generate-report dev-report dev-report-all ui-test ui-test-headed playwright-install playwright-cli-install generate-report-playwright research-vendor test-all
```

**Step 2: Add dev-report and dev-report-all targets**

Insert after the `generate-report` target (after line 26), before the `# Browser automation` comment:

```makefile

# Dev mode report generation (multi-industry)
dev-report:
	@echo "Generating $(or $(INDUSTRY),ecommerce) report..."
	cd backend && python -m src.cli.generate_report --industry $(or $(INDUSTRY),ecommerce) $(ARGS)

dev-report-all:
	@echo "Generating one report per industry..."
	cd backend && python -m src.cli.generate_report --batch --all-industries $(ARGS)

```

**Step 3: Verify Makefile syntax**

Run: `make -n dev-report INDUSTRY=dental` (dry run)

Expected: Shows the command that would execute without actually running it.

Run: `make -n dev-report-all`

Expected: Shows the all-industries batch command.

**Step 4: Commit**

```bash
git add Makefile
git commit -m "feat: add dev-report and dev-report-all Makefile targets"
```

---

## Task 7: Smoke Test — Generate One Report Per Industry

This is the final verification. Run each industry through the real pipeline.

**Step 1: Generate a dental report**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser && make dev-report INDUSTRY=dental ARGS="--no-review --report-tier quick"`

Expected: Report generates successfully with a report ID. Watch for:
- "Workshop transcript: X messages loaded" in the output
- No errors during generation
- Report ID printed at the end

**Step 2: Generate a professional-services report**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser && make dev-report INDUSTRY=professional-services ARGS="--no-review --report-tier quick"`

Expected: Same as above — successful generation with report ID.

**Step 3: Generate an ecommerce report (backward compat)**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser && make dev-report ARGS="--no-review --report-tier quick"`

Expected: Works without specifying industry (defaults to ecommerce).

**Step 4: Test all-industries batch**

Run: `cd /Users/larsmusic/CRB\ Analyser/crb-analyser && make dev-report-all ARGS="--no-review --report-tier quick"`

Expected: Generates 3 reports (one per industry), prints batch summary table.

**Step 5: Commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address smoke test findings for multi-industry dev mode"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Dental seeds + transcripts | `backend/src/cli/seeds/dental.json` |
| 2 | Prof services seeds + transcripts | `backend/src/cli/seeds/professional-services.json` |
| 3 | Add transcripts to ecommerce seeds | `backend/src/cli/seeds/ecommerce.json` |
| 4 | Generalize fabricator | `backend/src/cli/fabricator.py` |
| 5 | Extend CLI with --industry | `backend/src/cli/generate_report.py` |
| 6 | Makefile targets | `Makefile` |
| 7 | Smoke test all 3 industries | (verification only) |

**Total new/modified files:** 6
**No changes to:** `report_service.py`, frontend, database schema
