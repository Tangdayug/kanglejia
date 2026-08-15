<template>
  <div class="mobile-home page-padding">
    <div class="home-header">
      <div class="user-info">
        <img src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" alt="avatar" class="avatar" />
        <div>
          <div class="greeting">{{ greeting }}，{{ user.name || user.username || '朋友' }}</div>
          <div class="date">{{ today }}</div>
        </div>
      </div>
    </div>

    <div class="welcome-card">
      <div class="welcome-text">
        <h2>今天感觉如何？</h2>
        <p>康乐家时刻守护您的健康</p>
      </div>
      <img src="@shared/assets/imgs/grandparents.png" alt="illustration" class="welcome-img" />
    </div>

    <div class="today-card mobile-card" @click="goToTest">
      <div class="today-left">
        <form-outlined class="today-icon" />
        <div>
          <h3>今日健康测试</h3>
          <p>花 3 分钟了解身体状况</p>
        </div>
      </div>
      <right-outlined class="today-arrow" />
    </div>

    <div class="today-card mobile-card chat-card" @click="goToChat">
      <div class="today-left">
        <message-outlined class="today-icon" />
        <div>
          <h3>AI 健康咨询</h3>
          <p>随时随地获取健康建议</p>
        </div>
      </div>
      <right-outlined class="today-arrow" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  FormOutlined,
  MessageOutlined,
  RightOutlined
} from '@ant-design/icons-vue'
import { useSpeech } from '@shared/composables/useSpeech'
import { checkReadiness } from '@shared/api/chatAI'

const router = useRouter()
const { stop, speakPageTitle } = useSpeech()

const user = JSON.parse(localStorage.getItem('student-user') || '{}')

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 11) return '早安'
  if (hour >= 11 && hour < 13) return '中午好'
  if (hour >= 13 && hour < 18) return '下午好'
  if (hour >= 18 && hour < 23) return '晚上好'
  return '夜深了'
})

onMounted(async () => {
  const userMode = localStorage.getItem('user-mode')
  if (!userMode) {
    message.warning('请先选择使用模式')
    setTimeout(() => router.replace('/mode-select'), 1000)
    return
  }
  speakPageTitle('首页')
  try {
    const res = await checkReadiness()
    const guideShown = localStorage.getItem('mobile-home-guide-shown')
    if (!guideShown && !res.data.hasHealthRecord && !res.data.hasHealthTest) {
      localStorage.setItem('mobile-home-guide-shown', '1')
      Modal.info({
        title: '欢迎使用康乐家',
        content: '建议您先填写健康档案或完成健康测试，以便获得更精准的建议。',
        okText: '去填写档案',
        onOk: () => router.push('/health-info')
      })
    }
  } catch (e) {}
})

onUnmounted(() => stop())

function goToChat() { router.push('/chat-ai') }
function goToTest() { router.push('/test') }
</script>

<style scoped>
.mobile-home {
  padding-bottom: 120px;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
}

.greeting {
  font-size: 20px;
  font-weight: 700;
  color: #111;
}

.date {
  font-size: 16px;
  color: #666;
}

.welcome-card {
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  overflow: hidden;
}

.welcome-text h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #111;
}

.welcome-text p {
  margin: 0;
  font-size: 17px;
  color: #444;
}

.welcome-img {
  width: 100px;
  height: 100px;
  object-fit: contain;
}

.today-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.today-card:active {
  transform: scale(0.99);
}

.today-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.today-icon {
  font-size: 32px;
  color: #047857;
}

.today-card h3 {
  margin: 0 0 4px 0;
  font-size: 19px;
  color: #111;
}

.today-card p {
  margin: 0;
  font-size: 15px;
  color: #666;
}

.today-arrow {
  font-size: 18px;
  color: #bbb;
}

.chat-card .today-icon {
  color: #1890ff;
}
</style>
