import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Layout } from '../Layout';

// Mock React Router's Outlet
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet">Outlet Content</div>,
  };
});

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Layout', () => {
  it('should render header with title', () => {
    renderWithRouter(<Layout />);
    expect(screen.getByText('2Dto3D Converter')).toBeInTheDocument();
  });

  it('should render navigation links', () => {
    renderWithRouter(<Layout />);
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Upload' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Jobs' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Downloads' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'System' })).toBeInTheDocument();
  });

  it('should render Outlet', () => {
    renderWithRouter(<Layout />);
    expect(screen.getByTestId('outlet')).toBeInTheDocument();
  });

  it('should have sidebar navigation', () => {
    renderWithRouter(<Layout />);
    const nav = screen.getByRole('navigation', { name: 'Main navigation' });
    expect(nav).toBeInTheDocument();
  });

  it('should render icons for each nav item', () => {
    renderWithRouter(<Layout />);
    const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
    expect(dashboardLink.querySelector('svg')).toBeInTheDocument();
  });

  it('should have correct link destinations', () => {
    renderWithRouter(<Layout />);
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: 'Upload' })).toHaveAttribute('href', '/upload');
    expect(screen.getByRole('link', { name: 'Jobs' })).toHaveAttribute('href', '/jobs');
    expect(screen.getByRole('link', { name: 'Downloads' })).toHaveAttribute('href', '/downloads');
    expect(screen.getByRole('link', { name: 'System' })).toHaveAttribute('href', '/system');
  });

  it('should have main content area', () => {
    renderWithRouter(<Layout />);
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('should display "Web Dashboard" subtitle', () => {
    renderWithRouter(<Layout />);
    expect(screen.getByText('Web Dashboard')).toBeInTheDocument();
  });
});
