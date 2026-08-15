/**
 * Intervention API - API calls for intervention log management
 */
import request from '@/utils/request'

/**
 * Get user's intervention logs
 * @param {Object} params - Query parameters
 * @param {string} params.status - Optional filter by status (pending, completed, dismissed)
 * @param {number} params.limit - Maximum number of records (default: 50)
 * @returns {Promise}
 */
export function getInterventions(params = {}) {
  return request({
    url: '/intervention/user',
    method: 'get',
    params: {
      limit: params.limit || 50,
      ...params.status && { status: params.status }
    }
  })
}

/**
 * Update intervention execution status
 * @param {Object} data - Request data
 * @param {number} data.interventionId - Intervention log ID
 * @param {string} data.status - New status (pending, completed, dismissed)
 * @returns {Promise}
 */
export function updateInterventionStatus(data) {
  return request({
    url: '/intervention/status',
    method: 'put',
    data: data
  })
}

/**
 * Add user feedback to intervention log
 * @param {Object} data - Request data
 * @param {number} data.interventionId - Intervention log ID
 * @param {string} data.feedback - User's feedback
 * @param {boolean} data.executed - Whether the user executed the intervention
 * @param {string} data.effectiveness - Effectiveness rating (very_good, good, moderate, poor, very_poor)
 * @returns {Promise}
 */
export function addInterventionFeedback(data) {
  return request({
    url: '/intervention/feedback',
    method: 'post',
    data: data
  })
}

/**
 * Delete an intervention log
 * @param {number} interventionId - Intervention log ID
 * @returns {Promise}
 */
export function deleteIntervention(interventionId) {
  return request({
    url: `/intervention/${interventionId}`,
    method: 'delete'
  })
}
