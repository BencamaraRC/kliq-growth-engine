import { NavLink } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import {
  ChartBarIcon,
  UserGroupIcon,
  UserIcon,
  ChartBarSquareIcon,
  EnvelopeIcon,
  BuildingStorefrontIcon,
  Cog6ToothIcon,
  CommandLineIcon,
  ShareIcon,
} from '@heroicons/react/24/outline'

const navItems = [
  { to: '/', label: 'Dashboard', icon: ChartBarIcon },
  { to: '/profiles', label: 'Profiles', icon: UserGroupIcon },
  { to: '/profile', label: 'Profile Detail', icon: UserIcon },
  { to: '/pipeline', label: 'Pipeline', icon: ChartBarSquareIcon },
  { to: '/campaigns', label: 'Campaigns', icon: EnvelopeIcon },
  { to: '/store-preview', label: 'Store Preview', icon: BuildingStorefrontIcon },
  { to: '/cms-admin', label: 'CMS Admin', icon: Cog6ToothIcon },
  { to: '/operations', label: 'Operations', icon: CommandLineIcon },
  { to: '/linkedin', label: 'LinkedIn Outreach', icon: ShareIcon },
]

export function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="fixed inset-y-0 left-0 w-60 bg-kliq-green flex flex-col">
      <div className="px-6 pt-5 pb-3">
        <h1 className="text-lg font-bold text-white tracking-tight">KLIQ Growth Engine</h1>
      </div>

      {user && (
        <div className="px-6 pb-1">
          <p className="text-xs text-white/70">
            Logged in as <span className="text-white font-medium">{user.name}</span>
          </p>
        </div>
      )}

      <div className="mx-6 border-t border-white/10 my-3" />

      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-white/80 hover:bg-white/8 hover:text-white'
              }`
            }
          >
            <Icon className="h-5 w-5 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mx-6 border-t border-white/10 my-3" />

      <div className="px-3 pb-4">
        <button
          onClick={logout}
          className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-white/70 hover:bg-white/8 hover:text-white transition-colors"
        >
          Logout
        </button>
        <p className="px-3 mt-2 text-xs text-white/40">v0.2.0 | Growth Engine</p>
      </div>
    </aside>
  )
}
