import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Adjunta el token JWT a cada petición autenticada
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('rinkos_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirige al login si el token expira
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('rinkos_token')
      localStorage.removeItem('rinkos_session')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
