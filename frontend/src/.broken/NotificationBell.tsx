import { useState, useRef, useEffect } from 'react';
import { Bell, X, RefreshCw, AlertTriangle, CheckCircle, XCircle, Info, Clock } from 'lucide-react';
import { useNotifications } from '../contexts/NotificationContext';
import { formatDistanceToNow } from '../utils/format';
import type { Notification, NotificationType } from '../api';

interface NotificationBellProps {
  /** Optional class name for styling */
  className?: string;
}

/** Get icon for notification type */
function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case 'job_completed':
      return <CheckCircle className="h-5 w-5 text-green-500" aria-hidden="true" />;
    case 'job_failed':
      return <XCircle className="h-5 w-5 text-red-500" aria-hidden="true" />;
    case 'job_cancelled':
      return <XCircle className="h-5 w-5 text-gray-500" aria-hidden="true" />;
    case 'job_started':
      return <Clock className="h-5 w-5 text-blue-500" aria-hidden="true" />;
    case 'job_progress':
      return <Clock className="h-5 w-5 text-blue-400" aria-hidden="true" />;
    case 'job_retrying':
      return <RefreshCw className="h-5 w-5 text-yellow-500" aria-hidden="true" />;
    case 'system_alert':
      return <AlertTriangle className="h-5 w-5 text-orange-500" aria-hidden="true" />;
    default:
      return <Info className="h-5 w-5 text-gray-400" aria-hidden="true" />;
  }
}

export function NotificationBell({ className = '' }: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const {
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
  } = useNotifications();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle notification click
  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.read) {
      await markAsRead(notification.notification_id);
    }
  };

  // Handle dismiss
  const handleDismiss = async (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation();
    await dismiss(notificationId);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Bell Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Bell className="h-5 w-5" aria-hidden="true" />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
          role="menu"
          aria-orientation="vertical"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={markAllAsRead}
                  className="text-xs text-primary-600 hover:text-primary-800"
                  title="Mark all as read"
                >
                  Mark all read
                </button>
              )}
              <button
                type="button"
                onClick={refresh}
                disabled={isLoading}
                className="p-1 text-gray-400 hover:text-gray-600 rounded disabled:opacity-50"
                title="Refresh"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="px-4 py-3 bg-red-50 border-b border-red-200">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <Bell className="h-8 w-8 mx-auto mb-2 text-gray-300" aria-hidden="true" />
                <p className="text-sm">No notifications</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100" role="list">
                {notifications.map((notification) => (
                  <li
                    key={notification.notification_id}
                    className={`relative px-4 py-3 hover:bg-gray-50 cursor-pointer ${
                      !notification.read ? 'bg-primary-50' : ''
                    }`}
                    onClick={() => handleNotificationClick(notification)}
                    role="menuitem"
                  >
                    <div className="flex gap-3">
                      {/* Icon */}
                      <div className="flex-shrink-0">
                        {getNotificationIcon(notification.notification_type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${!notification.read ? 'font-semibold' : ''} text-gray-900 truncate`}>
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="mt-1 text-xs text-gray-400">
                          {formatDistanceToNow(notification.created_at)}
                        </p>
                      </div>

                      {/* Dismiss Button */}
                      <button
                        type="button"
                        onClick={(e) => handleDismiss(e, notification.notification_id)}
                        className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 rounded"
                        title="Dismiss"
                      >
                        <X className="h-4 w-4" aria-hidden="true" />
                      </button>
                    </div>

                    {/* Unread Indicator */}
                    {!notification.read && (
                      <span className="absolute left-2 top-1/2 -translate-y-1/2 w-2 h-2 bg-primary-500 rounded-full" />
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {totalCount} notification{totalCount !== 1 ? 's' : ''}
                </span>
                <button
                  type="button"
                  onClick={clearAll}
                  className="text-xs text-red-600 hover:text-red-800"
                >
                  Clear all
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
