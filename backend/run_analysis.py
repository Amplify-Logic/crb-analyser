"""
Run CRB Analysis for Aquablu
"""
import asyncio
import sys
sys.path.insert(0, '/Users/larsmusic/CRB Analyser/crb-analyser/backend')

from src.agents.crb_agent import CRBAgent


async def run_analysis(audit_id: str):
    """Run the full analysis and print progress."""
    print(f"\n{'='*60}")
    print(f"RUNNING CRB ANALYSIS FOR AUDIT: {audit_id}")
    print(f"{'='*60}\n")

    agent = CRBAgent(audit_id)

    async for update in agent.run_analysis():
        phase = update.get("phase", "")
        step = update.get("step", "")
        progress = update.get("progress", 0)
        tool = update.get("tool", "")
        error = update.get("error", "")

        if error:
            print(f"\n[ERROR] {error}\n")
        elif tool:
            print(f"  [{progress:3d}%] [{phase.upper():12s}] Tool: {tool}")
        else:
            print(f"  [{progress:3d}%] [{phase.upper():12s}] {step}")

        if "result" in update:
            print(f"\n{'='*60}")
            print("ANALYSIS COMPLETE!")
            print(f"{'='*60}")
            result = update["result"]
            print(f"AI Readiness Score: {result.get('ai_readiness_score', 'N/A')}")
            print(f"Total Findings: {result.get('total_findings', 0)}")
            print(f"Total Potential Savings: €{result.get('total_potential_savings', 0):,.2f}")
            print(f"{'='*60}\n")


if __name__ == "__main__":
    audit_id = "dffefe00-168f-4116-a93a-da7a17485083"

    if len(sys.argv) > 1:
        audit_id = sys.argv[1]

    asyncio.run(run_analysis(audit_id))
