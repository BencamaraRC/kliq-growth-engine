import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-ivory">
      <Sidebar />
      <main className="ml-60 p-8">
        <Outlet />
      </main>
    </div>
  )
}
