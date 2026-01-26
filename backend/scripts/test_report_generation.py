#!/usr/bin/env python3
"""
E2E Report Generation Test

Run with: cd backend && source venv/bin/activate && python scripts/test_report_generation.py
"""

import asyncio
import json
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_test():
    from src.config.supabase_client import get_async_supabase
    from src.services.report_service import generate_report_streaming

    test_session_data = {
        'company_profile': {
            'basics': {
                'name': {'value': 'Smile Dental Auckland'},
                'website': {'value': 'smiledentalauckland.co.nz'},
                'description': {'value': 'Family dental practice in Ponsonby serving Auckland for 8 years. We offer general dentistry, cosmetic procedures, orthodontics, and emergency dental care.'}
            },
            'industry': {
                'primary_industry': {'value': 'dental'}
            },
            'size': {
                'employee_range': {'value': '11-50'},
                'employee_count': {'value': 9}
            }
        },
        'quiz_answers': {
            'industry': 'dental',
            'company_description': 'Family dental practice in Ponsonby, Auckland. 3 dentists, 2 hygienists, 4 admin staff.',
            'employee_count': '11-50',
            'annual_revenue': '1m_5m',
            'primary_goals': ['increase_revenue', 'improve_efficiency', 'improve_customer_experience'],
            'main_processes': ['patient_scheduling', 'billing', 'patient_communication', 'insurance_verification'],
            'biggest_bottlenecks': ['no_shows', 'phone_tag', 'insurance_claims'],
            'time_on_admin': '40_60_percent',
            'current_tools': ['practice_management', 'accounting_software', 'email'],
            'biggest_challenge': 'We lose 15-20% appointments to no-shows. Front desk spends 3+ hours daily on phone tag. Insurance verification takes 20-30 mins per patient.',
            'budget_for_solutions': '5000_15000',
            'implementation_timeline': '3_6_months'
        },
        'interview_data': {
            'messages': [
                {'role': 'user', 'content': 'Our biggest pain is no-shows. We run about 18% no-show rate which costs us probably 8-10k per month in lost revenue.'},
                {'role': 'user', 'content': 'Insurance verification is a nightmare. Sarah spends 2-3 hours every morning calling insurance companies.'},
                {'role': 'user', 'content': 'We use EXACT for accounting but our practice management Dental4Windows is old and doesnt integrate with anything.'},
                {'role': 'user', 'content': 'After hours calls go to voicemail. We probably miss 5-10 potential new patients a week.'},
                {'role': 'user', 'content': 'Recall compliance is maybe 40% on 3000+ patients. Thats a lot of hygiene revenue on the table.'}
            ]
        }
    }

    supabase = await get_async_supabase()
    session_id = str(uuid.uuid4())

    session_data = {
        'id': session_id,
        'email': 'test-smile-dental@crb-test.local',
        'tier': 'quick',
        'status': 'paid',
        'current_section': 0,
        'current_question': 0,
        'answers': test_session_data['quiz_answers'],
        'company_name': 'Smile Dental Auckland',
        'company_website': 'smiledentalauckland.co.nz',
        'company_profile': test_session_data['company_profile'],
        'interview_data': test_session_data['interview_data'],
    }

    await supabase.table('quiz_sessions').insert(session_data).execute()
    print(f'Session: {session_id}')
    print('Generating report (this takes 60-120 seconds)...')
    print()

    report_id = None
    async for event in generate_report_streaming(session_id, 'quick'):
        if event.startswith('data: '):
            try:
                data = json.loads(event[6:].strip())
                if data.get('step'):
                    progress = data.get('progress', 0)
                    step = data.get('step')
                    print(f"  {progress:3d}% - {step}")
                    sys.stdout.flush()
                if data.get('report_id'):
                    report_id = data['report_id']
                if data.get('phase') == 'error':
                    print(f"ERROR: {data.get('error')}")
            except json.JSONDecodeError:
                pass

    if report_id:
        print()
        print(f'Report generated: {report_id}')
        print(f'View at: http://localhost:5174/report/{report_id}')

        result = await supabase.table('reports').select('*').eq('id', report_id).single().execute()
        if result.data:
            output_path = '/tmp/smile-dental-report.json'
            with open(output_path, 'w') as f:
                json.dump(result.data, f, indent=2)
            print(f'Saved to: {output_path}')

            # Print summary
            report = result.data
            print()
            print('=' * 60)
            print('REPORT SUMMARY')
            print('=' * 60)

            if 'executive_summary' in report:
                es = report['executive_summary']
                print(f"AI Readiness Score: {es.get('ai_readiness_score', 'N/A')}")
                print(f"Key Insight: {es.get('key_insight', 'N/A')[:100]}...")

            if 'findings' in report:
                print(f"\nFindings: {len(report['findings'])}")
                for i, f in enumerate(report['findings'][:3], 1):
                    title = f.get('title', f.get('name', 'Untitled'))
                    print(f"  {i}. {title}")

            if 'recommendations' in report:
                print(f"\nRecommendations: {len(report['recommendations'])}")

    else:
        print('ERROR: No report_id returned')

    return report_id


if __name__ == '__main__':
    report_id = asyncio.run(run_test())
