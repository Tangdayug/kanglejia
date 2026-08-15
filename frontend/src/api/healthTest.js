import request from '@/utils/request'

/**
 * Submit health test
 * @param {Object} data - Health test answers
 * @returns {Promise}
 */
export function submitHealthTest(data) {
  return request({
    url: '/health-test/submit',
    method: 'post',
    data
  })
}

/**
 * Get all health tests for current user
 * @returns {Promise}
 */
export function getHealthTestList() {
  return request({
    url: '/health-test/list',
    method: 'get'
  })
}

/**
 * Get a specific health test by ID
 * @param {number} id - Test ID
 * @returns {Promise}
 */
export function getHealthTestById(id) {
  return request({
    url: `/health-test/${id}`,
    method: 'get'
  })
}

/**
 * Get personalized recommendations (without saving test)
 * @param {Object} data - Test answers for recommendation
 * @returns {Promise}
 */
export function getRecommendations(data) {
  return request({
    url: '/health-test/recommendation',
    method: 'post',
    data
  })
}
