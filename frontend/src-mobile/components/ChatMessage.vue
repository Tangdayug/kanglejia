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
        src="@shared/assets/imgs/logo2.png"
        alt="AI助手"
      />
    </div>
    <div class="message-content-wrapper">
      <div class="message-role">
        {{ role === 'user' ? '我' : 'AI健康助手' }}
      </div>
      <div class="message-bubble">
        <div class="message-text" v-html="formatMessage(content)"></div>
      </div>
      <div class="message-time">{{ formatTime(createdAt) }}</div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, required: true },
  sources: { type: Object, default: null },
  createdAt: { type: String, default: null }
})

marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false
})

function formatMessage(content) {
  if (!content) return ''
  try {
    return marked.parse(content)
  } catch (error) {
    return content.replace(/\n/g, '<br>')
  }
}

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
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f0f0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 78%;
}

.user-message .message-content-wrapper {
  align-items: flex-end;
}

.message-role {
  font-size: 14px;
  color: #888;
  margin-bottom: 5px;
  font-weight: 700;
}

.message-bubble {
  padding: 14px 16px;
  border-radius: 18px;
  overflow-wrap: break-word;
  word-break: break-word;
}

.user-message .message-bubble {
  background: #1890ff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant-message .message-bubble {
  background: #fff;
  color: #222;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.message-text {
  font-size: 18px;
  line-height: 1.7;
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(ul), .message-text :deep(ol) {
  margin: 6px 0;
  padding-left: 1.4rem;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-time {
  font-size: 13px;
  color: #999;
  margin-top: 5px;
}

.user-message .message-time {
  text-align: right;
}
</style>
