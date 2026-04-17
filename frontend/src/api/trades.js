import api from './client'

export const fetchTradeGroups = (params = {}) => api.get('/trades/groups/', { params })
export const fetchTradeGroupDetail = (id) => api.get(`/trades/groups/${id}/`)
export const fetchTradeDashboard = (params = {}) => api.get('/trades/groups/dashboard/', { params })
export const fetchTradeMonthlyReport = (params = {}) => api.get('/trades/groups/monthly-report/', { params })
export const fetchTradeFilterOptions = () => api.get('/trades/groups/filter-options/')
export const fetchClosedTradeAnalytics = (params = {}) => api.get('/trades/groups/closed-analytics/', { params })
export const fetchRawExecutions = (params = {}) => api.get('/trades/raw-executions/', { params })
