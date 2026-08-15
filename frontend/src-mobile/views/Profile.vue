<template>
  <div class="mobile-profile page-padding">
    <div class="profile-header">
      <img
        src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png"
        alt="avatar"
        class="avatar"
      />
      <div class="user-meta">
        <div class="username">{{ user.name || user.username || '用户' }}</div>
        <div class="date">{{ today }}</div>
      </div>
    </div>

    <div class="menu-card mobile-card">
      <h3 class="card-title">健康数据</h3>
      <a-list>
        <a-list-item @click="goTo('/health-info')">
          <div class="menu-item">
            <file-text-outlined class="menu-icon" />
            <span>健康档案</span>
          </div>
          <right-outlined class="arrow" />
        </a-list-item>
        <a-list-item @click="goTo('/health-history')">
          <div class="menu-item">
            <line-chart-outlined class="menu-icon" />
            <span>历史趋势</span>
          </div>
          <right-outlined class="arrow" />
        </a-list-item>
        <a-list-item @click="goTo('/intervention')">
          <div class="menu-item">
            <medicine-box-outlined class="menu-icon" />
            <span>今日建议</span>
          </div>
          <right-outlined class="arrow" />
        </a-list-item>
      </a-list>
    </div>

    <div class="menu-card mobile-card">
      <h3 class="card-title">偏好设置</h3>
      <a-list>
        <a-list-item @click="toggleMode">
          <div class="menu-item">
            <sound-outlined class="menu-icon" />
            <span>当前模式：{{ currentModeText }}</span>
          </div>
        </a-list-item>
        <a-list-item @click="toggleAccessibility">
          <div class="menu-item">
            <eye-outlined class="menu-icon" />
            <span>{{ isElderlyMode ? '切换到标准模式' : '切换到长辈模式' }}</span>
          </div>
        </a-list-item>
        <a-list-item @click="goTo('/mode-select')">
          <div class="menu-item">
            <setting-outlined class="menu-icon" />
            <span>模式与音量设置</span>
          </div>
          <right-outlined class="arrow" />
        </a-list-item>
      </a-list>
    </div>

    <div class="logout-section">
      <a-button danger block size="large" @click="logout" class="logout-btn">
        退出登录
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  FileTextOutlined,
  LineChartOutlined,
  MedicineBoxOutlined,
  SoundOutlined,
  EyeOutlined,
  SettingOutlined,
  RightOutlined
} from '@ant-design/icons-vue'
import { useSpeech } from '@shared/composables/useSpeech'
import { useAccessibility } from '@shared/composables/useAccessibility'

const router = useRouter()
const { speak, stop, speakPageTitle } = useSpeech()
const { isElderlyMode, toggleMode: toggleAccessibilityMode } = useAccessibility()

const user = JSON.parse(localStorage.getItem('student-user') || '{}')

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const currentModeText = computed(() => {
  return localStorage.getItem('user-mode') === 'voice' ? '语音模式' : '文字模式'
})

onMounted(() => {
  speakPageTitle('我的')
})

onUnmounted(() => stop())

function goTo(path) {
  router.push(path)
}

function toggleMode() {
  const current = localStorage.getItem('user-mode') || 'voice'
  const next = current === 'voice' ? 'text' : 'voice'
  localStorage.setItem('user-mode', next)
  if (next === 'voice') speak('已切换到语音模式')
  else stop()
  message.success(`已切换到${next === 'voice' ? '语音' : '文字'}模式`)
}

function toggleAccessibility() {
  const newMode = toggleAccessibilityMode()
  message.success(newMode === 'elderly' ? '已切换到长辈模式' : '已切换到标准模式')
}

function logout() {
  Modal.confirm({
    title: '确认退出',
    content: '退出后需要重新登录',
    okText: '退出',
    cancelText: '取消',
    onOk: () => {
      stop()
      localStorage.clear()
      message.success('已退出登录')
      router.push('/login')
    }
  })
}
</script>

<style scoped>
.mobile-profile {
  padding-bottom: 120px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 8px 0;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #f0f0f0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.username {
  font-size: 22px;
  font-weight: 700;
  color: #111;
}

.date {
  font-size: 15px;
  color: #666;
}

.menu-card {
  margin-bottom: 20px;
}

.card-title {
  margin: 0 0 14px 0;
  font-size: 20px;
  font-weight: 700;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 18px;
  width: 100%;
  color: #222;
}

.menu-icon {
  font-size: 22px;
  color: #047857;
}

.arrow {
  color: #bbb;
  font-size: 16px;
}

.logout-section {
  margin-top: 12px;
}

.logout-btn {
  min-height: 54px;
  font-size: 18px;
  border-radius: 14px;
}
</style>
