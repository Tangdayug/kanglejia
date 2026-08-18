<template>
  <div class="modern-ai-app">
    
    <div class="ai-sidebar-container" :class="{ open: sidebarOpen }">
      <div class="sidebar-body">
        <ChatSidebar
          ref="sidebarRef"
          :current-session-id="currentSession?.id"
          @select-session="handleSelectSession"
          @new-chat="handleNewChat"
        />
      </div>
      <div class="sidebar-footer">
        <button class="back-nav-btn" @click="goHome">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
      </div>
    </div>

    <div class="ai-sidebar-overlay" :class="{ open: sidebarOpen }" @click="sidebarOpen = false"></div>

    <div class="ai-main-container">

      <header class="ai-topbar">
        <button class="menu-toggle-btn" @click="sidebarOpen = !sidebarOpen">
          <el-icon><Menu /></el-icon>
        </button>
        <div class="topbar-actions">
          <button class="help-btn" @click="showHelp" title="帮助">
            <el-icon><Help /></el-icon>
            <span class="help-text">帮助</span>
          </button>
          <button v-if="messages.length > 0" class="clear-chat-btn" @click="handleClearMessages" title="清空对话">
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </header>

      <div class="ai-chat-viewport" ref="messagesRef">
        <Transition name="fade-in" mode="out-in">
          
          <div v-if="messages.length === 0 && !isStreaming" key="empty" class="ai-empty-state">
            
            <div class="greeting-section">
              <div class="greeting-logo">
                <img src="@/assets/imgs/logo2.png" alt="康乐家" />
              </div>
              <p class="greeting-subtitle">今天我能帮您解答什么健康问题？</p>
            </div>

            <Transition name="fade-up">
              <div v-if="showReadiness" class="readiness-inline-card">
                <div class="r-icon"><el-icon><Help /></el-icon></div>
                <div class="r-content">
                  <h4>让建议更贴近您的身体情况</h4>
                  <p>花 2 分钟回答几个简单问题，AI 就能给出更适合您的健康建议。</p>
                  <div class="r-actions">
                    <button class="r-btn primary" @click="goToHealthTest">先回答几个问题</button>
                    <button class="r-btn secondary" @click="showReadiness = false">直接聊天</button>
                  </div>
                </div>
              </div>
            </Transition>

            <div v-if="recommendations.length > 0" class="bento-suggestions">
              <button 
                v-for="(rec, index) in recommendations" 
                :key="index"
                class="bento-card"
                @click="handleRecommendationClick(rec)"
              >
                <span>{{ rec }}</span>
                <el-icon class="bento-arrow"><TopRight /></el-icon>
              </button>
            </div>
            
          </div>

          <div v-else key="chat" class="ai-message-stream">
            <ChatMessage
              v-for="message in messages"
              :key="message.id"
              :role="message.role"
              :content="message.content"
              :sources="message.sources"
              :created-at="message.createdAt"
              :is-speaking="currentlySpeakingMessageId === message.id"
              @speak="speakMessage"
              @pause="pauseMessage"
            />

            <div v-if="isStreaming && (!messages.length || messages[messages.length - 1].role !== 'assistant')" class="ai-thinking-row">
              <div class="ai-avatar"><img src="@/assets/imgs/logo2.png" alt="AI" /></div>
              <div class="thinking-bubbles">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
              </div>
            </div>
            
            <div class="scroll-spacer"></div>
          </div>
        </Transition>
      </div>

      <div class="ai-input-zone">
        <div class="input-container-inner">
          <div class="glass-input-wrapper">
            <ChatInput
              :disabled="isStreaming"
              :is-loading="isStreaming"
              @send="handleSendMessage"
            />
          </div>
          <div class="ai-disclaimer">
            <el-icon><Warning /></el-icon>
            AI 助手生成的医疗健康建议仅供参考，不能替代专业医生的诊断。
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Warning, DocumentCopy, Folder, ArrowLeft, TopRight, Help, Menu } from '@element-plus/icons-vue'
import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'
import { createSession, getMessages, streamMessage, getRecommendations, checkReadiness } from '@/api/chatAI'
import { submitFeedback } from '@/api/care'
import { useSpeech } from '@/composables/useSpeech'
import tts from '@/utils/tts'

const router = useRouter()
const route = useRoute()

const userStr = localStorage.getItem('student-user')
const user = userStr ? JSON.parse(userStr) : {}
const username = ref(user.name || user.username || '朋友')

const { speakWithCallback, stop, isEnabled: speechEnabled } = useSpeech()
const lastSpokenMessageId = ref(null)
const currentlySpeakingMessageId = ref(null)

const showReadiness = ref(false) 
const readiness = ref({ hasHealthRecord: false, hasHealthTest: false, isReady: false })
const currentSession = ref(null)
const messages = ref([])
const recommendations = ref([])
const isStreaming = ref(false)
const sidebarRef = ref(null)
const messagesRef = ref(null)

const interventionContext = ref(null)
const hasProcessedCareMessage = ref(false)
const sidebarOpen = ref(false)
const autoPlayVoice = ref(true)
const pollTimer = ref(null)

onMounted(async () => {
  await checkUserReadiness()
  // 不再每次进入都自动创建空会话，避免产生大量“新对话”空白记录
  currentSession.value = null
  messages.value = []
  await loadRecommendations()

  // 初始化语音播报（用于健康对话自动播报）
  if (autoPlayVoice.value) {
    tts.init().catch(() => {})
  }

  // 定时轮询当前会话消息，实现硬件/网页对话实时同步
  startPolling()

  const careMessage = route.query.careMessage
  const interventionId = route.query.interventionId

  if (careMessage && !hasProcessedCareMessage.value) {
    hasProcessedCareMessage.value = true
    if (interventionId) interventionContext.value = { id: parseInt(interventionId) }
    await nextTick()
    if (currentSession.value) handleSendMessage(careMessage)
  }
})

onUnmounted(() => {
  stop()
  stopPolling()
})

function startPolling() {
  stopPolling()
  pollTimer.value = setInterval(async () => {
    if (!currentSession.value?.id || isStreaming.value) return
    try {
      const res = await getMessages(currentSession.value.id)
      const freshMessages = res.data.messages || []
      if (freshMessages.length !== messages.value.length) {
        messages.value = freshMessages
        scrollToBottom()
      }
    } catch (error) {
      // 静默忽略轮询失败，避免打断用户
    }
  }, 2000)
}

function stopPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

function stripMarkdown(text) {
  if (!text) return ''
  return text.replace(/^#{1,6}\s+/gm, '').replace(/\*\*/g, '').replace(/__/g, '').replace(/\*/g, '')
    .replace(/_/g, '').replace(/```[\s\S]*?```/g, '代码块').replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\n{3,}/g, '\n\n').trim()
}

function speakMessage(content, messageId) {
  if (!content) return
  const id = messageId || Date.now()
  lastSpokenMessageId.value = id
  currentlySpeakingMessageId.value = id
  const plainText = stripMarkdown(content)
  if (!plainText) {
    currentlySpeakingMessageId.value = null
    return
  }
  tts.speak(plainText, {
    onEnd: () => {
      if (currentlySpeakingMessageId.value === id) {
        currentlySpeakingMessageId.value = null
      }
    },
    onError: () => {
      if (currentlySpeakingMessageId.value === id) {
        currentlySpeakingMessageId.value = null
      }
    }
  })
}

function pauseMessage() {
  tts.stop()
  currentlySpeakingMessageId.value = null
}

watch(messages, (newMessages, oldMessages) => {
  if (newMessages.length > (oldMessages?.length || 0)) {
    const latestMessage = newMessages[newMessages.length - 1]
    // 自动播报 AI 回复（默认开启）
    if (autoPlayVoice.value && latestMessage.role === 'assistant' && latestMessage.id !== lastSpokenMessageId.value && !isStreaming.value) {
      speakMessage(latestMessage.content, latestMessage.id)
    }
    if (latestMessage.role === 'user' && interventionContext.value && currentSession.value) {
      submitFeedback({ interventionId: interventionContext.value.id, feedback: latestMessage.content, sessionId: currentSession.value.id })
      interventionContext.value = null
    }
  }
}, { deep: true })

watch(isStreaming, (newValue, oldValue) => {
  if (oldValue === true && newValue === false && messages.value.length > 0) {
    const latestMessage = messages.value[messages.value.length - 1]
    if (autoPlayVoice.value && latestMessage.role === 'assistant' && latestMessage.id !== lastSpokenMessageId.value) {
      speakMessage(latestMessage.content, latestMessage.id)
    }
  }
})

async function checkUserReadiness() {
  try {
    const res = await checkReadiness()
    readiness.value = res.data
    if (!res.data.hasHealthRecord && !res.data.hasHealthTest) {
      showReadiness.value = true
    }
  } catch (error) {
    console.error('Failed to check readiness:', error)
  }
}

async function createNewSession() {
  try {
    const res = await createSession({ title: '新对话' })
    currentSession.value = res.data
    messages.value = []
    isStreaming.value = false
    await loadRecommendations()
  } catch (error) {
    ElMessage.error('创建对话失败')
  }
}

async function loadRecommendations() {
  if (!currentSession.value?.id) {
    // 如果会话不存在，设置默认推荐
    recommendations.value = ['如何改善睡眠质量？', '老年人适合哪些运动？', '怎样保持健康饮食？']
    return
  }
  try {
    const res = await getRecommendations(currentSession.value.id)
    if (res.code === '200' && res.data.recommendations && res.data.recommendations.length > 0) {
      recommendations.value = res.data.recommendations
    } else {
      // API 返回空或失败，使用默认推荐
      recommendations.value = ['如何改善睡眠质量？', '老年人适合哪些运动？', '怎样保持健康饮食？']
    }
  } catch (error) {
    console.error('加载推荐失败:', error)
    recommendations.value = ['如何改善睡眠质量？', '老年人适合哪些运动？', '怎样保持健康饮食？']
  }
}

async function handleSelectSession(session) {
  try {
    currentSession.value = session
    isStreaming.value = false
    const res = await getMessages(session.id)
    messages.value = res.data.messages || []
    await scrollToBottom()
  } catch (error) {
    ElMessage.error('加载对话失败')
  }
}

function handleNewChat() { createNewSession() }

async function handleSendMessage(text) {
  if (isStreaming.value) return

  // 首次发送时才真正创建会话，避免空会话堆积
  if (!currentSession.value) {
    try {
      const res = await createSession({ title: '新对话' })
      currentSession.value = res.data
      await sidebarRef.value?.reload()
    } catch (error) {
      ElMessage.error('创建对话失败')
      return
    }
  }

  isStreaming.value = true
  const userMessage = { id: Date.now(), role: 'user', content: text, createdAt: new Date().toISOString() }
  messages.value.push(userMessage)
  await scrollToBottom()

  let assistantContent = ''
  let assistantMessageAdded = false
  let assistantMessageId = Date.now() + 1

  try {
    await streamMessage(
      currentSession.value.id, text,
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
      (error) => { ElMessage.error('发送消息失败'); isStreaming.value = false },
      (sources) => {
        isStreaming.value = false
        if (sources && assistantMessageAdded) {
          const lastIndex = messages.value.length - 1
          Object.assign(messages.value[lastIndex], { sources: sources })
        }
        loadRecommendations()
      }
    )
  } catch (error) {
    ElMessage.error('发送消息失败')
    isStreaming.value = false
  }
}

function handleRecommendationClick(question) { handleSendMessage(question) }

// 右上角的清空对话按钮逻辑
function handleClearMessages() {
  ElMessageBox.confirm(
    '清空后将无法恢复，确定要清空当前对话吗？', 
    '清空对话', 
    {
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
      customClass: 'modern-confirm-dialog danger-action', 
      center: true,
      showClose: false
    }
  ).then(() => {
    currentSession.value = null
    messages.value = []
    isStreaming.value = false
    loadRecommendations()
  }).catch(() => {})
}

function goToHealthTest() { router.push('/test') }
function goToHealthRecord() { router.push('/health-record/info') }
function goHome() { router.push('/home') }
function showHelp() {
  ElMessageBox.alert(
    '您可以输入文字或点击“说话”按钮语音提问。AI 会根据您的情况给出健康建议，但严重不适时请尽快就医或联系家人。',
    '使用帮助',
    { confirmButtonText: '我知道了', customClass: 'modern-confirm-dialog', showClose: false }
  )
}

onBeforeRouteLeave((to, from, next) => {
  ElMessage.closeAll()
  ElMessageBox.close()
  next()
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      requestAnimationFrame(() => { messagesRef.value.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' }) })
    }
  })
}
</script>

<style scoped>
/* ===============================================
全局重置与框架 (修正了 z-index 为 1500)
=============================================== */
.modern-ai-app {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: #FFFFFF; 
  z-index: 1500; /* 已修复层级，确保弹窗正常显示 */
  display: flex;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
  overflow: hidden;
}

/* 左侧边栏 - GPT风格极简 */
.ai-sidebar-container {
  width: 260px; background: #F9F9F9; border-right: 1px solid #F0F0F0;
  display: flex; flex-direction: column; flex-shrink: 0;
}
.sidebar-body { flex: 1; overflow-y: auto; }
.sidebar-footer { padding: 12px; border-top: 1px solid #F0F0F0; }
.back-nav-btn {
  width: 100%; display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px;
  background: transparent; border: 1px solid var(--sn-primary); border-radius: 12px;
  font-size: 15px; font-weight: 700; color: var(--sn-primary); cursor: pointer; transition: 0.2s;
}
.back-nav-btn:hover { background: rgba(23, 114, 246, 0.06); }
.back-nav-btn .el-icon { font-size: 16px; }

/* ===============================================
右侧主聊天区域
=============================================== */
.ai-main-container { flex: 1; display: flex; flex-direction: column; position: relative; }

/* 顶部透明状态栏 */
.ai-topbar {
  height: 64px; display: flex; justify-content: space-between; align-items: center; padding: 0 24px;
  position: absolute; top: 0; left: 0; right: 0; z-index: 10; pointer-events: none;
  background: rgba(249, 249, 249, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.topbar-actions { display: flex; align-items: center; gap: 8px; pointer-events: auto; margin-left: auto; }
.back-nav-btn.mobile-back {
  display: none;
  pointer-events: auto;
}
.menu-toggle-btn {
  display: none; pointer-events: auto; background: transparent; border: 1px solid #E5E5E5;
  width: 40px; height: 40px; border-radius: 50%; align-items: center; justify-content: center;
  color: #666; cursor: pointer; transition: 0.2s;
}
.menu-toggle-btn:hover { background: #F5F5F5; border-color: #D1D5DB; color: #333; }
.help-btn {
  background: transparent; border: 1px solid #E5E5E5; border-radius: var(--sn-radius-md);
  display: flex; align-items: center; gap: 6px; padding: 8px 14px;
  font-size: 14px; font-weight: 700; color: #666; cursor: pointer; transition: 0.2s;
}
.help-btn:hover { background: #F5F5F5; border-color: #D1D5DB; color: #333; }
.clear-chat-btn {
  pointer-events: auto; background: transparent; border: 1px solid #E5E5E5; width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; color: #666; cursor: pointer; transition: 0.2s;
}
.clear-chat-btn:hover { background: #FEE2E2; color: #EF4444; border-color: #FECACA; }

/* 滚动视口 */
.ai-chat-viewport { flex: 1; overflow-y: auto; padding-top: 60px; scroll-behavior: smooth; }

/* ===============================================
空状态区域 (Gemini 渐变风 + 便当盒)
=============================================== */
.ai-empty-state {
  max-width: 760px; 
  margin: 8vh auto 0 auto; 
  padding: 0 24px 140px 24px; 
  display: flex; 
  flex-direction: column; 
  align-items: center;
}
.greeting-section { text-align: center; margin-bottom: 40px; }
.greeting-logo { 
  display: flex; justify-content: center; align-items: center; 
  margin-bottom: 20px; 
}
.greeting-logo img { max-width: 200px; max-height: 120px; object-fit: contain; }
.greeting-title { font-size: 40px; font-weight: 700; margin: 0 0 12px 0; letter-spacing: -1px; }
.gradient-text {
  color: var(--sn-primary);
}
.greeting-subtitle { font-size: 20px; color: #444; font-weight: 500; margin: 0; }

.readiness-inline-card {
  width: 100%; background: #EFF6FF; border: 2px solid #BFDBFE; border-radius: var(--sn-radius-lg);
  padding: 28px; display: flex; gap: 20px; margin-bottom: 40px; text-align: left;
}
.r-icon { width: 56px; height: 56px; background: transparent; color: #374151; border: 2px solid #E5E7EB; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; flex-shrink: 0; }
.r-content h4 { margin: 0 0 12px 0; font-size: 22px; font-weight: 800; color: #1E3A8A; }
.r-content p { margin: 0 0 24px 0; font-size: 17px; color: #1D4ED8; line-height: 1.6; }
.r-actions { display: flex; gap: 16px; flex-wrap: wrap; }
.r-btn { min-height: 48px; padding: 0 24px; border-radius: var(--sn-radius-md); font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.2s; border: 2px solid transparent; }
.r-btn.primary { background: transparent; color: var(--sn-primary); border-color: var(--sn-primary); }
.r-btn.primary:hover { background: rgba(23, 114, 246, 0.06); }
.r-btn.secondary { background: #FFF; color: var(--sn-primary); border-color: var(--sn-primary); }
.r-btn.secondary:hover { background: rgba(23, 114, 246, 0.06); }

.bento-suggestions {
  width: 100%; display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 40px;
}
.bento-card {
  background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: var(--sn-radius-md); padding: 20px;
  display: flex; justify-content: space-between; align-items: flex-start; text-align: left;
  cursor: pointer; transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
  font-size: 15px; font-weight: 500; color: #333; line-height: 1.5; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.bento-card:hover { background: #F9FAFB; border-color: #D1D5DB; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.05); }
.bento-arrow { color: #9CA3AF; font-size: 18px; opacity: 0; transition: 0.3s; transform: translate(-4px, 4px); }
.bento-card:hover .bento-arrow { opacity: 1; transform: translate(0, 0); color: #111; }

/* ===============================================
消息流区域
=============================================== */
.ai-message-stream { max-width: 800px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 32px; }
.scroll-spacer { height: 160px; }

.ai-thinking-row { display: flex; gap: 16px; align-items: center; animation: fadeIn 0.4s; }
.ai-avatar { width: 32px; height: 32px; border-radius: 50%; border: 1px solid #E5E5E5; display: flex; align-items: center; justify-content: center; background: #FFF; }
.ai-avatar img { width: 20px; height: 20px; }
.thinking-bubbles { display: flex; gap: 6px; }
.thinking-bubbles .dot { width: 8px; height: 8px; background: #D1D5DB; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.thinking-bubbles .dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-bubbles .dot:nth-child(2) { animation-delay: -0.16s; }

/* ===============================================
底部悬浮输入区域 (GPT/Gemini 胶囊)
=============================================== */
.ai-input-zone {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.8) 30%, rgba(255,255,255,1) 100%);
  padding: 0 24px 24px 24px; display: flex; justify-content: center; pointer-events: none; z-index: 20;
}
.input-container-inner { width: 100%; max-width: 800px; pointer-events: auto; }

.glass-input-wrapper {
  background: #F4F4F5; border-radius: var(--sn-radius-xl); transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.02);
  overflow: hidden;
}
.glass-input-wrapper:focus-within { background: #FFFFFF; border-color: #E5E7EB; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }

:deep(.chat-input-container) { border: none !important; padding: 6px 10px !important; background: transparent !important; }
:deep(.input-wrapper) { align-items: center !important; }
:deep(.message-input .el-textarea__inner) { 
  background: transparent !important; 
  border: none !important; 
  box-shadow: none !important; 
  font-size: 16px !important; 
  padding: 10px 12px !important; 
  line-height: 1.5 !important;
  color: #111; 
  scrollbar-width: none; 
}
:deep(.message-input .el-textarea__inner::-webkit-scrollbar) { display: none; }
:deep(.send-button) { border-radius: var(--sn-radius-md) !important; height: 40px !important; padding: 0 20px !important; font-weight: 600 !important; background: transparent !important; border: 1px solid var(--sn-primary) !important; color: var(--sn-primary) !important; }
:deep(.send-button:hover) { background: rgba(23, 114, 246, 0.06) !important; }
:deep(.send-button:disabled) { background: #E0E0E0 !important; border-color: #E0E0E0 !important; color: #999 !important; }
:deep(.input-hint) { display: none !important; }

.ai-disclaimer {
  text-align: center; font-size: 15px; color: #555; margin-top: 12px;
  display: flex; align-items: center; justify-content: center; gap: 6px; font-weight: 600;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); background: #9CA3AF; } }
.fade-up-enter-active, .fade-up-leave-active { transition: all 0.4s ease; }
.fade-up-enter-from { opacity: 0; transform: translateY(20px); }
.fade-up-leave-to { opacity: 0; transform: translateY(-20px); }
.fade-in-enter-active, .fade-in-leave-active { transition: opacity 0.3s; }
.fade-in-enter-from, .fade-in-leave-to { opacity: 0; }

html[data-accessibility="elderly"] .greeting-logo img { max-width: 320px; max-height: 200px; }
html[data-accessibility="elderly"] .greeting-subtitle { font-size: 26px; color: #333; }
html[data-accessibility="elderly"] .bento-card { font-size: 22px; padding: 28px; }
html[data-accessibility="elderly"] .r-content h4 { font-size: 26px; }
html[data-accessibility="elderly"] .r-content p { font-size: 20px; }
html[data-accessibility="elderly"] .r-btn { min-height: 56px; font-size: 18px; }
html[data-accessibility="elderly"] .ai-disclaimer { font-size: 18px; color: #444; font-weight: 700; }
html[data-accessibility="elderly"] :deep(.message-input .el-textarea__inner) { font-size: 22px !important; }

.ai-sidebar-overlay {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 150;
}
.ai-sidebar-overlay.open { display: block; }

@media (max-width: 768px) {
  .modern-ai-app { flex-direction: column; }
  .ai-sidebar-container {
    position: fixed; top: 0; left: 0; bottom: 0; width: 75vw; max-width: 280px;
    transform: translateX(-100%); transition: transform 0.3s ease; z-index: 200;
  }
  .ai-sidebar-container.open { transform: translateX(0); }
  .ai-main-container { width: 100vw; }
  .menu-toggle-btn { display: flex; }
  .help-text { display: none; }
  .ai-empty-state { margin-top: 4vh; padding: 0 16px 120px; }
  .greeting-logo img { max-width: 140px; max-height: 90px; }
  .greeting-subtitle { font-size: 18px; }
  .readiness-inline-card { padding: 20px; flex-direction: column; gap: 16px; }
  .r-icon { width: 48px; height: 48px; font-size: 24px; }
  .r-content h4 { font-size: 18px; }
  .r-content p { font-size: 15px; }
  .r-actions { flex-direction: column; gap: 10px; }
  .r-btn { width: 100%; }
  .bento-suggestions { grid-template-columns: 1fr; }
  .bento-card { padding: 16px; font-size: 15px; }
  .ai-message-stream { padding: 12px; gap: 20px; }
  .ai-input-zone { padding: 0 12px 12px; }
  .ai-disclaimer { font-size: 13px; padding: 0 8px; }
}
</style>

<style>
.modern-confirm-dialog.el-message-box {
  border-radius: var(--sn-radius-xl) !important;
  padding: 40px 32px !important;
  background: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12) !important;
  max-width: 420px !important;
  width: 90% !important;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif !important;
}

.modern-confirm-dialog .el-message-box__status { display: none !important; }

.modern-confirm-dialog .el-message-box__header { padding: 0 !important; margin-bottom: 16px !important; }
.modern-confirm-dialog .el-message-box__title { font-size: 24px !important; font-weight: 800 !important; color: #111 !important; text-align: center !important; letter-spacing: -0.5px !important; }

.modern-confirm-dialog .el-message-box__content { padding: 0 !important; margin-bottom: 32px !important; }
.modern-confirm-dialog .el-message-box__message { font-size: 16px !important; font-weight: 500 !important; color: #666 !important; line-height: 1.6 !important; text-align: center !important; }

.modern-confirm-dialog .el-message-box__btns { padding: 0 !important; display: flex !important; gap: 12px !important; justify-content: center !important; }
.modern-confirm-dialog .el-button { flex: 1 !important; height: 48px !important; border-radius: var(--sn-radius-md) !important; font-size: 16px !important; font-weight: 700 !important; border: none !important; transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1) !important; }

.modern-confirm-dialog .el-button--default { background: #F4F5F7 !important; color: #333 !important; }
.modern-confirm-dialog .el-button--default:hover { background: #EAEAEA !important; transform: translateY(-2px) !important; }

.modern-confirm-dialog .el-button--primary { background: var(--sn-primary) !important; color: #FFF !important; box-shadow: 0 4px 12px rgba(23,114,246,0.15) !important; }
.modern-confirm-dialog .el-button--primary:hover { background: #333 !important; transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important; }

.modern-confirm-dialog.danger-action .el-button--primary { background: #EF4444 !important; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important; }
.modern-confirm-dialog.danger-action .el-button--primary:hover { background: #DC2626 !important; box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3) !important; }
</style>