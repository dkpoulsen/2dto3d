import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  ListVideo,
  Download,
  Activity,
  Video,
  GitCompare,
} from 'lucide-react';
// import { NotificationBell } from './NotificationBell'; // Temporarily disabled
const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload' },
  { to: '/jobs', icon: ListVideo, label: 'Jobs' },
  { to: '/downloads', icon: Download, label: 'Downloads' },
  { to: '/compare', icon: GitCompare, label: 'Compare' },
  { to: '/system', icon: Activity, label: 'System' },
] as const;

export function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Video className="h-8 w-8 text-primary-600" aria-hidden="true" />
              <h1 className="text-xl font-bold text-gray-900">2Dto3D Converter</h1>
            </div>
            <div className="flex items-center gap-2">
              {/* <NotificationBell /> */}
              <span className="text-sm text-gray-500">Web Dashboard</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-4rem)] sticky top-16">
          <nav className="p-4 space-y-1" aria-label="Main navigation">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`
                }
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="flex-1 p-6" role="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
