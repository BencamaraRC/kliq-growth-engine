import { Link, Outlet } from 'react-router-dom'

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-ivory flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/landing" className="text-xl font-bold text-kliq-green tracking-tight">
            KLIQ
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              to="/blog"
              className="text-sm font-medium text-gray-600 hover:text-kliq-green transition-colors"
            >
              Blog
            </Link>
            <Link
              to="/login"
              className="text-sm font-medium text-gray-600 hover:text-kliq-green transition-colors"
            >
              Login
            </Link>
            <Link
              to="/signup"
              className="text-sm font-semibold text-white bg-kliq-green px-4 py-2 rounded-lg hover:bg-kliq-green-hover transition-colors"
            >
              Sign Up
            </Link>
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-kliq-green text-white">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-lg font-bold mb-3">KLIQ</h3>
              <p className="text-sm text-gray-300">
                The all-in-one platform for fitness and wellness creators to build, launch, and grow
                their coaching business.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-3 uppercase tracking-wider text-gray-300">
                Product
              </h4>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>
                  <Link to="/landing" className="hover:text-white transition-colors">
                    Features
                  </Link>
                </li>
                <li>
                  <Link to="/blog" className="hover:text-white transition-colors">
                    Blog
                  </Link>
                </li>
                <li>
                  <Link to="/signup" className="hover:text-white transition-colors">
                    Get Started
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-3 uppercase tracking-wider text-gray-300">
                Account
              </h4>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>
                  <Link to="/login" className="hover:text-white transition-colors">
                    Login
                  </Link>
                </li>
                <li>
                  <Link to="/signup" className="hover:text-white transition-colors">
                    Sign Up
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-white/20 text-center text-sm text-gray-400">
            &copy; {new Date().getFullYear()} KLIQ. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
