"""
Test script to run full CRB analysis flow for Aquablu
"""
import asyncio
import json
import sys
sys.path.insert(0, '/Users/larsmusic/CRB Analyser/crb-analyser/backend')

from src.config.supabase_client import get_supabase


# Aquablu intake responses based on research
AQUABLU_INTAKE = {
    # Section 1: Company Overview
    "company_description": """Aquablu manufactures smart water dispensing systems for commercial spaces.
Our flagship product, the REFILL+ Series 2, provides filtered water with customizable flavoring,
carbonation, and vitamin/mineral enhancement options. We serve enterprise clients like Intel, Microsoft,
Heineken, EY, and Pfizer across 10+ European cities, reaching over 100,000 employees.
Our mission is to eliminate 1 billion plastic bottles by 2030.""",

    "employee_count": "51-200",

    "annual_revenue": "5m_plus",

    "primary_goals": ["scale_operations", "improve_efficiency", "increase_revenue", "enter_new_markets"],

    # Section 2: Current Operations
    "main_processes": """Our main processes include:
1. Manufacturing and assembly of water dispensers in our production facility
2. Installation and onboarding of new enterprise clients
3. Ongoing maintenance and filter replacement scheduling across 10+ cities
4. Cartridge/consumables supply chain management and logistics
5. Customer success management for enterprise accounts
6. Sales pipeline management for new B2B opportunities
7. Sustainability reporting and plastic bottle reduction tracking""",

    "repetitive_tasks": """We spend significant time on:
- Manually tracking filter replacement schedules across hundreds of units
- Generating monthly usage and sustainability reports for each enterprise client
- Processing service requests and scheduling technician visits
- Updating inventory levels across multiple distribution centers
- Following up on leads and managing the sales pipeline
- Compiling compliance and sustainability documentation""",

    "biggest_bottlenecks": """Our biggest bottlenecks are:
1. Predicting when filters need replacement - currently reactive rather than proactive
2. Coordinating service technicians across multiple cities efficiently
3. Manual sustainability report generation for enterprise clients takes days
4. Sales team spends too much time on admin vs. actual selling
5. No real-time visibility into machine performance across our fleet""",

    "time_on_admin": 80,

    "manual_data_entry": "yes",
    "manual_data_entry_details": """We manually transfer data between:
- Service tickets from email to our scheduling system
- Machine telemetry data to Excel for analysis
- Sales opportunities from various sources to our CRM
- Usage data to sustainability reports for clients
- Inventory updates across our ERP and distribution systems""",

    # Section 3: Technology & Tools
    "current_tools": ["crm", "project_management", "accounting", "spreadsheets", "communication", "analytics"],

    "tool_pain_points": """Our main frustrations:
- Our CRM doesn't integrate well with our IoT platform that tracks machine data
- We rely heavily on spreadsheets for analytics because our BI tools are limited
- Service scheduling is done in a separate system that doesn't talk to CRM
- No automated alerts when machines need attention
- Sustainability calculations are done manually in Excel""",

    "integration_issues": 4,

    "technology_comfort": 7,

    "ai_tools_used": ["chatgpt", "writing"],

    # Section 4: Pain Points & Challenges
    "biggest_challenge": """Scaling our operations efficiently across Europe while maintaining service quality.
As we grow from 10 to 25+ cities, our current manual processes won't scale. We need predictive
maintenance, automated scheduling, and better analytics to manage a growing fleet of machines
without proportionally increasing headcount.""",

    "time_wasters": """Tasks that feel like a waste:
- Manually compiling monthly sustainability reports (8+ hours per enterprise client)
- Reactive maintenance - technicians traveling to sites only to find minor issues
- Sales team manually researching prospects when data is available
- Re-entering the same data in multiple systems
- Creating custom presentations for each sales pitch""",

    "missed_opportunities": """We're missing:
- Upselling opportunities based on usage patterns (could recommend premium flavors)
- Faster lead response time (currently 24-48 hours, should be instant)
- Proactive customer success interventions (churn prediction)
- Real-time sustainability dashboards that clients can share with their employees
- Geographic expansion held back by operational complexity""",

    "cost_concerns": ["labor", "software", "outsourcing"],

    "quality_issues": "yes",
    "quality_issues_details": """We see inconsistencies in:
- Service response times vary significantly by city
- Report quality depends on who creates them
- Some technicians miss issues that others would catch
- Customer communication styles vary across team members""",

    # Section 5: AI & Automation Readiness
    "ai_interest_areas": ["operations", "sales", "analytics", "customer_service"],

    "budget_for_solutions": "1000_5000",

    "implementation_timeline": "1_3_months",

    "decision_makers": "me_input",

    "additional_context": """We're at an inflection point. We've proven product-market fit with major
enterprise clients and now need to scale efficiently. Our IoT-enabled machines generate valuable data
that we're not fully utilizing. We believe AI could help us with predictive maintenance, automated
reporting, sales intelligence, and customer success - but we need a clear roadmap with ROI justification
to get budget approval from leadership.""",

    # Industry-specific (tech_company)
    "product_type": "hardware"
}


async def run_aquablu_test():
    """Run the full flow for Aquablu"""
    supabase = get_supabase()

    # Get the workspace (using the test user)
    user_result = supabase.table("users").select("workspace_id").eq(
        "email", "lars.tolhurst1@gmail.com"
    ).single().execute()

    workspace_id = user_result.data["workspace_id"]
    print(f"Using workspace: {workspace_id}")

    # Check if Aquablu client already exists
    client_result = supabase.table("clients").select("*").eq(
        "workspace_id", workspace_id
    ).eq("name", "Aquablu").execute()

    if client_result.data:
        client_id = client_result.data[0]["id"]
        print(f"Found existing Aquablu client: {client_id}")
    else:
        # Create Aquablu client
        client_data = {
            "workspace_id": workspace_id,
            "name": "Aquablu",
            "industry": "tech_company",
            "company_size": "51-200",
            "website": "https://www.aquablu.com/",
        }
        client_result = supabase.table("clients").insert(client_data).execute()
        client_id = client_result.data[0]["id"]
        print(f"Created Aquablu client: {client_id}")

    # Check if audit already exists for this client
    audit_result = supabase.table("audits").select("*").eq(
        "client_id", client_id
    ).execute()

    if audit_result.data:
        audit_id = audit_result.data[0]["id"]
        print(f"Found existing audit: {audit_id}")
    else:
        # Create audit
        audit_data = {
            "workspace_id": workspace_id,
            "client_id": client_id,
            "title": "Aquablu - CRB Audit",
            "tier": "professional",
            "status": "intake",
        }
        audit_result = supabase.table("audits").insert(audit_data).execute()
        audit_id = audit_result.data[0]["id"]
        print(f"Created audit: {audit_id}")

    # Check if intake_responses already exists
    intake_result = supabase.table("intake_responses").select("*").eq(
        "audit_id", audit_id
    ).execute()

    if intake_result.data:
        # Update existing intake responses
        supabase.table("intake_responses").update({
            "responses": AQUABLU_INTAKE,
            "is_complete": True,
        }).eq("audit_id", audit_id).execute()
        print(f"Updated intake responses for audit: {audit_id}")
    else:
        # Create new intake responses
        supabase.table("intake_responses").insert({
            "audit_id": audit_id,
            "responses": AQUABLU_INTAKE,
            "is_complete": True,
            "current_section": 5,
            "completed_sections": [1, 2, 3, 4, 5],
        }).execute()
        print(f"Created intake responses for audit: {audit_id}")

    # Update audit status to analyzing
    supabase.table("audits").update({
        "status": "analyzing",
        "current_phase": "discovery"
    }).eq("id", audit_id).execute()
    print(f"Set audit status to 'analyzing'")

    print("\n" + "="*60)
    print("AUDIT READY FOR ANALYSIS")
    print("="*60)
    print(f"Audit ID: {audit_id}")
    print(f"Client: Aquablu")
    print(f"Status: analyzing")
    print("\nNow running CRB agent analysis...")
    print("="*60 + "\n")

    return audit_id


if __name__ == "__main__":
    audit_id = asyncio.run(run_aquablu_test())
    print(f"\nAudit ID for analysis: {audit_id}")
