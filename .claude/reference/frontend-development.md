# Frontend Development Reference

> Load this when working on React components, pages, or frontend features.

---

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Router (routing)
- Vitest + Testing Library (tests)

## Project Structure

```
frontend/src/
├── pages/              # Route-level components
│   ├── Quiz.tsx        # Multi-step wizard
│   ├── ReportViewer.tsx
│   ├── Dashboard.tsx
│   └── admin/          # Admin pages
├── components/         # Reusable components
│   ├── report/         # Report-specific
│   └── ui/             # Generic UI
├── contexts/           # React contexts
│   └── AuthContext.tsx
├── services/           # API calls
├── hooks/              # Custom hooks
└── __tests__/          # Co-located tests
```

## Route Structure

```
# Public
/                        Landing page
/login, /signup          Auth
/terms, /privacy         Legal pages
/professional-services   Professional Services industry page
/dental                  Dental industry page
/ecommerce               E-commerce industry page

# Anonymous Quiz Flow (main conversion path)
/quiz                    Multi-step quiz wizard
/quiz/interview          Voice interview (optional)
/quiz/adaptive           Adaptive follow-up questions
/quiz/preview            Report teaser before payment
/checkout                Stripe checkout
/checkout/success        Post-payment redirect

# Post-payment
/interview               90-minute workshop
/workshop                Workshop facilitation (same as /interview)
/report/:id              Public report viewer (quiz-based)
/report/:id/progress     Report generation progress

# Authenticated
/dashboard               List audits
/new-audit               Create new audit
/audit/:id/intake        Audit intake questionnaire
/audit/:id/progress      Audit progress tracking
/audit/:id/report        Audit-based report viewer

# Admin (requires auth)
/admin                   Admin dashboard
/admin/vendors           Vendor database management
/admin/knowledge         Knowledge base editor
/admin/insights          Insights list and management
/admin/insights/extract  AI-powered insight extraction
```

## Component Patterns

### Page Component
```tsx
// pages/NewFeature.tsx
export default function NewFeature() {
  const { user } = useAuth();
  const [data, setData] = useState<FeatureData | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="container mx-auto p-4">
      {/* Content */}
    </div>
  );
}
```

### API Service
```tsx
// services/feature.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL;

export async function getFeatureData(id: string): Promise<FeatureData> {
  const response = await fetch(`${API_BASE}/api/feature/${id}`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  if (!response.ok) throw new Error('Failed to fetch');
  return response.json();
}
```

## Key Components

| Component | Purpose |
|-----------|---------|
| `Quiz.tsx` | Multi-step wizard with progress tracking |
| `ReportViewer.tsx` | Full report with interactive sections |
| `AutomationRoadmap.tsx` | Visual roadmap in reports |
| `VendorAdmin.tsx` | Vendor database management |

## Testing

```bash
cd frontend && npm test
```

```tsx
// __tests__/Component.test.tsx
import { render, screen } from '@testing-library/react';
import { Component } from '../Component';

test('renders correctly', () => {
  render(<Component />);
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

## Environment Variables

```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Anti-Patterns

- Console.log statements in production code
- Inline styles (use Tailwind)
- Direct API calls in components (use services/)
- Missing loading/error states
- Hardcoded API URLs (use env vars)
