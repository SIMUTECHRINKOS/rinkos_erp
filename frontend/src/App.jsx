import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import esES from 'antd/locale/es_ES'
import LoginPage from './modules/auth/LoginPage'
import HomePage from './modules/home/HomePage'
import ProtectedRoute from './router/ProtectedRoute'

const rinkosTheme = {
  token: {
    colorPrimary: '#681db7',
    colorLink: '#681db7',
    borderRadius: 8,
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  },
}

export default function App() {
  return (
    <ConfigProvider theme={rinkosTheme} locale={esES}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/home"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          {/* Redirige raíz al home (o login si no está autenticado) */}
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="*" element={<Navigate to="/home" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}
