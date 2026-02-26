import React, { Suspense } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import { ProtectedRoute, AnonymousRoute } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'

// Lazy-loaded page components (code splitting)
const LandingHome = React.lazy(() => import('./pages/LandingHome'))
const ProfessionalServices = React.lazy(() => import('./pages/industries/ProfessionalServices'))
const Dental = React.lazy(() => import('./pages/industries/Dental'))
const Ecommerce = React.lazy(() => import('./pages/industries/Ecommerce'))
const B2BPlatforms = React.lazy(() => import('./pages/industries/B2BPlatforms'))
const Login = React.lazy(() => import('./pages/Login'))
const Signup = React.lazy(() => import('./pages/Signup'))
const Quiz = React.lazy(() => import('./pages/Quiz'))
const Checkout = React.lazy(() => import('./pages/Checkout'))
const CheckoutSuccess = React.lazy(() => import('./pages/CheckoutSuccess'))
const Dashboard = React.lazy(() => import('./pages/Dashboard'))
const NewAuditV2 = React.lazy(() => import('./pages/NewAuditV2'))
const Intake = React.lazy(() => import('./pages/Intake'))
const AuditProgress = React.lazy(() => import('./pages/AuditProgress'))
const Report = React.lazy(() => import('./pages/Report'))
const ReportViewer = React.lazy(() => import('./pages/ReportViewer'))
const ReportProgress = React.lazy(() => import('./pages/ReportProgress'))
const VoiceQuizInterview = React.lazy(() => import('./pages/VoiceQuizInterview'))
const AdaptiveQuiz = React.lazy(() => import('./pages/AdaptiveQuiz'))
const PreviewReport = React.lazy(() => import('./pages/PreviewReport'))
const Workshop = React.lazy(() => import('./pages/Workshop'))
const Terms = React.lazy(() => import('./pages/Terms'))
const Privacy = React.lazy(() => import('./pages/Privacy'))
const KnowledgeBase = React.lazy(() => import('./pages/admin/KnowledgeBase'))
const VendorAdmin = React.lazy(() => import('./pages/admin/VendorAdmin'))
const AdminDashboard = React.lazy(() => import('./pages/admin/AdminDashboard'))
const InsightsAdmin = React.lazy(() => import('./pages/admin/InsightsAdmin'))
const InsightExtractor = React.lazy(() => import('./pages/admin/InsightExtractor'))

// Loading fallback for code-split pages
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
)

// 404 page
const NotFound = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
      <p className="text-gray-600 mb-4">Page not found</p>
      <Link to="/" className="text-primary-600 hover:text-primary-700">
        Go home
      </Link>
    </div>
  </div>
)

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
      <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingHome />} />
      <Route path="/professional-services" element={<ProfessionalServices />} />
      <Route path="/dental" element={<Dental />} />
      <Route path="/ecommerce" element={<Ecommerce />} />
      <Route path="/b2b-platforms" element={<B2BPlatforms />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Legal pages */}
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />

      {/* Free quiz and checkout - anonymous users only */}
      <Route path="/quiz" element={
        <AnonymousRoute>
          <Quiz />
        </AnonymousRoute>
      } />
      <Route path="/quiz/interview" element={
        <AnonymousRoute>
          <VoiceQuizInterview />
        </AnonymousRoute>
      } />
      <Route path="/quiz/adaptive" element={
        <AnonymousRoute>
          <AdaptiveQuiz />
        </AnonymousRoute>
      } />
      <Route path="/quiz/preview" element={
        <AnonymousRoute>
          <PreviewReport />
        </AnonymousRoute>
      } />
      <Route path="/checkout" element={
        <AnonymousRoute>
          <Checkout />
        </AnonymousRoute>
      } />
      <Route path="/checkout/success" element={<CheckoutSuccess />} />

      {/* Post-payment workshop (90-min deep interview) */}
      <Route path="/interview" element={<Workshop />} />
      <Route path="/workshop" element={<Workshop />} />

      {/* Public report viewer (for quiz-based reports) */}
      <Route path="/report/:id" element={<ReportViewer />} />
      <Route path="/report/:id/progress" element={<ReportProgress />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/new-audit"
        element={
          <ProtectedRoute>
            <NewAuditV2 />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit/:id/intake"
        element={
          <ProtectedRoute>
            <Intake />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit/:id/progress"
        element={
          <ProtectedRoute>
            <AuditProgress />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit/:id/report"
        element={
          <ProtectedRoute>
            <Report />
          </ProtectedRoute>
        }
      />

      {/* Admin routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/knowledge"
        element={
          <ProtectedRoute>
            <KnowledgeBase />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/vendors"
        element={
          <ProtectedRoute>
            <VendorAdmin />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/insights"
        element={
          <ProtectedRoute>
            <InsightsAdmin />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/insights/extract"
        element={
          <ProtectedRoute>
            <InsightExtractor />
          </ProtectedRoute>
        }
      />

      {/* 404 */}
      <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}

export default App
