"""
Industry-Specific Software Options for Existing Stack Capture

Maps industries to software options that users might already have.
Used in the quiz to capture user's existing tools for Connect vs Replace recommendations.

Options include both:
1. Industry-specific software (dental PMS, ATS systems, etc.)
2. Cross-industry tools (CRM, scheduling, marketing, etc.)
"""

from typing import TypedDict, List, Optional


class SoftwareOption(TypedDict):
    """A software option for the existing stack question."""
    slug: str  # Vendor slug from vendors table, or custom identifier
    name: str  # Display name
    category: str  # Category for grouping in UI


# ============================================================================
# CROSS-INDUSTRY SOFTWARE (shown to all industries)
# ============================================================================

CROSS_INDUSTRY_SOFTWARE: List[SoftwareOption] = [
    # CRM
    {"slug": "hubspot", "name": "HubSpot", "category": "CRM"},
    {"slug": "salesforce", "name": "Salesforce", "category": "CRM"},
    {"slug": "pipedrive", "name": "Pipedrive", "category": "CRM"},
    {"slug": "zoho-crm", "name": "Zoho CRM", "category": "CRM"},
    {"slug": "freshsales", "name": "Freshsales", "category": "CRM"},

    # Scheduling
    {"slug": "calendly", "name": "Calendly", "category": "Scheduling"},
    {"slug": "acuity-scheduling", "name": "Acuity Scheduling", "category": "Scheduling"},
    {"slug": "cal-com", "name": "Cal.com", "category": "Scheduling"},
    {"slug": "google-calendar", "name": "Google Calendar", "category": "Scheduling"},
    {"slug": "microsoft-outlook", "name": "Microsoft Outlook/Calendar", "category": "Scheduling"},

    # Email Marketing
    {"slug": "mailchimp", "name": "Mailchimp", "category": "Email Marketing"},
    {"slug": "klaviyo", "name": "Klaviyo", "category": "Email Marketing"},
    {"slug": "activecampaign", "name": "ActiveCampaign", "category": "Email Marketing"},
    {"slug": "constant-contact", "name": "Constant Contact", "category": "Email Marketing"},
    {"slug": "brevo", "name": "Brevo (Sendinblue)", "category": "Email Marketing"},

    # Customer Support
    {"slug": "zendesk", "name": "Zendesk", "category": "Customer Support"},
    {"slug": "intercom", "name": "Intercom", "category": "Customer Support"},
    {"slug": "freshdesk", "name": "Freshdesk", "category": "Customer Support"},
    {"slug": "helpscout", "name": "Help Scout", "category": "Customer Support"},

    # Accounting
    {"slug": "quickbooks", "name": "QuickBooks", "category": "Accounting"},
    {"slug": "xero", "name": "Xero", "category": "Accounting"},
    {"slug": "freshbooks", "name": "FreshBooks", "category": "Accounting"},
    {"slug": "sage", "name": "Sage", "category": "Accounting"},
    {"slug": "wave", "name": "Wave", "category": "Accounting"},

    # Phone & SMS
    {"slug": "twilio", "name": "Twilio", "category": "Phone & SMS"},
    {"slug": "ringcentral", "name": "RingCentral", "category": "Phone & SMS"},
    {"slug": "dialpad", "name": "Dialpad", "category": "Phone & SMS"},
    {"slug": "aircall", "name": "Aircall", "category": "Phone & SMS"},

    # Project Management
    {"slug": "asana", "name": "Asana", "category": "Project Management"},
    {"slug": "monday-com", "name": "Monday.com", "category": "Project Management"},
    {"slug": "trello", "name": "Trello", "category": "Project Management"},
    {"slug": "notion", "name": "Notion", "category": "Project Management"},
    {"slug": "clickup", "name": "ClickUp", "category": "Project Management"},

    # Communication
    {"slug": "slack", "name": "Slack", "category": "Communication"},
    {"slug": "microsoft-teams", "name": "Microsoft Teams", "category": "Communication"},
    {"slug": "zoom", "name": "Zoom", "category": "Communication"},
    {"slug": "google-meet", "name": "Google Meet", "category": "Communication"},
]


# ============================================================================
# INDUSTRY-SPECIFIC SOFTWARE
# ============================================================================

DENTAL_SOFTWARE: List[SoftwareOption] = [
    # Practice Management Systems (PMS)
    {"slug": "open-dental", "name": "Open Dental", "category": "Practice Management"},
    {"slug": "dentrix", "name": "Dentrix", "category": "Practice Management"},
    {"slug": "eaglesoft", "name": "Eaglesoft", "category": "Practice Management"},
    {"slug": "curve-dental", "name": "Curve Dental", "category": "Practice Management"},
    {"slug": "denticon", "name": "Denticon", "category": "Practice Management"},
    {"slug": "tab32", "name": "tab32", "category": "Practice Management"},
    {"slug": "carestack", "name": "CareStack", "category": "Practice Management"},
    {"slug": "dentally", "name": "Dentally", "category": "Practice Management"},
    {"slug": "axiom", "name": "Axiom", "category": "Practice Management"},
    {"slug": "software-of-excellence", "name": "Software of Excellence (SOE)", "category": "Practice Management"},

    # Patient Communication
    {"slug": "weave", "name": "Weave", "category": "Patient Communication"},
    {"slug": "solutionreach", "name": "Solutionreach", "category": "Patient Communication"},
    {"slug": "lighthouse-360", "name": "Lighthouse 360", "category": "Patient Communication"},
    {"slug": "revenue-well", "name": "RevenueWell", "category": "Patient Communication"},
    {"slug": "podium", "name": "Podium", "category": "Patient Communication"},
    {"slug": "demandforce", "name": "Demandforce", "category": "Patient Communication"},

    # Imaging
    {"slug": "pearl-ai", "name": "Pearl AI", "category": "Imaging & AI"},
    {"slug": "overjet", "name": "Overjet", "category": "Imaging & AI"},
    {"slug": "dexis", "name": "DEXIS", "category": "Imaging"},
    {"slug": "romexis", "name": "Romexis", "category": "Imaging"},
]

PROFESSIONAL_SERVICES_SOFTWARE: List[SoftwareOption] = [
    # Practice Management (Accounting/Legal)
    {"slug": "cch-axcess", "name": "CCH Axcess", "category": "Practice Management"},
    {"slug": "practice-ignition", "name": "Practice Ignition (Ignition)", "category": "Practice Management"},
    {"slug": "karbon", "name": "Karbon", "category": "Practice Management"},
    {"slug": "canopy", "name": "Canopy", "category": "Practice Management"},
    {"slug": "taxdome", "name": "TaxDome", "category": "Practice Management"},
    {"slug": "jetpack-workflow", "name": "Jetpack Workflow", "category": "Practice Management"},
    {"slug": "clio", "name": "Clio", "category": "Practice Management"},  # Legal
    {"slug": "practicepanther", "name": "PracticePanther", "category": "Practice Management"},  # Legal

    # Document Management
    {"slug": "sharefile", "name": "ShareFile", "category": "Document Management"},
    {"slug": "docusign", "name": "DocuSign", "category": "Document Management"},
    {"slug": "pandadoc", "name": "PandaDoc", "category": "Document Management"},
    {"slug": "smartvault", "name": "SmartVault", "category": "Document Management"},

    # Time Tracking & Billing
    {"slug": "harvest", "name": "Harvest", "category": "Time & Billing"},
    {"slug": "toggl", "name": "Toggl", "category": "Time & Billing"},
    {"slug": "clockify", "name": "Clockify", "category": "Time & Billing"},
    {"slug": "bill-com", "name": "Bill.com", "category": "Billing"},
]

ECOMMERCE_SOFTWARE: List[SoftwareOption] = [
    # E-Commerce Platforms
    {"slug": "shopify", "name": "Shopify", "category": "Platform"},
    {"slug": "woocommerce", "name": "WooCommerce", "category": "Platform"},
    {"slug": "bigcommerce", "name": "BigCommerce", "category": "Platform"},
    {"slug": "magento", "name": "Magento / Adobe Commerce", "category": "Platform"},
    {"slug": "squarespace", "name": "Squarespace", "category": "Platform"},
    {"slug": "wix", "name": "Wix", "category": "Platform"},

    # Customer Support
    {"slug": "gorgias", "name": "Gorgias", "category": "Support"},
    {"slug": "richpanel", "name": "Richpanel", "category": "Support"},

    # Email & SMS Marketing
    {"slug": "klaviyo", "name": "Klaviyo", "category": "Email & SMS"},
    {"slug": "attentive", "name": "Attentive", "category": "Email & SMS"},
    {"slug": "postscript", "name": "Postscript", "category": "SMS"},
    {"slug": "omnisend", "name": "Omnisend", "category": "Email & SMS"},

    # Attribution & Analytics
    {"slug": "triple-whale", "name": "Triple Whale", "category": "Attribution"},
    {"slug": "northbeam", "name": "Northbeam", "category": "Attribution"},
    {"slug": "lifetimely", "name": "Lifetimely", "category": "Analytics"},
    {"slug": "polar-analytics", "name": "Polar Analytics", "category": "Analytics"},

    # Subscriptions & Loyalty
    {"slug": "recharge", "name": "Recharge", "category": "Subscriptions"},
    {"slug": "yotpo", "name": "Yotpo", "category": "Reviews & Loyalty"},
    {"slug": "stamped-io", "name": "Stamped.io", "category": "Reviews & Loyalty"},
    {"slug": "smile-io", "name": "Smile.io", "category": "Loyalty"},

    # Fulfillment & Operations
    {"slug": "shipstation", "name": "ShipStation", "category": "Fulfillment"},
    {"slug": "shipbob", "name": "ShipBob", "category": "Fulfillment"},
    {"slug": "returnly", "name": "Returnly / Loop", "category": "Returns"},
    {"slug": "loop-returns", "name": "Loop Returns", "category": "Returns"},
    {"slug": "returngo", "name": "ReturnGO", "category": "Returns"},

    # EU Logistics & Payments
    {"slug": "sendcloud", "name": "Sendcloud", "category": "Shipping (EU)"},
    {"slug": "picqer", "name": "Picqer", "category": "Warehouse (EU)"},
    {"slug": "mollie", "name": "Mollie", "category": "Payments (EU)"},
    {"slug": "channable", "name": "Channable", "category": "Feed Management"},

    # Marketplaces
    {"slug": "bol-com", "name": "Bol.com", "category": "Marketplace (EU)"},
    {"slug": "zalando", "name": "Zalando", "category": "Marketplace (EU)"},
    {"slug": "kaufland", "name": "Kaufland", "category": "Marketplace (EU)"},
]


B2B_PLATFORMS_SOFTWARE: List[SoftwareOption] = [
    # IoT Platforms
    {"slug": "azure-iot-hub", "name": "Azure IoT Hub", "category": "IoT Platform"},
    {"slug": "aws-iot-core", "name": "AWS IoT Core", "category": "IoT Platform"},
    {"slug": "particle", "name": "Particle", "category": "IoT Platform"},

    # ERP
    {"slug": "exact-online", "name": "Exact Online", "category": "ERP"},
    {"slug": "netsuite", "name": "NetSuite", "category": "ERP"},
    {"slug": "odoo", "name": "Odoo", "category": "ERP"},

    # Field Service
    {"slug": "salesforce-fsl", "name": "Salesforce Field Service", "category": "Field Service"},
    {"slug": "servicemax", "name": "ServiceMax", "category": "Field Service"},
    {"slug": "zuper", "name": "Zuper", "category": "Field Service"},

    # Subscription Billing
    {"slug": "chargebee", "name": "Chargebee", "category": "Billing"},
    {"slug": "zuora", "name": "Zuora", "category": "Billing"},
    {"slug": "stripe-billing", "name": "Stripe Billing", "category": "Billing"},

    # Partner Management
    {"slug": "impartner", "name": "Impartner", "category": "Partner Management"},
    {"slug": "partnerstack", "name": "PartnerStack", "category": "Partner Management"},

    # Customer Success
    {"slug": "gainsight", "name": "Gainsight", "category": "Customer Success"},
    {"slug": "vitally", "name": "Vitally", "category": "Customer Success"},
    {"slug": "planhat", "name": "Planhat", "category": "Customer Success"},

    # Supply Chain
    {"slug": "katana", "name": "Katana", "category": "Supply Chain"},
    {"slug": "inflow", "name": "inFlow", "category": "Supply Chain"},
]


# ============================================================================
# INDUSTRY MAPPING
# ============================================================================

INDUSTRY_SOFTWARE_MAP: dict[str, List[SoftwareOption]] = {
    "dental": DENTAL_SOFTWARE,
    "professional-services": PROFESSIONAL_SERVICES_SOFTWARE,
    "ecommerce": ECOMMERCE_SOFTWARE,
    "b2b-platforms": B2B_PLATFORMS_SOFTWARE,
}


def get_software_options_for_industry(industry: Optional[str]) -> List[SoftwareOption]:
    """
    Get software options for a specific industry.

    Combines industry-specific software with cross-industry software.
    Returns sorted by category for better UI grouping.
    """
    options: List[SoftwareOption] = []

    # Add industry-specific software first (if industry provided)
    if industry and industry in INDUSTRY_SOFTWARE_MAP:
        options.extend(INDUSTRY_SOFTWARE_MAP[industry])

    # Add cross-industry software
    options.extend(CROSS_INDUSTRY_SOFTWARE)

    return options


def get_all_categories(industry: Optional[str]) -> List[str]:
    """Get all unique categories for an industry's software options."""
    options = get_software_options_for_industry(industry)
    categories = sorted(set(opt["category"] for opt in options))
    return categories


def get_software_options_grouped(industry: Optional[str]) -> dict[str, List[SoftwareOption]]:
    """
    Get software options grouped by category.

    Returns a dict where keys are categories and values are lists of options.
    Industry-specific categories appear first.
    """
    options = get_software_options_for_industry(industry)
    grouped: dict[str, List[SoftwareOption]] = {}

    for opt in options:
        category = opt["category"]
        if category not in grouped:
            grouped[category] = []
        # Avoid duplicates (same slug)
        if not any(existing["slug"] == opt["slug"] for existing in grouped[category]):
            grouped[category].append(opt)

    return grouped
