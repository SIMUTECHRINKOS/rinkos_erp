import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Select, Alert, Typography } from 'antd'
import { MailOutlined, LockOutlined, BankOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'
import './LoginPage.css'

const { Text } = Typography

// Imágenes de fondo disponibles (en /public/images/)
const BG_IMAGES = [
  'cabaniabosque.webp',
  'cascada.webp',
  'fondo.webp',
  'flor.webp',
  'conchas.webp',
  'cielo.webp',
  'carretera.webp',
  'cieloestrellas.webp',
  'globonoche.webp',
  'gota.webp',
  'invierno.webp',
  'otonio.webp',
  'palmeras.webp',
  'montaña.webp',
  'jardinjapones.webp',
]

function pickRandomImage() {
  return BG_IMAGES[Math.floor(Math.random() * BG_IMAGES.length)]
}

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [form] = Form.useForm()

  const [bgImage] = useState(() => pickRandomImage())
  const [step, setStep] = useState('credentials') // 'credentials' | 'company'
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [credentials, setCredentials] = useState(null) // { email, password }

  // ─── Paso 1: Validar credenciales y obtener compañías ─────────────────────
  async function handleVerificar(values) {
    setLoading(true)
    setError(null)
    try {
      const res = await authApi.companiasDisponibles(values.email, values.password)
      const lista = res.data
      if (!lista || lista.length === 0) {
        setError('No tienes compañías disponibles. Contacta al administrador.')
        return
      }
      setCredentials({ email: values.email, password: values.password })
      setCompanies(lista)
      setStep('company')
      // Pre-seleccionar si hay solo una
      if (lista.length === 1) {
        form.setFieldValue('company_id', lista[0].id)
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Credenciales incorrectas.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  // ─── Paso 2: Login con compañía seleccionada ─────────────────────────────
  async function handleIngresar(values) {
    setLoading(true)
    setError(null)
    try {
      const res = await authApi.login(
        credentials.email,
        credentials.password,
        values.company_id
      )
      const data = res.data
      setAuth(data.access_token, {
        user_id: data.user_id,
        full_name: data.full_name,
        is_superuser: data.is_superuser,
        company_id: data.company_id,
        modules: data.modules,
      })
      navigate('/home')
    } catch (err) {
      const msg = err.response?.data?.detail || 'No se pudo iniciar sesión.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function handleOtraCuenta() {
    setStep('credentials')
    setCompanies([])
    setCredentials(null)
    setError(null)
    form.resetFields()
  }

  return (
    <div
      className="login-root"
      style={{ backgroundImage: `url('/images/${bgImage}')` }}
    >
      {/* Overlay oscuro sobre la imagen */}
      <div className="login-overlay" />

      {/* Tarjeta de login */}
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <img src="/brand/LOGO_RINKOS-01.svg" alt="RINKOS ERP" />
        </div>

        <h2 className="login-title">
          {step === 'credentials' ? 'Iniciar sesión' : 'Selecciona tu empresa'}
        </h2>
        {step === 'company' && (
          <p className="login-subtitle">
            Tu cuenta tiene acceso a múltiples compañías
          </p>
        )}

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={step === 'credentials' ? handleVerificar : handleIngresar}
          requiredMark={false}
        >
          {/* ── Paso 1: Correo + Contraseña ── */}
          {step === 'credentials' && (
            <>
              <Form.Item
                name="email"
                label="Correo electrónico"
                rules={[
                  { required: true, message: 'Ingresa tu correo' },
                  { type: 'email', message: 'Correo no válido' },
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="usuario@empresa.com"
                  size="large"
                  autoComplete="email"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="Contraseña"
                rules={[{ required: true, message: 'Ingresa tu contraseña' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="••••••••"
                  size="large"
                  autoComplete="current-password"
                />
              </Form.Item>

              <Form.Item style={{ marginBottom: 8 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  size="large"
                  loading={loading}
                  className="login-btn-primary"
                >
                  Continuar
                </Button>
              </Form.Item>
            </>
          )}

          {/* ── Paso 2: Selector de compañía ── */}
          {step === 'company' && (
            <>
              <Form.Item
                name="company_id"
                label="Compañía"
                rules={[{ required: true, message: 'Selecciona una compañía' }]}
              >
                <Select
                  placeholder="Selecciona tu empresa"
                  size="large"
                  suffixIcon={<BankOutlined />}
                  options={companies.map((c) => ({
                    value: c.id,
                    label: c.name,
                  }))}
                />
              </Form.Item>

              <Form.Item style={{ marginBottom: 8 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  size="large"
                  loading={loading}
                  className="login-btn-primary"
                >
                  Ingresar al portal
                </Button>
              </Form.Item>
            </>
          )}
        </Form>

        {/* Usar otra cuenta */}
        {step === 'company' && (
          <div style={{ textAlign: 'center', marginTop: 8 }}>
            <Button
              type="link"
              icon={<ArrowLeftOutlined />}
              onClick={handleOtraCuenta}
              style={{ color: '#681db7' }}
            >
              Usar otra cuenta
            </Button>
          </div>
        )}

        <div className="login-footer">
          © {new Date().getFullYear()} RINKOS ERP — Todos los derechos reservados
        </div>
      </div>
    </div>
  )
}
