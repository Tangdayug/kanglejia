<template>
  <div class="mobile-chat-ai">
    <div class="chat-header">
      <a-button type="text" shape="circle" @click="sidebarOpen = true">
        <menu-outlined />
      </a-button>
      <span class="header-title">{{ currentSession?.title || 'AI 健康助手' }}</span>
      <a-button type="text" shape="circle" @click="showHelp">
        <question-circle-outlined />
      </a-button>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0 && !isStreaming" class="empty-state">
        <img src="@shared/assets/imgs/logo2.png" alt="logo" class="empty-logo" />
        <p class="empty-text">今天我能帮您解答什么健康问题？</p>

        <div v-if="showReadiness" class="readiness-card">
          <h4>让建议更贴近您</h4>
          <p>花 2 分钟回答几个问题，AI 就能给出更适合您的建议。</p>
          <div class="readiness-actions">
            <a-button type="primary" size="small" @click="goToHealthTest">去回答</a-button>
            <a-button size="small" @click="dismissReadiness">直接聊天</a-button>
          </div>
        </div>

        <div v-if="recommendations.length > 0" class="recommendations">
          <a-button
            v-for="(rec, index) in recommendations"
            :key="index"
            class="rec-btn"
            @click="handleRecommendationClick(rec)"
          >
            {{ rec }}
          </a-button>
        </div>
      </div>

      <div v-else class="message-list">
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :role="message.role"
          :content="message.content"
          :sources="message.sources"
          :created-at="message.createdAt"
        />
        <div v-if="isStreaming" class="thinking-row">
          <img src="@shared/assets/imgs/logo2.png" alt="AI" class="thinking-avatar" />
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <ChatInput
        :disabled="!currentSession"
        :is-loading="isStreaming"
        @send="handleSendMessage"
      />
      <p class="disclaimer">AI 建议仅供参考，不能替代专业医生诊断</p>
    </div>

    <a-drawer
      v-model:open="sidebarOpen"
      placement="left"
      title="对话列表"
      width="280px"
    >
      <a-button type="primary" block class="new-chat-btn" @click="handleNewChat">
        <plus-outlined /> 新对话
      </a-button>
      <a-list :data-source="sessions" class="session-list">
        <template #renderItem="{ item }">
          <a-list-item
            :class="['session-item', { active: currentSession?.id === item.id }]"
            @click="handleSelectSession(item)"
          >
            <div class="session-title">{{ item.title }}</div>
            <div class="session-time">{{ formatSessionTime(item.updatedAt) }}</div>
            <template #actions>
              <a-button type="text" danger size="small" @click.stop="handleDeleteSession(item.id)">
                <delete-outlined />
              </a-button>
            </template>
          </a-list-item>
        </template>
        <template #empty>
          <a-empty description="暂无历史对话" />
        </template>
      </a-list>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  MenuOutlined,
  QuestionCircleOutlined,
  PlusOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'
import {
  createSession,
  getSessions,
  getMessages,
  streamMessage,
  getRecommendations,
  checkReadiness,
  deleteSession
} from '@shared/api/chatAI'
import { useSpeech } from '@shared/composables/useSpeech'

const router = useRouter()
const route = useRoute()
const { speakWithCallback, stop, isEnabled: speechEnabled } = useSpeech()

const userStr = localStorage.getItem('student-user')
const user = userStr ? JSON.parse(userStr) : {}

const sidebarOpen = ref(false)
const sessions = ref([])
const currentSession = ref(null)
const messages = ref([])
const recommendations = ref([])
const isStreaming = ref(false)
const showReadiness = ref(false)
const messagesRef = ref(null)
const lastSpokenMessageId = ref(null)
const currentlySpeakingMessageId = ref(null)

onMounted(async () => {
  await checkUserReadiness()
  await loadSessions()
  await createNewSession()

  const careMessage = route.query.careMessage
  if (careMessage && currentSession.value) {
    await nextTick()
    handleSendMessage(careMessage)
  }
})

onUnmounted(() => stop())

watch(messages, (newMessages, oldMessages) => {
  if (!speechEnabled.value) return
  if (newMessages.length > (oldMessages?.length || 0)) {
    const latestMessage = newMessages[newMessages.length - 1]
    if (latestMessage.role === 'assistant' && latestMessage.id !== lastSpokenMessageId.value && !isStreaming.value) {
      lastSpokenMessageId.value = latestMessage.id
      currentlySpeakingMessageId.value = latestMessage.id
      const plainText = stripMarkdown(latestMessage.content)
      if (plainText) speakWithCallback(plainText, () => { currentlySpeakingMessageId.value = null }, 500)
    }
  }
}, { deep: true })

watch(isStreaming, (newValue, oldValue) => {
  if (!speechEnabled.value) return
  if (oldValue === true && newValue === false && messages.value.length > 0) {
    const latestMessage = messages.value[messages.value.length - 1]
    if (latestMessage.role === 'assistant' && latestMessage.id !== lastSpokenMessageId.value) {
      lastSpokenMessageId.value = latestMessage.id
      currentlySpeakingMessageId.value = latestMessage.id
      const plainText = stripMarkdown(latestMessage.content)
      if (plainText) speakWithCallback(plainText, () => { currentlySpeakingMessageId.value = null }, 300)
    }
  }
})

async function checkUserReadiness() {
  try {
    const res = await checkReadiness()
    const readinessDismissed = localStorage.getItem('mobile-chat-readiness-dismissed')
    if (!readinessDismissed && !res.data.hasHealthRecord && !res.data.hasHealthTest) {
      showReadiness.value = true
    }
  } catch (error) {}
}

async function loadSessions() {
  try {
    const res = await getSessions()
    sessions.value = res.data.sessions || []
  } catch (error) {
    console.error('Failed to load sessions:', error)
  }
}

async function createNewSession() {
  try {
    const res = await createSession({ title: '新对话' })
    currentSession.value = res.data
    messages.value = []
    isStreaming.value = false
    await loadRecommendations()
    await loadSessions()
  } catch (error) {
    message.error('创建对话失败')
  }
}

async function loadRecommendations() {
  if (!currentSession.value?.id) {
    recommendations.value = ['如何改善睡眠质量？', '老年人适合哪些运动？', '怎样保持健康饮食？']
    return
  }
  try {
    const res = await getRecommendations(currentSession.value.id)
    if (res.code === '200' && res.data.recommendations?.length > 0) {
      recommendations.value = res.data.recommendations
    } else {
      recommendations.value = ['如何改善睡眠质量？', '老年人适合哪些运动？', '怎样保持健康饮食？']
    }
  } catch (error) {
    recommendations.value = ['如何改善睡眠质量？', '老年人适合哪些运动？', '怎样保持健康饮食？']
  }
}

async function handleSelectSession(session) {
  sidebarOpen.value = false
  try {
    currentSession.value = session
    isStreaming.value = false
    const res = await getMessages(session.id)
    messages.value = res.data.messages || []
    await scrollToBottom()
  } catch (error) {
    message.error('加载对话失败')
  }
}

function handleNewChat() {
  sidebarOpen.value = false
  createNewSession()
}

async function handleDeleteSession(sessionId) {
  Modal.confirm({
    title: '删除对话',
    content: '删除后将无法找回，确定删除吗？',
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteSession(sessionId)
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
        if (currentSession.value?.id === sessionId) {
          await createNewSession()
        }
        message.success('删除成功')
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

async function handleSendMessage(text) {
  if (!currentSession.value || isStreaming.value) return
  isStreaming.value = true
  const userMessage = { id: Date.now(), role: 'user', content: text, createdAt: new Date().toISOString() }
  messages.value.push(userMessage)
  await scrollToBottom()

  let assistantContent = ''
  let assistantMessageAdded = false
  let assistantMessageId = Date.now() + 1

  try {
    await streamMessage(
      currentSession.value.id,
      text,
      (chunk) => {
        assistantContent += chunk
        if (!assistantMessageAdded && assistantContent) {
          messages.value.push({ id: assistantMessageId, role: 'assistant', content: assistantContent, sources: null, createdAt: new Date().toISOString() })
          assistantMessageAdded = true
        } else if (assistantMessageAdded) {
          const lastIndex = messages.value.length - 1
          if (lastIndex >= 0 && messages.value[lastIndex].role === 'assistant') {
            Object.assign(messages.value[lastIndex], { content: assistantContent })
          }
        }
        scrollToBottom()
      },
      (error) => {
        message.error('发送消息失败')
        isStreaming.value = false
      },
      (sources) => {
        isStreaming.value = false
        if (sources && assistantMessageAdded) {
          const lastIndex = messages.value.length - 1
          Object.assign(messages.value[lastIndex], { sources })
        }
        loadRecommendations()
      }
    )
  } catch (error) {
    message.error('发送消息失败')
    isStreaming.value = false
  }
}

function handleRecommendationClick(question) { handleSendMessage(question) }
function goToHealthTest() { router.push('/test') }
function dismissReadiness() {
  localStorage.setItem('mobile-chat-readiness-dismissed', '1')
  showReadiness.value = false
}
function showHelp() {
  Modal.info({
    title: '使用帮助',
    content: '您可以输入文字或点击话筒语音提问。AI 会根据您的情况给出健康建议，但严重不适时请尽快就医。'
  })
}

function stripMarkdown(text) {
  if (!text) return ''
  return text.replace(/^#{1,6}\s+/gm, '').replace(/\*\*/g, '').replace(/__/g, '').replace(/\*/g, '')
    .replace(/_/g, '').replace(/```[\s\S]*?```/g, '代码块').replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\n{3,}/g, '\n\n').trim()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      requestAnimationFrame(() => {
        messagesRef.value.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
      })
    }
  })
}

function formatSessionTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return `今天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return `昨天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<style scoped>
.mobile-chat-ai {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  color: #111;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 40px;
}

.empty-logo {
  width: 120px;
  height: 120px;
  object-fit: contain;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 18px;
  color: #666;
  margin: 0 0 24px 0;
}

.readiness-card {
  width: 100%;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
}

.readiness-card h4 {
  margin: 0 0 8px 0;
  font-size: 17px;
}

.readiness-card p {
  margin: 0 0 12px 0;
  color: #555;
  font-size: 15px;
}

.readiness-actions {
  display: flex;
  gap: 10px;
}

.recommendations {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rec-btn {
  min-height: 48px;
  font-size: 15px;
  text-align: left;
  border-radius: 12px;
  white-space: normal;
  height: auto;
  line-height: 1.4;
  padding: 12px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.thinking-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.thinking-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #fff;
  padding: 4px;
  border: 1px solid #eee;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); background: #999; }
}

.chat-input-area {
  flex-shrink: 0;
  background: #fff;
  border-top: 1px solid #eee;
  padding-bottom: env(safe-area-inset-bottom);
}

.disclaimer {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin: 0;
  padding: 6px 12px;
}

.new-chat-btn {
  margin-bottom: 12px;
  min-height: 44px;
}

.session-list :deep(.ant-list-item) {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
}

.session-list :deep(.ant-list-item.active) {
  background: #e6f7ff;
}

.session-title {
  font-weight: 700;
  font-size: 15px;
}

.session-time {
  font-size: 12px;
  color: #999;
}
</style>
