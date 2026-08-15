<template>
  <div class="cgpt-sidebar">
    <div class="sidebar-header">
      <button class="new-chat-btn" @click="handleNewChat">
        <el-icon><Plus /></el-icon>
        <span>新对话</span>
      </button>
    </div>

    <div class="sidebar-content">
      <div v-if="loading" class="sidebar-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="sessions.length === 0" class="sidebar-empty">
        <span class="empty-text">暂无历史对话</span>
      </div>

      <div v-else class="session-list">
        <div class="list-title">历史记录</div>
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === currentSessionId }]"
          @click="handleSelectSession(session)"
        >
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ formatSessionTime(session.updatedAt) }}</div>
          </div>
          <button
            class="delete-button"
            title="删除对话"
            @click.stop="handleDeleteSession(session.id)"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// ---- 逻辑代码 100% 保持不变 ----
import { ref, onMounted, computed } from 'vue'
import { Plus, Delete, Loading } from '@element-plus/icons-vue'
import { getSessions, deleteSession } from '@/api/chatAI'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  currentSessionId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['select-session', 'new-chat'])

const sessions = ref([])
const loading = ref(false)

async function loadSessions() {
  loading.value = true
  try {
    const res = await getSessions()
    sessions.value = res.data.sessions || []
  } catch (error) {
    console.error('Failed to load sessions:', error)
    ElMessage.error('加载对话列表失败')
  } finally {
    loading.value = false
  }
}

function handleNewChat() { emit('new-chat') }
function handleSelectSession(session) { emit('select-session', session) }

async function handleDeleteSession(sessionId) {
  try {
    await ElMessageBox.confirm(
  '删除后将无法找回，确定要删除这个对话吗？',
  '删除对话', // 标题已修改
  {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    customClass: 'modern-confirm-dialog danger-action', // 🌟 必须加上这个类名
    center: true,
    showClose: false
  }
)
    await deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (props.currentSessionId === sessionId) { emit('new-chat') }
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') { console.error('Failed to delete session:', error); ElMessage.error('删除失败') }
  }
}

function formatSessionTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return `今天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (diff < 172800000 && date.getDate() === yesterday.getDate()) {
    return `昨天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

onMounted(() => { loadSessions() })
defineExpose({ reload: loadSessions })
</script>

<style scoped>
/* ChatGPT 极简侧边栏样式 */
.cgpt-sidebar {
  width: 260px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #F9F9F9; /* 融入整体环境，不设硬边框 */
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
}

.sidebar-header {
  padding: 16px 12px 12px 12px;
}

/* 新对话按钮：浅色填充 + 品牌色文字/描边 */
.new-chat-btn {
  width: 100%;
  height: 48px;
  background-color: var(--sn-primary-light);
  border: 1px solid var(--sn-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--sn-primary);
  cursor: pointer;
  transition: all 0.2s;
}
.new-chat-btn:hover {
  background-color: var(--sn-primary-soft);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}
/* 隐藏滚动条但保留功能 */
.sidebar-content::-webkit-scrollbar { width: 0px; }

.sidebar-loading, .sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #999;
  font-size: 13px;
  font-weight: 500;
}

.list-title {
  font-size: 13px;
  font-weight: 800;
  color: #666;
  padding: 8px 8px 10px 8px;
  letter-spacing: 0.5px;
}

/* 胶囊状会话项 */
.session-item {
  padding: 14px;
  border-radius: 14px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  transition: all 0.2s;
  border: 1px solid transparent;
  background-color: #FFFFFF;
}
.session-item:hover {
  background-color: #F0F0F0;
}
.session-item.active {
  background-color: #EFF6FF;
  border-color: #2563EB;
  box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}

.session-info {
  flex: 1;
  overflow: hidden;
}
.session-title {
  font-size: 15px;
  font-weight: 700;
  color: #111;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-time {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.delete-button {
  background: transparent;
  border: none;
  color: #999;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
}
.session-item:hover .delete-button {
  opacity: 1;
}
.delete-button:hover {
  background-color: #FFEBEB;
  color: #FF4D4F;
}

html[data-accessibility="elderly"] .new-chat-btn { height: 60px; font-size: 20px; }
html[data-accessibility="elderly"] .session-title { font-size: 20px; }
html[data-accessibility="elderly"] .session-time { font-size: 16px; }
html[data-accessibility="elderly"] .list-title { font-size: 16px; }
</style>