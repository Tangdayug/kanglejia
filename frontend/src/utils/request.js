import { ElMessage } from 'element-plus'
import router from '../router'
import axios from "axios";

const request = axios.create({
    baseURL: import.meta.env.VITE_BASE_URL,
    timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(config => {
    const user = JSON.parse(localStorage.getItem('student-user'))
    // 只有未显式设置 Content-Type 且非文件上传时，才默认使用 JSON
    const isFormData = config.data instanceof FormData
    if (!config.headers['Content-Type'] && !isFormData) {
        config.headers['Content-Type'] = 'application/json;charset=utf-8';
    }
    // FormData 必须由浏览器自动设置 Content-Type（含 boundary），否则后端无法解析文件
    if (isFormData) {
        delete config.headers['Content-Type']
    }
    if (user){
        config.headers.Authorization = `Bearer ${user.token}`;
    }

    return config
}, error => {
    return Promise.reject(error)
});

// 响应拦截器
request.interceptors.response.use(
    response => {
        let res = response.data;
        // 处理文件响应
        if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
            return res
        }
        // 兼容字符串数据
        if (typeof res === 'string') {
            res = res ? JSON.parse(res) : res
        }
        // 处理权限验证失败
        if (res.code === '401') {
            ElMessage.error(res.msg);
            router.push("/login")
        }
        return res;
    },
    error => {
        // 处理 HTTP 401 错误
        if (error.response && error.response.status === 401) {
            ElMessage.error('登录已过期，请重新登录');
            localStorage.removeItem('student-user');
            router.push("/login");
        }
        return Promise.reject(error)
    }
)


export default request