import api from './client'

export const startIBKRSync = () => api.post('/syncs/ibkr/start/')
export const fetchSyncJobs = (params = {}) => api.get('/syncs/jobs/', { params })
export const fetchIBKRConfigStatus = () => api.get('/syncs/ibkr/config-debug/')
