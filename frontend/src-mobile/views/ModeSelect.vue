<template>
  <div class="mobile-mode-select">
    <div class="mode-content">
      <h1 class="page-title">选择使用模式</h1>
      <p class="page-subtitle">我们将根据您的选择调整交互方式</p>

      <div class="mode-cards">
        <div
          class="mode-card"
          :class="{ active: selectedMode === 'voice' }"
          @click="selectMode('voice')"
        >
          <audio-outlined class="mode-icon" />
          <div class="mode-info">
            <h3>语音模式</h3>
            <p>系统自动播报页面内容</p>
          </div>
          <check-circle-filled v-if="selectedMode === 'voice'" class="check-icon" />
        </div>

        <div
          class="mode-card"
          :class="{ active: selectedMode === 'text' }"
          @click="selectMode('text')"
        >
          <file-text-outlined class="mode-icon" />
          <div class="mode-info">
            <h3>文字模式</h3>
            <p>安静阅读，不被打扰</p>
          </div>
          <check-circle-filled v-if="selectedMode === 'text'" class="check-icon" />
        </div>
      </div>

      <div v-if="selectedMode === 'voice'" class="volume-panel">
        <div class="volume-header">
          <sound-outlined />
          <span>语音音量</span>
          <span class="volume-value">{{ volume }}%</span>
        </div>
        <a-slider v-model:value="volume" :min="0" :max="100" :step="5" />
        <a-button block @click="testVolume" class="test-voice-btn">试听语音</a-button>
      </div>

      <div class="accessibility-row">
        <a-button type="link" @click="toggleAccessibility">
          {{ isElderlyMode ? '切换到标准模式' : '切换到长辈模式' }}
        </a-button>
      </div>

      <a-button type="primary" size="large" block class="confirm-btn" @click="confirmMode">
        确认进入
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  AudioOutlined,
  FileTextOutlined,
  CheckCircleFilled,
  SoundOutlined
} from '@ant-design/icons-vue'
import { useSpeech } from '@shared/composables/useSpeech'
import { useAccessibility } from '@shared/composables/useAccessibility'

const router = useRouter()
const { speak, stop, speakPageTitle } = useSpeech()
const { isElderlyMode, toggleMode } = useAccessibility()

const selectedMode = ref('voice')
const volume = ref(80)

onMounted(() => {
  const savedMode = localStorage.getItem('user-mode')
  if (savedMode) selectedMode.value = savedMode
  const savedVolume = localStorage.getItem('speech-volume')
  if (savedVolume) volume.value = Math.round(parseFloat(savedVolume) * 100)
  speakPageTitle('选择使用模式')
})

function selectMode(mode) {
  selectedMode.value = mode
  if (mode === 'voice') {
    speak('已选择语音模式')
  } else {
    stop()
  }
}

function testVolume() {
  speak('您好，这是语音播报测试。')
}

function toggleAccessibility() {
  const newMode = toggleMode()
  message.success(newMode === 'elderly' ? '已切换到长辈模式' : '已切换到标准模式')
}

function confirmMode() {
  localStorage.setItem('user-mode', selectedMode.value)
  localStorage.setItem('speech-volume', (volume.value / 100).toString())
  message.success(`已选择${selectedMode.value === 'voice' ? '语音' : '文字'}模式`)
  router.replace('/home')
}
</script>

<style scoped>
.mobile-mode-select {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 24px;
  background: #fff;
}

.mode-content {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 800;
  color: #111;
  margin: 0 0 8px 0;
  text-align: center;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0 0 32px 0;
  text-align: center;
}

.mode-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px solid #eee;
  border-radius: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-card.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.mode-icon {
  font-size: 32px;
  color: #666;
}

.mode-card.active .mode-icon {
  color: #1890ff;
}

.mode-info {
  flex: 1;
}

.mode-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #111;
}

.mode-info p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.check-icon {
  font-size: 24px;
  color: #1890ff;
}

.volume-panel {
  background: #f5f5f5;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
}

.volume-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 600;
}

.volume-value {
  margin-left: auto;
  color: #1890ff;
  font-weight: 700;
}

.test-voice-btn {
  margin-top: 8px;
  min-height: 44px;
}

.accessibility-row {
  text-align: center;
  margin-bottom: 24px;
}

.confirm-btn {
  min-height: 52px;
  font-size: 18px;
  border-radius: 12px;
}
</style>
