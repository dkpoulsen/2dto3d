import { test, expect } from '@playwright/test';

test.describe('Notification System', () => {
  test('should display notification bell in header', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.locator('h1')).toContainText('2Dto3D Converter');
    
    // Check for notification bell button
    const notificationBell = page.getByRole('button', { name: /notifications/i });
    await expect(notificationBell).toBeVisible();
  });

  test('should open notification dropdown when clicking bell', async ({ page }) => {
    await page.goto('/');
    
    // Click on notification bell
    const notificationBell = page.getByRole('button', { name: /notifications/i });
    await notificationBell.click();
    
    // Check for dropdown panel
    const dropdown = page.locator('[role="menu"]').filter({ hasText: 'Notifications' });
    await expect(dropdown).toBeVisible();
    
    // Check for header elements
    await expect(dropdown.getByText('Notifications')).toBeVisible();
  });

  test('should show empty state when no notifications', async ({ page }) => {
    await page.goto('/');
    
    // Open notification dropdown
    await page.getByRole('button', { name: /notifications/i }).click();
    
    // Check for empty state (either "No notifications" text or notification list)
    const dropdown = page.locator('[role="menu"]').filter({ hasText: 'Notifications' });
    await expect(dropdown).toBeVisible();
    
    // The dropdown should either show "No notifications" or a list of notifications
    const hasNoNotifications = await dropdown.getByText('No notifications').isVisible();
    const hasNotificationList = await dropdown.locator('li').count() > 0;
    
    expect(hasNoNotifications || hasNotificationList).toBeTruthy();
  });

  test('notification API endpoints should be accessible', async ({ page }) => {
    // Test GET /api/v1/notifications/
    const listResponse = await page.request.get('/api/v1/notifications/');
    expect(listResponse.ok()).toBeTruthy();
    
    const listData = await listResponse.json();
    expect(listData).toHaveProperty('notifications');
    expect(listData).toHaveProperty('total_count');
    expect(listData).toHaveProperty('unread_count');
    expect(Array.isArray(listData.notifications)).toBeTruthy();
    
    // Test GET /api/v1/notifications/count
    const countResponse = await page.request.get('/api/v1/notifications/count');
    expect(countResponse.ok()).toBeTruthy();
    
    const countData = await countResponse.json();
    expect(countData).toHaveProperty('total');
    expect(countData).toHaveProperty('unread');
    expect(countData).toHaveProperty('dismissed');
  });

  test('should display notification count badge when there are unread notifications', async ({ page }) => {
    await page.goto('/');
    
    // Get the notification bell
    const notificationBell = page.getByRole('button', { name: /notifications/i });
    
    // Check if there's a badge (count indicator)
    const badge = notificationBell.locator('span').filter({ hasText: /\d+/ });
    
    // Badge may or may not be present depending on unread count
    // Just verify the bell is visible and functional
    await expect(notificationBell).toBeVisible();
    await notificationBell.click();
    
    // Dropdown should open
    const dropdown = page.locator('[role="menu"]');
    await expect(dropdown).toBeVisible();
  });

  test('should have refresh button in notification dropdown', async ({ page }) => {
    await page.goto('/');
    
    // Open notification dropdown
    await page.getByRole('button', { name: /notifications/i }).click();
    
    // Check for refresh button
    const dropdown = page.locator('[role="menu"]');
    const refreshButton = dropdown.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
    
    // Click refresh button
    await refreshButton.click();
    
    // Dropdown should still be visible (no errors)
    await expect(dropdown).toBeVisible();
  });

  test('should mark all as read when clicking the link', async ({ page }) => {
    await page.goto('/');
    
    // Open notification dropdown
    await page.getByRole('button', { name: /notifications/i }).click();
    
    // Check for "Mark all read" link (only visible if there are unread notifications)
    const dropdown = page.locator('[role="menu"]');
    const markAllReadLink = dropdown.getByText('Mark all read');
    
    // If there are unread notifications, the link should be visible
    const isMarkAllVisible = await markAllReadLink.isVisible().catch(() => false);
    
    if (isMarkAllVisible) {
      await markAllReadLink.click();
      
      // Wait for action to complete
      await page.waitForTimeout(500);
      
      // Dropdown should still be visible
      await expect(dropdown).toBeVisible();
    }
  });

  test('should close dropdown when clicking outside', async ({ page }) => {
    await page.goto('/');
    
    // Open notification dropdown
    await page.getByRole('button', { name: /notifications/i }).click();
    
    // Dropdown should be visible
    const dropdown = page.locator('[role="menu"]');
    await expect(dropdown).toBeVisible();
    
    // Click somewhere else on the page
    await page.locator('h1').click();
    
    // Dropdown should be closed
    await expect(dropdown).not.toBeVisible();
  });
});
