import { test, expect } from '@playwright/test';

test.describe('Web Dashboard', () => {
  test('should load the dashboard homepage', async ({ page }) => {
    await page.goto('/');
    
    // Check for the main title
    await expect(page.locator('h1')).toContainText('2Dto3D Converter');
    
    // Check for navigation links
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Upload' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Jobs' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Downloads' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'System' })).toBeVisible();
  });

  test('should display dashboard statistics', async ({ page }) => {
    await page.goto('/');
    
    // Wait for stats to load
    await expect(page.getByText('Total Jobs')).toBeVisible();
    await expect(page.getByText('Completed')).toBeVisible();
    await expect(page.getByText('Failed')).toBeVisible();
    await expect(page.getByText('Success Rate')).toBeVisible();
  });

  test('should navigate to Upload page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Upload');
    await expect(page).toHaveURL('/upload');
    
    // Check for upload zone
    await expect(page.getByText('Click to upload')).toBeVisible();
    await expect(page.getByText('Uploaded Files')).toBeVisible();
  });

  test('should navigate to Jobs page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Jobs');
    await expect(page).toHaveURL('/jobs');
    
    // Check for jobs page elements
    await expect(page.getByRole('heading', { name: 'Jobs' })).toBeVisible();
    await expect(page.getByText('New Job')).toBeVisible();
  });

  test('should navigate to Downloads page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=Downloads');
    await expect(page).toHaveURL('/downloads');
    
    // Check for downloads page elements
    await expect(page.getByRole('heading', { name: 'Downloads' })).toBeVisible();
  });

  test('should navigate to System page', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=System');
    await expect(page).toHaveURL('/system');
    
    // Check for system page elements
    await expect(page.getByRole('heading', { name: 'System' })).toBeVisible();
    await expect(page.getByText('GPU Status')).toBeVisible();
    await expect(page.getByText('System Memory')).toBeVisible();
  });

  test('should filter jobs by status', async ({ page }) => {
    await page.goto('/jobs');
    
    // Check filter buttons are present
    await expect(page.getByRole('button', { name: 'All' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Pending' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Completed' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Failed' })).toBeVisible();
  });

  test('should have responsive sidebar navigation', async ({ page }) => {
    await page.goto('/');
    
    // Sidebar should be visible on desktop
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();
    
    // Check navigation items in sidebar
    await expect(sidebar.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Upload' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Jobs' })).toBeVisible();
  });

  test('API health endpoint should return healthy status', async ({ page }) => {
    const response = await page.request.get('/health');
    expect(response.ok()).toBeTruthy();
    
    const health = await response.json();
    expect(health).toHaveProperty('status');
    expect(health).toHaveProperty('version');
    expect(health).toHaveProperty('queue_running');
  });
});
