import React from 'react';
import { render, screen } from '@testing-library/react';
import KPIWidget from './KPIWidget';
import { Users } from 'lucide-react';
import '@testing-library/jest-dom';

describe('KPIWidget', () => {
  const defaultProps = {
    label: 'Total Leads',
    value: '1,234',
    change: '+10%',
    icon: Users,
    color: '#0ea5e9',
    trend: 'up'
  };

  test('renders label and value correctly', () => {
    render(<KPIWidget {...defaultProps} />);
    expect(screen.getByText('Total Leads')).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
  });

  test('renders change percentage', () => {
    render(<KPIWidget {...defaultProps} />);
    expect(screen.getByText('+10%')).toBeInTheDocument();
  });

  test('applies correct trend colors', () => {
    const { rerender } = render(<KPIWidget {...defaultProps} />);
    expect(screen.getByText('+10%')).toHaveClass('text-[var(--success)]');

    rerender(<KPIWidget {...defaultProps} change="-5%" trend="down" />);
    expect(screen.getByText('-5%')).toHaveClass('text-[var(--error)]');
  });
});
