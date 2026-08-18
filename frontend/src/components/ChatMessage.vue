<template>
  <div :class="['chat-message', role === 'user' ? 'user-message' : 'assistant-message']">
    <div class="message-avatar">
      <img
        v-if="role === 'user'"
        src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png"
        alt="用户"
      />
      <img
        v-else
        src="@/assets/imgs/logo2.png"
        alt="AI助手"
      />
    </div>
    <div class="message-content-wrapper">
      <div class="message-role">
        {{ role === 'user' ? '我' : 'AI健康助手' }}
        <!-- 语音暂停按钮 - 仅对 AI 消息显示 -->
        <el-button
          v-if="role === 'assistant' && isSpeaking"
          :icon="VideoPause"
          circle
          size="small"
          class="pause-btn"
          @click="handlePause"
          title="暂停语音"
        />
      </div>
      <div class="message-bubble">
        <!-- 用户消息保持原样；AI 消息拆分为简要 + 详情两部分 -->
        <div v-if="role === 'user'" class="message-text" v-html="formatMessage(content)"></div>
        <div v-else class="message-text ai-message-text">
          <div class="message-summary" v-html="summaryHtml"></div>
          <div v-if="hasDetail && showDetail" class="message-detail" v-html="detailHtml"></div>
          <button
            v-if="hasDetail"
            class="detail-toggle-btn"
            @click.stop="toggleDetail"
          >
            {{ showDetail ? '收起详情' : '查看详情' }}
          </button>
        </div>
      </div>
      <!-- 移除灰色来源标签，AI回复中已标注知识来源 -->
      <div class="message-actions">
        <span class="message-time">{{ formatTime(createdAt) }}</span>
        <button
          v-if="role === 'assistant'"
          class="message-speaker-btn"
          :class="{ 'is-speaking': isSpeaking }"
          @click.stop="handleSpeakerClick"
          title="语音播报"
        >
          <el-icon><component :is="isSpeaking ? 'VideoPause' : 'Microphone'" /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed, ref } from 'vue'
import { marked } from 'marked'
import { VideoPause, Microphone } from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'

const { stop } = useSpeech()

const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (value) => ['user', 'assistant'].includes(value)
  },
  content: {
    type: String,
    required: true
  },
  sources: {
    type: Object,
    default: null
  },
  createdAt: {
    type: String,
    default: null
  },
  isSpeaking: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['speak', 'pause'])

const showDetail = ref(false)

const handlePause = () => {
  stop()
  emit('pause')
}

const handleSpeakerClick = () => {
  if (props.isSpeaking) {
    stop()
    emit('pause')
  } else {
    emit('speak', props.content)
  }
}

const toggleDetail = () => {
  showDetail.value = !showDetail.value
}

// Configure marked for better rendering
marked.setOptions({
  breaks: true,  // Convert \n to <br>
  gfm: true,     // GitHub Flavored Markdown
  headerIds: false,
  mangle: false
})

function formatMessage(content) {
  if (!content) return ''

  try {
    return marked.parse(content)
  } catch (error) {
    console.error('Markdown parsing error:', error)
    return content.replace(/\n/g, '<br>')
  }
}

const messageParts = computed(() => {
  if (!props.content) return { summary: '', detail: '' }
  const parts = props.content.split(/\n\s*\n/)
  return {
    summary: parts[0] || '',
    detail: parts.slice(1).join('\n\n') || ''
  }
})

const summaryHtml = computed(() => formatMessage(messageParts.value.summary))
const detailHtml = computed(() => formatMessage(messageParts.value.detail))
const hasDetail = computed(() => messageParts.value.detail.trim().length > 0)

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
/* 1. 核心文本容器：禁用 pre-wrap 以免与 Markdown 的 <br> 冲突 */
 .message-text {
  line-height: 1.7 !important;
  letter-spacing: 0 !important;
  font-size: 18px;
  word-break: break-word;
  white-space: normal !important; /* 关键修复：让 HTML 标签控制换行 */
}

/* 2. 深度干预：彻底消除段落堆叠 */
.message-text :deep(p) {
  margin: 0 0 6px 0 !important; /* 统一控制下边距 */
  line-height: 1.5 !important;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0 !important;
}

/* 3. 列表紧凑化 */
.message-text :deep(ul), .message-text :deep(ol) {
  margin: 4px 0 !important;
  padding-left: 1.2rem !important;
}

.message-text :deep(li) {
  margin: 2px 0 !important;
  line-height: 1.5 !important;
}

/* 4. 气泡内边距修正 */
.message-bubble {
  padding: 12px 16px !important;
  border-radius: 16px;
  overflow-wrap: break-word;
}

/* === Component Layout === */
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px !important;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  background-color: #f0f0f0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.user-message .message-content-wrapper {
  align-items: flex-end;
}

.message-role {
  font-size: 14px;
  color: #666;
  margin-bottom: 6px !important;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.pause-btn {
  padding: 4px !important;
  width: 24px !important;
  height: 24px !important;
  min-height: 24px !important;
  background-color: #0c98d5 !important;
  border-color: #0c98d5 !important;
  color: white !important;
  transition: all 0.2s ease;
}

.pause-btn:hover {
  background-color: #0b86be !important;
  border-color: #0b86be !important;
  transform: scale(1.1);
}

.user-message .message-bubble {
  background-color: #0c98d5;
  color: white;
}

.assistant-message .message-bubble {
  background-color: #fff;
  color: #333;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* === Markdown Headers === */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  margin: 10px 0 6px 0 !important;
  font-weight: 600;
  color: inherit;
  line-height: 1.3 !important;
}

.message-text :deep(h1) { font-size: 1.3em; }
.message-text :deep(h2) { font-size: 1.2em; }
.message-text :deep(h3) { font-size: 1.1em; }

/* === Markdown Code === */
.message-text :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 5px !important;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.user-message .message-text :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
}

.message-text :deep(pre) {
  background-color: #f5f5f5;
  border-radius: 6px;
  padding: 8px 10px !important;
  overflow-x: auto;
  margin: 6px 0 !important;
}

.user-message .message-text :deep(pre) {
  background-color: rgba(255, 255, 255, 0.1);
}

.message-text :deep(pre code) {
  background-color: transparent !important;
  padding: 0 !important;
}

/* === Markdown Blockquote === */
.message-text :deep(blockquote) {
  border-left: 3px solid #ddd;
  padding-left: 10px !important;
  margin: 6px 0 !important;
  color: #666;
}

.user-message .message-text :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.4) !important;
  color: rgba(255, 255, 255, 0.9);
}

/* === Markdown Text Formatting === */
.message-text :deep(strong),
.message-text :deep(b) {
  font-weight: 600;
}

.message-text :deep(em),
.message-text :deep(i) {
  font-style: italic;
}

/* === Markdown Links === */
.message-text :deep(a) {
  color: #0c98d5;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

.user-message .message-text :deep(a) {
  color: #fff;
  text-decoration: underline;
}

/* === Markdown Tables === */
.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 6px 0 !important;
  font-size: 0.95em;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 10px !important;
  text-align: left;
}

.message-text :deep(th) {
  background-color: #f5f5f5;
  font-weight: 600;
}

.user-message .message-text :deep(th),
.user-message .message-text :deep(td) {
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.user-message .message-text :deep(th) {
  background-color: rgba(255, 255, 255, 0.1);
}

/* === Markdown Horizontal Rule === */
.message-text :deep(hr) {
  border: none;
  border-top: 1px solid #eee;
  margin: 8px 0 !important;
}

.user-message .message-text :deep(hr) {
  border-top-color: rgba(255, 255, 255, 0.2) !important;
}

/* === AI 消息：简要 / 详情折叠 === */
.message-summary {
  font-weight: 500;
}

.message-detail {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(0, 0, 0, 0.08);
}

.detail-toggle-btn {
  margin-top: 10px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--sn-primary);
  color: var(--sn-primary);
  border-radius: var(--sn-radius-md);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.detail-toggle-btn:hover {
  background: rgba(23, 114, 246, 0.06);
}

/* === Sources & Time === */
.message-sources {
  margin-top: 8px !important;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.source-tag {
  font-size: 13px;
  padding: 3px 8px !important;
  border-radius: 4px;
  font-weight: 500;
  background-color: #f5f5f5;
  color: #888;
  border: 1px solid #eee;
}

.message-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.message-time {
  font-size: 13px;
  color: #888;
  font-weight: 500;
}

.message-speaker-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid #E5E7EB;
  background: #FFF;
  color: #666;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.message-speaker-btn:hover {
  border-color: var(--sn-primary);
  color: var(--sn-primary);
}

.message-speaker-btn.is-speaking {
  background: var(--sn-primary);
  border-color: var(--sn-primary);
  color: #FFF;
}

/* === Streaming indicator === */
.chat-message.streaming .message-bubble {
  border-bottom-left-radius: 4px;
}

/* === Typing indicator === */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #ccc;
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}
</style>
