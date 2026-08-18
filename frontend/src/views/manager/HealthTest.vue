<template>
  <div class="figma-immersive-test">
    <header class="test-header">
      <div class="header-inner">
        <div class="brand-side" @click="goHome">
          <img src="@/assets/imgs/logo2.png" class="brand-logo" alt="Logo" />
          <span class="brand-text">康乐家 健康评估</span>
        </div>
        
        <div class="progress-section" v-if="isQuestionStep">
          <div class="progress-bar-container">
            <div class="progress-line" :style="{ width: getProgressPercentage + '%' }"></div>
          </div>
          <span class="progress-count">进度 {{ getQuestionNumber() }} / 13</span>
        </div>
      </div>
    </header>

    <main class="test-viewport" :class="{ 'is-results': currentStep === 'results' }">
      <transition name="step-fade" mode="out-in">
        
        <div v-if="currentStep === 'intro'" class="test-canvas intro-canvas" key="intro">
          <h1 class="hero-title">内在能力减退初筛测试</h1>
          <p class="hero-subtitle">
            本测试旨在帮助您了解自身的健康状态，涵盖认知、运动、活力、视力、听力和心理。预计完成时间：5-10 分钟。
          </p>

          <div class="selection-box">
            <div class="mode-pill" :class="{ active: assistanceMode === 'alone' }" @click="assistanceMode = 'alone'">
              <div class="icon">👤</div>
              <div class="txt">独自回答</div>
            </div>
            <div class="mode-pill" :class="{ active: assistanceMode === 'assisted' }" @click="assistanceMode = 'assisted'">
              <div class="icon">🤝</div>
              <div class="txt">他人协助</div>
            </div>
          </div>

          <button class="giant-start-btn" :disabled="!assistanceMode" @click="startTest">
            立即开始测试
          </button>
        </div>

        <div v-else-if="isQuestionStep" class="test-canvas question-canvas" :key="currentStep">
          <div class="q-meta">
            <span class="tag">{{ getDimensionLabel(getCurrentDimension()) }}</span>
            <button v-if="canGoBack()" class="back-link" @click="goBack">← 返回上一题</button>
          </div>

          <h2 v-if="currentStep !== 'q2_result'" class="q-statement">{{ getCurrentQuestion().text }}</h2>

          <div class="interaction-zone">
            <template v-if="['q1', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9'].includes(currentStep)">
              <div class="binary-grid">
                <div class="choice-card yes" @click="handleBinaryClick(true)">是 (Yes)</div>
                <div class="choice-card no" @click="handleBinaryClick(false)">否 (No)</div>
              </div>
            </template>

            <template v-else-if="currentStep === 'q1_1'">
              <div class="word-reveal">
                <div class="word">花</div>
                <div class="word">门</div>
                <div class="word">米饭</div>
              </div>
              <button class="action-btn" @click="handleQ1_1Next">我已经记住了</button>
            </template>

            <template v-else-if="['q1_2', 'q1_3', 'q1_4'].includes(currentStep)">
              <div class="input-focus-group">
                <el-date-picker 
                  v-if="currentStep === 'q1_2'" 
                  v-model="answers.q1_2TodayDate" 
                  type="date" 
                  value-format="YYYY-MM-DD"
                  placeholder="点击选择日期"
                  :teleported="false"
                  class="figma-input-style"
                />
                
                <el-input 
                  v-else-if="currentStep === 'q1_3'" 
                  v-model="answers.q1_3Location" 
                  placeholder="输入您所在的位置..."
                  class="figma-input-style"
                />

                <div v-else-if="currentStep === 'q1_4'" class="recall-option-grid">
                  <button
                    v-for="option in recallOptions"
                    :key="option.value"
                    class="recall-option-card"
                    :class="{ active: answers.q1_4Recall === option.value }"
                    @click="selectRecallAnswer(option.value)"
                  >
                    {{ option.label }}
                  </button>
                </div>

                <button class="record-assist" v-if="assistanceMode === 'alone'" @click="startRecording">
                  <el-icon><Microphone /></el-icon> 点击录音辅助
                </button>
              </div>
              <button class="action-btn" @click="handleNext">确认进入下一题</button>
            </template>

            <template v-else-if="currentStep === 'q2'">
              <div class="timer-canvas">
                <div class="timer-clock">{{ formatTime(timer.elapsed) }}<span>s</span></div>
                <button v-if="!timer.running" class="timer-trigger start" @click="startTimer">开始计时</button>
                <button v-else class="timer-trigger stop" @click="stopTimer">停止</button>
              </div>
            </template>

            <template v-else-if="currentStep === 'q2_result'">
              <div class="timer-canvas">
                <div class="timer-result">
                  <div class="time-display">您的用时：{{ formatTime(timer.elapsed) }}秒</div>
                  <p class="time-question">请问您能否在14秒内完成5次起坐？</p>
                </div>
                <div class="binary-grid">
                  <div class="choice-card yes" @click="handleQ2ResultClick(true)">是，可以完成</div>
                  <div class="choice-card no" @click="handleQ2ResultClick(false)">否，不能完成</div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <div v-else-if="currentStep === 'results'" class="test-canvas results-canvas" key="results">
          <div class="result-top">
            <div class="score-disk" :class="getOverallRiskClass()">
              <div class="val">{{ testResult.scores?.total || 0 }}</div>
              <div class="lab">总评分</div>
            </div>
            <div class="title-group">
              <h2>{{ getOverallRiskText() }}</h2>
              <p>本次评估数据已保存至您的健康档案</p>
            </div>
          </div>

          <div class="dimension-grid">
            <div v-for="dim in dimensions" :key="dim.key" class="dim-pill" :class="{ alert: testResult.risks?.[dim.key] }">
              <el-icon class="dim-icon"><component :is="dim.icon" /></el-icon>
              <div class="dim-name">{{ dim.label }}</div>
              <div class="dim-status">{{ testResult.risks?.[dim.key] ? '风险' : '正常' }}</div>
            </div>
          </div>

          <div class="result-visual-panel">
            <div
              v-for="dim in dimensions"
              :key="`${dim.key}-bar`"
              class="result-bar-row"
            >
              <div class="bar-label">
                <span>{{ dim.label }}</span>
                <strong>{{ testResult.scores?.[dim.key] || 0 }} 分</strong>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :class="{ alert: testResult.risks?.[dim.key] }"
                  :style="{ width: getDimensionBarWidth(dim.key) + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <div v-if="testResult.recommendations" class="figma-recommendations">
            <h3 class="rec-main-title">个性化健康建议报告</h3>
            
            <div v-for="(recs, dimension) in testResult.recommendations" :key="dimension" class="rec-group">
              <template v-if="recs && recs.length > 0 && dimension !== 'overall'">
                <div class="rec-dim-title" :class="{ 'is-risk': testResult.risks?.[dimension] }">
                  <span class="dot"></span>{{ getDimensionLabel(dimension) }}干预建议
                  <span v-if="testResult.risks?.[dimension]" class="risk-tag">需重点干预</span>
                </div>
                <ul class="rec-list">
                  <li v-for="(rec, idx) in recs" :key="idx">{{ rec }}</li>
                </ul>
              </template>
            </div>
            
            <div v-if="testResult.recommendations.overall" class="rec-group overall-group">
              <div class="rec-dim-title"><el-icon><Warning /></el-icon> 总体指导方案</div>
              <ul class="rec-list">
                <li v-for="(rec, idx) in testResult.recommendations.overall" :key="idx">{{ rec }}</li>
              </ul>
            </div>
          </div>

          <div class="cta-group">
            <button class="btn-secondary" @click="retakeTest">重新测试</button>
            <button class="btn-primary" @click="goHome">返回</button>
          </div>
        </div>
      </transition>
    </main>

    <el-dialog
      v-model="showAIConnectDialog"
      title=""
      width="440px"
      :close-on-click-modal="false"
      :show-close="false"
      class="modern-ai-dialog"
    >
      <div class="ai-connect-content">
        <div class="ai-connect-icon">
          <el-icon :size="56"><Bell /></el-icon>
        </div>
        <h3 class="ai-connect-title">一键连线 AI 健康管家</h3>
        <p class="ai-connect-desc">系统已生成您的评估报告，<br>是否让 AI 结合结果，为您定制专属调理方案？</p>
      </div>
      <template #footer>
        <div class="ai-connect-footer">
          <button class="modern-btn secondary" @click="handleCloseDialog">暂时不用</button>
          <button class="modern-btn primary" @click="handleAIConnect">立即咨询 AI</button>
        </div>
      </template>
    </el-dialog>

    <button class="exit-btn-fixed" @click="confirmExit">
      <el-icon><ArrowLeft /></el-icon>
      <span>退出测试</span>
    </button>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Microphone, Clock, View, Warning, Sunny, CircleCheck, Bell, ArrowLeft } from '@element-plus/icons-vue'
import { submitHealthTest } from '@/api/healthTest'
import { useSpeech } from '@/composables/useSpeech'
import {
  HEALTH_TEST_STEPS,
  RECALL_OPTIONS,
  getNextHealthTestStep,
  getPreviousHealthTestStep,
  toHealthTestSubmitPayload
} from '@/utils/healthTestFlow.mjs'

const router = useRouter()
const { speak, stop, speakWithCallback } = useSpeech()

// --- 核心状态 ---
const currentStep = ref('intro')
const assistanceMode = ref(null)

// AI连线弹窗状态与定时器
const showAIConnectDialog = ref(false)
let aiConnectTimer = null

const answers = reactive({
  q1MemoryIssue: null, q1_1Remembered: false, q1_2TodayDate: '', q1_3Location: '',
  q1_4Recall: '', q2Completed: null, q2TimeSeconds: 0, q3WeightLoss: null, q4AppetiteLoss: null,
  q5VisionIssue: null, q6DiabetesHypertension: null, q7HearingIssue: null,
  q8Depressed: null, q9InterestLoss: null
})
const timer = reactive({ running: false, startTime: null, elapsed: 0 })
const testResult = reactive({ scores: null, risks: null, recommendations: null }) 

// --- 监听步骤变化，自动播报题目/评估结果 ---
watch(currentStep, (newStep, oldStep) => {
  if (aiConnectTimer) {
    clearTimeout(aiConnectTimer)
    aiConnectTimer = null
  }

  if (newStep.startsWith('q') && newStep !== oldStep) {
    // 进入每一道题目后自动播报题干
    stop()
    let text = getCurrentQuestion().text
    if (newStep === 'q2_result') {
      text = `您完成测试用时 ${formatTime(timer.elapsed)} 秒。请问您能否在14秒内完成5次起坐？`
    }
    setTimeout(() => speak(text), 400)
  } else if (newStep === 'results' && oldStep !== 'results') {
    // 进入结果页面后，先语音播报评估结果摘要，播报完成后再弹出 AI 连线提示
    stop()
    setTimeout(() => {
      speakResultSummary(() => {
        aiConnectTimer = setTimeout(() => {
          showAIConnectDialog.value = true
          speak('一键连线AI健康管家，结合您的筛查结果，即刻定制专属健康方案')
        }, 3000)
      })
    }, 600)
  }
})

// --- 题目配置 ---
const questions = {
  q1: { text: '您是否有记忆力或定向方面的问题（比如不知道自己在哪里或今天是哪一天）？' },
  q1_1: { text: '请先记住这三个词：花、门、米饭，等一会儿我会让你回忆这三个词。' },
  q1_2: { text: '今天是哪年哪月哪天？' },
  q1_3: { text: '您现在在哪里？' },
  q1_4: { text: '刚才的三个词是什么？' },
  q2: { text: '不借助手臂，您是否可以在14秒内完成5次从椅子上站起来的动作？' },
  q2_result: { text: `您完成测试用时：{{timer.elapsed.toFixed(1)}}秒，请问您能否在14秒内完成5次起坐？` },
  q3: { text: '过去3个月内您是否无意中体重下降了3公斤或以上？' },
  q4: { text: '您是否有过食欲减退？' },
  q5: { text: '您的眼睛有什么问题吗？看近或看远模糊吗？' },
  q6: { text: '您是否有糖尿病、高血压，或正在使用眼科药物？' },
  q7: { text: '您的听力有问题吗？' },
  q8: { text: '过去两周内，您是否感受到情绪低落或绝望？' },
  q9: { text: '过去两周内，您是否觉得对做事缺乏兴趣？' }
}

const dimensions = [
  { key: 'cognitive', label: '认知能力', icon: 'CircleCheck' },
  { key: 'motor', label: '运动能力', icon: 'Sunny' },
  { key: 'vitality', label: '活力状态', icon: 'Clock' },
  { key: 'vision', label: '视力', icon: 'View' },
  { key: 'hearing', label: '听力', icon: 'Bell' },
  { key: 'psychological', label: '心理状态', icon: 'Warning' }
]
const recallOptions = RECALL_OPTIONS

// --- 逻辑控制 ---
const isQuestionStep = computed(() => currentStep.value.startsWith('q'))
const getCurrentQuestion = () => questions[currentStep.value] || { text: '' }
const getQuestionNumber = () => {
  return HEALTH_TEST_STEPS.indexOf(currentStep.value) + 1
}
const getProgressPercentage = computed(() => (getQuestionNumber() / 13) * 100)

const handleBinaryClick = (val) => {
  const map = { q1:'q1MemoryIssue', q3:'q3WeightLoss', q4:'q4AppetiteLoss', q5:'q5VisionIssue', q6:'q6DiabetesHypertension', q7:'q7HearingIssue', q8:'q8Depressed', q9:'q9InterestLoss' }
  if(map[currentStep.value]) answers[map[currentStep.value]] = val
  handleNext()
}

const handleNext = () => {
  const next = getNextHealthTestStep(currentStep.value, answers)
  if (next === 'results') submitResult()
  else currentStep.value = next
}

const startTest = () => currentStep.value = 'q1'
const goBack = () => { 
  currentStep.value = getPreviousHealthTestStep(currentStep.value, answers)
}
const goHome = () => {
  stop() // 停止语音播放
  router.push('/home')
}
const retakeTest = () => location.reload()
const confirmExit = () => {
  const testContainer = document.querySelector('.figma-immersive-test')
  if (testContainer) { testContainer.style.zIndex = '100' }

  ElMessageBox.confirm(
    '确定退出测试吗？进度将不被保存。',
    '退出确认',
    {
      confirmButtonText: '确定退出',
      cancelButtonText: '继续测试',
      type: 'warning',
      customClass: 'exit-confirm-dialog'
    }
  ).then(() => { goHome() }).catch(() => {
    if (testContainer) { testContainer.style.zIndex = '2500' }
  })
}
const canGoBack = () => currentStep.value !== 'q1'

let tInterval
const startTimer = () => { timer.running = true; timer.startTime = Date.now(); tInterval = setInterval(() => { timer.elapsed = (Date.now() - timer.startTime) / 1000 }, 100) }
const stopTimer = () => { clearInterval(tInterval); timer.running = false; answers.q2TimeSeconds = timer.elapsed; currentStep.value = 'q2_result' }
const formatTime = (s) => s.toFixed(1)
const handleQ2ResultClick = (val) => { answers.q2Completed = val; handleNext() }
const selectRecallAnswer = (value) => { answers.q1_4Recall = value }

// --- 提交结果与 AI 功能 ---
const submitResult = () => {
  const payload = toHealthTestSubmitPayload(answers, assistanceMode.value)
  submitHealthTest(payload).then(res => {
    if (res.code === '200') {
      testResult.scores = res.data.scores
      testResult.risks = res.data.risks
      testResult.recommendations = res.data.recommendations 
      currentStep.value = 'results'
    }
  })
}

function handleAIConnect() {
  showAIConnectDialog.value = false
  stop()
  router.push('/chat-ai')
}
function handleCloseDialog() {
  showAIConnectDialog.value = false
}

// --- 评估结果语音播报 ---
const speakResultSummary = (onComplete) => {
  if (!testResult.scores || !testResult.risks) {
    if (onComplete) onComplete()
    return
  }

  const total = testResult.scores.total || 0
  const riskLevel = total > 3 ? '建议进一步检查' : '健康状况良好'
  const riskDims = dimensions.filter(d => testResult.risks[d.key]).map(d => d.label)

  let summary = `健康评估已完成。您的总评分为 ${total} 分，${riskLevel}。`
  if (riskDims.length > 0) {
    summary += `需要关注的维度包括：${riskDims.join('、')}。`
  } else {
    summary += `各维度状态均正常，请继续保持。`
  }

  const overallRecs = testResult.recommendations?.overall || []
  if (overallRecs.length > 0) {
    summary += `总体建议：${overallRecs.slice(0, 2).join('；')}。`
  }

  // 后端 TTS 单条限制 1000 字符，做安全截断
  if (summary.length > 900) {
    summary = summary.slice(0, 900).replace(/[^。；，、]$/, '') + '。'
  }

  speakWithCallback(summary, onComplete)
}

const getDimensionLabel = (k) => dimensions.find(d => d.key === k)?.label || '评估'
const getCurrentDimension = () => (['q1','q1_1','q1_2','q1_3','q1_4'].includes(currentStep.value) ? 'cognitive' : 'other')
const getOverallRiskClass = () => testResult.scores?.total > 3 ? 'risk' : 'safe'
const getOverallRiskText = () => testResult.scores?.total > 3 ? '建议进一步检查' : '健康状况良好'
const handleQ1_1Next = () => handleNext()
const getDimensionBarWidth = (key) => {
  const maxScoreMap = { cognitive: 4, motor: 1, vitality: 2, vision: 2, hearing: 1, psychological: 2 }
  const score = testResult.scores?.[key] || 0
  const maxScore = maxScoreMap[key] || 1
  return Math.min(100, Math.round((score / maxScore) * 100))
}

onMounted(() => { speak('欢迎开始内在能力健康测评。请先选择评估模式。') })
onUnmounted(() => {
  stop()
  if (aiConnectTimer) { clearTimeout(aiConnectTimer); aiConnectTimer = null }
})
</script>

<style scoped>
.figma-immersive-test {
  position: fixed; inset: 0; z-index: 2500;
  background: var(--sn-surface); display: flex; flex-direction: column;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
  overflow: hidden;
}

.test-header { 
  padding: 16px 40px; 
  background: rgba(249, 249, 249, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.header-inner { display: flex; justify-content: space-between; align-items: center; max-width: 1280px; margin: 0 auto; }
.brand-side { display: flex; align-items: center; gap: 14px; cursor: pointer; }
.brand-logo { height: 32px; }
.brand-text { font-weight: 700; font-size: 18px; color: var(--sn-text); }

.progress-section { display: flex; align-items: center; gap: 24px; flex: 1; justify-content: center; max-width: 500px; margin: 0 40px; }
.progress-bar-container { flex: 1; height: 8px; background: var(--sn-slate-light); border-radius: 10px; overflow: hidden; }
.progress-line { height: 100%; background: var(--sn-primary); border-radius: 10px; transition: width 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
.progress-count { font-size: 14px; font-weight: 600; color: var(--sn-text-muted); white-space: nowrap; }

.exit-btn-fixed {
  position: fixed;
  bottom: 32px;
  left: 32px;
  z-index: 2600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: transparent;
  border: 1px solid var(--sn-primary);
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  color: var(--sn-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.exit-btn-fixed:hover { background: rgba(13, 148, 136, 0.06); }

.test-viewport { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px; overflow-y: auto;}
.test-viewport.is-results { align-items: flex-start; }
.test-canvas { width: 100%; max-width: 860px; text-align: center; }
.test-canvas.results-canvas { max-width: 1080px; }

.hero-title { font-size: 56px; font-weight: 800; letter-spacing: -2px; line-height: 1.1; margin-bottom: 24px; color: var(--sn-text); }
.hero-subtitle { font-size: 20px; color: var(--sn-text-secondary); line-height: 1.6; margin-bottom: 48px; }

.selection-box { display: flex; gap: 24px; margin-bottom: 48px; }
.mode-pill { 
  flex: 1; padding: 48px; border: 2px solid var(--sn-slate-light); border-radius: 32px; cursor: pointer;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}
.mode-pill.active { border-color: var(--sn-primary); background: var(--sn-primary-light); transform: translateY(-4px); box-shadow: 0 10px 30px rgba(13, 148, 136,0.08); }
.mode-pill .icon { font-size: 48px; margin-bottom: 16px; }
.mode-pill .txt { font-weight: 800; font-size: 22px; color: var(--sn-text); }

.giant-start-btn, .action-btn { 
  width: 100%; padding: 24px; background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary);
  border-radius: 20px; font-size: 20px; font-weight: 700; cursor: pointer; transition: 0.3s;
}
.giant-start-btn:hover, .action-btn:hover { background: rgba(13, 148, 136, 0.06); }
.giant-start-btn:disabled { background: var(--sn-slate-light); border-color: var(--sn-border); color: var(--sn-text-muted); cursor: not-allowed; }

.q-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.tag { background: transparent; color: var(--sn-primary); padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 700; border: 1px solid var(--sn-primary); }
.back-link { background: none; border: none; color: var(--sn-text-muted); font-weight: 600; cursor: pointer; }
.q-statement { font-size: 42px; font-weight: 800; line-height: 1.25; letter-spacing: -1.5px; margin-bottom: 60px; color: var(--sn-text); }

.binary-grid { display: flex; gap: 24px; }
.choice-card { 
  flex: 1; padding: 60px; border-radius: 32px; font-size: 32px; font-weight: 800; cursor: pointer;
  border: 2px solid var(--sn-slate-light); background: var(--sn-surface); transition: 0.3s;
}
.choice-card:hover { border-color: var(--sn-primary); color: var(--sn-primary); }
.choice-card.no:hover { border-color: var(--sn-danger); color: var(--sn-danger); }

.timer-clock { font-size: 120px; font-weight: 800; letter-spacing: -6px; margin-bottom: 40px; color: var(--sn-text); }
.timer-clock span { font-size: 40px; color: var(--sn-text-muted); margin-left: 10px; }
.timer-trigger { padding: 20px 60px; border-radius: 100px; font-size: 24px; font-weight: 800; cursor: pointer; transition: 0.3s; }
.timer-trigger.start { background: transparent; color: var(--sn-primary); border: 2px solid var(--sn-primary); }
.timer-trigger.start:hover { background: rgba(13, 148, 136, 0.06); }
.timer-trigger.stop { background: transparent; color: var(--sn-danger); border: 2px solid var(--sn-danger); }
.timer-trigger.stop:hover { background: var(--sn-danger-light); }

.timer-result { text-align: center; margin-bottom: 40px; }
.time-display { font-size: 48px; font-weight: 800; color: var(--sn-text); margin-bottom: 20px; }
.time-question { font-size: 24px; font-weight: 600; color: var(--sn-text-secondary); }

.word-reveal { display: flex; gap: 24px; justify-content: center; margin-bottom: 60px; }
.word { padding: 30px 60px; background: transparent; color: var(--sn-primary); border: 2px solid var(--sn-primary); font-size: 40px; font-weight: 800; border-radius: 24px; }

/* 报告页面顶部分数区 */
.results-canvas { padding: 40px 0; }
.score-disk {
  width: 140px; height: 140px; border-radius: 70px;
  display: inline-flex; flex-direction: column; align-items: center; justify-content: center;
  background: var(--sn-slate-light); margin-bottom: 24px;
}
.score-disk.risk { background: var(--sn-danger-light); color: var(--sn-danger); }
.score-disk .val { font-size: 48px; font-weight: 800; }

.dimension-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 48px 0; }
.dim-pill { padding: 24px; border-radius: 24px; background: var(--sn-slate-light); text-align: center; border: 1px solid var(--sn-border); transition: 0.3s; }
.dim-pill.alert { background: var(--sn-danger-light); border-color: var(--sn-danger-border); color: var(--sn-danger); }
.dim-name { font-weight: 700; margin-top: 12px; }

/* 个性化建议样式 */
.figma-recommendations {
  text-align: left;
  background: var(--sn-surface);
  border-radius: 32px;
  padding: 40px;
  margin-bottom: 48px;
  border: 1px solid var(--sn-border);
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}
.rec-main-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--sn-text);
  margin: 0 0 32px 0;
  text-align: center;
}
.rec-group { margin-bottom: 24px; }
.rec-dim-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--sn-text);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.rec-dim-title .dot {
  width: 8px; height: 8px; background: var(--sn-primary); border-radius: 50%;
}

/* 👇 针对存在风险维度的红色警示样式 */
.rec-dim-title.is-risk {
  color: var(--sn-danger);
}
.rec-dim-title.is-risk .dot {
  background: var(--sn-danger);
  box-shadow: 0 0 8px rgba(255, 77, 79, 0.4);
}
.risk-tag {
  font-size: 12px;
  font-weight: 700;
  color: var(--sn-danger);
  background: var(--sn-danger-light);
  padding: 2px 8px;
  border-radius: 100px;
  margin-left: 4px;
  border: 1px solid var(--sn-danger-border);
}

.rec-list {
  margin: 0;
  padding-left: 16px;
  color: var(--sn-text-secondary);
  font-size: 16px;
  line-height: 1.8;
  font-weight: 500;
}
.rec-list li { margin-bottom: 12px; }

.overall-group {
  background: var(--sn-primary-soft);
  padding: 24px;
  border-radius: var(--sn-radius-lg);
  margin-top: 32px;
  border: 1px solid var(--sn-primary-light);
}
.overall-group .rec-dim-title { color: var(--sn-primary-dark); }
.overall-group .rec-list { color: var(--sn-primary); }

.cta-group { display: flex; gap: 16px; justify-content: center; }
.btn-primary { padding: 18px 40px; background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary); border-radius: 14px; font-weight: 700; cursor: pointer; transition: 0.3s; }
.btn-primary:hover { background: rgba(13, 148, 136, 0.06); }
.btn-secondary { padding: 18px 40px; background: var(--sn-slate-light); color: var(--sn-text); border: none; border-radius: 14px; font-weight: 700; cursor: pointer; transition: 0.3s; }
.btn-secondary:hover { background: var(--sn-border); }

.step-fade-enter-active, .step-fade-leave-active { transition: all 0.4s ease; }
.step-fade-enter-from { opacity: 0; transform: translateY(20px); }
.step-fade-leave-to { opacity: 0; transform: translateY(-20px); }

.input-focus-group { margin-bottom: 40px; }
.figma-input-style { width: 100%; height: 80px; font-size: 24px; border-radius: 20px; margin-bottom: 12px; }
.record-assist { background: none; border: 1px solid var(--sn-border); padding: 12px 24px; border-radius: 12px; cursor: pointer; color: var(--sn-text-muted); font-weight: 600; }
.recall-option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 12px;
}
.recall-option-card {
  min-height: 96px;
  border: 2px solid var(--sn-border);
  background: var(--sn-surface);
  border-radius: 20px;
  color: var(--sn-text);
  font-size: 22px;
  font-weight: 800;
  cursor: pointer;
  transition: 0.2s;
}
.recall-option-card:hover,
.recall-option-card.active {
  border-color: var(--sn-primary);
  background: transparent;
  color: var(--sn-primary);
}
.result-visual-panel {
  background: var(--sn-slate-light);
  border: 1px solid var(--sn-border);
  border-radius: 24px;
  padding: 28px;
  margin: 0 0 40px 0;
  text-align: left;
}
.result-bar-row + .result-bar-row { margin-top: 18px; }
.bar-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--sn-text);
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 8px;
}
.bar-label strong { color: var(--sn-slate); }
.bar-track {
  height: 12px;
  background: var(--sn-border);
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: var(--sn-primary);
  border-radius: inherit;
  min-width: 4px;
  transition: width 0.4s ease;
}
.bar-fill.alert { background: var(--sn-danger); }

/* 退出确认弹窗样式 */
:deep(.exit-confirm-dialog) { z-index: 9999 !important; }
:deep(.exit-confirm-dialog .el-message-box__wrapper) { z-index: 9999 !important; position: fixed !important; }

/* AI 连线现代弹窗样式 */
:deep(.modern-ai-dialog) {
  border-radius: 32px !important;
  overflow: hidden;
  padding: 0 !important;
}
:deep(.modern-ai-dialog .el-dialog__header) { display: none; }
:deep(.modern-ai-dialog .el-dialog__body) { padding: 40px 32px 0 32px !important; }
:deep(.modern-ai-dialog .el-dialog__footer) { padding: 0 !important; }

.ai-connect-content { text-align: center; }
.ai-connect-icon { color: var(--sn-text); margin-bottom: 24px; }
.ai-connect-title { font-size: 26px; font-weight: 800; color: var(--sn-text); margin: 0 0 16px 0; letter-spacing: -0.5px; }
.ai-connect-desc { font-size: 16px; color: var(--sn-text-secondary); line-height: 1.6; margin: 0 0 32px 0; font-weight: 500;}
.ai-connect-footer { display: flex; gap: 12px; padding: 0 32px 32px 32px; }

.modern-btn {
  flex: 1; height: 52px; border-radius: 100px; font-size: 16px; font-weight: 700; cursor: pointer; border: none; transition: 0.3s cubic-bezier(0.19, 1, 0.22, 1);
}
.modern-btn.primary { background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary); box-shadow: none; }
.modern-btn.primary:hover { background: rgba(13, 148, 136, 0.06); transform: translateY(-2px); }
.modern-btn.secondary { background: var(--sn-slate-light); color: var(--sn-text); }
.modern-btn.secondary:hover { background: var(--sn-border); transform: translateY(-2px); }

/* --- 放大适配 --- */
html[data-accessibility="elderly"] .ai-connect-title { font-size: 32px; }
html[data-accessibility="elderly"] .ai-connect-desc { font-size: 20px; }
html[data-accessibility="elderly"] .modern-btn { font-size: 20px; height: 60px; }
html[data-accessibility="elderly"] .rec-main-title { font-size: 32px; }
html[data-accessibility="elderly"] .rec-dim-title { font-size: 24px; }
html[data-accessibility="elderly"] .rec-list { font-size: 20px; }

@media (max-width: 992px) {
  .test-header { padding: 16px 24px; }
  .header-inner { max-width: 100%; }
  .progress-section { margin: 0 20px; }
  .hero-title { font-size: 42px; }
  .hero-subtitle { font-size: 18px; }
  .mode-pill { padding: 32px 24px; }
  .choice-card { padding: 36px 24px; font-size: 24px; }
  .q-statement { font-size: 32px; }
  .word { padding: 20px 36px; font-size: 28px; }
  .dimension-grid { grid-template-columns: repeat(2, 1fr); }
  .results-canvas { padding: 24px; }
}

@media (max-width: 576px) {
  .test-header { padding: 12px 16px; }
  .brand-text { font-size: 16px; }
  .progress-section { display: none; }
  .test-viewport { padding: 16px 16px 80px 16px; }
  .hero-title { font-size: 32px; }
  .selection-box { flex-direction: column; }
  .mode-pill { padding: 24px; }
  .binary-grid { flex-direction: column; }
  .choice-card { padding: 28px 20px; font-size: 20px; }
  .q-statement { font-size: 24px; margin-bottom: 32px; }
  .timer-clock { font-size: 64px; }
  .timer-trigger { padding: 16px 40px; font-size: 20px; }
  .word-reveal { flex-direction: column; align-items: center; }
  .word { padding: 16px 32px; font-size: 24px; }
  .dimension-grid { grid-template-columns: 1fr; }
  .cta-group { flex-direction: column; }
  .btn-primary, .btn-secondary { width: 100%; }
  .exit-btn-fixed { bottom: 16px; left: 16px; padding: 10px 16px; font-size: 14px; }
}
</style>

<style>
/* 退出弹窗全局修正 */
.exit-confirm-dialog.el-message-box {
  border-radius: 32px !important;
  padding: 48px !important;
  background: var(--sn-surface) !important;
  border: none !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15) !important;
  max-width: 500px !important;
  width: 90% !important;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif !important;
}
.exit-confirm-dialog .el-message-box__header { padding: 0 !important; margin-bottom: 24px !important; }
.exit-confirm-dialog .el-message-box__title { font-size: 32px !important; font-weight: 800 !important; color: var(--sn-text) !important; letter-spacing: -1px !important; line-height: 1.2 !important; text-align: center !important; }
.exit-confirm-dialog .el-message-box__content { padding: 0 !important; margin-bottom: 40px !important; }
.exit-confirm-dialog .el-message-box__message { font-size: 20px !important; font-weight: 600 !important; color: var(--sn-text-secondary) !important; line-height: 1.6 !important; text-align: center !important; }
.exit-confirm-dialog .el-message-box__btns { padding: 0 !important; display: flex !important; gap: 16px !important; justify-content: center !important; }
.exit-confirm-dialog .el-button { flex: 1 !important; max-width: 200px !important; padding: 18px 32px !important; border-radius: 16px !important; font-size: 18px !important; font-weight: 700 !important; border: 2px solid !important; transition: all 0.3s cubic-bezier(0.2, 0, 0, 1) !important; }
.exit-confirm-dialog .el-button--default { background: var(--sn-slate-light) !important; border-color: var(--sn-slate-light) !important; color: var(--sn-text) !important; }
.exit-confirm-dialog .el-button--default:hover { background: var(--sn-border) !important; border-color: var(--sn-border) !important; transform: translateY(-2px) !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important; }
.exit-confirm-dialog .el-button--primary { background: var(--sn-danger) !important; border-color: var(--sn-danger) !important; color: var(--sn-surface) !important; }
.exit-confirm-dialog .el-button--primary:hover { background: var(--sn-danger-hover) !important; border-color: var(--sn-danger-hover) !important; transform: translateY(-2px) !important; box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3) !important; }
.exit-confirm-dialog .el-message-box__headerbtn { display: none !important; }
</style>
