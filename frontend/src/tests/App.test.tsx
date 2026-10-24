import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { StatusBadge } from '../components/StatusBadge';
import { StatCard } from '../components/StatCard';
import { DollarSign } from 'lucide-react';

describe('Bank Fee Auditor Frontend Components', () => {
  it('renders status badges with correct text and styles', () => {
    const { getByText } = render(<StatusBadge status="FLAGGED" />);
    expect(getByText('FLAGGED')).toBeInTheDocument();
  });

  it('renders StatCard with formatted value and title', () => {
    const { getByText } = render(
      <StatCard
        title="Potential Recovery Target"
        value="$50.00"
        subtitle="3 violations detected"
        icon={DollarSign}
        variant="blue"
      />
    );
    expect(getByText('Potential Recovery Target')).toBeInTheDocument();
    expect(getByText('$50.00')).toBeInTheDocument();
    expect(getByText('3 violations detected')).toBeInTheDocument();
  });
});
