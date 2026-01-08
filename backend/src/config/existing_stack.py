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

RECRUITING_SOFTWARE: List[SoftwareOption] = [
    # ATS (Applicant Tracking Systems)
    {"slug": "bullhorn", "name": "Bullhorn", "category": "ATS"},
    {"slug": "greenhouse", "name": "Greenhouse", "category": "ATS"},
    {"slug": "lever", "name": "Lever", "category": "ATS"},
    {"slug": "workable", "name": "Workable", "category": "ATS"},
    {"slug": "jobvite", "name": "Jobvite", "category": "ATS"},
    {"slug": "icims", "name": "iCIMS", "category": "ATS"},
    {"slug": "manatal", "name": "Manatal", "category": "ATS"},
    {"slug": "recruitee", "name": "Recruitee", "category": "ATS"},
    {"slug": "jazz-hr", "name": "JazzHR", "category": "ATS"},
    {"slug": "teamtailor", "name": "Teamtailor", "category": "ATS"},
    {"slug": "breezy-hr", "name": "Breezy HR", "category": "ATS"},

    # Sourcing & Outreach
    {"slug": "linkedin-recruiter", "name": "LinkedIn Recruiter", "category": "Sourcing"},
    {"slug": "hiretual", "name": "Hiretual (hireEZ)", "category": "Sourcing"},
    {"slug": "gem", "name": "Gem", "category": "Sourcing"},
    {"slug": "entelo", "name": "Entelo", "category": "Sourcing"},
    {"slug": "seekout", "name": "SeekOut", "category": "Sourcing"},

    # Assessment
    {"slug": "hirevue", "name": "HireVue", "category": "Assessment"},
    {"slug": "codility", "name": "Codility", "category": "Assessment"},
    {"slug": "hackerrank", "name": "HackerRank", "category": "Assessment"},
    {"slug": "testgorilla", "name": "TestGorilla", "category": "Assessment"},
]

HOME_SERVICES_SOFTWARE: List[SoftwareOption] = [
    # Job Management
    {"slug": "jobber", "name": "Jobber", "category": "Job Management"},
    {"slug": "servicetitan", "name": "ServiceTitan", "category": "Job Management"},
    {"slug": "housecall-pro", "name": "Housecall Pro", "category": "Job Management"},
    {"slug": "buildertrend", "name": "Buildertrend", "category": "Job Management"},
    {"slug": "coconstruct", "name": "CoConstruct", "category": "Job Management"},
    {"slug": "procore", "name": "Procore", "category": "Job Management"},
    {"slug": "fieldedge", "name": "FieldEdge", "category": "Job Management"},
    {"slug": "servicem8", "name": "ServiceM8", "category": "Job Management"},

    # Estimating
    {"slug": "buildertrend", "name": "Buildertrend (Estimating)", "category": "Estimating"},
    {"slug": "stack", "name": "STACK", "category": "Estimating"},
    {"slug": "planswift", "name": "PlanSwift", "category": "Estimating"},
    {"slug": "clear-estimates", "name": "Clear Estimates", "category": "Estimating"},

    # Fleet & Dispatch
    {"slug": "dispatch", "name": "Dispatch", "category": "Dispatch"},
    {"slug": "commusoft", "name": "Commusoft", "category": "Dispatch"},
    {"slug": "fergus", "name": "Fergus", "category": "Job Management"},
]

VETERINARY_SOFTWARE: List[SoftwareOption] = [
    # Practice Management
    {"slug": "evetpractice", "name": "eVetPractice", "category": "Practice Management"},
    {"slug": "avimark", "name": "AVImark", "category": "Practice Management"},
    {"slug": "cornerstone", "name": "Cornerstone", "category": "Practice Management"},
    {"slug": "impromed", "name": "ImproMed", "category": "Practice Management"},
    {"slug": "vetter-software", "name": "Vetter Software", "category": "Practice Management"},
    {"slug": "hippo-manager", "name": "Hippo Manager", "category": "Practice Management"},
    {"slug": "covetrus-pulse", "name": "Covetrus Pulse", "category": "Practice Management"},
    {"slug": "evet-practice", "name": "eVetPractice", "category": "Practice Management"},

    # Client Communication
    {"slug": "petdesk", "name": "PetDesk", "category": "Client Communication"},
    {"slug": "vet2pet", "name": "Vet2Pet", "category": "Client Communication"},
    {"slug": "allydvm", "name": "AllyDVM", "category": "Client Communication"},
    {"slug": "vetspire", "name": "Vetspire", "category": "Client Communication"},

    # Lab & Diagnostics
    {"slug": "idexx", "name": "IDEXX VetLab", "category": "Lab & Diagnostics"},
    {"slug": "zoetis", "name": "Zoetis", "category": "Lab & Diagnostics"},
    {"slug": "antech", "name": "Antech Diagnostics", "category": "Lab & Diagnostics"},
]

COACHING_SOFTWARE: List[SoftwareOption] = [
    # Coaching Platforms
    {"slug": "coachaccountable", "name": "CoachAccountable", "category": "Coaching Platform"},
    {"slug": "paperbell", "name": "Paperbell", "category": "Coaching Platform"},
    {"slug": "practice", "name": "Practice", "category": "Coaching Platform"},
    {"slug": "satori", "name": "Satori", "category": "Coaching Platform"},
    {"slug": "nudge-coach", "name": "Nudge Coach", "category": "Coaching Platform"},
    {"slug": "delenta", "name": "Delenta", "category": "Coaching Platform"},

    # Course & Content
    {"slug": "kajabi", "name": "Kajabi", "category": "Course Platform"},
    {"slug": "teachable", "name": "Teachable", "category": "Course Platform"},
    {"slug": "thinkific", "name": "Thinkific", "category": "Course Platform"},
    {"slug": "podia", "name": "Podia", "category": "Course Platform"},
    {"slug": "circle", "name": "Circle", "category": "Community"},
    {"slug": "mighty-networks", "name": "Mighty Networks", "category": "Community"},

    # Payments
    {"slug": "stripe", "name": "Stripe", "category": "Payments"},
    {"slug": "gumroad", "name": "Gumroad", "category": "Payments"},
    {"slug": "payhip", "name": "Payhip", "category": "Payments"},
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

PHYSICAL_THERAPY_SOFTWARE: List[SoftwareOption] = [
    # PT Practice Management
    {"slug": "webpt", "name": "WebPT", "category": "Practice Management"},
    {"slug": "clinicient", "name": "Clinicient", "category": "Practice Management"},
    {"slug": "net-health", "name": "Net Health (ReDoc)", "category": "Practice Management"},
    {"slug": "prompt-emr", "name": "Prompt EMR", "category": "Practice Management"},
    {"slug": "better-pt", "name": "BetterPT", "category": "Practice Management"},
    {"slug": "jane-app", "name": "Jane App", "category": "Practice Management"},
    {"slug": "simple-practice", "name": "SimplePractice", "category": "Practice Management"},
    {"slug": "drchrono", "name": "DrChrono", "category": "Practice Management"},

    # Patient Engagement
    {"slug": "physitrack", "name": "Physitrack", "category": "Patient Engagement"},
    {"slug": "medbridge", "name": "MedBridge", "category": "Patient Engagement"},
    {"slug": "pt-ally", "name": "PT Ally", "category": "Patient Engagement"},
]

MEDSPA_SOFTWARE: List[SoftwareOption] = [
    # MedSpa/Aesthetic Practice Management
    {"slug": "aesthetics-pro", "name": "AestheticsPro", "category": "Practice Management"},
    {"slug": "boulevard", "name": "Boulevard", "category": "Practice Management"},
    {"slug": "vagaro", "name": "Vagaro", "category": "Practice Management"},
    {"slug": "zenoti", "name": "Zenoti", "category": "Practice Management"},
    {"slug": "meevo", "name": "Meevo 2", "category": "Practice Management"},
    {"slug": "pabau", "name": "Pabau", "category": "Practice Management"},
    {"slug": "aesthetic-record", "name": "Aesthetic Record", "category": "Practice Management"},

    # Marketing & Reviews
    {"slug": "demandforce", "name": "Demandforce", "category": "Marketing"},
    {"slug": "realself", "name": "RealSelf", "category": "Marketing"},
    {"slug": "podium", "name": "Podium", "category": "Reviews"},
]


# ============================================================================
# INDUSTRY MAPPING
# ============================================================================

INDUSTRY_SOFTWARE_MAP: dict[str, List[SoftwareOption]] = {
    "dental": DENTAL_SOFTWARE,
    "recruiting": RECRUITING_SOFTWARE,
    "home-services": HOME_SERVICES_SOFTWARE,
    "veterinary": VETERINARY_SOFTWARE,
    "coaching": COACHING_SOFTWARE,
    "professional-services": PROFESSIONAL_SERVICES_SOFTWARE,
    "physical-therapy": PHYSICAL_THERAPY_SOFTWARE,
    "medspa": MEDSPA_SOFTWARE,
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
