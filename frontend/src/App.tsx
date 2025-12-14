import { Routes, Route, Link } from 'react-router-dom'
import { ProtectedRoute } from './contexts/AuthContext'
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
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Free quiz and checkout */}
      <Route path="/quiz" element={<Quiz />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/checkout/success" element={<CheckoutSuccess />} />

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

      {/* Admin routes - to be implemented */}
      {/* <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} /> */}

      {/* 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
