<template>
  <div class="sn-subpage history-page">
    
    <div class="sn-subpage-header">
      <div class="sn-subpage-header-inner">
        <button class="sn-back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
      </div>
    </div>

    <div class="sn-subpage-body">
      <div class="sn-page-header">
        <div class="sn-page-header-main">
          <h1 class="sn-page-title">健康评估日志</h1>
          <p class="sn-page-subtitle">追踪您的内在能力变化趋势</p>
        </div>
        <div class="sn-page-header-actions header-actions">
          <button class="whoop-btn-secondary" @click="loadHistory">
            <el-icon><Refresh /></el-icon> 刷新
          </button>
          <button class="whoop-btn-primary" @click="analyzeHistory">
            <el-icon><Search /></el-icon> AI 深度分析
          </button>
        </div>
      </div>

      <div v-loading="loading" class="whoop-feed">
        <el-empty v-if="!loading && historyList.length === 0" description="暂无历史数据" class="empty-state">
          <button class="whoop-btn-primary" @click="goToTest">开启首次测试</button>
        </el-empty>

        <div v-else class="whoop-card-list">
          <div
            v-for="(item, index) in historyList"
            :key="item.id"
            class="whoop-data-card"
            @click="speakHistoryItem(item)"
          >
            <div class="card-meta">
              <span class="meta-date">{{ formatDate(item.created_at) }}</span>
              <div class="risk-badge" :class="`risk-${item.risk_level}`">
                {{ getRiskLabel(item.risk_level) }}
              </div>
            </div>

            <div class="card-body">
              
              <div class="hero-metric">
                <div class="score-circle" :style="{ borderColor: getScoreColor(item.score_total) }">
                  <div class="score-value" :style="{ color: getScoreColor(item.score_total) }">
                    {{ item.score_total }}
                  </div>
                  <div class="score-label">综合得分</div>
                </div>
              </div>

              <div class="sub-metrics-grid">
                <div class="metric-pill">
                  <span class="m-name">认知</span>
                  <span class="m-val" :style="{ color: getProgressColor(item.score_cognitive) }">{{ item.score_cognitive }}</span>
                </div>
                <div class="metric-pill">
                  <span class="m-name">运动</span>
                  <span class="m-val" :style="{ color: getProgressColor(item.score_motor) }">{{ item.score_motor }}</span>
                </div>
                <div class="metric-pill">
                  <span class="m-name">活力</span>
                  <span class="m-val" :style="{ color: getProgressColor(item.score_vitality) }">{{ item.score_vitality }}</span>
                </div>
                <div class="metric-pill">
                  <span class="m-name">视觉</span>
                  <span class="m-val" :style="{ color: getProgressColor(item.score_vision) }">{{ item.score_vision }}</span>
                </div>
                <div class="metric-pill">
                  <span class="m-name">听力</span>
                  <span class="m-val" :style="{ color: getProgressColor(item.score_hearing) }">{{ item.score_hearing }}</span>
                </div>
                <div class="metric-pill">
                  <span class="m-name">心理</span>
                  <span class="m-val" :style="{ color: getProgressColor(item.score_psychological) }">{{ item.score_psychological }}</span>
                </div>
              </div>

            </div>

            <div class="card-footer">
              <div class="test-index">TEST ID: {{ item.id }}</div>
              <button class="detail-link" @click.stop="viewDetail(item)">查看完整报告 <span class="arrow">&rarr;</span></button>
            </div>
          </div>
        </div>
      </div>

      <el-dialog
        v-model="analysisVisible"
        title="AI 趋势洞察 (Insights)"
        width="800px"
        class="whoop-insight-dialog"
        :close-on-click-modal="false"
        @opened="speakAnalysisResult"
      >
        <div v-loading="analyzing" class="insight-content">
          <div v-if="analysisResult" class="insight-result">
            <div class="insight-text" v-html="formatAnalysis(analysisResult)"></div>
          </div>
          <el-empty v-else-if="!analyzing" description="正在生成深度洞察..." />
        </div>
        <template #footer>
          <div class="insight-actions">
            <button class="whoop-btn-text" @click="analysisVisible = false">关闭</button>
            <div class="right-group">
              <button class="whoop-btn-secondary" @click="speakAnalysisResult" v-if="analysisResult && speechEnabled">
                <el-icon><Microphone /></el-icon> 播报
              </button>
              <button class="whoop-btn-primary" @click="copyAnalysis" v-if="analysisResult">
                复制洞察报告
              </button>
            </div>
          </div>
        </template>
      </el-dialog>

      <el-dialog
        v-model="detailVisible"
        title="健康测试完整报告"
        width="860px"
        class="whoop-detail-dialog"
      >
        <div v-if="selectedDetail" class="detail-content">
          <div class="detail-summary">
            <div>
              <div class="detail-date">{{ formatDate(selectedDetail.created_at) }}</div>
              <div class="detail-risk" :class="`risk-${selectedDetail.risk_level}`">
                {{ getRiskLabel(selectedDetail.risk_level) }}
              </div>
            </div>
            <div class="detail-score">
              <strong>{{ selectedDetail.score_total }}</strong>
              <span>综合得分</span>
            </div>
          </div>

          <div class="detail-grid">
            <div
              v-for="dim in dimensionRows"
              :key="dim.key"
              class="detail-dim"
              :class="{ alert: selectedDetail.risks?.[dim.key] }"
            >
              <span>{{ dim.label }}</span>
              <strong>{{ selectedDetail.scores?.[dim.key] || 0 }} 分</strong>
              <em>{{ selectedDetail.risks?.[dim.key] ? '存在风险' : '正常' }}</em>
            </div>
          </div>

          <div v-if="selectedDetail.recommendations" class="detail-recommendations">
            <h3>个性化建议</h3>
            <div
              v-for="dim in dimensionRowsWithOverall"
              :key="dim.key"
              class="detail-rec-group"
              v-show="selectedDetail.recommendations?.[dim.key]?.length"
            >
              <h4>{{ dim.label }}</h4>
              <ul>
                <li v-for="(rec, idx) in selectedDetail.recommendations[dim.key]" :key="idx">{{ rec }}</li>
              </ul>
            </div>
          </div>
        </div>
      </el-dialog>

    </div>
  </div>
</template>

<script setup>
// ---- 所有逻辑代码 100% 保持原样，没有任何删减 ----
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock, Refresh, Search, Microphone, ArrowLeft } from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'
import request from '@/utils/request'
import {
  cleanAnalysisMarkdown,
  formatAnalysisHtml,
  formatTrendDate,
  riskLevelFromRisks
} from '@/utils/healthTrendFormat.mjs'

const router = useRouter()
const { speak, stop, speakPageTitle, isEnabled: speechEnabled } = useSpeech()

const loading = ref(false)

// 播报历史记录详情
function speakHistoryItem(item) {
  if (!speechEnabled.value) return
  stop()

  const date = formatDate(item.created_at)
  const riskLabel = getRiskLabel(item.risk_level)

  const text = `${date}的健康测试。综合得分${item.score_total}分，风险等级${riskLabel}。` +
    `认知能力${item.score_cognitive}分，` +
    `运动能力${item.score_motor}分，` +
    `活力水平${item.score_vitality}分，` +
    `视觉能力${item.score_vision}分，` +
    `听力能力${item.score_hearing}分，` +
    `心理状态${item.score_psychological}分。`

  speak(text)
}

// 播报AI分析结果
function speakAnalysisResult() {
  if (!speechEnabled.value || !analysisResult.value) return

  const plainText = analysisResult.value
    .replace(/#{1,6}\s+/g, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/\n/g, '，')
    .trim()

  if (plainText) {
    speak(plainText)
  }
}
const historyList = ref([])
const analysisVisible = ref(false)
const analyzing = ref(false)
const analysisResult = ref('')
const detailVisible = ref(false)
const selectedDetail = ref(null)
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
  speakPageTitle('历史评估记录')
  loadHistory()
})

onUnmounted(() => { stop() })

function goBack() { router.push('/home') }
function goToTest() { router.push('/test') }

// 加载历史记录
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
            answers: data.answers,
            score_total: scores.total,
            score_cognitive: scores.cognitive,
            score_motor: scores.motor,
            score_vitality: scores.vitality,
            score_vision: scores.vision,
            score_hearing: scores.hearing,
            score_psychological: scores.psychological,
            risk_cognitive: risks.cognitive,
            risk_motor: risks.motor,
            risk_vitality: risks.vitality,
            risk_vision: risks.vision,
            risk_hearing: risks.hearing,
            risk_psychological: risks.psychological,
            created_at: data.createdAt,
            updated_at: data.updatedAt
          }
        }
        return null
      }).filter(Boolean)

      historyList.value = historyList.value.map(test => {
        return { ...test, risk_level: riskLevelFromRisks(test.risks) }
      })
    } else {
      historyList.value = []
    }
  } catch (err) {
    ElMessage.error('加载失败: ' + (err.response?.data?.msg || err.message))
  } finally {
    loading.value = false
  }
}

// AI 分析历史
function analyzeHistory() {
  if (historyList.value.length === 0) { ElMessage.warning('暂无历史数据可分析'); return }
  analysisVisible.value = true; analyzing.value = true; analysisResult.value = ''

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
    else ElMessage.error(res.msg || '分析失败')
  }).catch(err => { ElMessage.error('分析失败') }).finally(() => { analyzing.value = false })
}

function formatAnalysis(text) { return formatAnalysisHtml(text) }
function copyAnalysis() { navigator.clipboard.writeText(cleanAnalysisMarkdown(analysisResult.value)).then(() => { ElMessage.success('已复制到剪贴板') }) }
function viewDetail(item) {
  selectedDetail.value = item
  detailVisible.value = true
}

function formatDate(dateStr) {
  return formatTrendDate(dateStr)
}

function getScoreColor(score) {
  if (score > 20) return score >= 80 ? 'var(--sn-success)' : score >= 60 ? 'var(--sn-warning)' : 'var(--sn-danger)'
  if (score === 0) return 'var(--sn-success)'
  if (score <= 2) return 'var(--sn-warning)'
  return 'var(--sn-danger)'
}

function getProgressColor(score) {
  if (score === 0) return 'var(--sn-success)'
  if (score === 1) return 'var(--sn-warning)'
  return 'var(--sn-danger)'
}

function getRiskLabel(level) {
  const map = { low: '低风险状态', medium: '中度风险', high: '高风险警报' }
  return map[level] || '未知'
}
</script>

<style scoped>
/* =========================================
全屏突破与深色/纯白高对比度基调
========================================= */
.sn-subpage {
  background-color: var(--sn-slate-light);
}



@media (max-width: 992px) {
  .sn-subpage-body { padding: 0 24px 80px 24px; }
  .sn-subpage-header { padding: 16px 24px; }
  .card-body { grid-template-columns: 1fr; gap: 24px; }
  .hero-metric { display: flex; justify-content: center; }
  .sub-metrics-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 576px) {
  .sn-subpage-body { padding: 0 16px 60px 16px; }
  .sn-subpage-header { padding: 12px 16px; }
  .sub-metrics-grid { grid-template-columns: 1fr; }
}
.header-actions { display: flex; gap: 12px; }

/* 现代质感按钮 */
.whoop-btn-primary, .whoop-btn-secondary, .whoop-btn-text {
  height: 48px; padding: 0 24px; border-radius: var(--sn-radius-md);
  font-weight: 700; font-size: 15px; display: inline-flex; align-items: center; gap: 8px;
  cursor: pointer; border: none; transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1);
}
.whoop-btn-primary { background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary); box-shadow: none; }
.whoop-btn-primary:hover { background: rgba(10, 127, 206, 0.06); transform: translateY(-2px); }
.whoop-btn-secondary { background: var(--sn-surface); color: var(--sn-text); border: 1px solid var(--sn-border); box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.whoop-btn-secondary:hover { background: var(--sn-slate-light); transform: translateY(-2px); }
.whoop-btn-text { background: transparent; color: var(--sn-text-secondary); }
.whoop-btn-text:hover { color: var(--sn-text); background: var(--sn-slate-light); }

/* =========================================
WHOOP 风格数据卡片 (核心)
========================================= */
.whoop-card-list { display: flex; flex-direction: column; gap: 32px; }

.whoop-data-card {
  background: var(--sn-surface);
  border-radius: var(--sn-radius-lg);
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1);
  cursor: pointer;
  border: 1px solid rgba(0,0,0,0.03);
}
.whoop-data-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.08);
}

/* 卡片顶部：日期与徽章 */
.card-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.meta-date { font-size: 24px; font-weight: 800; color: var(--sn-text); letter-spacing: -0.5px; }
.risk-badge {
  padding: 8px 16px; border-radius: var(--sn-radius-sm); font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;
}
.risk-low { background: var(--sn-success-light); color: var(--sn-success); }
.risk-medium { background: var(--sn-danger-light); color: var(--sn-warning); }
.risk-high { background: var(--sn-danger-light); color: var(--sn-danger-dark); }

/* 卡片主体网格：左圈右框 */
.card-body {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 40px;
  align-items: center;
  margin-bottom: 32px;
}

/* 核心巨大指标圈 (类似 WHOOP 恢复环) */
.hero-metric {
  display: flex; justify-content: center; align-items: center;
}
.score-circle {
  width: 140px; height: 140px;
  border-radius: 50%;
  border: 8px solid; /* 动态颜色边界 */
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  background: var(--sn-surface);
  box-shadow: inset 0 4px 12px rgba(0,0,0,0.04);
}
.score-value { font-size: 48px; font-weight: 900; line-height: 1; letter-spacing: -2px; }
.score-label { font-size: 13px; font-weight: 700; color: var(--sn-text-secondary); margin-top: 4px; text-transform: uppercase; }

/* 右侧：高密度数据药丸 (Pills) */
.sub-metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.metric-pill {
  background: var(--sn-slate-light);
  padding: 16px;
  border-radius: var(--sn-radius-md);
  display: flex; flex-direction: column; justify-content: space-between;
  border: 1px solid transparent;
  transition: 0.2s;
}
.whoop-data-card:hover .metric-pill { background: var(--sn-slate-light); }
.m-name { font-size: 14px; font-weight: 600; color: var(--sn-text-secondary); margin-bottom: 8px; }
.m-val { font-size: 24px; font-weight: 800; line-height: 1; }

/* 卡片底栏 */
.card-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 24px; border-top: 1px solid var(--sn-slate-light);
}
.test-index { font-size: 13px; font-weight: 700; color: var(--sn-text-muted); letter-spacing: 1px; }
.detail-link {
  background: none; border: none; font-size: 15px; font-weight: 700; color: var(--sn-text);
  cursor: pointer; display: flex; align-items: center; gap: 4px; transition: 0.2s;
}
.detail-link .arrow { transition: transform 0.2s; }
.whoop-data-card:hover .detail-link .arrow { transform: translateX(6px); }

/* --- 洞察弹窗 (Insights Dialog) --- */
:deep(.whoop-insight-dialog) {
  border-radius: var(--sn-radius-xl) !important; overflow: hidden; padding: 0; border: 1px solid var(--sn-border);
}
:deep(.whoop-insight-dialog .el-dialog__header) {
  padding: 32px 40px 16px 40px; margin: 0;
}
:deep(.whoop-insight-dialog .el-dialog__title) {
  font-size: 28px; font-weight: 900; color: var(--sn-text); letter-spacing: -0.5px;
}
.insight-content { padding: 0 40px 24px 40px; min-height: 150px; }
.insight-result { background: var(--sn-slate-light); border-radius: var(--sn-radius-lg); padding: 32px; }
.insight-text { font-size: 16px; line-height: 1.8; color: var(--sn-text-secondary); }

.insight-actions { display: flex; justify-content: space-between; width: 100%; padding: 0 24px; }
.right-group { display: flex; gap: 12px; }
.empty-state { padding: 120px 0; }

:deep(.whoop-detail-dialog) {
  border-radius: var(--sn-radius-xl) !important;
  overflow: hidden;
}
:deep(.whoop-detail-dialog .el-dialog__header) {
  padding: 28px 32px 12px 32px;
  margin: 0;
}
:deep(.whoop-detail-dialog .el-dialog__title) {
  font-size: 26px;
  font-weight: 900;
  color: var(--sn-text);
}
.detail-content { padding: 8px 32px 32px 32px; }
.detail-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  background: var(--sn-slate-light);
  border: 1px solid var(--sn-border);
  border-radius: var(--sn-radius-lg);
  padding: 24px;
  margin-bottom: 24px;
}
.detail-date {
  font-size: 22px;
  font-weight: 900;
  color: var(--sn-text);
  margin-bottom: 10px;
}
.detail-risk {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 900;
}
.detail-score {
  width: 118px;
  height: 118px;
  border-radius: 59px;
  background: var(--sn-primary);
  color: var(--sn-surface);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}
.detail-score strong {
  font-size: 42px;
  line-height: 1;
}
.detail-score span {
  font-size: 13px;
  font-weight: 800;
  margin-top: 6px;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 28px;
}
.detail-dim {
  border: 1px solid var(--sn-border);
  background: var(--sn-surface);
  border-radius: var(--sn-radius-md);
  padding: 18px;
}
.detail-dim.alert {
  background: var(--sn-danger-light);
  border-color: var(--sn-danger-border);
}
.detail-dim span,
.detail-dim strong,
.detail-dim em {
  display: block;
}
.detail-dim span {
  font-size: 14px;
  color: var(--sn-text-secondary);
  font-weight: 800;
}
.detail-dim strong {
  font-size: 26px;
  color: var(--sn-text);
  margin: 8px 0 4px 0;
}
.detail-dim em {
  font-style: normal;
  font-size: 13px;
  color: var(--sn-text-secondary);
  font-weight: 700;
}
.detail-dim.alert em { color: var(--sn-danger-dark); }
.detail-recommendations h3 {
  margin: 0 0 16px 0;
  font-size: 22px;
  font-weight: 900;
  color: var(--sn-text);
}
.detail-rec-group {
  background: var(--sn-slate-light);
  border-radius: var(--sn-radius-md);
  padding: 18px 22px;
  margin-bottom: 14px;
}
.detail-rec-group h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 900;
  color: var(--sn-text);
}
.detail-rec-group ul {
  margin: 0;
  padding-left: 20px;
  color: var(--sn-text-secondary);
  line-height: 1.8;
  font-weight: 600;
}

/* --- 老年人模式放大适配 --- */
html[data-accessibility="elderly"] .sn-page-title { font-size: 56px; }
html[data-accessibility="elderly"] .meta-date { font-size: 32px; }
html[data-accessibility="elderly"] .score-circle { width: 180px; height: 180px; border-width: 12px; }
html[data-accessibility="elderly"] .score-value { font-size: 64px; }
html[data-accessibility="elderly"] .m-name { font-size: 18px; }
html[data-accessibility="elderly"] .m-val { font-size: 32px; }
</style>
