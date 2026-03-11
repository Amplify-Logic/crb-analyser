"""
CRB Analyser - Questionnaire Configuration

Defines the intake questionnaire structure with ~25 questions across 5 sections.
Industry-specific variations supported.
"""

from typing import List, Dict, Any, Optional
from enum import Enum

from src.skills.base import LOCATION_OPTIONS, COUNTRY_CURRENCY_MAP


class QuestionType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    SCALE = "scale"  # 1-10 rating
    YES_NO = "yes_no"
    NUMBER = "number"
    CURRENCY = "currency"


# Question definition structure
QUESTIONNAIRE_SECTIONS = [
    {
        "id": 1,
        "title": "Company Overview",
        "description": "Tell us about your business",
        "questions": [
            {
                "id": "company_location",
                "question": "Where is your business based?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {**opt, "currency": COUNTRY_CURRENCY_MAP.get(opt["value"], "EUR")}
                    for opt in LOCATION_OPTIONS
                ],
            },
            {
                "id": "company_description",
                "question": "Briefly describe what your company does and your main products/services.",
                "type": QuestionType.TEXTAREA,
                "required": True,
                "placeholder": "We are an online store selling sustainable fashion to eco-conscious consumers...",
            },
            {
                "id": "employee_count",
                "question": "How many employees does your company have?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "1", "label": "Just me (solo)"},
                    {"value": "2-10", "label": "2-10 employees"},
                    {"value": "11-50", "label": "11-50 employees"},
                    {"value": "51-200", "label": "51-200 employees"},
                    {"value": "200+", "label": "200+ employees"},
                ],
            },
            {
                "id": "annual_revenue",
                "question": "What is your approximate annual revenue?",
                "type": QuestionType.SELECT,
                "required": False,
                "options": [
                    {"value": "under_100k", "label": "Under 100K"},
                    {"value": "100k_500k", "label": "100K - 500K"},
                    {"value": "500k_1m", "label": "500K - 1M"},
                    {"value": "1m_5m", "label": "1M - 5M"},
                    {"value": "5m_plus", "label": "5M+"},
                    {"value": "prefer_not_say", "label": "Prefer not to say"},
                ],
            },
            {
                "id": "primary_goals",
                "question": "What are your primary business goals for the next 12 months?",
                "type": QuestionType.MULTI_SELECT,
                "required": True,
                "options": [
                    {"value": "increase_revenue", "label": "Increase revenue"},
                    {"value": "reduce_costs", "label": "Reduce operational costs"},
                    {"value": "improve_efficiency", "label": "Improve efficiency"},
                    {"value": "scale_operations", "label": "Scale operations"},
                    {"value": "improve_customer_experience", "label": "Improve customer experience"},
                    {"value": "enter_new_markets", "label": "Enter new markets"},
                    {"value": "other", "label": "Other"},
                ],
            },
        ],
    },
    {
        "id": 2,
        "title": "Current Operations",
        "description": "Help us understand your day-to-day operations",
        "questions": [
            {
                "id": "main_processes",
                "question": "Describe your main business processes that take the most time or resources.",
                "type": QuestionType.TEXTAREA,
                "required": True,
                "placeholder": "Our main processes include order processing, inventory management, customer support, marketing campaigns...",
            },
            {
                "id": "repetitive_tasks",
                "question": "What repetitive tasks do you or your team perform regularly?",
                "type": QuestionType.TEXTAREA,
                "required": True,
                "placeholder": "We spend hours each week on order confirmations, shipping updates, return processing, product listing updates, inventory reconciliation...",
            },
            {
                "id": "biggest_bottlenecks",
                "question": "What are your biggest operational bottlenecks?",
                "type": QuestionType.TEXTAREA,
                "required": True,
                "placeholder": "We often get delayed by cart abandonment recovery, returns processing, inventory forecasting, multi-channel sync...",
            },
            {
                "id": "time_on_admin",
                "question": "Roughly how many hours per week does your team spend on administrative tasks?",
                "type": QuestionType.NUMBER,
                "required": True,
                "min": 0,
                "max": 500,
                "placeholder": "20",
            },
            {
                "id": "manual_data_entry",
                "question": "Do you have processes that require manual data entry between systems?",
                "type": QuestionType.YES_NO,
                "required": True,
                "follow_up": {
                    "condition": "yes",
                    "question_id": "manual_data_entry_details",
                    "question": "Please describe these processes briefly.",
                    "type": QuestionType.TEXTAREA,
                },
            },
        ],
    },
    {
        "id": 3,
        "title": "Technology & Tools",
        "description": "What tools and systems do you currently use?",
        "questions": [
            {
                "id": "current_tools",
                "question": "What software tools does your business currently use?",
                "type": QuestionType.MULTI_SELECT,
                "required": True,
                "options": [
                    {"value": "ecommerce_platform", "label": "Ecommerce Platform (Shopify, WooCommerce, Magento)"},
                    {"value": "email_marketing", "label": "Email/SMS Marketing (Klaviyo, Omnisend, Mailchimp)"},
                    {"value": "helpdesk", "label": "Helpdesk (Gorgias, Zendesk, Freshdesk)"},
                    {"value": "reviews_ugc", "label": "Reviews & UGC (Yotpo, Okendo, Loox)"},
                    {"value": "analytics", "label": "Analytics (GA4, Triple Whale, Polar)"},
                    {"value": "ads_platform", "label": "Ads Platform (Meta, Google, TikTok)"},
                    {"value": "inventory_management", "label": "Inventory Management"},
                    {"value": "shipping_fulfillment", "label": "Shipping & Fulfillment (ShipStation, ShipBob)"},
                    {"value": "returns_management", "label": "Returns Management (Loop, Returnly)"},
                    {"value": "subscriptions", "label": "Subscriptions (Recharge, Bold, Skio)"},
                    {"value": "spreadsheets", "label": "Spreadsheets (Excel, Google Sheets)"},
                    {"value": "other", "label": "Other"},
                ],
            },
            {
                "id": "tool_pain_points",
                "question": "What frustrations do you have with your current tools?",
                "type": QuestionType.TEXTAREA,
                "required": False,
                "placeholder": "They don't integrate well, too expensive, missing features...",
            },
            {
                "id": "integration_issues",
                "question": "Do your tools integrate well with each other?",
                "type": QuestionType.SCALE,
                "required": True,
                "scale_min": 1,
                "scale_max": 10,
                "scale_labels": {"1": "Not at all", "5": "Somewhat", "10": "Perfectly integrated"},
            },
            {
                "id": "technology_comfort",
                "question": "How comfortable is your team with adopting new technology?",
                "type": QuestionType.SCALE,
                "required": True,
                "scale_min": 1,
                "scale_max": 10,
                "scale_labels": {"1": "Very resistant", "5": "Neutral", "10": "Very eager"},
            },
            {
                "id": "ai_tools_used",
                "question": "Have you used any AI tools in your business?",
                "type": QuestionType.MULTI_SELECT,
                "required": False,
                "options": [
                    {"value": "chatgpt", "label": "ChatGPT / Claude"},
                    {"value": "image_gen", "label": "Image generation (Midjourney, DALL-E)"},
                    {"value": "writing", "label": "AI writing assistants"},
                    {"value": "automation", "label": "AI-powered automation"},
                    {"value": "analytics", "label": "AI analytics/insights"},
                    {"value": "none", "label": "None"},
                ],
            },
        ],
    },
    {
        "id": 4,
        "title": "Implementation Preferences",
        "description": "Help us understand how you prefer to solve problems",
        "questions": [
            {
                "id": "implementation_capability",
                "question": "How would you describe your technical comfort level?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "non_technical", "label": "I avoid anything technical - just give me something that works"},
                    {"value": "tutorial_follower", "label": "I can follow tutorials and use no-code tools like Notion or Airtable"},
                    {"value": "automation_user", "label": "I'm comfortable with automation tools like Zapier or Make"},
                    {"value": "ai_coder", "label": "I can code or am learning AI coding tools like Cursor"},
                    {"value": "has_developers", "label": "I have developers on staff or easy access to technical help"},
                ],
            },
            {
                "id": "implementation_preference",
                "question": "When solving business problems with software, you prefer to...",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "buy", "label": "Find a ready-made solution that just works"},
                    {"value": "connect", "label": "Customize and connect my existing tools"},
                    {"value": "build", "label": "Build exactly what I need, even if it takes longer"},
                    {"value": "hire", "label": "Hire someone to handle it for me"},
                ],
            },
            {
                "id": "budget_comfort",
                "question": "For a tool that saves you 10+ hours/month, what's your comfort zone?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "low", "label": "Under €50/month"},
                    {"value": "moderate", "label": "€50-200/month"},
                    {"value": "comfortable", "label": "€200-500/month"},
                    {"value": "high", "label": "€500+/month or one-time €2K-10K investment"},
                ],
            },
            {
                "id": "implementation_urgency",
                "question": "How soon do you need solutions working?",
                "type": QuestionType.SELECT,
                "required": False,
                "options": [
                    {"value": "this_week", "label": "This week"},
                    {"value": "this_month", "label": "This month"},
                    {"value": "this_quarter", "label": "This quarter"},
                    {"value": "no_rush", "label": "No rush, want it done right"},
                ],
            },
        ],
    },
    {
        "id": 5,
        "title": "Pain Points & Challenges",
        "description": "Where do you struggle the most?",
        "questions": [
            {
                "id": "biggest_challenge",
                "question": "What is the single biggest challenge in your business right now?",
                "type": QuestionType.TEXTAREA,
                "required": True,
                "placeholder": "Cart abandonment is our biggest revenue leak — customers add items but don't complete checkout...",
            },
            {
                "id": "time_wasters",
                "question": "What tasks feel like a waste of time but you have to do them anyway?",
                "type": QuestionType.TEXTAREA,
                "required": True,
                "placeholder": "Manual order tracking updates, returns processing, inventory counting, product description writing, support ticket triage...",
            },
            {
                "id": "missed_opportunities",
                "question": "What opportunities do you feel you're missing due to lack of time or resources?",
                "type": QuestionType.TEXTAREA,
                "required": False,
                "placeholder": "Personalised product recommendations, abandoned cart recovery, repeat purchase campaigns, upsell/cross-sell at checkout...",
            },
            {
                "id": "cost_concerns",
                "question": "Which operational costs concern you the most?",
                "type": QuestionType.MULTI_SELECT,
                "required": True,
                "options": [
                    {"value": "shipping_logistics", "label": "Shipping & logistics"},
                    {"value": "returns_processing", "label": "Returns processing"},
                    {"value": "customer_acquisition", "label": "Customer acquisition (CAC)"},
                    {"value": "software_subscriptions", "label": "Software subscriptions"},
                    {"value": "inventory_waste", "label": "Inventory waste / dead stock"},
                    {"value": "marketing_spend", "label": "Marketing spend / ROAS"},
                    {"value": "manual_labor", "label": "Manual labor"},
                    {"value": "marketplace_fees", "label": "Marketplace fees (Amazon, eBay)"},
                ],
            },
            {
                "id": "quality_issues",
                "question": "Do you experience quality or consistency issues in your operations?",
                "type": QuestionType.YES_NO,
                "required": True,
                "follow_up": {
                    "condition": "yes",
                    "question_id": "quality_issues_details",
                    "question": "Please describe these issues.",
                    "type": QuestionType.TEXTAREA,
                },
            },
        ],
    },
    {
        "id": 6,
        "title": "AI & Automation Readiness",
        "description": "Let's assess your readiness for AI implementation",
        "questions": [
            {
                "id": "ai_interest_areas",
                "question": "Which areas would you most like to automate or enhance with AI?",
                "type": QuestionType.MULTI_SELECT,
                "required": True,
                "options": [
                    {"value": "customer_service", "label": "Customer service / support"},
                    {"value": "sales", "label": "Sales & lead generation"},
                    {"value": "marketing", "label": "Marketing & content creation"},
                    {"value": "operations", "label": "Operations & logistics"},
                    {"value": "finance", "label": "Finance & accounting"},
                    {"value": "hr", "label": "HR & recruitment"},
                    {"value": "product", "label": "Product development"},
                    {"value": "analytics", "label": "Data analysis & insights"},
                    {"value": "other", "label": "Other"},
                ],
            },
            {
                "id": "budget_for_solutions",
                "question": "What budget do you have available for new tools or solutions?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "under_100", "label": "Under €100/month"},
                    {"value": "100_500", "label": "€100-500/month"},
                    {"value": "500_1000", "label": "€500-1,000/month"},
                    {"value": "1000_5000", "label": "€1,000-5,000/month"},
                    {"value": "5000_plus", "label": "€5,000+/month"},
                    {"value": "not_sure", "label": "Not sure yet"},
                ],
            },
            {
                "id": "implementation_timeline",
                "question": "How quickly would you like to see improvements?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "asap", "label": "As soon as possible"},
                    {"value": "1_3_months", "label": "Within 1-3 months"},
                    {"value": "3_6_months", "label": "Within 3-6 months"},
                    {"value": "6_12_months", "label": "Within 6-12 months"},
                    {"value": "no_rush", "label": "No specific timeline"},
                ],
            },
            {
                "id": "decision_makers",
                "question": "Who makes technology decisions in your company?",
                "type": QuestionType.SELECT,
                "required": True,
                "options": [
                    {"value": "me", "label": "I do (sole decision maker)"},
                    {"value": "me_input", "label": "I do with input from others"},
                    {"value": "team", "label": "Decision by team/committee"},
                    {"value": "other", "label": "Someone else decides"},
                ],
            },
            {
                "id": "additional_context",
                "question": "Is there anything else you'd like us to know about your business or goals?",
                "type": QuestionType.TEXTAREA,
                "required": False,
                "placeholder": "Any additional context that might help us provide better recommendations...",
            },
        ],
    },
]


# Industry-specific additional questions
INDUSTRY_SPECIFIC_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "ecommerce": [
        {
            "id": "ecommerce_sub_type",
            "question": "What best describes your e-commerce business model?",
            "type": QuestionType.SELECT,
            "required": True,
            "options": [
                {"value": "dtc_brand", "label": "DTC brand (own products, own store)"},
                {"value": "multi_channel", "label": "Multi-channel retailer (own store + marketplaces)"},
                {"value": "subscription", "label": "Subscription / recurring revenue"},
                {"value": "fashion_apparel", "label": "Fashion & apparel"},
                {"value": "marketplace_seller", "label": "Primarily marketplace seller"},
                {"value": "b2b_wholesale", "label": "B2B / wholesale"},
                {"value": "other", "label": "Other"},
            ],
        },
        {
            "id": "monthly_orders",
            "question": "How many orders do you process per month?",
            "type": QuestionType.NUMBER,
            "required": True,
        },
        {
            "id": "sales_channels",
            "question": "Which sales channels do you use?",
            "type": QuestionType.MULTI_SELECT,
            "required": True,
            "options": [
                {"value": "own_website", "label": "Own website"},
                {"value": "amazon", "label": "Amazon"},
                {"value": "ebay", "label": "eBay"},
                {"value": "etsy", "label": "Etsy"},
                {"value": "shopify", "label": "Shopify"},
                {"value": "social", "label": "Social commerce"},
                {"value": "retail", "label": "Physical retail"},
            ],
        },
        {
            "id": "store_data_source",
            "question": "Would you like to share your store numbers for a more personalised analysis?",
            "type": QuestionType.SELECT,
            "required": True,
            "options": [
                {"value": "manual_entry", "label": "Yes, I'll enter a few numbers (2 min)"},
                {"value": "skip", "label": "Skip — use industry benchmarks"},
            ],
        },
    ],
}


def _apply_industry_overrides(
    sections: List[Dict[str, Any]], industry: str
) -> List[Dict[str, Any]]:
    """Apply industry-specific placeholder and option overrides to questionnaire sections."""
    override_key_placeholder = f"{industry}_placeholder"
    override_key_options = f"{industry}_options"

    for section in sections:
        for question in section["questions"]:
            # Swap placeholder if industry-specific one exists
            if override_key_placeholder in question:
                question["placeholder"] = question.pop(override_key_placeholder)
            # Swap options if industry-specific ones exist
            if override_key_options in question:
                question["options"] = question.pop(override_key_options)
    return sections


def get_questionnaire(industry: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get the full questionnaire, including ecommerce-specific questions.
    """
    import copy
    sections = copy.deepcopy(QUESTIONNAIRE_SECTIONS)
    # Always apply ecommerce overrides
    effective_industry = industry or "ecommerce"
    _apply_industry_overrides(sections, effective_industry)
    if effective_industry in INDUSTRY_SPECIFIC_QUESTIONS:
        industry_section = {
            "id": len(sections) + 1,
            "title": "Your E-Commerce Store",
            "description": "A few questions specific to your online store",
            "questions": INDUSTRY_SPECIFIC_QUESTIONS[effective_industry],
        }
        sections.append(industry_section)
    return sections


def get_total_questions(industry: Optional[str] = None) -> int:
    """Get total number of questions in questionnaire."""
    sections = get_questionnaire(industry)
    return sum(len(section["questions"]) for section in sections)


def get_section_count(industry: Optional[str] = None) -> int:
    """Get number of sections in questionnaire."""
    return len(get_questionnaire(industry))
