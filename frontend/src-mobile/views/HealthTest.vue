<template>
  <div class="mobile-health-test">
    <div class="test-header">
      <a-button type="text" @click="confirmExit">
        <left-outlined /> 退出
      </a-button>
      <span v-if="isQuestionStep" class="progress-text">{{ getQuestionNumber() }} / 13</span>
      <div style="width: 60px;"></div>
    </div>

    <div class="progress-bar" v-if="isQuestionStep">
      <div class="progress-fill" :style="{ width: getProgressPercentage + '%' }"></div>
    </div>

    <div class="test-body">
      <transition name="fade" mode="out-in">
        <!-- Intro -->
        <div v-if="currentStep === 'intro'" class="step intro" key="intro">
          <h1 class="step-title">内在能力减退初筛测试</h1>
          <p class="step-desc">本测试涵盖认知、运动、活力、视力、听力和心理，预计 5-10 分钟完成。</p>

          <div class="mode-select">
            <div
              class="mode-option"
              :class="{ active: assistanceMode === 'alone' }"
              @click="assistanceMode = 'alone'"
            >
              <span class="mode-emoji">👤</span>
              <span>独自回答</span>
            </div>
            <div
              class="mode-option"
              :class="{ active: assistanceMode === 'assisted' }"
              @click="assistanceMode = 'assisted'"
            >
              <span class="mode-emoji">🤝</span>
              <span>他人协助</span>
            </div>
          </div>

          <a-button type="primary" size="large" block :disabled="!assistanceMode" @click="startTest" class="action-btn">
            立即开始测试
          </a-button>
        </div>

        <!-- Questions -->
        <div v-else-if="isQuestionStep" class="step question" :key="currentStep">
          <div class="dimension-tag">{{ getDimensionLabel(getCurrentDimension()) }}</div>
          <h2 class="question-text">{{ getCurrentQuestion().text }}</h2>

          <div class="interaction-zone">
            <template v-if="['q1', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9'].includes(currentStep)">
              <div class="binary-choice">
                <a-button size="large" block class="yes-btn" @click="handleBinaryClick(true)">是</a-button>
                <a-button size="large" block class="no-btn" @click="handleBinaryClick(false)">否</a-button>
              </div>
            </template>

            <template v-else-if="currentStep === 'q1_1'">
              <div class="word-list">
                <div class="word">花</div>
                <div class="word">门</div>
                <div class="word">米饭</div>
              </div>
              <a-button type="primary" size="large" block @click="handleNext" class="action-btn">我已经记住了</a-button>
            </template>

            <template v-else-if="['q1_2', 'q1_3', 'q1_4'].includes(currentStep)">
              <div class="input-zone">
                <a-date-picker
                  v-if="currentStep === 'q1_2'"
                  v-model:value="answers.q1_2TodayDate"
                  value-format="YYYY-MM-DD"
                  placeholder="点击选择日期"
                  style="width: 100%"
                  size="large"
                />
                <a-input
                  v-else-if="currentStep === 'q1_3'"
                  v-model:value="answers.q1_3Location"
                  placeholder="输入您所在的位置"
                  size="large"
                />
                <div v-else-if="currentStep === 'q1_4'" class="recall-options">
                  <a-button
                    v-for="option in recallOptions"
                    :key="option.value"
                    block
                    size="large"
                    :type="answers.q1_4Recall === option.value ? 'primary' : 'default'"
                    @click="selectRecallAnswer(option.value)"
                    class="recall-btn"
                  >
                    {{ option.label }}
                  </a-button>
                </div>
              </div>
              <a-button type="primary" size="large" block @click="handleNext" class="action-btn">确认进入下一题</a-button>
            </template>

            <template v-else-if="currentStep === 'q2'">
              <div class="timer-zone">
                <div class="timer-display">{{ formatTime(timer.elapsed) }}<span>s</span></div>
                <a-button
                  v-if="!timer.running"
                  type="primary"
                  size="large"
                  block
                  @click="startTimer"
                  class="action-btn"
                >开始计时</a-button>
                <a-button
                  v-else
                  danger
                  size="large"
                  block
                  @click="stopTimer"
                  class="action-btn"
                >停止计时</a-button>
              </div>
            </template>

            <template v-else-if="currentStep === 'q2_result'">
              <div class="timer-result">
                <p>您的用时：{{ formatTime(timer.elapsed) }} 秒</p>
                <p class="sub-question">请问您能否在14秒内完成5次起坐？</p>
              </div>
              <div class="binary-choice">
                <a-button size="large" block class="yes-btn" @click="handleQ2ResultClick(true)">是，可以完成</a-button>
                <a-button size="large" block class="no-btn" @click="handleQ2ResultClick(false)">否，不能完成</a-button>
              </div>
            </template>
          </div>

          <a-button v-if="canGoBack()" type="link" block @click="goBack" class="back-btn">
            ← 返回上一题
          </a-button>
        </div>

        <!-- Results -->
        <div v-else-if="currentStep === 'results'" class="step results" key="results">
          <div class="score-card" :class="getOverallRiskClass()">
            <div class="score-value">{{ testResult.scores?.total || 0 }}</div>
            <div class="score-label">总评分</div>
            <div class="score-text">{{ getOverallRiskText() }}</div>
          </div>

          <div class="dimension-list">
            <div
              v-for="dim in dimensions"
              :key="dim.key"
              class="dim-item"
              :class="{ alert: testResult.risks?.[dim.key] }"
            >
              <span>{{ dim.label }}</span>
              <span class="dim-score">{{ testResult.scores?.[dim.key] || 0 }} 分</span>
              <span class="dim-status">{{ testResult.risks?.[dim.key] ? '风险' : '正常' }}</span>
            </div>
          </div>

          <div v-if="testResult.recommendations" class="recommendations">
            <h3>个性化健康建议</h3>
            <div
              v-for="(recs, dimension) in testResult.recommendations"
              :key="dimension"
              v-show="recs && recs.length > 0 && dimension !== 'overall'"
              class="rec-group"
            >
              <h4 :class="{ risk: testResult.risks?.[dimension] }">
                {{ getDimensionLabel(dimension) }}建议
              </h4>
              <ul>
                <li v-for="(rec, idx) in recs" :key="idx">{{ rec }}</li>
              </ul>
            </div>
            <div v-if="testResult.recommendations.overall" class="rec-group overall">
              <h4>总体指导方案</h4>
              <ul>
                <li v-for="(rec, idx) in testResult.recommendations.overall" :key="idx">{{ rec }}</li>
              </ul>
            </div>
          </div>

          <div class="result-actions">
            <a-button size="large" block @click="retakeTest">重新测试</a-button>
            <a-button type="primary" size="large" block @click="goHome" class="action-btn">返回首页</a-button>
          </div>
        </div>
      </transition>
    </div>

    <a-modal
      v-model:open="showAIConnectDialog"
      title="AI 健康管家"
      :closable="false"
      :mask-closable="false"
      centered
      @ok="handleAIConnect"
      @cancel="handleCloseDialog"
      ok-text="立即咨询"
      cancel-text="暂时不用"
    >
      <p>系统已生成您的评估报告，是否让 AI 结合结果为您定制专属调理方案？</p>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { LeftOutlined } from '@ant-design/icons-vue'
import { submitHealthTest } from '@shared/api/healthTest'
import { useSpeech } from '@shared/composables/useSpeech'
import {
  HEALTH_TEST_STEPS,
  RECALL_OPTIONS,
  getNextHealthTestStep,
  getPreviousHealthTestStep,
  toHealthTestSubmitPayload
} from '@shared/utils/healthTestFlow.mjs'

const router = useRouter()
const { speak, stop, speakPageTitle } = useSpeech()

const currentStep = ref('intro')
const assistanceMode = ref(null)
const answers = reactive({
  q1MemoryIssue: null,
  q1_1Remembered: false,
  q1_2TodayDate: '',
  q1_3Location: '',
  q1_4Recall: '',
  q2Completed: null,
  q2TimeSeconds: 0,
  q3WeightLoss: null,
  q4AppetiteLoss: null,
  q5VisionIssue: null,
  q6DiabetesHypertension: null,
  q7HearingIssue: null,
  q8Depressed: null,
  q9InterestLoss: null
})
const timer = reactive({ running: false, startTime: null, elapsed: 0 })
const testResult = reactive({ scores: null, risks: null, recommendations: null })
const showAIConnectDialog = ref(false)
let aiConnectTimer = null
let tInterval = null

const questions = {
  q1: { text: '您是否有记忆力或定向方面的问题（比如不知道自己在哪里或今天是哪一天）？' },
  q1_1: { text: '请先记住这三个词：花、门、米饭，等一会儿我会让你回忆这三个词。' },
  q1_2: { text: '今天是哪年哪月哪天？' },
  q1_3: { text: '您现在在哪里？' },
  q1_4: { text: '刚才的三个词是什么？' },
  q2: { text: '不借助手臂，您是否可以在14秒内完成5次从椅子上站起来的动作？' },
  q2_result: { text: `您完成测试用时：${timer.elapsed.toFixed(1)}秒，请问您能否在14秒内完成5次起坐？` },
  q3: { text: '过去3个月内您是否无意中体重下降了3公斤或以上？' },
  q4: { text: '您是否有过食欲减退？' },
  q5: { text: '您的眼睛有什么问题吗？看近或看远模糊吗？' },
  q6: { text: '您是否有糖尿病、高血压，或正在使用眼科药物？' },
  q7: { text: '您的听力有问题吗？' },
  q8: { text: '过去两周内，您是否感受到情绪低落或绝望？' },
  q9: { text: '过去两周内，您是否觉得对做事缺乏兴趣？' }
}

const dimensions = [
  { key: 'cognitive', label: '认知能力' },
  { key: 'motor', label: '运动能力' },
  { key: 'vitality', label: '活力状态' },
  { key: 'vision', label: '视力' },
  { key: 'hearing', label: '听力' },
  { key: 'psychological', label: '心理状态' }
]

const recallOptions = RECALL_OPTIONS
const isQuestionStep = computed(() => currentStep.value.startsWith('q'))
const getCurrentQuestion = () => questions[currentStep.value] || { text: '' }
const getQuestionNumber = () => HEALTH_TEST_STEPS.indexOf(currentStep.value) + 1
const getProgressPercentage = computed(() => (getQuestionNumber() / 13) * 100)

watch(currentStep, (newStep, oldStep) => {
  if (aiConnectTimer) {
    clearTimeout(aiConnectTimer)
    aiConnectTimer = null
  }
  if (newStep === 'results' && oldStep !== 'results') {
    aiConnectTimer = setTimeout(() => {
      showAIConnectDialog.value = true
      speak('一键连线AI健康管家，结合您的筛查结果，即刻定制专属健康方案')
    }, 8000)
  }
})

onMounted(() => { speakPageTitle('健康测试') })
onUnmounted(() => {
  stop()
  if (aiConnectTimer) clearTimeout(aiConnectTimer)
  if (tInterval) clearInterval(tInterval)
})

function startTest() { currentStep.value = 'q1' }
function goHome() { stop(); router.push('/home') }
function retakeTest() { location.reload() }
function canGoBack() { return currentStep.value !== 'q1' }
function goBack() { currentStep.value = getPreviousHealthTestStep(currentStep.value, answers) }

function handleBinaryClick(val) {
  const map = {
    q1: 'q1MemoryIssue',
    q3: 'q3WeightLoss',
    q4: 'q4AppetiteLoss',
    q5: 'q5VisionIssue',
    q6: 'q6DiabetesHypertension',
    q7: 'q7HearingIssue',
    q8: 'q8Depressed',
    q9: 'q9InterestLoss'
  }
  if (map[currentStep.value]) answers[map[currentStep.value]] = val
  handleNext()
}

function handleNext() {
  const next = getNextHealthTestStep(currentStep.value, answers)
  if (next === 'results') submitResult()
  else currentStep.value = next
}

function selectRecallAnswer(value) { answers.q1_4Recall = value }
function startTimer() {
  timer.running = true
  timer.startTime = Date.now()
  tInterval = setInterval(() => { timer.elapsed = (Date.now() - timer.startTime) / 1000 }, 100)
}
function stopTimer() {
  clearInterval(tInterval)
  timer.running = false
  answers.q2TimeSeconds = timer.elapsed
  currentStep.value = 'q2_result'
}
function formatTime(s) { return s.toFixed(1) }
function handleQ2ResultClick(val) { answers.q2Completed = val; handleNext() }

function submitResult() {
  const payload = toHealthTestSubmitPayload(answers, assistanceMode.value)
  submitHealthTest(payload).then(res => {
    if (res.code === '200') {
      testResult.scores = res.data.scores
      testResult.risks = res.data.risks
      testResult.recommendations = res.data.recommendations
      currentStep.value = 'results'
    } else {
      message.error(res.msg || '提交失败')
    }
  }).catch(() => {
    message.error('提交失败，请稍后重试')
  })
}

function confirmExit() {
  Modal.confirm({
    title: '退出测试',
    content: '确定退出测试吗？进度将不被保存。',
    okText: '退出',
    cancelText: '继续测试',
    onOk: () => goHome()
  })
}

function handleAIConnect() {
  showAIConnectDialog.value = false
  stop()
  router.push('/chat-ai')
}
function handleCloseDialog() { showAIConnectDialog.value = false }

function getDimensionLabel(k) { return dimensions.find(d => d.key === k)?.label || '评估' }
function getCurrentDimension() {
  return ['q1', 'q1_1', 'q1_2', 'q1_3', 'q1_4'].includes(currentStep.value) ? 'cognitive' : 'other'
}
function getOverallRiskClass() { return testResult.scores?.total > 3 ? 'risk' : 'safe' }
function getOverallRiskText() { return testResult.scores?.total > 3 ? '建议进一步检查' : '健康状况良好' }
</script>

<style scoped>
.mobile-health-test {
  min-height: 100vh;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.progress-text {
  font-size: 16px;
  font-weight: 700;
  color: #666;
}

.progress-bar {
  height: 4px;
  background: #f0f0f0;
}

.progress-fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.4s ease;
}

.test-body {
  flex: 1;
  padding: 24px 16px;
  overflow-y: auto;
}

.step {
  max-width: 100%;
}

.step-title {
  font-size: 26px;
  font-weight: 800;
  color: #111;
  margin: 0 0 12px 0;
}

.step-desc {
  font-size: 16px;
  color: #666;
  line-height: 1.6;
  margin: 0 0 24px 0;
}

.mode-select {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.mode-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 12px;
  border: 2px solid #eee;
  border-radius: 16px;
  background: #fafafa;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
}

.mode-option.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.mode-emoji {
  font-size: 32px;
}

.dimension-tag {
  display: inline-block;
  background: #111;
  color: #fff;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 16px;
}

.question-text {
  font-size: 22px;
  font-weight: 700;
  color: #111;
  line-height: 1.4;
  margin: 0 0 32px 0;
}

.binary-choice {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.yes-btn {
  min-height: 56px;
  font-size: 18px;
  border-radius: 12px;
}

.no-btn {
  min-height: 56px;
  font-size: 18px;
  border-radius: 12px;
}

.word-list {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 32px;
}

.word {
  padding: 20px 28px;
  background: #1890ff;
  color: #fff;
  border-radius: 16px;
  font-size: 28px;
  font-weight: 800;
}

.input-zone {
  margin-bottom: 16px;
}

.input-zone :deep(.ant-picker) {
  width: 100%;
  min-height: 52px;
}

.recall-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recall-btn {
  min-height: 52px;
  font-size: 16px;
  border-radius: 12px;
}

.timer-zone {
  text-align: center;
  margin-bottom: 24px;
}

.timer-display {
  font-size: 72px;
  font-weight: 800;
  color: #111;
  margin-bottom: 24px;
}

.timer-display span {
  font-size: 28px;
  color: #999;
  margin-left: 4px;
}

.timer-result {
  text-align: center;
  margin-bottom: 24px;
}

.timer-result p {
  font-size: 20px;
  font-weight: 700;
  color: #111;
  margin: 0 0 8px 0;
}

.sub-question {
  font-size: 16px !important;
  color: #666 !important;
  font-weight: 500 !important;
}

.back-btn {
  margin-top: 16px;
  min-height: 44px;
}

.action-btn {
  min-height: 52px;
  font-size: 18px;
  border-radius: 12px;
}

.score-card {
  text-align: center;
  padding: 32px 24px;
  border-radius: 20px;
  margin-bottom: 20px;
}

.score-card.safe {
  background: #f6ffed;
  color: #52c41a;
}

.score-card.risk {
  background: #fff2f0;
  color: #ff4d4f;
}

.score-value {
  font-size: 56px;
  font-weight: 900;
  line-height: 1;
}

.score-label {
  font-size: 16px;
  margin-top: 8px;
}

.score-text {
  font-size: 18px;
  font-weight: 700;
  margin-top: 12px;
}

.dimension-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.dim-item {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dim-item.alert {
  background: #fff2f0;
  border-color: #ffccc7;
}

.dim-score {
  font-size: 24px;
  font-weight: 800;
  color: #111;
}

.dim-status {
  font-size: 13px;
  color: #666;
}

.dim-item.alert .dim-status {
  color: #ff4d4f;
}

.recommendations {
  background: #fafafa;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
}

.recommendations h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: 800;
}

.rec-group {
  margin-bottom: 16px;
}

.rec-group h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 700;
}

.rec-group h4.risk {
  color: #ff4d4f;
}

.rec-group ul {
  margin: 0;
  padding-left: 18px;
  color: #444;
  line-height: 1.7;
}

.rec-group.overall {
  background: #e6f7ff;
  padding: 12px;
  border-radius: 12px;
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
