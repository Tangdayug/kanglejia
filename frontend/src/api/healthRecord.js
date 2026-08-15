import request from '@/utils/request'

/**
 * Save or update health record
 * @param {Object} data - Health record data
 * @param {number} data.record_id - Record ID (null for new record)
 * @param {Object} data.data - Form data with 7 sections
 * @param {boolean} data.is_draft - Whether this is a draft (true) or completed (false)
 * @returns {Promise}
 */
export function saveHealthRecord(data) {
  return request({
    url: '/health-record/save',
    method: 'post',
    data
  })
}

/**
 * Get the latest draft for current user
 * @returns {Promise}
 */
export function getDraft() {
  return request({
    url: '/health-record/draft',
    method: 'get'
  })
}

/**
 * Get all health records for current user
 * @returns {Promise}
 */
export function getHealthRecordList() {
  return request({
    url: '/health-record/list',
    method: 'get'
  })
}

/**
 * Get a specific health record by ID
 * @param {number} id - Record ID
 * @returns {Promise}
 */
export function getHealthRecordById(id) {
  return request({
    url: `/health-record/${id}`,
    method: 'get'
  })
}

/**
 * Submit/completed a draft health record
 * @param {number} id - Record ID
 * @returns {Promise}
 */
export function submitHealthRecord(id) {
  return request({
    url: `/health-record/${id}/submit`,
    method: 'post'
  })
}

/**
 * 上传图片进行 OCR 识别
 * @param {File} file - 图片文件
 * @returns {Promise}
 */
export function ocrHealthRecordImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/health-record/ocr',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
