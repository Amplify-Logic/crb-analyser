# Vendor Research Handoff - 2026-01-04

## Mission
Research and import HIGH QUALITY vendor data for each industry in the CRB Analyser knowledge base. Each vendor must have VERIFIED pricing, ratings, and features from authoritative sources (G2, Capterra, official websites).

## Completed Industries ✅

| Industry | Vendors | Script Location |
|----------|---------|-----------------|
| **dental** | 17 | `backend/src/scripts/import_dental_vendors.py` |
| **recruitment** | 21 | `backend/src/scripts/import_recruitment_vendors.py` |
| **professional-services** | 22 | `backend/src/scripts/import_professional_services_vendors.py` |
| **home-services** | 13 | `backend/src/scripts/import_home_services_vendors.py` |
| **coaching** | 11 | `backend/src/scripts/import_coaching_vendors.py` |
| **veterinary** | 10 | `backend/src/scripts/import_veterinary_vendors.py` |
| **physical-therapy** | 12 | `backend/src/scripts/import_physical_therapy_vendors.py` |
| **medspa** | 11 | `backend/src/scripts/import_medspa_vendors.py` |

**Total imported: 117 vendors across 8 industries** ✅

---

## Session Summaries

### Session 2 (Continued 2026-01-04)

**Physical Therapy (12 vendors):**
- Tier 1: WebPT, Jane App, Prompt Health, ChiroTouch
- Tier 2: SimplePractice, Practice Better, TheraOffice, Clinicient Insight
- Tier 3: Raintree Systems, SPRY, Juvonno, Zanda

**MedSpa (11 vendors):**
- Tier 1: Mangomint, Vagaro, Boulevard
- Tier 2: Zenoti, AestheticsPro, Aesthetic Record, GlossGenius
- Tier 3: Fresha, Pabau, Meevo, Square Appointments

### Session 1 (2026-01-04)

**Home Services (13 vendors):**
- Tier 1: Housecall Pro, Jobber, ServiceTitan
- Tier 2: Service Fusion, ServiceM8, Workiz, FieldPulse, FieldEdge, Zuper
- Tier 3: mHelpDesk, Kickserv, GorillaDesk, Simpro

**Coaching (11 vendors):**
- Tier 1: CoachAccountable, Paperbell, HoneyBook
- Tier 2: Practice.do, Satori, Simply.Coach, CoachingLoft, Trafft
- Tier 3: Coaches Console, CoachHub, EZRA

**Veterinary (10 vendors + Weave linked):**
- Tier 1: ezyVet, Shepherd, Digitail
- Tier 2: VetPort, Covetrus Pulse, DaySmart Vet, Instinct Science, Weave
- Tier 3: AVImark, Cornerstone, Neo

---

## All Industries Complete! 🎉

All planned industries now have vendor data imported. Future work could include:
- Adding more niche vendors to existing industries
- Refreshing pricing data quarterly
- Adding new industries as CRB expands

## Research Methodology

### Step 1: Web Search (3-4 searches per industry)
```
"best [industry] software 2025 2026 G2 reviews pricing"
"[key vendor] pricing cost per user 2025"
"[industry] practice management software reviews Capterra"
```

### Step 2: Verify from Sources
- G2.com ratings and review counts
- Capterra ratings
- Official pricing pages
- Software Advice reviews

### Step 3: Create Import Script
Pattern from existing scripts:
```python
# backend/src/scripts/import_[industry]_vendors.py
VENDORS = [
    {
        "slug": "vendor-name",
        "name": "Vendor Name",
        "category": "category_slug",
        "website": "https://...",
        "pricing": {
            "model": "subscription",
            "starting_price": 49,
            "currency": "USD",
            "free_tier": False,
            "tiers": [...]
        },
        "g2_score": 4.5,
        "our_rating": 4.3,
        "tier": 1,  # 1=Highly Recommended, 2=Worth Considering, 3=Niche
        ...
    }
]
```

### Step 4: Run Import
```bash
cd backend && source venv/bin/activate
python -m src.scripts.import_[industry]_vendors
```

## Quality Requirements

**CRITICAL - Every vendor MUST have:**
- ✅ Verified starting price (from official site or recent review)
- ✅ G2 or Capterra rating with review count
- ✅ Clear category assignment
- ✅ Best-for use cases
- ✅ Key capabilities (5-8 items)
- ✅ Known integrations

**DO NOT:**
- ❌ Guess pricing - mark as "Contact Sales" if not public
- ❌ Include vendors without verifiable websites
- ❌ Skip tier assignments

## Vendor Categories Available

From `CLAUDE.md`:
- `crm`, `customer_support`, `ai_sales_tools`, `automation`, `analytics`
- `ecommerce`, `finance`, `hr_payroll`, `marketing`, `project_management`
- `ai_assistants`, `ai_agents`, `ai_content_creation`, `dev_tools`

Industry-specific (create as needed):
- `field_service_management`, `veterinary_practice_management`
- `coaching_platform`, `medspa_management`, `pt_practice_management`

## Example Prompt for Next Session

```
Continue vendor research for CRB Analyser. Read the handoff at:
docs/handoffs/2026-01-04-vendor-research-handoff.md

Start with home-services industry. Research these vendors with VERIFIED pricing:
- ServiceTitan
- Housecall Pro
- Jobber
- FieldEdge
- ServiceM8
- Workiz
- Service Fusion
- mHelpDesk

Create import script and run it. Then proceed to remaining industries.
```

## Files Reference

- Industry definitions: `backend/src/knowledge/__init__.py`
- Vendor model: `backend/src/models/vendor.py`
- Admin routes: `backend/src/routes/admin_vendors.py`
- Example scripts: `backend/src/scripts/import_dental_vendors.py`

## Database Tables

- `vendors` - Main vendor catalog
- `industry_vendor_tiers` - Tier assignments per industry (1/2/3)
- `vendor_audit_log` - Change tracking
