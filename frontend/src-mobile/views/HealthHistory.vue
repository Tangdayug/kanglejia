<template>
  <div class="mobile-health-history page-padding">
    <div class="page-header">
      <a-button type="text" class="back-btn" @click="goBack">
        <left-outlined /> 返回
      </a-button>
      <h1 class="page-title">健康历史</h1>
      <a-button type="primary" size="small" @click="loadHistory">刷新</a-button>
    </div>

    <a-empty v-if="!loading && historyList.length === 0" description="暂无历史数据">
      <a-button type="primary" @click="goToTest">开启首次测试</a-button>
    </a-empty>

    <div v-else class="history-list">
      <div
        v-for="item in historyList"
        :key="item.id"
        class="history-card"
        @click="viewDetail(item)"
      >
        <div class="card-header">
          <span class="test-date">{{ formatDate(item.created_at) }}</span>
          <a-tag :color="getRiskColor(item.risk_level)">{{ getRiskLabel(item.risk_level) }}</a-tag>
        </div>
        <div class="score-row">
          <div class="total-score" :style="{ color: getScoreColor(item.score_total) }">
            {{ item.score_total }}
            <span>综合分</span>
          </div>
          <div class="sub-scores">
            <div class="sub-item">
              <span>认知</span>
              <strong :style="{ color: getProgressColor(item.score_cognitive) }">{{ item.score_cognitive }}</strong>
            </div>
            <div class="sub-item">
              <span>运动</span>
              <strong :style="{ color: getProgressColor(item.score_motor) }">{{ item.score_motor }}</strong>
            </div>
            <div class="sub-item">
              <span>活力</span>
              <strong :style="{ color: getProgressColor(item.score_vitality) }">{{ item.score_vitality }}</strong>
            </div>
            <div class="sub-item">
              <span>视力</span>
              <strong :style="{ color: getProgressColor(item.score_vision) }">{{ item.score_vision }}</strong>
            </div>
            <div class="sub-item">
              <span>听力</span>
              <strong :style="{ color: getProgressColor(item.score_hearing) }">{{ item.score_hearing }}</strong>
            </div>
            <div class="sub-item">
              <span>心理</span>
              <strong :style="{ color: getProgressColor(item.score_psychological) }">{{ item.score_psychological }}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>

    <a-button v-if="historyList.length > 0" type="primary" block size="large" class="analyze-btn" @click="analyzeHistory">
      AI 深度分析
    </a-button>

    <a-modal v-model:open="detailVisible" title="测试详情" width="100%" :footer="null">
      <div v-if="selectedDetail" class="detail-content">
        <div class="detail-summary">
          <span>{{ formatDate(selectedDetail.created_at) }}</span>
          <a-tag :color="getRiskColor(selectedDetail.risk_level)">{{ getRiskLabel(selectedDetail.risk_level) }}</a-tag>
        </div>
        <div class="detail-grid">
          <div
            v-for="dim in dimensionRows"
            :key="dim.key"
            class="detail-dim"
            :class="{ alert: selectedDetail.risks?.[dim.key] }"
          >
            <span>{{ dim.label }}</span>
            <strong>{{ selectedDetail.scores?.[dim.key] || 0 }}</strong>
            <em>{{ selectedDetail.risks?.[dim.key] ? '风险' : '正常' }}</em>
          </div>
        </div>
        <div v-if="selectedDetail.recommendations" class="detail-recs">
          <h4>个性化建议</h4>
          <div
            v-for="dim in dimensionRowsWithOverall"
            :key="dim.key"
            v-show="selectedDetail.recommendations?.[dim.key]?.length"
            class="rec-block"
          >
            <h5>{{ dim.label }}</h5>
            <ul>
              <li v-for="(rec, idx) in selectedDetail.recommendations[dim.key]" :key="idx">{{ rec }}</li>
            </ul>
          </div>
        </div>
      </div>
    </a-modal>

    <a-modal v-model:open="analysisVisible" title="AI 趋势洞察" :footer="null">
      <div v-if="analyzing" class="analysis-loading">
        <a-spin tip="正在生成深度洞察..." />
      </div>
      <div v-else-if="analysisResult" class="analysis-result" v-html="formatAnalysis(analysisResult)"></div>
      <a-empty v-else description="暂无分析结果" />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { LeftOutlined } from '@ant-design/icons-vue'
import { useSpeech } from '@shared/composables/useSpeech'
import request from '@shared/utils/request'
import {
  cleanAnalysisMarkdown,
  formatAnalysisHtml,
  formatTrendDate,
  riskLevelFromRisks
} from '@shared/utils/healthTrendFormat.mjs'

const router = useRouter()
const { speak, stop, speakPageTitle } = useSpeech()

function goBack() {
  router.back()
}

const loading = ref(false)
const historyList = ref([])
const detailVisible = ref(false)
const selectedDetail = ref(null)
const analysisVisible = ref(false)
const analyzing = ref(false)
const analysisResult = ref('')

const dimensionRows = [
  { key: 'cognitive', label: '认知能力' },
  { key: 'motor', label: '运动能力' },
  { key: 'vitality', label: '活力状态' },
  { key: 'vision', label: '视力' },
  { key: 'hearing', label: '听力' },
  { key: 'psychological', label: '心理状态' }
]
const dimensionRowsWithOverall = [...dimensionRows, { key: 'overall', label: '总体指导' }]

onMounted(() => {
  speakPageTitle('健康历史')
  loadHistory()
})
onUnmounted(() => stop())

function goToTest() { router.push('/test') }

async function loadHistory() {
  loading.value = true
  try {
    const listRes = await request.get('/health-test/list')
    if (listRes.code !== '200') throw new Error(listRes.msg || '加载失败')

    const tests = listRes.data?.tests || []
    if (tests.length > 0) {
      const detailPromises = tests.map(test => request.get(`/health-test/${test.id}`))
      const detailResults = await Promise.all(detailPromises)

      historyList.value = detailResults.map(res => {
        if (res.code === '200') {
          const data = res.data
          const risks = {
            cognitive: data.risks?.cognitive || false,
            motor: data.risks?.motor || false,
            vitality: data.risks?.vitality || false,
            vision: data.risks?.vision || false,
            hearing: data.risks?.hearing || false,
            psychological: data.risks?.psychological || false
          }
          const scores = {
            total: data.scores?.total || 0,
            cognitive: data.scores?.cognitive || 0,
            motor: data.scores?.motor || 0,
            vitality: data.scores?.vitality || 0,
            vision: data.scores?.vision || 0,
            hearing: data.scores?.hearing || 0,
            psychological: data.scores?.psychological || 0
          }
          return {
            id: data.id,
            scores,
            risks,
            recommendations: data.recommendations,
            score_total: scores.total,
            score_cognitive: scores.cognitive,
            score_motor: scores.motor,
            score_vitality: scores.vitality,
            score_vision: scores.vision,
            score_hearing: scores.hearing,
            score_psychological: scores.psychological,
            created_at: data.createdAt,
            risk_level: riskLevelFromRisks(risks)
          }
        }
        return null
      }).filter(Boolean)
    } else {
      historyList.value = []
    }
  } catch (err) {
    message.error('加载失败: ' + (err.response?.data?.msg || err.message))
  } finally {
    loading.value = false
  }
}

function viewDetail(item) {
  selectedDetail.value = item
  detailVisible.value = true
}

function analyzeHistory() {
  if (historyList.value.length === 0) {
    message.warning('暂无历史数据可分析')
    return
  }
  analysisVisible.value = true
  analyzing.value = true
  analysisResult.value = ''

  const summary = historyList.value.map(item => ({
    date: formatDate(item.created_at),
    totalScore: item.score_total,
    riskLevel: item.risk_level,
    cognitive: item.score_cognitive,
    motor: item.score_motor,
    vitality: item.score_vitality
  }))

  request.post('/chat/analyze-health-history', { history: summary }).then(res => {
    if (res.code === '200') analysisResult.value = cleanAnalysisMarkdown(res.data.analysis)
    else message.error(res.msg || '分析失败')
  }).catch(() => message.error('分析失败')).finally(() => { analyzing.value = false })
}

function formatAnalysis(text) { return formatAnalysisHtml(text) }
function formatDate(dateStr) { return formatTrendDate(dateStr) }

function getScoreColor(score) {
  if (score === 0) return '#52c41a'
  if (score <= 2) return '#faad14'
  return '#ff4d4f'
}

function getProgressColor(score) {
  if (score === 0) return '#52c41a'
  if (score === 1) return '#faad14'
  return '#ff4d4f'
}

function getRiskColor(level) {
  const map = { low: 'green', medium: 'orange', high: 'red' }
  return map[level] || 'default'
}

function getRiskLabel(level) {
  const map = { low: '低风险', medium: '中度风险', high: '高风险' }
  return map[level] || '未知'
}
</script>

<style scoped>
.mobile-health-history {
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.test-date {
  font-size: 16px;
  font-weight: 700;
  color: #111;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.total-score {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 900;
  flex-shrink: 0;
}

.total-score span {
  font-size: 12px;
  font-weight: 600;
  color: #666;
}

.sub-scores {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.sub-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fafafa;
  border-radius: 10px;
  padding: 8px;
}

.sub-item span {
  font-size: 12px;
  color: #666;
}

.sub-item strong {
  font-size: 20px;
  font-weight: 800;
}

.analyze-btn {
  margin-top: 16px;
  min-height: 52px;
  font-size: 18px;
  border-radius: 12px;
}

.detail-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.detail-dim {
  background: #fafafa;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}

.detail-dim.alert {
  background: #fff2f0;
}

.detail-dim span {
  font-size: 13px;
  color: #666;
}

.detail-dim strong {
  display: block;
  font-size: 24px;
  font-weight: 800;
  margin: 4px 0;
}

.detail-dim em {
  font-size: 12px;
  color: #999;
  font-style: normal;
}

.detail-recs h4 {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 12px 0;
}

.rec-block {
  margin-bottom: 12px;
}

.rec-block h5 {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 6px 0;
}

.rec-block ul {
  margin: 0;
  padding-left: 18px;
  color: #444;
  line-height: 1.7;
}

.analysis-loading {
  padding: 40px;
  text-align: center;
}

.analysis-result {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 16px;
  line-height: 1.8;
}
</style>
