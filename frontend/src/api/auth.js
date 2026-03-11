import client from './client'

export const authApi = {
  /** Valida credenciales y devuelve compañías disponibles */
  companiasDisponibles: (email, password) =>
    client.post('/auth/companias-disponibles', { email, password }),

  /** Login completo — devuelve JWT */
  login: (email, password, company_id) =>
    client.post('/auth/login', { email, password, company_id }),

  /** Datos del usuario autenticado */
  me: () => client.get('/auth/me'),
}
