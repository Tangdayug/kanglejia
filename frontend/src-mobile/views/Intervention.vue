<template>
  <div class="mobile-intervention page-padding">
    <div class="page-header">
      <a-button type="text" class="back-btn" @click="goBack">
        <left-outlined /> 返回
      </a-button>
      <h1 class="page-title">今日建议</h1>
      <a-button type="primary" size="small" @click="loadInterventions">刷新</a-button>
    </div>

    <a-empty v-if="!loading && interventionList.length === 0" description="暂无干预记录">
      <a-button type="primary" @click="goToChat">咨询 AI 建议</a-button>
    </a-empty>

    <div v-else class="intervention-list">
      <div
        v-for="log in interventionList"
        :key="log.id"
        class="intervention-card"
        :class="{ completed: log.status === 'completed' }"
      >
        <div class="card-main" @click="speakIntervention(log)">
          <div class="status-toggle" @click.stop="toggleStatus(log)">
            <check-circle-filled v-if="log.status === 'completed'" class="checked-icon" />
            <div v-else class="unchecked-circle"></div>
          </div>
          <div class="card-content">
            <p class="content-text">{{ log.content }}</p>
            <div class="card-meta">
              <a-tag :color="getTypeColor(log.type)">{{ getTypeLabel(log.type) }}</a-tag>
              <span class="date">{{ formatDate(log.created_at) }}</span>
            </div>
          </div>
        </div>
        <div v-if="log.status === 'completed'" class="feedback-area">
          <a-textarea
            v-model:value="log.feedback"
            placeholder="完成情况如何？（可选）"
            :rows="2"
            class="feedback-input"
          />
          <a-button type="primary" size="small" @click="submitFeedback(log)">提交反馈</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { CheckCircleFilled, LeftOutlined } from '@ant-design/icons-vue'
import { useSpeech } from '@shared/composables/useSpeech'
import { getInterventions, updateInterventionStatus, addInterventionFeedback } from '@shared/api/intervention'

const router = useRouter()
const { speak, stop, speakPageTitle, isEnabled: speechEnabled } = useSpeech()

function goBack() {
  router.back()
}

const loading = ref(false)
const interventionList = ref([])

onMounted(() => {
  speakPageTitle('今日建议')
  loadInterventions()
})
onUnmounted(() => stop())

function goToChat() { router.push('/chat-ai') }

function speakIntervention(log) {
  if (!speechEnabled.value) return
  stop()
  const statusText = log.status === 'completed' ? '已完成' : '待办'
  speak(`${formatDate(log.created_at)}的健康建议，当前状态${statusText}。${log.content}`)
}

async function loadInterventions() {
  loading.value = true
  try {
    const res = await getInterventions()
    if (String(res.code) !== '200') throw new Error(res.msg || '加载失败')
    interventionList.value = (res.data.interventions || []).map(item => ({
      id: item.id,
      content: item.suggestion || '暂无具体建议内容',
      type: item.type || 'general',
      source: item.source || 'ai',
      status: item.status || 'pending',
      created_at: item.createdAt || item.created_at,
      feedback: ''
    }))
  } catch (err) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function toggleStatus(log) {
  const oldStatus = log.status
  const newStatus = oldStatus === 'completed' ? 'pending' : 'completed'
  log.status = newStatus
  try {
    const res = await updateInterventionStatus({ interventionId: log.id, status: newStatus })
    if (String(res.code) !== '200') throw new Error('API Update Failed')
    if (newStatus === 'completed') message.success('已标记为已完成')
  } catch (err) {
    log.status = oldStatus
    message.error('更新状态失败')
  }
}

async function submitFeedback(log) {
  try {
    await addInterventionFeedback({
      interventionId: log.id,
      feedback: log.feedback,
      executed: true,
      effectiveness: 'good'
    })
    message.success('反馈已提交')
    log.feedback = ''
  } catch (err) {
    message.error('提交反馈失败')
  }
}

function getTypeLabel(type) {
  const map = { exercise: '运动', diet: '饮食', sleep: '睡眠', mental: '心理', general: '综合' }
  return map[type] || '综合'
}

function getTypeColor(type) {
  const map = { exercise: 'blue', diet: 'green', sleep: 'purple', mental: 'orange', general: 'default' }
  return map[type] || 'default'
}

function formatDate(dateStr) {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<style scoped>
.mobile-intervention {
  padding-bottom: 100px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.page-title {
  flex: 1;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}

.back-btn {
  padding: 0;
  font-size: 17px;
  color: #666;
}

.intervention-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.intervention-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
}

.intervention-card.completed {
  background: #f6ffed;
}

.card-main {
  display: flex;
  gap: 12px;
}

.status-toggle {
  flex-shrink: 0;
  padding-top: 2px;
}

.checked-icon {
  font-size: 24px;
  color: #52c41a;
}

.unchecked-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid #d9d9d9;
}

.card-content {
  flex: 1;
}

.content-text {
  margin: 0 0 10px 0;
  font-size: 16px;
  line-height: 1.6;
  color: #111;
}

.intervention-card.completed .content-text {
  text-decoration: line-through;
  color: #999;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date {
  font-size: 13px;
  color: #999;
}

.feedback-area {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feedback-input {
  font-size: 15px;
}
</style>
