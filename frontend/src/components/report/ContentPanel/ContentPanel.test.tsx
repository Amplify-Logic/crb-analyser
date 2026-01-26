import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ContentPanel } from './ContentPanel'

describe('ContentPanel', () => {
  it('renders breadcrumb navigation', () => {
    render(
      <ContentPanel
        breadcrumb={['Findings', 'Manual Invoicing']}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        prevLabel="Overview"
        nextLabel="Appointment Gaps"
      >
        <div>Content here</div>
      </ContentPanel>
    )
    
    expect(screen.getByText('Findings')).toBeInTheDocument()
    expect(screen.getByText('Manual Invoicing')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <ContentPanel
        breadcrumb={['Overview']}
        onPrev={vi.fn()}
        onNext={vi.fn()}
      >
        <div data-testid="content">Test content</div>
      </ContentPanel>
    )
    
    expect(screen.getByTestId('content')).toBeInTheDocument()
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('renders prev/next navigation when labels provided', () => {
    const onPrev = vi.fn()
    const onNext = vi.fn()
    
    render(
      <ContentPanel
        breadcrumb={['Findings']}
        onPrev={onPrev}
        onNext={onNext}
        prevLabel="Overview"
        nextLabel="Actions"
      >
        <div>Content</div>
      </ContentPanel>
    )
    
    expect(screen.getByText(/Overview/)).toBeInTheDocument()
    expect(screen.getByText(/Actions/)).toBeInTheDocument()
  })

  it('calls onPrev when prev button clicked', () => {
    const onPrev = vi.fn()
    
    render(
      <ContentPanel
        breadcrumb={['Findings']}
        onPrev={onPrev}
        onNext={vi.fn()}
        prevLabel="Overview"
      >
        <div>Content</div>
      </ContentPanel>
    )
    
    fireEvent.click(screen.getByText(/Overview/))
    expect(onPrev).toHaveBeenCalled()
  })

  it('calls onNext when next button clicked', () => {
    const onNext = vi.fn()
    
    render(
      <ContentPanel
        breadcrumb={['Findings']}
        onPrev={vi.fn()}
        onNext={onNext}
        nextLabel="Actions"
      >
        <div>Content</div>
      </ContentPanel>
    )
    
    fireEvent.click(screen.getByText(/Actions/))
    expect(onNext).toHaveBeenCalled()
  })

  it('hides prev button when no prevLabel', () => {
    render(
      <ContentPanel
        breadcrumb={['Overview']}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        nextLabel="Findings"
      >
        <div>Content</div>
      </ContentPanel>
    )
    
    // Should only have the next button visible
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBe(1)
  })
})
