import { create } from 'zustand'

const SESSION_KEY = 'rinkos_session'
const TOKEN_KEY = 'rinkos_token'

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = create((set) => ({
  token: localStorage.getItem(TOKEN_KEY) || null,
  session: loadSession(), // { user_id, full_name, is_superuser, company_id, modules }

  setAuth: (token, session) => {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    set({ token, session })
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(SESSION_KEY)
    set({ token: null, session: null })
  },

  isAuthenticated: () => {
    const state = useAuthStore.getState()
    return !!state.token && !!state.session
  },
}))
