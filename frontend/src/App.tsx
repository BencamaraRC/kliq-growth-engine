import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthContext, useAuthState } from '@/hooks/useAuth'
import { AppLayout } from '@/components/layout/AppLayout'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { SignupPage } from '@/pages/SignupPage'
import { ClaimPage } from '@/pages/ClaimPage'
import { OnboardingPage } from '@/pages/OnboardingPage'
import { LandingPage } from '@/pages/LandingPage'
import { BlogListPage } from '@/pages/BlogListPage'
import { BlogDetailPage } from '@/pages/BlogDetailPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { PipelinePage } from '@/pages/PipelinePage'
import { ProfilesPage } from '@/pages/ProfilesPage'
import { ProfileDetailPage } from '@/pages/ProfileDetailPage'
import { CampaignsPage } from '@/pages/CampaignsPage'
import { LinkedInOutreachPage } from '@/pages/LinkedInOutreachPage'
import { StorePreviewPage } from '@/pages/StorePreviewPage'
import { OperationsPage } from '@/pages/OperationsPage'
import { CmsAdminPage } from '@/pages/CmsAdminPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  const auth = useAuthState()

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={auth}>
        <BrowserRouter>
          <Routes>
            {/* Public routes with PublicLayout (header + footer) */}
            <Route element={<PublicLayout />}>
              <Route path="/landing" element={<LandingPage />} />
              <Route path="/blog" element={<BlogListPage />} />
              <Route path="/blog/:id" element={<BlogDetailPage />} />
            </Route>

            {/* Public routes without layout */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/claim" element={<ClaimPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />

            {/* Protected routes with AppLayout (sidebar) */}
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="pipeline" element={<PipelinePage />} />
              <Route path="profiles" element={<ProfilesPage />} />
              <Route path="profile" element={<ProfileDetailPage />} />
              <Route path="profile/:id" element={<ProfileDetailPage />} />
              <Route path="campaigns" element={<CampaignsPage />} />
              <Route path="linkedin" element={<LinkedInOutreachPage />} />
              <Route path="store-preview" element={<StorePreviewPage />} />
              <Route path="operations" element={<OperationsPage />} />
              <Route path="cms-admin" element={<CmsAdminPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  )
}
