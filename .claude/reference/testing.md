# Testing Reference

> Load this when writing tests, fixing test failures, or reviewing test code.

---

## Frameworks

| Layer | Framework |
|-------|-----------|
| Backend | pytest + pytest-asyncio |
| Frontend | vitest + @testing-library/react |

## Running Tests

```bash
# Backend
cd backend && pytest
cd backend && pytest -v tests/test_report_service.py  # Single file
cd backend && pytest -k "test_calculate"              # By name pattern

# Frontend
cd frontend && npm test
```

## Test Structure

```
backend/tests/
├── conftest.py         # Shared fixtures
├── test_*.py           # Test files (flat structure)
└── skills/             # Skill-specific tests

frontend/src/
└── __tests__/          # Co-located with components
```

## Backend Patterns

### Unit Test (Fast, Isolated)
```python
def test_calculate_roi_with_high_confidence():
    result = calculate_roi(base=10000, confidence="HIGH")
    assert result == 10000  # 1.0 factor
```

### Integration Test (With Mocks)
```python
async def test_get_vendor_caches_result(mock_supabase, mock_redis):
    service = VendorService(mock_supabase, mock_redis)
    await service.get_vendor("123")
    mock_redis.setex.assert_called_once()
```

### Fixture Pattern
```python
# conftest.py
@pytest.fixture
def mock_supabase():
    with patch('src.config.supabase_client.get_async_supabase') as mock:
        yield mock

@pytest.fixture
def sample_vendor():
    return {
        "slug": "test-vendor",
        "name": "Test Vendor",
        "category": "crm",
        "pricing": {"starting_price": 49}
    }
```

## Frontend Patterns

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Component } from '../Component';

test('renders correctly', () => {
  render(<Component />);
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});

test('handles click', async () => {
  const onSubmit = vi.fn();
  render(<Form onSubmit={onSubmit} />);

  fireEvent.click(screen.getByRole('button'));
  expect(onSubmit).toHaveBeenCalled();
});
```

## Critical Paths Requiring 80%+ Coverage

- Authentication flow
- Payment processing
- Report generation
- Quiz session management

## Anti-Patterns (NEVER DO THESE)

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| Tests that depend on execution order | Flaky, hard to debug | Each test is independent |
| Mocking the thing you're testing | Tests mock behavior, not real code | Mock dependencies, not SUT |
| Tests without assertions | Passes but proves nothing | Every test asserts something |
| Sleeping instead of polling | Slow, flaky | Use async/await, poll for condition |
| Testing implementation details | Breaks on refactor | Test behavior/output |
| Adding test-only methods to prod code | Pollutes production | Use dependency injection |

## Condition-Based Waiting (No Sleeps)

```python
# BAD
await asyncio.sleep(2)
assert result.status == "complete"

# GOOD
async def wait_for_completion(result, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        if result.status == "complete":
            return True
        await asyncio.sleep(0.1)
    return False

assert await wait_for_completion(result)
```

## TDD Workflow

1. **Red**: Write failing test first
2. **Green**: Write minimal code to pass
3. **Refactor**: Clean up, test still passes

The test MUST fail first. If it passes immediately, the test is wrong.
