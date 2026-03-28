import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../auth/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';
import Layout from '../components/Layout';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';

/**
 * AppRouter - Main Router Configuration
 *
 * Routes:
 * - /login       → Public login page
 * - /dashboard   → Protected (requires authentication)
 * - /            → Redirects to /dashboard
 *
 * Authentication:
 * - Protected routes use ProtectedRoute component
 * - Checks token in AuthContext/localStorage
 * - Redirects to /login if not authenticated
 *
 * Roles:
 * - owner: Full access
 * - professor: Limited access
 * Both roles can access /dashboard
 */
function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />

          {/* Protected Routes - Require authentication */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Route>

          {/* Catch all - redirect to dashboard or login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default AppRouter;
