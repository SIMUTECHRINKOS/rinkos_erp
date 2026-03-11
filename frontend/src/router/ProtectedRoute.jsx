import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  const session = useAuthStore((s) => s.session)

  if (!token || !session) {
    return <Navigate to="/login" replace />
  }
  return children
}
