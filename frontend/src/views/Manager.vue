<template>
  <div class="saas-app-layout">
    <div class="saas-body">
      <aside class="saas-floating-sidebar">
        <div class="sidebar-brand">
          <img src="@/assets/imgs/logo2.png" alt="Logo" class="sidebar-logo">
          <div class="sidebar-brand-name">康乐家</div>
        </div>

        <el-menu
            class="saas-menu"
            :default-active="$route.path"
        >
          <div class="menu-group-title">我的状态</div>
          <el-menu-item index="/home" @click="$router.push('/home')">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/health-record/history" @click="$router.push('/health-record/history')">
            <el-icon><DataLine /></el-icon>
            <span>趋势</span>
          </el-menu-item>

          <div class="menu-group-title">今日管理</div>
          <el-menu-item index="/health-record/intervention" @click="$router.push('/health-record/intervention')">
            <el-icon><Check /></el-icon>
            <span>今日建议</span>
          </el-menu-item>

          <div class="menu-group-title">专业评估</div>
          <el-menu-item index="/health-record/info" @click="$router.push('/health-record/info')">
            <el-icon><User /></el-icon>
            <span>我的</span>
          </el-menu-item>
          <el-menu-item index="/health-education" @click="$router.push('/health-education')">
            <el-icon><Reading /></el-icon>
            <span>科普</span>
          </el-menu-item>
          
          <div class="spacer"></div>
          
          <el-menu-item index="/login" @click="logout" class="logout-item">
            <el-icon><SwitchButton /></el-icon>
            <span>退出系统</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <main class="saas-main-canvas">
        <div class="canvas-wrapper">
          <router-view v-slot="{ Component }">
            <transition name="page-switch">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
// ---- 逻辑代码部分增加图标导入，其余保持不变 ----
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref, onMounted, watch } from 'vue'
import { 
  House, User, 
  SwitchButton, Reading, DataLine, Check 
} from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'

const $route = useRoute()
const $router = useRouter()

const { speak, stop } = useSpeech()
const isVoiceMode = ref(false)

onMounted(() => {
  const userMode = localStorage.getItem('user-mode')
  isVoiceMode.value = userMode === 'voice'

  if (isVoiceMode.value) {
    setTimeout(() => { speak(`欢迎来到康乐家`) }, 500)
  }
})

watch(() => $route.path, (newPath) => {
  if (!isVoiceMode.value) return
  const pageNames = {
    '/home': '系统首页',
    '/health-record/info': '我的档案',
    '/health-record/history': '健康历史',
    '/health-record/intervention': '今日建议',
    '/test': '能力测试',
    '/chat-ai': '健康咨询',
    '/health-education': '健康科普'
  }
  const pageName = pageNames[newPath]
  if (pageName) setTimeout(() => { speak(pageName) }, 300)
})

const logout = () => {
  stop()
  localStorage.removeItem('student-user')
  ElMessage.success('已退出登录')
  $router.push('/login')
}
</script>

<style scoped>
/* =========================================
SaaS 现代化框架样式 (扁平导航优化)
========================================= */
.saas-app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--sn-bg);
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
  overflow: hidden;
}

.saas-body {
  display: flex; flex: 1; overflow: hidden;
}

/* 侧边栏样式：与背景融合，弱化卡片感 */
.saas-floating-sidebar {
  width: 250px; background: var(--sn-slate-light);
  padding: 24px 16px;
  display: flex; flex-direction: column;
  border-right: 1px solid rgba(0,0,0,0.04);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 侧边栏品牌区：扁平化，与菜单入口对齐 */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px 20px 16px;
  margin-bottom: 8px;
}
.sidebar-logo { width: 28px; flex-shrink: 0; }
.sidebar-brand-name { font-weight: 700; font-size: 16px; color: var(--sn-text); letter-spacing: -0.2px; }

.menu-group-title {
  font-size: 11px; font-weight: 800; color: var(--sn-text-muted);
  padding: 16px 16px 8px 16px; text-transform: uppercase; letter-spacing: 1.2px;
}

.saas-menu { border-right: none !important; background: transparent; height: 100%; display: flex; flex-direction: column; }
.spacer { flex: 1; }

:deep(.el-menu-item) {
  height: 48px; line-height: 48px; border-radius: var(--sn-radius-sm);
  margin-bottom: 2px; font-weight: 600; color: var(--sn-text-secondary); font-size: 14px;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

:deep(.el-menu-item:hover) {
  background-color: rgba(10, 127, 206, 0.06) !important; color: var(--sn-primary);
}

:deep(.el-menu-item.is-active) {
  background-color: rgba(10, 127, 206, 0.1) !important; color: var(--sn-primary) !important;
  font-weight: 700;
}

.logout-item { color: var(--sn-danger) !important; margin-top: 16px; }
.logout-item:hover { background-color: var(--sn-danger-light) !important; }

.saas-main-canvas { flex: 1; overflow-y: auto; padding: 24px; }
.canvas-wrapper { min-height: 100%; position: relative; }

/* 二级页面切换动画 — 纯透明度淡入淡出，避免鼠标闪烁 */
.page-switch-enter-active,
.page-switch-leave-active {
  transition: opacity 0.25s ease;
}
.page-switch-leave-active {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  pointer-events: none;
}
.page-switch-enter-from,
.page-switch-leave-to {
  opacity: 0;
}

/* 老年模式放大 */
html[data-accessibility="elderly"] .saas-floating-sidebar { width: 320px; }
html[data-accessibility="elderly"] .sidebar-brand { padding: 0 16px 24px 16px; }
html[data-accessibility="elderly"] .sidebar-brand-name { font-size: 22px; }
html[data-accessibility="elderly"] .sidebar-logo { width: 36px; }
html[data-accessibility="elderly"] :deep(.el-menu-item) { height: 60px; line-height: 60px; font-size: 19px; border-radius: var(--sn-radius-md); }
html[data-accessibility="elderly"] .menu-group-title { font-size: 15px; }
</style>