import api from './client'

export const fetchDailyReviews = (params = {}) => api.get('/journal/daily-reviews/', { params })
export const createDailyReview = (payload) => api.post('/journal/daily-reviews/', payload)
export const updateDailyReview = (id, payload) => api.patch(`/journal/daily-reviews/${id}/`, payload)
export const deleteDailyReview = (id) => api.delete(`/journal/daily-reviews/${id}/`)
export const fetchDailyReviewTradeOptions = (date) => api.get('/journal/daily-reviews/trade-options/', { params: { date } })

export const uploadDailyReviewImages = (files) => {
  const form = new FormData()
  Array.from(files).forEach((file) => form.append('images', file))
  return api.post('/journal/daily-review-image-upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const fetchTradeJournalByTradeGroup = (tradeGroupId) => api.get('/journal/trade-journals/', { params: { trade_group: tradeGroupId } })
export const saveTradeJournal = (payload) => api.post('/journal/trade-journals/', payload)
