import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from '../StatCard';
import { CheckCircle } from 'lucide-react';

describe('StatCard', () => {
  it('should render title and value', () => {
    render(<StatCard title="Total Jobs" value={42} />);
    expect(screen.getByText('Total Jobs')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('should render string values', () => {
    render(<StatCard title="Status" value="Running" />);
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('should render subtitle', () => {
    render(
      <StatCard
        title="Success Rate"
        value="95%"
        subtitle="+5% from last week"
      />
    );
    expect(screen.getByText('+5% from last week')).toBeInTheDocument();
  });

  it('should render icon', () => {
    render(
      <StatCard
        title="Completed"
        value={100}
        icon={<CheckCircle className="h-6 w-6 text-green-600" data-testid="stat-icon" />}
      />
    );
    expect(screen.getByTestId('stat-icon')).toBeInTheDocument();
  });

  it('should render without icon', () => {
    render(<StatCard title="Jobs" value={10} />);
    expect(screen.getByText('Jobs')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('should apply up trend color', () => {
    render(
      <StatCard
        title="Success Rate"
        value="95%"
        trend="up"
        subtitle="Increasing"
      />
    );
    const subtitle = screen.getByText('Increasing');
    expect(subtitle).toHaveClass('text-green-600');
  });

  it('should apply down trend color', () => {
    render(
      <StatCard
        title="Error Rate"
        value="5%"
        trend="down"
        subtitle="Decreasing"
      />
    );
    const subtitle = screen.getByText('Decreasing');
    expect(subtitle).toHaveClass('text-red-600');
  });

  it('should apply neutral trend color', () => {
    render(
      <StatCard
        title="Stable"
        value="50%"
        trend="neutral"
        subtitle="No change"
      />
    );
    const subtitle = screen.getByText('No change');
    expect(subtitle).toHaveClass('text-gray-600');
  });

  it('should render without trend color when not specified', () => {
    render(
      <StatCard
        title="Jobs"
        value={10}
        subtitle="Total count"
      />
    );
    const subtitle = screen.getByText('Total count');
    expect(subtitle).toHaveClass('text-gray-500');
  });

  it('should render large numbers', () => {
    render(<StatCard title="Total" value={1000000} />);
    expect(screen.getByText('1000000')).toBeInTheDocument();
  });
});
