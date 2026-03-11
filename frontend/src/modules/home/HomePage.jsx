import { useNavigate } from 'react-router-dom'
import { Button, Tag, Typography, Avatar } from 'antd'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../store/authStore'
import './HomePage.css'

const { Title, Text } = Typography

// Mapa de módulos a etiqueta visible
const MODULE_LABELS = {
  accounting: 'Contabilidad',
  ar: 'Cuentas por Cobrar',
  ap: 'Cuentas por Pagar',
  inventory: 'Inventario',
  purchasing: 'Compras',
  sales: 'Ventas',
  hr: 'RRHH',
  production: 'Producción',
  service: 'Servicio Técnico',
  crm: 'CRM',
  tenants: 'Administración',
  auth: 'Usuarios',
}

export default function HomePage() {
  const navigate = useNavigate()
  const { session, logout } = useAuthStore()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  if (!session) {
    navigate('/login')
    return null
  }

  return (
    <div className="home-root">
      {/* ── Navbar ── */}
      <header className="home-navbar">
        <div className="home-navbar-brand">
          <img src="/brand/LOGO_RINKOS-04.svg" alt="RINKOS ERP" className="home-logo" />
        </div>
        <div className="home-navbar-actions">
          <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#681db7' }} />
          <Text className="home-username">{session.full_name}</Text>
          {session.is_superuser && (
            <Tag color="gold" style={{ marginLeft: 4 }}>SuperUsuario</Tag>
          )}
          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            className="home-logout-btn"
          >
            Salir
          </Button>
        </div>
      </header>

      {/* ── Contenido ── */}
      <main className="home-main">
        <div className="home-welcome">
          <Title level={3} style={{ color: '#1c0a3f', marginBottom: 4 }}>
            Bienvenido, {session.full_name.split(' ')[0]}
          </Title>
          <Text type="secondary">
            Módulos disponibles según tu licencia:
          </Text>
        </div>

        <div className="home-modules-grid">
          {session.modules.map((mod) => (
            <div key={mod} className="home-module-card">
              <div className="home-module-icon">
                {/* Placeholder — se reemplazará con ícono real por módulo */}
                <span className="home-module-initial">
                  {(MODULE_LABELS[mod] || mod)[0].toUpperCase()}
                </span>
              </div>
              <span className="home-module-name">
                {MODULE_LABELS[mod] || mod}
              </span>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
