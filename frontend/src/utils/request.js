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
    config.headers['Content-Type'] = 'application/json;charset=utf-8';
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