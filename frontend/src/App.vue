<template>
  <div id="app">
    <router-view />

    <!-- Daily Care Popup -->
    <CareBubble
      :visible="careVisible"
      :care-message="careMessage"
      @chat="handleCareChat"
      @later="handleCareLater"
    />

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CareBubble from '@/components/CareBubble.vue'
import { useDailyCare } from '@/composables/useDailyCare'

const router = useRouter()

// Daily care hook
const {
  visible: careVisible,
  careMessage,
  handleChat: handleCareChat,
  handleLater: handleCareLater,
  showCare
} = useDailyCare()

// 检查登录状态
function checkLoginStatus() {
  const user = localStorage.getItem('student-user')
  return !!user
}

// 页面加载时检查登录状态并导航
onMounted(() => {
  const isLoggedIn = checkLoginStatus()

  // 如果未登录且不在登录/注册/模式选择页面，跳转到登录页
  if (!isLoggedIn) {
    const currentPath = router.currentRoute.value.path
    if (currentPath !== '/login' &&
        currentPath !== '/register' &&
        currentPath !== '/home') {
      router.push('/login')
    }
  }
})

// 监听 localStorage 变化（多标签页同步）
window.addEventListener('storage', (e) => {
  if (e.key === 'student-user') {
    const isLoggedIn = !!e.newValue
    // 登录状态变化时重新导航
    if (!isLoggedIn) {
      // 用户被清除（退出登录），跳转到登录页
      router.push('/login')
    }
  }
})

// 暴露显示关怀气泡的方法（供模式选择页面调用）
window.showDailyCare = showCare
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
