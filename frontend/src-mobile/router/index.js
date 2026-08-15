import { createRouter, createWebHistory } from 'vue-router'
import tts from '@shared/utils/tts'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') },
    { path: '/mode-select', name: 'ModeSelect', component: () => import('@/views/ModeSelect.vue') },
    { path: '/home', name: 'Home', component: () => import('@/views/Home.vue') },
    { path: '/test', name: 'HealthTest', component: () => import('@/views/HealthTest.vue') },
    { path: '/chat-ai', name: 'ChatAI', component: () => import('@/views/ChatAI.vue') },
    { path: '/health-info', name: 'HealthInfo', component: () => import('@/views/HealthInfo.vue') },
    { path: '/health-history', name: 'HealthHistory', component: () => import('@/views/HealthHistory.vue') },
    { path: '/intervention', name: 'Intervention', component: () => import('@/views/Intervention.vue') },
    { path: '/health-education', name: 'HealthEducation', component: () => import('@/views/HealthEducation.vue') },
    { path: '/profile', name: 'Profile', component: () => import('@/views/Profile.vue') },
    { path: '/', redirect: '/home' }
  ]
})

router.beforeEach((to, from, next) => {
  tts.stop()

  const user = localStorage.getItem('student-user')
  const isLoggedIn = !!user

  const protectedRoutes = ['/home', '/test', '/chat-ai', '/health-info', '/health-history', '/intervention', '/health-education', '/profile']
  const isProtectedRoute = protectedRoutes.some(route => to.path.startsWith(route))

  if (isProtectedRoute && !isLoggedIn) {
    next('/login')
    return
  }

  if (isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/home')
    return
  }

  next()
})

export default router
