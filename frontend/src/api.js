import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: BASE_URL })

export const getSummary = () => api.get('/api/summary').then(r => r.data)
export const getTopics = () => api.get('/api/topics').then(r => r.data)
export const getFraming = (topic) => api.get('/api/framing', { params: topic ? { topic } : {} }).then(r => r.data)
export const getStories = (minDivergence = 5.0, topic = 'all') =>
  api.get('/api/stories', { params: { min_divergence: minDivergence, topic } }).then(r => r.data)
export const getOutlets = () => api.get('/api/outlets').then(r => r.data)
export const getOutletArticles = (outletName) =>
  api.get(`/api/outlets/${encodeURIComponent(outletName)}/articles`).then(r => r.data)
