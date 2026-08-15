/**
 * Care API - API calls for daily care functionality
 */
import request from '@/utils/request'

/**
 * Get daily care message
 * LLM-generated personalized care message based on intervention logs and conversation history
 * @returns {Promise}
 */
export function getDailyCareMessage() {
  return request({
    url: '/care/daily-message',
    method: 'get'
  })
}

/**
 * Submit user feedback for intervention
 * @param {Object} data - Feedback data
 * @param {number} data.interventionId - Intervention log ID
 * @param {string} data.feedback - User's feedback content
 * @param {number} data.sessionId - Chat session ID
 * @returns {Promise}
 */
export function submitFeedback(data) {
  return request({
    url: '/care/submit-feedback',
    method: 'post',
    data: data
  })
}
