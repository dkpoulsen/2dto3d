import React, { createContext, useContext, useCallback, useEffect, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '../api';
import { POLLING_INTERVALS } from '../utils/constants';
import type { Notification, NotificationListResponse, NotificationCountResponse } from '../api';

interface NotificationContextValue {
  /** List of notifications */
  notifications: Notification[];
  /** Total count of notifications */
  totalCount: number;
  /** Count of unread notifications */
  unreadCount: number;
  /** Whether notifications are loading */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Refresh notifications */
  refresh: () => Promise<void>;
  /** Mark a notification as read */
  markAsRead: (notificationId: string) => Promise<void>;
  /** Mark all notifications as read */
  markAllAsRead: () => Promise<void>;
  /** Dismiss a notification */
  dismiss: (notificationId: string) => Promise<void>;
  /** Clear all notifications */
  clearAll: () => Promise<void>;
  /** Delete a notification */
  deleteNotification: (notificationId: string) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

interface NotificationProviderProps {
  children: React.ReactNode;
  /** Polling interval in milliseconds (default: from constants) */
  pollingInterval?: number;
  /** Maximum number of notifications to keep in memory */
  maxNotifications?: number;
}

export function NotificationProvider({
  children,
  pollingInterval = POLLING_INTERVALS.SLOW,
  maxNotifications = 100,
}: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);
  const queryClient = useQueryClient();

  /** Fetch notifications from the API */
  const fetchNotifications = useCallback(async (isPolling = false) => {
    // Don't set loading state during polling
    if (!isPolling && mountedRef.current) {
      setIsLoading(true);
    }
    if (!isPolling && mountedRef.current) {
      setError(null);
    }

    try {
      const response = await notificationsApi.listNotifications({
        include_read: true,
        include_dismissed: false,
        page: 1,
        page_size: maxNotifications,
      });

      if (mountedRef.current) {
        setNotifications(response.notifications);
        setTotalCount(response.total_count);
        setUnreadCount(response.unread_count);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch notifications';
      console.error('Failed to fetch notifications:', err);
      // Only show errors from explicit refreshes, not polling
      if (!isPolling && mountedRef.current) {
        setError(message);
      }
    } finally {
      if (!isPolling && mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [maxNotifications]);

  /** Refresh notifications manually */
  const refresh = useCallback(async () => {
    await fetchNotifications(false);
  }, [fetchNotifications]);

  /** Mark a notification as read */
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await notificationsApi.markAsRead({ notification_ids: [notificationId] });
      
      // Update local state optimistically
      setNotifications((prev) =>
        prev.map((n) =>
          n.notification_id === notificationId ? { ...n, read: true } : n
        )
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to mark notification as read';
      console.error('Failed to mark notification as read:', err);
      setError(message);
    }
  }, [queryClient]);

  /** Mark all notifications as read */
  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsApi.markAllAsRead();
      
      // Update local state optimistically
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to mark all notifications as read';
      console.error('Failed to mark all notifications as read:', err);
      setError(message);
    }
  }, [queryClient]);

  /** Dismiss a notification */
  const dismiss = useCallback(async (notificationId: string) => {
    try {
      await notificationsApi.dismiss({ notification_ids: [notificationId] });
      
      // Update local state optimistically
      setNotifications((prev) => prev.filter((n) => n.notification_id !== notificationId));
      setTotalCount((prev) => Math.max(0, prev - 1));
      
      // Update unread count if the notification was unread
      const notification = notifications.find((n) => n.notification_id === notificationId);
      if (notification && !notification.read) {
        setUnreadCount((prev) => Math.max(0, prev - 1));
      }
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to dismiss notification';
      console.error('Failed to dismiss notification:', err);
      setError(message);
    }
  }, [notifications, queryClient]);

  /** Clear all notifications */
  const clearAll = useCallback(async () => {
    try {
      await notificationsApi.clearAll();
      
      // Update local state optimistically
      setNotifications([]);
      setTotalCount(0);
      setUnreadCount(0);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear notifications';
      console.error('Failed to clear notifications:', err);
      setError(message);
    }
  }, [queryClient]);

  /** Delete a notification */
  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      await notificationsApi.deleteNotification(notificationId);
      
      // Update local state optimistically
      setNotifications((prev) => prev.filter((n) => n.notification_id !== notificationId));
      setTotalCount((prev) => Math.max(0, prev - 1));
      
      // Update unread count if the notification was unread
      const notification = notifications.find((n) => n.notification_id === notificationId);
      if (notification && !notification.read) {
        setUnreadCount((prev) => Math.max(0, prev - 1));
      }
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete notification';
      console.error('Failed to delete notification:', err);
      setError(message);
    }
  }, [notifications, queryClient]);

  // Initial fetch and polling setup
  useEffect(() => {
    mountedRef.current = true;
    fetchNotifications(false);

    // Set up polling
    pollingRef.current = setInterval(() => fetchNotifications(true), pollingInterval);

    return () => {
      mountedRef.current = false;
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [fetchNotifications, pollingInterval]);

  const value: NotificationContextValue = {
    notifications,
    totalCount,
    unreadCount,
    isLoading,
    error,
    refresh,
    markAsRead,
    markAllAsRead,
    dismiss,
    clearAll,
    deleteNotification,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

/**
 * Hook to access the notification context.
 * Must be used within a NotificationProvider.
 */
export function useNotifications(): NotificationContextValue {
  const context = useContext(NotificationContext);
  
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  
  return context;
}

export { NotificationContext };
