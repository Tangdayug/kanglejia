<template>
  <div class="sn-subpage intervention-page">
    
    <div class="sn-subpage-header">
      <div class="sn-subpage-header-inner">
        <button class="sn-back-btn" @click="goHome">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
      </div>
    </div>

    <div class="sn-subpage-body">
      <div class="sn-page-header">
        <div class="sn-page-header-main">
          <h1 class="sn-page-title">健康干预建议</h1>
          <div class="sn-page-header-meta">
            <span class="linear-count-badge">{{ interventionList.length }} 项待办建议</span>
          </div>
        </div>
        <div class="sn-page-header-actions header-actions">
          <button class="linear-btn-secondary" @click="loadInterventions">
            <el-icon><Refresh /></el-icon>
            刷新
          </button>
          <button class="linear-btn-primary" @click="openAIChat">
            <el-icon><ChatDotRound /></el-icon>
            咨询 AI 建议
          </button>
        </div>
      </div>

      <div v-loading="loading" class="linear-list-view">
        <el-empty v-if="!loading && interventionList.length === 0" description="暂无干预记录">
          <button class="linear-btn-primary" @click="goToChat">开始 AI 健康咨询</button>
        </el-empty>

        <div v-else class="linear-rows-container">
          <div class="linear-list-header">
            <div class="col-status">状态</div>
            <div class="col-main">建议内容</div>
            <div class="col-meta">属性</div>
          </div>

          <div
            v-for="log in interventionList"
            :key="log.id"
            class="linear-row"
            :class="{ 'is-completed': log.status === 'completed' }"
            @click="speakIntervention(log)"
          >
            <div class="row-status">
              <button
                class="status-trigger"
                @click.stop="toggleStatus(log)"
                :title="log.status === 'completed' ? '重置为待办' : '标记为已完成'"
              >
                <div class="status-circle" :class="log.status">
                  <el-icon v-if="log.status === 'completed'" class="check-icon"><Check /></el-icon>
                </div>
              </button>
            </div>

            <div class="row-main">
              <div class="row-content">{{ log.content }}</div>
              <div class="row-sub-meta">
                <span class="issue-id">LOG-{{ String(log.id).padStart(4, '0') }}</span>
                <span class="issue-source">{{ log.source === 'ai' ? 'AI 智能引擎' : '专业医生' }}</span>
              </div>
            </div>

            <div class="row-meta">
              <span class="linear-label" :class="log.type">{{ getTypeLabel(log.type) }}</span>
              <span class="row-date">{{ formatDate(log.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ChatDotRound, ArrowLeft, Check } from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'
import { getInterventions, updateInterventionStatus } from '@/api/intervention' //

const router = useRouter()
const { speak, stop, speakPageTitle, isEnabled: speechEnabled } = useSpeech()

const loading = ref(false)
const interventionList = ref([])

function goHome() { router.push('/home') }
function goToChat() { router.push('/chat-ai') }
function openAIChat() { router.push('/chat-ai') }

// 语音播报逻辑
function speakIntervention(log) {
  if (!speechEnabled.value) return
  stop()
  const date = formatDate(log.created_at)
  const statusText = log.status === 'completed' ? '已完成' : '待办'
  const text = `${date}的健康建议，当前状态${statusText}。${log.content}`
  speak(text)
}

onMounted(() => {
  speakPageTitle('干预日志')
  loadInterventions()
})

onUnmounted(() => { stop() })

// 加载历史干预记录 - 保持严格的内容显示逻辑
async function loadInterventions() {
  loading.value = true
  try {
    const res = await getInterventions() //
    if (String(res.code) !== '200') throw new Error(res.msg || '加载失败')

    // 数据清洗与字段兼容：确保 suggestion 显示在 content 位置
    interventionList.value = (res.data.interventions || []).map(item => ({
      id: item.id,
      content: item.suggestion || '暂无具体建议内容',
      type: item.type || 'general',
      source: item.source || 'ai',
      status: item.status || 'pending',
      created_at: item.createdAt || item.created_at
    }))
  } catch (err) {
    console.error('加载干预日志失败:', err)
    ElMessage.error('数据同步失败，请检查网络')
  } finally {
    loading.value = false
  }
}

// 切换待办状态功能 - 修复参数名与乐观更新逻辑
async function toggleStatus(log) {
  const oldStatus = log.status
  const newStatus = oldStatus === 'completed' ? 'pending' : 'completed'

  // UI 优先更新（乐观更新），让圆圈立即变色
  log.status = newStatus

  try {
    // 调用项目定义的 updateInterventionStatus，参数名为 interventionId
    const res = await updateInterventionStatus({ 
      interventionId: log.id, 
      status: newStatus 
    })

    if (String(res.code) !== '200') {
      throw new Error('API Update Failed')
    }

    if (newStatus === 'completed') {
      ElMessage.success('已标记建议为达成')
    }
  } catch (err) {
    // 失败则回滚状态
    log.status = oldStatus
    ElMessage.error('更新状态失败')
  }
}

// 工具函数：类型标签转换
function getTypeLabel(type) {
  const map = { exercise: '运动', diet: '饮食', sleep: '睡眠', mental: '心理', general: '综合' }
  return map[type] || '综合'
}

// 工具函数：日期格式化
function formatDate(dateStr) {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<style scoped>
/* =========================================
Linear 设计系统：核心样式
========================================= */
.sn-subpage {
  background-color: var(--sn-slate-light);
  color: var(--sn-text);
}



.linear-count-badge {
  background: var(--sn-border); color: var(--sn-text-secondary);
  padding: 4px 10px; border-radius: var(--sn-radius-sm); font-size: 13px; font-weight: 600;
}

.header-actions { display: flex; gap: 12px; }
.linear-btn-primary, .linear-btn-secondary {
  height: 36px; padding: 0 16px; border-radius: var(--sn-radius-sm);
  font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;
  cursor: pointer; transition: all 0.2s; border: 1px solid transparent;
}
.linear-btn-primary {
  background: transparent;
  color: var(--sn-primary);
  border-color: var(--sn-primary);
  box-shadow: none;
}
.linear-btn-primary:hover { background: rgba(10, 127, 206, 0.06); }
.linear-btn-secondary {
  background: var(--sn-surface); color: var(--sn-text-secondary);
  border-color: var(--sn-border); box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.linear-btn-secondary:hover { background: var(--sn-slate-light); border-color: var(--sn-border); }

.linear-list-view {
  background: var(--sn-surface);
  border: 1px solid var(--sn-border);
  border-radius: var(--sn-radius-md);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  overflow: hidden;
}

.linear-list-header {
  display: flex; align-items: center;
  padding: 12px 20px;
  background: var(--sn-surface);
  border-bottom: 1px solid var(--sn-border);
  font-size: 12px; font-weight: 600; color: var(--sn-text-muted);
}
.col-status { width: 44px; }
.col-main { flex: 1; padding-right: 24px; }
.col-meta { width: 140px; display: flex; justify-content: flex-end; gap: 16px; }

.linear-row {
  display: flex; align-items: flex-start;
  padding: 16px 20px;
  border-bottom: 1px solid var(--sn-border);
  background: var(--sn-surface);
  transition: background-color 0.15s ease;
  cursor: pointer;
}
.linear-row:last-child { border-bottom: none; }
.linear-row:hover { background: var(--sn-slate-light); }

/* 勾选圆圈热区 - 修复交互无效的核心 CSS */
.status-trigger {
  background: transparent;
  border: none;
  padding: 2px 8px 2px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.status-circle {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1.5px solid var(--sn-border);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  pointer-events: none; /* 确保点击事件落在父级 trigger 上 */
}

.status-trigger:hover .status-circle:not(.completed) {
  border-color: var(--sn-primary);
  background: rgba(10, 127, 206, 0.05);
}

.status-circle.completed {
  background: var(--sn-primary);
  border-color: var(--sn-primary);
  color: var(--sn-surface);
}

.check-icon { font-size: 11px; font-weight: bold; }

.row-main { flex: 1; padding-right: 24px; display: flex; flex-direction: column; gap: 6px; }
.row-content {
  font-size: 14px; font-weight: 500; color: var(--sn-text); line-height: 1.5;
  transition: color 0.2s;
}
.linear-row.is-completed .row-content {
  color: var(--sn-text-muted); text-decoration: line-through;
}

.row-sub-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; font-weight: 500; color: var(--sn-text-muted); }
.issue-id { font-family: monospace; letter-spacing: 0.5px; }

.row-meta {
  width: 140px; display: flex; align-items: center; justify-content: flex-end; gap: 16px;
  padding-top: 2px;
}
.linear-label {
  padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;
  border: 1px solid var(--sn-border); background: var(--sn-surface); color: var(--sn-text-secondary);
}
.linear-label.exercise { color: var(--sn-primary); border-color: var(--sn-primary-light); background: var(--sn-primary-soft); }
.linear-label.diet { color: var(--sn-success); border-color: var(--sn-success-light); background: var(--sn-success-light); }
.row-date { font-size: 13px; color: var(--sn-text-muted); font-weight: 500; min-width: 45px; text-align: right; }

/* 老年人模式适配 */
html[data-accessibility="elderly"] .sn-page-title { font-size: 36px; }
html[data-accessibility="elderly"] .row-content { font-size: 20px; }
html[data-accessibility="elderly"] .linear-btn-primary, html[data-accessibility="elderly"] .linear-btn-secondary { height: 48px; font-size: 16px; padding: 0 24px;}
html[data-accessibility="elderly"] .status-circle { width: 24px; height: 24px; }
</style>