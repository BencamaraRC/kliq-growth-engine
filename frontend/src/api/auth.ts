import api from './client'

export async function login(username: string, password: string) {
  const { data } = await api.post('/auth/login', { username, password })
  return data as { access_token: string; user: { username: string; name: string } }
}

export async function signup(name: string, email: string, password: string) {
  const { data } = await api.post('/auth/signup', { name, email, password })
  return data as { access_token: string; user: { username: string; name: string } }
}

export async function getMe() {
  const { data } = await api.get('/auth/me')
  return data as { username: string; name: string }
}
