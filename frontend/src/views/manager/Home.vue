<template>
  <div class="bento-home-wrapper">
    <div class="bento-grid-container">
      
      <div class="bento-card hero-card">
        <div class="hero-content">
          <div class="hero-top-line">
            <h2 class="welcome-title">{{ greeting }}，{{ user.name || user.username || '朋友' }}</h2>
            <div class="date-capsule">
              {{ new Date().getFullYear() }}年{{ new Date().getMonth() + 1 }}月{{ new Date().getDate() }}日
            </div>
          </div>
          <p class="welcome-text">
            内在力量，活力人生。<br>
            今天感觉如何？<br>
            康乐家时刻守护您的健康。
          </p>
          <button class="hero-btn" @click="goToInfo">完善健康档案 &rarr;</button>
        </div>
        
        <img src="@/assets/imgs/grandparents.png" alt="人物插画" class="bg-illustration" />
      </div>

      <div class="bento-card control-center-card">
        <h3 class="card-mini-title">设置</h3>
        <div class="control-grid">
          <button class="control-btn toggle-row-btn" @click="toggleAccessibilityMode">
            <div class="toggle-label">
              <el-icon class="c-icon"><ZoomIn /></el-icon>
              <span>长辈模式</span>
            </div>
            <div class="toggle-switch" :class="{'is-active': isElderlyMode}">
              <div class="toggle-thumb"></div>
            </div>
          </button>

          <div class="control-btn segment-toggle">
            <div class="segment-track">
              <div class="segment-thumb" :class="{'is-text': selectedMode === 'text'}"></div>
              <button
                class="segment-btn"
                :class="{'is-active': selectedMode === 'voice'}"
                @click="setMode('voice')"
              >
                <el-icon class="c-icon"><Microphone /></el-icon>
                <span>语音</span>
              </button>
              <button
                class="segment-btn"
                :class="{'is-active': selectedMode === 'text'}"
                @click="setMode('text')"
              >
                <el-icon class="c-icon"><Document /></el-icon>
                <span>文字</span>
              </button>
            </div>
          </div>

          <div v-if="selectedMode === 'voice'" class="control-btn volume-row">
            <div class="volume-row-header">
              <div class="volume-row-label">
                <SpeakerIcon class="c-icon volume-icon" :class="`is-level-${volumeLevel}`" :level="volumeLevel" />
                <span>语音音量</span>
              </div>
              <span class="volume-row-value">{{ volume }}%</span>
            </div>
            <div class="volume-row-slider">
              <el-slider v-model="volume" :min="0" :max="100" :step="5" @change="onVolumeChange" :show-tooltip="false" />
            </div>
          </div>

          <button class="control-btn account-settings-btn" @click="openAccountSettings">
            <el-icon class="c-icon"><User /></el-icon>
            <span>账户与安全</span>
          </button>

          <button class="control-btn" @click="openOnboardingGuide">
            <el-icon class="c-icon"><Help /></el-icon>
            <span>使用指南</span>
          </button>
        </div>
      </div>

      <div class="bento-card action-card ai-chat-card" @click="goToChat">
        <el-icon class="action-card-icon"><ChatDotRound /></el-icon>
        <div class="action-text">
          <h3>AI 智能问答</h3>
          <p>随时随地，获取您的专属健康指导与干预方案</p>
        </div>
        <div class="card-arrow">&rarr;</div>
      </div>

      <div class="bento-card action-card health-test-card" @click="goToTest">
        <el-icon class="action-card-icon"><Document /></el-icon>
        <div class="action-text">
          <h3>健康能力评估</h3>
          <p>多维度测试您的内在能力，了解身体变化</p>
        </div>
        <div class="card-arrow">&rarr;</div>
      </div>
    </div>

    <el-dialog v-model="modeDialogVisible" title="语音音量" width="520px" :close-on-click-modal="false" class="modern-dialog">
      <div class="mode-dialog-content">
        <div class="volume-control-panel">
          <div class="volume-header">
            <span class="v-label"><el-icon><Notification /></el-icon> 语音音量调节</span>
            <span class="v-value">{{ volume }}%</span>
          </div>
          <el-slider v-model="volume" :min="0" :max="100" :step="5" @change="onVolumeChange" :show-tooltip="false" />
          <button class="test-voice-btn" @click="testVolume">点击试听音量</button>
        </div>
      </div>
      <template #footer>
        <button class="modern-confirm-btn" @click="modeDialogVisible = false">完成</button>
      </template>
    </el-dialog>

    <el-dialog v-model="accountDialogVisible" title="账户与安全" width="460px" class="modern-dialog">
      <div class="account-content">
        <div class="user-info-section">
          <div class="user-avatar"><img src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" alt="avatar" /></div>
          <div class="user-details">
            <div class="user-name">{{ user.username || user.name || '用户' }}</div>
            <div class="user-role">普通用户</div>
          </div>
        </div>
        
        <div class="action-list-group">
          <div class="action-list-item" @click="switchAccount">
            <div class="item-left">
              <div class="item-icon-box"><el-icon><Refresh /></el-icon></div>
              <span>切换账号</span>
            </div>
            <el-icon class="arrow-icon"><ArrowRight /></el-icon>
          </div>
          <div class="action-list-item" @click="changePassword">
            <div class="item-left">
              <div class="item-icon-box"><el-icon><Edit /></el-icon></div>
              <span>修改密码</span>
            </div>
            <el-icon class="arrow-icon"><ArrowRight /></el-icon>
          </div>
        </div>

        <button class="logout-text-btn" @click="logout">
          <el-icon><SwitchButton /></el-icon>退出当前登录
        </button>
      </div>
    </el-dialog>

    <el-dialog v-model="switchAccountDialogVisible" title="切换账号" width="420px" class="modern-dialog">
      <div class="custom-confirm-content">
        <div class="warning-icon"><el-icon><Warning /></el-icon></div>
        <p>切换账号需要退出当前登录，<br>确定要继续吗？</p>
      </div>
      <template #footer>
        <button class="modern-cancel-btn" @click="switchAccountDialogVisible = false">取消</button>
        <button class="modern-confirm-btn" @click="confirmSwitchAccount">确认切换</button>
      </template>
    </el-dialog>

    <el-dialog v-model="logoutDialogVisible" title="退出系统" width="420px" class="modern-dialog">
      <div class="custom-confirm-content">
        <div class="warning-icon" style="color: #EF4444; background: #FEF2F2;"><el-icon><SwitchButton /></el-icon></div>
        <p>您即将退出康乐家系统，<br>确定要继续吗？</p>
      </div>
      <template #footer>
        <button class="modern-cancel-btn" @click="logoutDialogVisible = false">取消</button>
        <button class="modern-confirm-btn danger-btn" @click="confirmLogout">确认退出</button>
      </template>
    </el-dialog>

    <el-dialog v-model="changePasswordDialogVisible" title="修改密码" width="420px" class="modern-dialog">
      <div class="custom-prompt-content">
        <p class="prompt-desc">为了您的账号安全，请设置一个不少于 6 位的新密码。</p>
        <div class="custom-input-wrapper" :class="{'has-error': passwordError}">
          <el-input 
            v-model="newPassword" 
            type="password" 
            show-password 
            placeholder="请输入新密码" 
            class="modern-input"
            @input="passwordError = ''"
            @keyup.enter="confirmChangePassword"
          />
        </div>
        <Transition name="fade-slide">
          <span v-if="passwordError" class="error-msg">{{ passwordError }}</span>
        </Transition>
      </div>
      <template #footer>
        <button class="modern-cancel-btn" @click="changePasswordDialogVisible = false">取消</button>
        <button class="modern-confirm-btn" @click="confirmChangePassword">确认修改</button>
      </template>
    </el-dialog>

    <el-dialog v-model="guideDialogVisible" title="" width="600px" :close-on-click-modal="false" :show-close="false" class="modern-dialog guide-dialog">
      <div class="guide-popup-content">
        <div class="guide-icon" style="color: #F59E0B;"><el-icon :size="55"><Warning /></el-icon></div>
        <h3 class="guide-title">欢迎使用系统</h3>
        <p class="guide-desc">为了给您提供更精准的健康评估和建议，建议您先完成以下操作：</p>
        <div class="guide-steps">
          <div class="guide-step">
            <div class="step-number">1</div>
            <div class="step-content">
              <div class="step-title">填写健康档案</div>
              <div class="step-desc">记录基本信息、生活习惯、健康状况等</div>
            </div>
          </div>
          <div class="guide-step">
            <div class="step-number">2</div>
            <div class="step-content">
              <div class="step-title">完成健康测试</div>
              <div class="step-desc">评估内在能力水平，了解身体状况</div>
            </div>
          </div>
        </div>
        <div class="guide-actions">
          <button class="modern-confirm-btn" style="flex:1" @click="goToInfo">立即填写档案</button>
          <button class="modern-cancel-btn" style="flex:1; border:1px solid #E5E7EB;" @click="goToTest">先做健康测试</button>
        </div>
        <button class="logout-text-btn" style="margin-top:20px; color:#999;" @click="skipGuide">稍后进行</button>
      </div>
    </el-dialog>

    <OnboardingDialog v-model:visible="onboardingVisible" @complete="handleOnboardingComplete" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
// 确保所有用到的图标都在这里被正确导入，漏掉一个就会报错
import {
  Setting, Microphone, Document, User, Refresh, Edit, SwitchButton, 
  ZoomIn, Help, ChatDotRound, Select, ArrowRight, Warning
} from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'
import { useAccessibility } from '@/composables/useAccessibility'
import { useOnboarding } from '@/composables/useOnboarding'
import OnboardingDialog from '@/components/OnboardingDialog.vue'
import SpeakerIcon from '@/components/SpeakerIcon.vue'
import { checkReadiness } from '@/api/chatAI'
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 11) return '早安'
  if (hour >= 11 && hour < 13) return '中午好'
  if (hour >= 13 && hour < 18) return '下午好'
  if (hour >= 18 && hour < 23) return '晚上好'
  return '夜深了' // 23:00 - 05:00
})
const volumeLevel = computed(() => {
  if (volume.value === 0) return 0
  if (volume.value <= 33) return 1
  if (volume.value <= 66) return 2
  return 3
})
const router = useRouter()
const { speak, stop } = useSpeech()
const { isElderlyMode, toggleMode } = useAccessibility()
const { checkOnboardingStatus, markOnboardingComplete } = useOnboarding()

const user = JSON.parse(localStorage.getItem('student-user') || '{}')

// 弹窗可见性控制变量
const modeDialogVisible = ref(false)
const accountDialogVisible = ref(false)
const guideDialogVisible = ref(false)
const onboardingVisible = ref(false)
const hasShownOnboarding = ref(false)

// 二次确认弹窗变量
const switchAccountDialogVisible = ref(false)
const logoutDialogVisible = ref(false)
const changePasswordDialogVisible = ref(false)
const newPassword = ref('')
const passwordError = ref('')

const selectedMode = ref('voice')
const volume = ref(80)
const HOME_GUIDE_DISMISSED_KEY = 'home-guide-dismissed'

onMounted(async () => {
  const userMode = localStorage.getItem('user-mode')
  if (!userMode) {
    setTimeout(() => { router.replace('/mode-select') }, 1500)
    return
  } else {
    selectedMode.value = userMode
  }

  const savedVolume = localStorage.getItem('speech-volume')
  if (savedVolume) {
    volume.value = Math.round(parseFloat(savedVolume) * 100)
  }

  await checkUserReadiness()

  const onboardingStatus = checkOnboardingStatus()
  if (!onboardingStatus.completed && !hasShownOnboarding.value) {
    setTimeout(() => {
      onboardingVisible.value = true
      hasShownOnboarding.value = true
    }, 500)
  }
})

onUnmounted(() => { stop() })

function toggleAccessibilityMode() {
  toggleMode()
}
function openModeSettings() { modeDialogVisible.value = true }
function openAccountSettings() { accountDialogVisible.value = true }
function openOnboardingGuide() { onboardingVisible.value = true }

function setMode(mode) {
  if (selectedMode.value === mode) return
  selectedMode.value = mode
  localStorage.setItem('user-mode', mode)
  localStorage.setItem('speech-volume', (volume.value / 100).toString())
  if (mode === 'voice') speak('已切换到语音模式')
  else stop()
}
function onModeChange() {
  if (selectedMode.value === 'voice') speak('已切换到语音模式')
  else stop()
}
function onVolumeChange(value) { localStorage.setItem('speech-volume', (value / 100).toString()) }
function testVolume() { speak('您好，这是语音播报测试。') }
function saveMode() {
  localStorage.setItem('user-mode', selectedMode.value)
  localStorage.setItem('speech-volume', (volume.value / 100).toString())
  modeDialogVisible.value = false
  setTimeout(() => { location.reload() }, 500)
}

// ================= 账号操作与二次确认逻辑 =================
function switchAccount() {
  accountDialogVisible.value = false 
  switchAccountDialogVisible.value = true
}
function confirmSwitchAccount() {
  localStorage.clear()
  router.push('/login')
}

function logout() {
  accountDialogVisible.value = false
  logoutDialogVisible.value = true
}
function confirmLogout() {
  stop()
  localStorage.clear()
  router.push('/login')
}

function changePassword() {
  accountDialogVisible.value = false
  newPassword.value = ''
  passwordError.value = ''
  changePasswordDialogVisible.value = true
}
function confirmChangePassword() {
  if (!newPassword.value || newPassword.value.length < 6) {
    passwordError.value = '密码长度不能少于6位！'
    return
  }
  changePasswordDialogVisible.value = false
  localStorage.clear()
  router.push('/login')
}

// ================= 其他逻辑 =================
async function checkUserReadiness() {
  try {
    const res = await checkReadiness()
    const alreadyDismissed = localStorage.getItem(HOME_GUIDE_DISMISSED_KEY) === '1'
    if (!alreadyDismissed && !res.data.hasHealthRecord && !res.data.hasHealthTest) {
      guideDialogVisible.value = true
    }
  } catch (error) { console.error(error) }
}
function dismissHomeGuide() {
  guideDialogVisible.value = false
  localStorage.setItem(HOME_GUIDE_DISMISSED_KEY, '1')
}
function goToInfo() { dismissHomeGuide(); router.push('/health-record/info') }
function goToTest() { dismissHomeGuide(); router.push('/test') }
function goToChat() { router.push('/chat-ai') }
function skipGuide() { dismissHomeGuide() }
function handleOnboardingComplete() { markOnboardingComplete() }
</script>

<style scoped>
/* =========================================
便当盒式 (Bento Box) 布局核心
========================================= */
.bento-home-wrapper { padding: 40px; min-height: 100%; box-sizing: border-box; display: flex; flex-direction: column; }
.bento-grid-container { display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: minmax(160px, auto); gap: 24px; max-width: 1280px; margin: 0 auto; width: 100%; }

@media (max-width: 1200px) {
  .bento-grid-container { grid-template-columns: repeat(2, 1fr); }
  .hero-card { grid-column: span 2; }
  .control-center-card { grid-column: span 2; grid-row: span 1; }
  .action-card { grid-column: span 1; }
}

@media (max-width: 768px) {
  .bento-home-wrapper { padding: 20px; }
  .bento-grid-container { grid-template-columns: 1fr; gap: 16px; }
  .hero-card, .control-center-card, .action-card { grid-column: span 1; grid-row: auto; }
  .hero-content { max-width: 100%; }
  .bg-illustration { display: none; }
  .welcome-title { font-size: 28px; }
  .welcome-text { font-size: 16px; }
}
.bento-card { background: #FFFFFF; border-radius: var(--sn-radius-lg); padding: 32px; position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02); border: 1px solid rgba(0,0,0,0.03); transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1); }

/* --- 1. 英雄欢迎卡片 --- */
.hero-card { grid-column: span 3; grid-row: span 2; background: linear-gradient(135deg, var(--sn-primary-light) 0%, var(--sn-primary-soft) 100%); display: flex; align-items: center; position: relative; }
.hero-content { flex: 1; z-index: 10; max-width: 60%; position: relative; }
.hero-top-line { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.date-capsule { font-weight: 700; color: var(--sn-text-secondary); font-size: 15px; letter-spacing: 0.5px; white-space: nowrap; }
.welcome-title { font-size: 36px; font-weight: 800; color: var(--sn-text); margin: 0; letter-spacing: -1px; }
.welcome-text { font-size: 18px; color: var(--sn-text-secondary); line-height: 1.8; font-weight: 500; margin-bottom: 32px; }
.hero-btn { background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary); padding: 16px 32px; border-radius: var(--sn-radius-md); font-weight: 700; cursor: pointer; transition: 0.3s; }
.hero-btn:hover { background: rgba(23, 114, 246, 0.06); transform: translateY(-2px); }

/* 彻底修复：插画定位，贴紧右下角 */
.bg-illustration { position: absolute; right: 0; bottom: 0; height: 100%; width: 50%; object-fit: contain; object-position: right bottom; pointer-events: none; z-index: 1; }

/* --- 2. 控制中心卡片 --- */
.control-center-card { grid-column: span 1; grid-row: span 2; display: flex; flex-direction: column; }
.card-mini-title { font-size: 13px; font-weight: 700; color: #9CA3AF; margin: 0 0 16px 0; }
.control-grid { display: flex; flex-direction: column; gap: 10px; flex: 1; }
.control-btn { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: var(--sn-radius-md); padding: 14px 16px; display: flex; align-items: center; gap: 12px; cursor: pointer; transition: all 0.2s ease; font-size: 15px; font-weight: 600; color: #374151; }
.control-btn:hover { border-color: #D1D5DB; background: #FAFAFA; }
.control-btn.is-active { background: var(--sn-primary); color: #FFF; }
.c-icon { font-size: 20px; color: #6B7280; }

/* Toggle switch 按钮：长辈模式 */
.control-btn.toggle-row-btn { justify-content: space-between; }
.toggle-label { display: flex; align-items: center; gap: 12px; }
.toggle-switch {
  width: 48px; height: 26px; border-radius: 13px; background: #E5E7EB;
  position: relative; transition: background 0.35s cubic-bezier(0.4, 0, 0.2, 1); flex-shrink: 0;
}
.toggle-switch.is-active { background: var(--sn-primary); }
.toggle-thumb {
  width: 22px; height: 22px; border-radius: 50%; background: #FFF;
  position: absolute; top: 2px; left: 2px;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease;
  box-shadow: 0 2px 6px rgba(0,0,0,0.18);
}
.toggle-switch.is-active .toggle-thumb { transform: translateX(22px); box-shadow: 0 2px 8px rgba(23,114,246,0.25); }

/* 音量内联滑动条 */
.control-btn.volume-row { flex-direction: column; align-items: stretch; gap: 8px; cursor: default; }
.control-btn.volume-row:hover { transform: none; background: #FFFFFF; border-color: #E5E7EB; }
.volume-row-header { display: flex; align-items: center; justify-content: space-between; }
.volume-row-label { display: flex; align-items: center; gap: 10px; font-weight: 600; color: #374151; }
.volume-row-value { font-size: 13px; font-weight: 700; color: var(--sn-primary); transition: color 0.3s ease; }
.volume-icon { transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), color 0.3s ease; }
.volume-icon.is-level-0 { color: #9CA3AF; transform: scale(1); }
.volume-icon.is-level-1 { color: #6B7280; transform: scale(1.05); }
.volume-icon.is-level-2 { color: #374151; transform: scale(1.12); }
.volume-icon.is-level-3 { color: #374151; transform: scale(1.18); }
.volume-row-slider { padding: 0 4px; }
.volume-row-slider :deep(.el-slider__runway) { height: 6px; background: #E5E7EB; border-radius: 3px; }
.volume-row-slider :deep(.el-slider__bar) { background: var(--sn-primary); border-radius: 3px; }
.volume-row-slider :deep(.el-slider__button) { width: 16px; height: 16px; border: 2px solid var(--sn-primary); background: #FFF; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
.volume-row-slider :deep(.el-slider__button:hover) { transform: scale(1.1); }

/* Segment toggle 按钮：语音/文字 — 等重双容器 + 物理滑块 */
.control-btn.segment-toggle { padding: 4px; background: #F3F4F6; border-color: #E5E7EB; gap: 0; }
.segment-track {
  position: relative;
  display: flex;
  width: 100%;
}
.segment-thumb {
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  background: #FFFFFF;
  border-radius: var(--sn-radius-sm);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}
.segment-thumb.is-text { transform: translateX(100%); }
.segment-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px; border-radius: var(--sn-radius-sm); border: none; background: transparent;
  font-size: 14px; font-weight: 600; color: #374151; cursor: pointer;
  transition: color 0.3s ease;
  position: relative;
  z-index: 1;
}
.segment-btn.is-active { color: var(--sn-primary); }
.segment-btn .c-icon { font-size: 17px; color: currentColor; }

/* --- 3 & 4. 快捷操作卡片 --- */
.action-card { grid-column: span 2; cursor: pointer; display: flex; align-items: flex-start; gap: 24px; }
.action-card:hover { transform: translateY(-6px); box-shadow: 0 16px 40px rgba(0,0,0,0.06); }
.action-card-icon { font-size: 32px; color: #374151; flex-shrink: 0; }
/* 配色由 global.css 统一管控：同层级入口统一为品牌蓝 */
.action-text { flex: 1; }
.card-arrow { font-size: 24px; font-weight: bold; color: #111; opacity: 0.2; transition: 0.3s; }
.action-card:hover .card-arrow { opacity: 1; transform: translateX(4px); }

/* =========================================
对话框深度样式复写 (Modern Dialog)
========================================= */
:deep(.modern-dialog) { border-radius: var(--sn-radius-xl) !important; overflow: hidden; padding: 0 !important; }
:deep(.modern-dialog .el-dialog__header) { padding: 32px 32px 20px 32px; margin-right: 0; }
:deep(.modern-dialog .el-dialog__title) { font-size: 26px; font-weight: 800; color: #111; letter-spacing: -0.5px; }
:deep(.modern-dialog .el-dialog__body) { padding: 0 32px 32px 32px; }
:deep(.modern-dialog .el-dialog__footer) { padding: 24px 32px; background: #F9FAFB; border-top: 1px solid #F3F4F6; display: flex; justify-content: flex-end; gap: 12px; }
.modern-cancel-btn { background: transparent; border: none; font-size: 15px; font-weight: 700; color: #6B7280; padding: 0 20px; height: 44px; border-radius: 100px; cursor: pointer; transition: 0.2s; }
.modern-cancel-btn:hover { background: #E5E7EB; color: #111; }
.modern-confirm-btn { background: var(--sn-primary); color: #FFF; border: none; font-size: 15px; font-weight: 700; padding: 0 28px; height: 44px; border-radius: 100px; cursor: pointer; box-shadow: 0 4px 12px rgba(23,114,246,0.2); transition: 0.3s; }
.modern-confirm-btn:hover { background: var(--sn-primary-dark); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(23,114,246,0.25); }

/* --- UI重构：模式选择选项卡 --- */
.modern-option-cards { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.option-card { display: flex; align-items: center; padding: 20px; border-radius: 20px; border: 2px solid #F3F4F6; background: #FFFFFF; cursor: pointer; transition: all 0.3s cubic-bezier(0.2, 0, 0, 1); position: relative; }
.option-card:hover { border-color: #E5E7EB; background: #F9FAFB; transform: translateY(-2px); }
.option-card.is-selected { border-color: var(--sn-primary); background: rgba(23, 114, 246, 0.03); box-shadow: 0 8px 24px rgba(23, 114, 246, 0.06); }
.card-icon { width: 48px; height: 48px; border-radius: 50%; background: #F3F4F6; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #6B7280; margin-right: 16px; transition: 0.3s; }
.option-card.is-selected .card-icon { background: var(--sn-primary); color: #FFF; }
.card-text h4 { margin: 0 0 6px 0; font-size: 17px; font-weight: 800; color: #111; }
.card-text p { margin: 0; font-size: 14px; color: #6B7280; line-height: 1.4; }
.check-circle { position: absolute; right: 24px; color: #047857; font-size: 24px; font-weight: bold; animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.volume-control-panel { background: #F9FAFB; border-radius: 20px; padding: 24px; border: 1px solid #F3F4F6; }
.volume-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; font-weight: 700; color: #111; }
.volume-header .v-label { display: flex; align-items: center; gap: 8px; }
.volume-header .v-value { color: var(--sn-primary); font-size: 18px; }
.test-voice-btn { width: 100%; background: #FFF; border: 1px solid #E5E7EB; height: 44px; border-radius: 12px; font-weight: 700; color: #374151; cursor: pointer; transition: 0.2s; margin-top: 12px; }
.test-voice-btn:hover { border-color: #D1D5DB; color: #111; }

/* --- UI重构：账户与安全 --- */
.user-info-section { display: flex; align-items: center; gap: 20px; padding: 24px; background: #F9FAFB; border-radius: 24px; border: 1px solid #F3F4F6; margin-bottom: 24px; }
.user-avatar img { width: 64px; height: 64px; border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.user-name { font-size: 20px; font-weight: 800; color: #111; margin-bottom: 4px; }
.user-role { font-size: 13px; font-weight: 600; color: #6B7280; background: #E5E7EB; display: inline-block; padding: 2px 8px; border-radius: 6px; }
.action-list-group { background: #FFF; border: 1px solid #F3F4F6; border-radius: 20px; overflow: hidden; margin-bottom: 24px; }
.action-list-item { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; cursor: pointer; transition: 0.2s; border-bottom: 1px solid #F3F4F6; }
.action-list-item:last-child { border-bottom: none; }
.action-list-item:hover { background: #F9FAFB; }
.item-left { display: flex; align-items: center; gap: 12px; font-size: 15px; font-weight: 600; color: #111; }
.item-icon-box { width: 36px; height: 36px; background: #F3F4F6; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #4B5563; font-size: 18px; }
.arrow-icon { color: #9CA3AF; font-size: 16px; transition: 0.2s; }
.action-list-item:hover .arrow-icon { transform: translateX(4px); color: #111; }
.logout-text-btn { width: 100%; display: flex; justify-content: center; align-items: center; gap: 8px; background: transparent; border: none; color: #EF4444; font-weight: 700; font-size: 15px; padding: 16px; cursor: pointer; border-radius: 16px; transition: 0.2s; }
.logout-text-btn:hover { background: #FEF2F2; }

/* --- 彻底定制：二次确认与密码输入 --- */
.custom-confirm-content { text-align: center; padding: 20px 0 10px 0; }
.warning-icon { width: 64px; height: 64px; background: #FFFBEB; color: #F59E0B; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 20px auto; }
.custom-confirm-content p { font-size: 16px; color: #374151; margin: 0; font-weight: 600; line-height: 1.6; }
.danger-btn { background: #EF4444 !important; }
.danger-btn:hover { background: #DC2626 !important; box-shadow: 0 6px 16px rgba(239,68,68,0.2) !important; }

.custom-prompt-content { padding: 10px 0; }
.prompt-desc { font-size: 14px; color: #6B7280; margin-bottom: 20px; line-height: 1.5; font-weight: 500;}
.custom-input-wrapper { margin-bottom: 8px; }
:deep(.modern-input .el-input__wrapper) { background: #F3F4F6; border-radius: 16px; height: 52px; box-shadow: none !important; border: 2px solid transparent; transition: 0.3s; }
:deep(.modern-input .el-input__wrapper.is-focus) { background: #FFF; border-color: #111; }
.has-error :deep(.modern-input .el-input__wrapper) { border-color: #EF4444; background: #FEF2F2; }
.error-msg { color: #EF4444; font-size: 13px; font-weight: 600; display: inline-block; margin-top: 4px; }

/* 引导弹窗简化保留 */
.guide-popup-content { text-align: center; }
.guide-icon { color: #047857; margin-bottom: 16px; }
.guide-title { font-size: 26px; font-weight: 800; margin-bottom: 12px; color: #111; }
.guide-desc { color: #666; margin-bottom: 24px; line-height: 1.5; }
.guide-steps { display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }
.guide-step { display: flex; gap: 16px; text-align: left; padding: 16px; background: #F9FAFB; border-radius: 16px; border: 1px solid #F3F4F6; }
.step-number { width: 28px; height: 28px; background: var(--sn-primary); color: #FFF; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; flex-shrink: 0; }
.step-title { font-weight: 800; font-size: 16px; color: #111; margin-bottom: 4px; }
.step-desc { font-size: 13px; color: #666; }
.guide-actions { display: flex; gap: 12px; }

/* 动画效果 */
@keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.3s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* 模式切换时的平滑过渡 */
.welcome-title, .welcome-text, .control-btn, .action-card h3, .action-card p, .date-capsule, .card-text h4, .card-text p, .item-left, .user-name, .logout-text-btn, .modern-confirm-btn, .modern-cancel-btn, .custom-confirm-content p {
  transition: font-size 0.35s ease, padding 0.35s ease, gap 0.35s ease, height 0.35s ease, border-radius 0.35s ease, color 0.25s ease, background-color 0.25s ease, transform 0.3s ease, box-shadow 0.3s ease;
}

/* =========================================
老年人模式适配 (长辈模式)
========================================= */
html[data-accessibility="elderly"] .welcome-title { font-size: 48px; }
html[data-accessibility="elderly"] .welcome-text { font-size: 24px; }
html[data-accessibility="elderly"] .control-btn { padding: 20px; font-size: 20px; border-radius: 24px; }
html[data-accessibility="elderly"] .control-btn.segment-toggle { padding: 6px; }
html[data-accessibility="elderly"] .segment-track { min-height: 56px; }
html[data-accessibility="elderly"] .segment-thumb { border-radius: 18px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
html[data-accessibility="elderly"] .segment-btn { font-size: 20px; gap: 10px; padding: 14px 10px; border-radius: 18px; }
html[data-accessibility="elderly"] .segment-btn .c-icon { font-size: 22px; }
html[data-accessibility="elderly"] .action-card h3 { font-size: 32px; }
html[data-accessibility="elderly"] .action-card p { font-size: 20px; }
html[data-accessibility="elderly"] .bento-grid-container { grid-template-columns: 1fr; gap: 32px; }
html[data-accessibility="elderly"] .date-capsule { font-size: 24px; }
html[data-accessibility="elderly"] .hero-content { max-width: 100%; }
html[data-accessibility="elderly"] .bg-illustration { opacity: 0.15; right: -5%; }
html[data-accessibility="elderly"] .card-text h4 { font-size: 22px; }
html[data-accessibility="elderly"] .card-text p { font-size: 18px; }
html[data-accessibility="elderly"] .item-left { font-size: 20px; }
html[data-accessibility="elderly"] .user-name { font-size: 26px; }
html[data-accessibility="elderly"] .logout-text-btn { font-size: 20px; padding: 24px; }
html[data-accessibility="elderly"] .modern-confirm-btn, html[data-accessibility="elderly"] .modern-cancel-btn { font-size: 18px; height: 56px; }
html[data-accessibility="elderly"] .custom-confirm-content p { font-size: 20px; }
</style>