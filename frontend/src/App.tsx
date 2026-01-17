import { Routes, Route, Link } from 'react-router-dom'
import { ProtectedRoute, AnonymousRoute } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Quiz from './pages/Quiz'
import Checkout from './pages/Checkout'
import CheckoutSuccess from './pages/CheckoutSuccess'
import Dashboard from './pages/Dashboard'
import NewAudit from './pages/NewAudit'
import NewAuditV2 from './pages/NewAuditV2'
import Intake from './pages/Intake'
import AuditProgress from './pages/AuditProgress'
import Report from './pages/Report'
import ReportViewer from './pages/ReportViewer'
import ReportProgress from './pages/ReportProgress'
import Interview from './pages/Interview'
import VoiceQuizInterview from './pages/VoiceQuizInterview'
import AdaptiveQuiz from './pages/AdaptiveQuiz'
import PreviewReport from './pages/PreviewReport'
import ReportPreview from './pages/ReportPreview'
import Workshop from './pages/Workshop'
import Terms from './pages/Terms'
import Privacy from './pages/Privacy'
import KnowledgeBase from './pages/admin/KnowledgeBase'
import VendorAdmin from './pages/admin/VendorAdmin'
import AdminDashboard from './pages/admin/AdminDashboard'
import InsightsAdmin from './pages/admin/InsightsAdmin'
import InsightExtractor from './pages/admin/InsightExtractor'

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
      <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Legal pages */}
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />

      {/* Visual Preview - Mock data only */}
      <Route path="/preview/report" element={<ReportPreview />} />

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

      {/* Legacy interview route */}
      <Route path="/interview-legacy" element={<Interview />} />

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
        path="/new-audit-legacy"
        element={
          <ProtectedRoute>
            <NewAudit />
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
    </ErrorBoundary>
  )
}

export default App
