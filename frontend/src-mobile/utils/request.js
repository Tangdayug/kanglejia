import axios from 'axios'
import { message } from 'ant-design-vue'

const request = axios.create({
  baseURL: import.meta.env.VITE_BASE_URL,
  timeout: 30000
})

request.interceptors.request.use(config => {
  const userStr = localStorage.getItem('student-user')
  config.headers['Content-Type'] = 'application/json;charset=utf-8'
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      config.headers.Authorization = `Bearer ${user.token}`
    } catch (e) {}
  }
  return config
}, error => Promise.reject(error))

request.interceptors.response.use(
  response => {
    let res = response.data
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return res
    }
    if (typeof res === 'string') {
      res = res ? JSON.parse(res) : res
    }
    if (res.code === '401') {
      message.error(res.msg)
      localStorage.removeItem('student-user')
      window.location.href = '/login'
    }
    return res
  },
  error => {
    if (error.response && error.response.status === 401) {
      message.error('登录已过期，请重新登录')
      localStorage.removeItem('student-user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default request
