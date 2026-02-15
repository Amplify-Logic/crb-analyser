# AGENT 5: Integrations & Services

> **Mission:** Connect all external services seamlessly - Stripe for payments, SendGrid for emails, PDF generation for reports. Make the customer journey smooth from payment to delivery.

---

## Context

**Product:** CRB Analyser - AI-powered Cost/Risk/Benefit analysis
**Price Point:** €147 one-time payment
**Flow:** Quiz → Payment → Report Generation → Email Delivery → PDF Download

**External Services:**
- Stripe (Payments)
- SendGrid (Transactional Email)
- PDF Generation (Server-side)
- Supabase Storage (File hosting)

---

## Current State

```
backend/src/routes/
├── payment_routes.py    # Basic Stripe checkout
└── report_routes.py     # PDF endpoint (basic)

No email integration currently
No proper PDF generation
```

**What Works:**
- Basic Stripe checkout session creation
- Simple payment verification

**What's Missing:**
- Stripe webhook handling (critical for reliability)
- Email notifications at key stages
- Professional PDF generation
- Receipt/invoice generation
- Retry logic for failed operations

---

## Target State

### 1. Stripe Integration (Complete)

**Payment Flow:**
```
1. User completes quiz
2. Frontend creates checkout session
3. User pays on Stripe hosted page
4. Stripe webhook confirms payment
5. System triggers report generation
6. Email sent with progress link
```

**Checkout Session Creation:**
```python
@router.post("/create-checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Create Stripe checkout session for quiz payment.

    Request:
    {
        "quiz_session_id": "uuid",
        "email": "user@example.com",
        "tier": "full",  # Only tier for now
        "success_url": "https://crb-analyser.com/report/{session_id}",
        "cancel_url": "https://crb-analyser.com/checkout?cancelled=true"
    }
    """

    # Verify quiz session exists and is complete
    quiz = await get_quiz_session(supabase, request.quiz_session_id)
    if not quiz or quiz["status"] != "completed":
        raise HTTPException(400, "Quiz must be completed before payment")

    # Create Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=request.email,
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "CRB Analysis Report",
                    "description": "AI-powered Cost/Risk/Benefit analysis for your business",
                    "images": ["https://crb-analyser.com/report-preview.png"]
                },
                "unit_amount": 14700,  # €147.00 in cents
            },
            "quantity": 1,
        }],
        metadata={
            "quiz_session_id": request.quiz_session_id,
            "tier": request.tier,
            "email": request.email
        },
        success_url=request.success_url.replace("{session_id}", request.quiz_session_id),
        cancel_url=request.cancel_url,
        expires_at=int((datetime.utcnow() + timedelta(hours=24)).timestamp())
    )

    # Update quiz session with Stripe session ID
    await supabase.table("quiz_sessions").update({
        "stripe_session_id": session.id,
        "status": "pending_payment"
    }).eq("id", request.quiz_session_id).execute()

    return {"checkout_url": session.url, "session_id": session.id}
```

**Webhook Handler (Critical):**
```python
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Handle Stripe webhook events.

    Events handled:
    - checkout.session.completed: Payment successful
    - checkout.session.expired: Payment abandoned
    - charge.refunded: Refund processed
    """

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_successful_payment(session, supabase)

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        await handle_expired_session(session, supabase)

    elif event["type"] == "charge.refunded":
        charge = event["data"]["object"]
        await handle_refund(charge, supabase)

    return {"received": True}


async def handle_successful_payment(session: dict, supabase: AsyncClient):
    """
    Process successful payment:
    1. Update quiz session status
    2. Create report record
    3. Trigger report generation
    4. Send confirmation email
    """

    quiz_session_id = session["metadata"]["quiz_session_id"]
    email = session["metadata"]["email"]

    # Update quiz session
    await supabase.table("quiz_sessions").update({
        "status": "paid",
        "amount_paid": session["amount_total"] / 100,
        "payment_completed_at": datetime.utcnow().isoformat()
    }).eq("id", quiz_session_id).execute()

    # Create report record
    report_result = await supabase.table("reports").insert({
        "quiz_session_id": quiz_session_id,
        "tier": session["metadata"]["tier"],
        "status": "generating"
    }).execute()

    report_id = report_result.data[0]["id"]

    # Update quiz with report link
    await supabase.table("quiz_sessions").update({
        "report_id": report_id,
        "status": "generating"
    }).eq("id", quiz_session_id).execute()

    # Trigger report generation (async)
    await trigger_report_generation(report_id, quiz_session_id)

    # Send confirmation email
    await send_payment_confirmation_email(email, report_id)
```

**Idempotency:**
```python
async def handle_successful_payment(session: dict, supabase: AsyncClient):
    """Handle with idempotency check."""

    # Check if already processed (idempotency)
    quiz_session_id = session["metadata"]["quiz_session_id"]
    existing = await supabase.table("quiz_sessions")\
        .select("status")\
        .eq("id", quiz_session_id)\
        .single()\
        .execute()

    if existing.data["status"] in ["paid", "generating", "delivered"]:
        logger.info(f"Payment already processed for {quiz_session_id}")
        return  # Already processed, skip

    # Continue with processing...
```

### 2. Email Notifications (SendGrid)

**Email Triggers:**
```python
EMAIL_TRIGGERS = {
    "payment_confirmed": {
        "template_id": "d-payment-confirmed",
        "subject": "Your CRB Analysis is Being Generated",
        "trigger": "checkout.session.completed"
    },
    "report_ready": {
        "template_id": "d-report-ready",
        "subject": "Your CRB Analysis Report is Ready",
        "trigger": "report.completed"
    },
    "report_failed": {
        "template_id": "d-report-failed",
        "subject": "Issue with Your CRB Analysis",
        "trigger": "report.failed"
    },
    "follow_up_7_day": {
        "template_id": "d-follow-up",
        "subject": "How's Your AI Implementation Going?",
        "trigger": "scheduled_7_days_after_delivery"
    }
}
```

**Email Service:**
```python
# backend/src/services/email_service.py

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType

class EmailService:
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = "reports@crb-analyser.com"
        self.from_name = "CRB Analyser"

    async def send_payment_confirmation(self, to_email: str, report_id: str):
        """Send payment confirmation with report link."""

        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject="Your CRB Analysis is Being Generated"
        )

        message.dynamic_template_data = {
            "report_url": f"https://crb-analyser.com/report/{report_id}",
            "estimated_time": "1-2 minutes",
            "support_email": "support@crb-analyser.com"
        }
        message.template_id = "d-xxxxxxxx"  # SendGrid template ID

        response = await asyncio.to_thread(
            self.client.send, message
        )
        return response.status_code == 202

    async def send_report_ready(
        self,
        to_email: str,
        report_id: str,
        key_stats: dict,
        attach_pdf: bool = True
    ):
        """Send report ready notification with optional PDF attachment."""

        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject="Your CRB Analysis Report is Ready"
        )

        message.dynamic_template_data = {
            "report_url": f"https://crb-analyser.com/report/{report_id}",
            "ai_readiness_score": key_stats["ai_readiness_score"],
            "total_value_potential": f"€{key_stats['total_value']:,}",
            "top_opportunity": key_stats["top_opportunity"],
            "verdict": key_stats["verdict"]
        }
        message.template_id = "d-yyyyyyyy"

        # Attach PDF if requested and file exists
        if attach_pdf:
            pdf_path = f"/tmp/reports/{report_id}.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_data = base64.b64encode(f.read()).decode()

                attachment = Attachment(
                    FileContent(pdf_data),
                    FileName(f"CRB-Analysis-{report_id[:8]}.pdf"),
                    FileType("application/pdf")
                )
                message.attachment = attachment

        response = await asyncio.to_thread(self.client.send, message)
        return response.status_code == 202

    async def send_follow_up(self, to_email: str, report_id: str, days_since: int):
        """Send follow-up email X days after report delivery."""

        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject="How's Your AI Implementation Going?"
        )

        message.dynamic_template_data = {
            "report_url": f"https://crb-analyser.com/report/{report_id}",
            "days_since": days_since,
            "booking_url": "https://calendly.com/crb-analyser/implementation-call"
        }
        message.template_id = "d-zzzzzzzz"

        response = await asyncio.to_thread(self.client.send, message)
        return response.status_code == 202
```

**Email Templates (SendGrid Dynamic Templates):**

```html
<!-- Payment Confirmed Template -->
<h1>Thanks for your purchase!</h1>
<p>We're generating your personalized CRB Analysis Report right now.</p>

<div class="status-box">
  <h3>What happens next:</h3>
  <ol>
    <li>Our AI analyzes your responses (1-2 minutes)</li>
    <li>We research vendor options and pricing</li>
    <li>We calculate ROI for each recommendation</li>
    <li>Your report will be ready at: <a href="{{report_url}}">{{report_url}}</a></li>
  </ol>
</div>

<p>We'll email you again when it's ready.</p>
```

```html
<!-- Report Ready Template -->
<h1>Your CRB Analysis is Ready!</h1>

<div class="highlight-box verdict-{{verdict_color}}">
  <h2>{{verdict_headline}}</h2>
  <p>AI Readiness Score: <strong>{{ai_readiness_score}}/100</strong></p>
  <p>Total Value Potential: <strong>{{total_value_potential}}</strong></p>
</div>

<div class="top-opportunity">
  <h3>Your Top Opportunity:</h3>
  <p><strong>{{top_opportunity.title}}</strong></p>
  <p>Potential value: {{top_opportunity.value}}</p>
</div>

<a href="{{report_url}}" class="cta-button">View Full Report</a>

<p>Your PDF report is attached to this email.</p>
```

### 3. PDF Generation

**Professional PDF with Charts:**
```python
# backend/src/services/pdf_service.py

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import io
import base64

class PDFService:
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates/pdf")
        )

    async def generate_report_pdf(self, report: dict) -> bytes:
        """
        Generate professional PDF from report data.

        Sections:
        1. Cover page
        2. Executive summary with verdict
        3. Score dashboard (charts)
        4. Value projection chart
        5. Findings overview
        6. Detailed recommendations (with Three Options)
        7. Implementation roadmap
        8. Methodology & sources
        """

        # Generate charts as base64 images
        charts = await self.generate_charts(report)

        # Render HTML template
        template = self.jinja_env.get_template("report.html")
        html_content = template.render(
            report=report,
            charts=charts,
            generated_at=datetime.utcnow().strftime("%B %d, %Y")
        )

        # Convert to PDF
        pdf_bytes = HTML(string=html_content).write_pdf(
            stylesheets=[CSS("templates/pdf/report.css")]
        )

        return pdf_bytes

    async def generate_charts(self, report: dict) -> dict:
        """Generate all charts as base64 PNG images."""

        charts = {}

        # AI Readiness Gauge
        charts["readiness_gauge"] = self.create_gauge_chart(
            score=report["executive_summary"]["ai_readiness_score"],
            title="AI Readiness Score"
        )

        # Two Pillars Chart
        charts["two_pillars"] = self.create_two_pillars_chart(
            cv_score=report["executive_summary"]["customer_value_score"],
            bh_score=report["executive_summary"]["business_health_score"]
        )

        # Value Timeline
        charts["value_timeline"] = self.create_value_timeline(
            value_summary=report["value_summary"]
        )

        # ROI Comparison
        charts["roi_comparison"] = self.create_roi_comparison(
            recommendations=report["recommendations"]
        )

        return charts

    def create_gauge_chart(self, score: int, title: str) -> str:
        """Create gauge chart and return as base64."""

        fig, ax = plt.subplots(figsize=(4, 3), subplot_kw={'projection': 'polar'})

        # ... matplotlib gauge implementation ...

        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    def create_two_pillars_chart(self, cv_score: int, bh_score: int) -> str:
        """Create horizontal bar chart for Two Pillars."""

        fig, ax = plt.subplots(figsize=(6, 2))

        categories = ['Customer Value', 'Business Health']
        scores = [cv_score, bh_score]
        colors = ['#3b82f6', '#8b5cf6']

        bars = ax.barh(categories, scores, color=colors, height=0.5)
        ax.set_xlim(0, 10)
        ax.set_xlabel('Score (1-10)')

        # Add score labels
        for bar, score in zip(bars, scores):
            ax.text(score + 0.2, bar.get_y() + bar.get_height()/2,
                   f'{score}/10', va='center', fontsize=12, fontweight='bold')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
```

**PDF Template (Jinja2):**
```html
<!-- templates/pdf/report.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>CRB Analysis Report</title>
  <link rel="stylesheet" href="report.css">
</head>
<body>

  <!-- Cover Page -->
  <div class="cover-page">
    <div class="logo">CRB Analyser</div>
    <h1>Cost/Risk/Benefit Analysis</h1>
    <h2>AI Implementation Report</h2>
    <div class="company-name">{{ report.company_name or "Your Business" }}</div>
    <div class="date">{{ generated_at }}</div>
  </div>

  <!-- Executive Summary -->
  <div class="page">
    <h1>Executive Summary</h1>

    <!-- Verdict -->
    <div class="verdict verdict-{{ report.executive_summary.verdict.color }}">
      <h2>{{ report.executive_summary.verdict.headline }}</h2>
      <p>{{ report.executive_summary.verdict.subheadline }}</p>
    </div>

    <!-- Key Metrics -->
    <div class="metrics-grid">
      <div class="metric">
        <img src="data:image/png;base64,{{ charts.readiness_gauge }}" alt="AI Readiness">
      </div>
      <div class="metric">
        <img src="data:image/png;base64,{{ charts.two_pillars }}" alt="Two Pillars">
      </div>
    </div>

    <!-- Key Insight -->
    <div class="insight-box">
      <h3>Key Insight</h3>
      <p>{{ report.executive_summary.key_insight }}</p>
    </div>
  </div>

  <!-- Value Projection -->
  <div class="page">
    <h1>Value Projection</h1>
    <img src="data:image/png;base64,{{ charts.value_timeline }}" alt="Value Timeline" class="full-width-chart">

    <div class="value-summary">
      <div class="value-item">
        <span class="label">3-Year Value Potential:</span>
        <span class="value">€{{ "{:,.0f}".format(report.value_summary.total.min) }} - €{{ "{:,.0f}".format(report.value_summary.total.max) }}</span>
      </div>
    </div>
  </div>

  <!-- Recommendations -->
  {% for rec in report.recommendations %}
  <div class="page recommendation">
    <h2>{{ rec.title }}</h2>
    <p class="priority priority-{{ rec.priority }}">{{ rec.priority|upper }} PRIORITY</p>

    <p>{{ rec.description }}</p>

    <!-- Three Options -->
    <div class="options-grid">
      <div class="option {% if rec.our_recommendation == 'off_the_shelf' %}recommended{% endif %}">
        <h4>Option A: Off-the-Shelf</h4>
        <p class="vendor">{{ rec.options.off_the_shelf.name }}</p>
        <p class="cost">€{{ rec.options.off_the_shelf.monthly_cost }}/month</p>
        <ul>
          {% for pro in rec.options.off_the_shelf.pros %}
          <li class="pro">{{ pro }}</li>
          {% endfor %}
          {% for con in rec.options.off_the_shelf.cons %}
          <li class="con">{{ con }}</li>
          {% endfor %}
        </ul>
      </div>

      <div class="option {% if rec.our_recommendation == 'best_in_class' %}recommended{% endif %}">
        <h4>Option B: Best-in-Class</h4>
        <p class="vendor">{{ rec.options.best_in_class.name }}</p>
        <p class="cost">€{{ rec.options.best_in_class.monthly_cost }}/month</p>
        <!-- ... -->
      </div>

      <div class="option {% if rec.our_recommendation == 'custom_solution' %}recommended{% endif %}">
        <h4>Option C: Custom Solution</h4>
        <p class="approach">{{ rec.options.custom_solution.approach }}</p>
        <p class="cost">€{{ rec.options.custom_solution.estimated_cost.min }}-{{ rec.options.custom_solution.estimated_cost.max }}</p>
        <p class="tools">Tools: {{ rec.options.custom_solution.build_tools|join(", ") }}</p>
        <!-- ... -->
      </div>
    </div>

    <div class="recommendation-rationale">
      <h4>Our Recommendation: {{ rec.our_recommendation|replace("_", " ")|title }}</h4>
      <p>{{ rec.recommendation_rationale }}</p>
    </div>

    <!-- ROI Box -->
    <div class="roi-box">
      <div class="roi-metric">
        <span class="label">ROI:</span>
        <span class="value">{{ rec.roi_percentage }}%</span>
      </div>
      <div class="roi-metric">
        <span class="label">Payback:</span>
        <span class="value">{{ rec.payback_months }} months</span>
      </div>
    </div>

    <!-- Assumptions -->
    <div class="assumptions">
      <h5>Assumptions:</h5>
      <ul>
        {% for assumption in rec.assumptions %}
        <li>{{ assumption }}</li>
        {% endfor %}
      </ul>
    </div>
  </div>
  {% endfor %}

  <!-- Methodology -->
  <div class="page methodology">
    <h1>Methodology & Sources</h1>

    <h3>Two Pillars Framework</h3>
    <p>Every finding is evaluated on two dimensions:</p>
    <ul>
      <li><strong>Customer Value (1-10):</strong> How much does this help your customers?</li>
      <li><strong>Business Health (1-10):</strong> How much does this strengthen your business?</li>
    </ul>

    <h3>Sources</h3>
    <ul>
      {% for source in report.methodology_notes.sources %}
      <li>{{ source }}</li>
      {% endfor %}
    </ul>

    <div class="disclaimer">
      <p>This report was generated by CRB Analyser using AI-powered analysis.
         All vendor pricing was verified within the last 30 days.
         ROI projections are estimates based on stated assumptions.</p>
    </div>
  </div>

  <!-- Back Cover -->
  <div class="back-cover">
    <h2>Need Help Implementing?</h2>
    <p>The team behind CRB Analyser can help you build custom AI solutions.</p>
    <p class="cta">Contact: hello@crb-analyser.com</p>
    <div class="logo-small">CRB Analyser</div>
  </div>

</body>
</html>
```

### 4. File Storage (Supabase)

```python
# backend/src/services/storage_service.py

class StorageService:
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase
        self.bucket = "reports"

    async def upload_pdf(self, report_id: str, pdf_bytes: bytes) -> str:
        """Upload PDF to Supabase storage, return public URL."""

        file_path = f"pdfs/{report_id}.pdf"

        # Upload to Supabase Storage
        result = await self.supabase.storage.from_(self.bucket).upload(
            file_path,
            pdf_bytes,
            {"content-type": "application/pdf"}
        )

        if result.error:
            raise Exception(f"Upload failed: {result.error}")

        # Get public URL
        url_result = self.supabase.storage.from_(self.bucket).get_public_url(file_path)

        return url_result

    async def get_pdf_url(self, report_id: str) -> str:
        """Get signed URL for PDF download (expires in 1 hour)."""

        file_path = f"pdfs/{report_id}.pdf"

        result = await self.supabase.storage.from_(self.bucket).create_signed_url(
            file_path,
            expires_in=3600  # 1 hour
        )

        return result["signedURL"]
```

---

## Specific Tasks

### Phase 1: Stripe (Critical Path)
- [ ] Implement checkout session creation
- [ ] Set up Stripe webhook endpoint
- [ ] Handle checkout.session.completed
- [ ] Handle checkout.session.expired
- [ ] Handle charge.refunded
- [ ] Add idempotency checks
- [ ] Test full payment flow

### Phase 2: Email
- [ ] Set up SendGrid account and API key
- [ ] Create dynamic email templates (3)
- [ ] Implement EmailService class
- [ ] Payment confirmation email
- [ ] Report ready email (with PDF attachment)
- [ ] Set up follow-up email scheduler
- [ ] Test email delivery

### Phase 3: PDF Generation
- [ ] Set up WeasyPrint
- [ ] Create PDF template (Jinja2)
- [ ] Implement chart generation (matplotlib)
- [ ] Style PDF professionally
- [ ] Test all report sections render correctly
- [ ] Optimize file size

### Phase 4: Storage
- [ ] Set up Supabase Storage bucket
- [ ] Implement upload service
- [ ] Implement signed URL generation
- [ ] Set up cleanup for old files (30 days)
- [ ] Test download flow

### Phase 5: Integration Testing
- [ ] Full flow: Quiz → Payment → Email → PDF
- [ ] Error scenarios: Failed payment, failed generation
- [ ] Webhook retry handling
- [ ] Email bounce handling

---

## Dependencies

**Needs from Agent 2 (Backend):**
- Quiz session data structure
- Report generation trigger mechanism

**Needs from Agent 3 (AI Engine):**
- Report data structure for PDF template
- Chart data format

**Needs from Agent 1 (Frontend):**
- Success/cancel URLs for Stripe
- PDF download UI

---

## Deliverables

1. **Stripe Integration** - Complete payment flow with webhooks
2. **Email Service** - SendGrid integration with templates
3. **PDF Generator** - Professional report PDFs
4. **Storage Service** - Supabase file handling
5. **Integration Tests** - Full flow validation

---

## Environment Variables

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...  # For frontend

# SendGrid
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=reports@crb-analyser.com

# Supabase Storage
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

---

## Quality Criteria

- [ ] Stripe webhook handles all events correctly
- [ ] Emails have < 5% bounce rate
- [ ] PDFs render correctly on all viewers
- [ ] File downloads work reliably
- [ ] No payment can be processed twice
- [ ] Failed payments don't create reports

---

## File Structure

```
backend/src/
├── routes/
│   ├── payment_routes.py (enhance)
│   └── webhook_routes.py (new)
├── services/
│   ├── email_service.py (new)
│   ├── pdf_service.py (new)
│   └── storage_service.py (new)
└── templates/
    └── pdf/
        ├── report.html
        └── report.css

emails/  (SendGrid templates - stored in SendGrid dashboard)
├── payment-confirmed.html
├── report-ready.html
└── follow-up.html
```
