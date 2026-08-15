import {createRouter, createWebHistory} from 'vue-router'
import tts from '@/utils/tts'
import HealthEducation from '@/views/manager/HealthEducation.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
// ... 其他 import 保持不变
    routes: [
        {
            path: '/',
            name: 'Manager',
            component: () => import('@/views/Manager.vue'),
            redirect: '/home',
            children: [
                { path: 'home', name: 'Home', component: () => import('@/views/manager/Home.vue') },
                { path: 'health-record/info', name: 'HealthRecordInfo', component: () => import('@/views/manager/health/Info.vue') },
                { path: 'health-record/history', name: 'HealthRecordHistory', component: () => import('@/views/manager/health/History.vue') },
                { path: 'health-record/intervention', name: 'HealthRecordIntervention', component: () => import('@/views/manager/health/Intervention.vue') },
                { path: 'chat-ai', name: 'ChatAI', component: () => import('@/views/manager/ChatAI.vue') },
                { path: 'health-education', name: 'HealthEducation', component: HealthEducation },
            ]
        },
        // 🌟 将 HealthTest / ModeSelect 移到这里，与 Manager 平级，这样它们就不会有侧边栏了
        {
            path: '/test',
            name: 'HealthTest',
            component: () => import('@/views/manager/HealthTest.vue')
        },
        {
            path: '/mode-select',
            name: 'ModeSelect',
            component: () => import('@/views/ModeSelect.vue')
        },
        { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
        { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') }
    ]
// ...
})

// 全局路由守卫：页面切换时停止语音播放
router.beforeEach((to, from, next) => {
  // 停止当前正在播放的语音
  tts.stop()

  // 检查登录状态
  const user = localStorage.getItem('student-user')
  const isLoggedIn = !!user

  // 需要登录的页面列表
  const protectedRoutes = ['/home', '/chat-ai', '/health-record', '/test', '/health-education']
  const isProtectedRoute = protectedRoutes.some(route => to.path.startsWith(route))

  // 如果访问需要登录的页面但未登录，重定向到登录页
  if (isProtectedRoute && !isLoggedIn) {
    next('/login')
    return
  }

  // 如果已登录且访问登录/注册页，重定向到首页
  if (isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/home')
    return
  }

  next()
})

export default router
