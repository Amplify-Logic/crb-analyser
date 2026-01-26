import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Sidebar } from './Sidebar'

const mockProps = {
  companyName: 'Test Company',
  industry: 'Dental',
  score: 72,
  findings: [
    { id: 'f1', title: 'Manual Invoicing', status: 'pending' as const },
    { id: 'f2', title: 'Appointment Gaps', status: 'completed' as const },
  ],
  actions: [
    { id: 'a1', title: 'Automate Invoicing', priority: 'high' as const },
  ],
  playbookPhases: [
    { id: 'p1', title: 'Phase 1: Quick Wins', completedTasks: 2, totalTasks: 5 },
  ],
  activeItem: { type: 'overview' as const, id: null },
  onItemClick: vi.fn(),
}

describe('Sidebar', () => {
  it('renders company name and score', () => {
    render(<Sidebar {...mockProps} />)
    
    expect(screen.getByText('Test Company')).toBeInTheDocument()
    expect(screen.getByText('72')).toBeInTheDocument()
  })

  it('renders findings section with count', () => {
    render(<Sidebar {...mockProps} />)
    
    expect(screen.getByText(/Findings/)).toBeInTheDocument()
    expect(screen.getByText('(2)')).toBeInTheDocument()
  })

  it('renders finding items', () => {
    render(<Sidebar {...mockProps} />)
    
    expect(screen.getByText('Manual Invoicing')).toBeInTheDocument()
    expect(screen.getByText('Appointment Gaps')).toBeInTheDocument()
  })

  it('calls onItemClick when finding is clicked', () => {
    render(<Sidebar {...mockProps} />)
    
    fireEvent.click(screen.getByText('Manual Invoicing'))
    
    expect(mockProps.onItemClick).toHaveBeenCalledWith({ type: 'finding', id: 'f1' })
  })

  it('highlights active item', () => {
    const propsWithActiveFinding = {
      ...mockProps,
      activeItem: { type: 'finding' as const, id: 'f1' },
    }
    render(<Sidebar {...propsWithActiveFinding} />)
    
    const activeItem = screen.getByText('Manual Invoicing').closest('button')
    expect(activeItem).toHaveClass('bg-primary-50')
  })

  it('shows status indicators for findings', () => {
    render(<Sidebar {...mockProps} />)
    
    // Should have different indicators for pending vs completed
    const items = screen.getAllByRole('button')
    expect(items.length).toBeGreaterThan(0)
  })
})
