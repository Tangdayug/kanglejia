<template>
  <div class="mode-select-container">
    <div class="mode-select-box">
      <div class="title">请选择使用模式</div>

      <div v-if="currentSavedMode" class="current-mode-hint">
        当前模式：<span class="mode-badge">{{ currentModeLabel }}</span>
      </div>

      <div class="mode-buttons">
        <button
          class="mode-button"
          :class="{ 'is-active': selectedMode === 'voice' }"
          @click="selectMode('voice')"
        >
          <el-icon :size="32"><Microphone /></el-icon>
          <span>语音模式（推荐）</span>
        </button>

        <button
          class="mode-button"
          :class="{ 'is-active': selectedMode === 'text' }"
          @click="selectMode('text')"
        >
          <el-icon :size="32"><Document /></el-icon>
          <span>文字模式</span>
        </button>
      </div>

      <div v-if="selectedMode === 'voice'" class="mode-description">
        <div class="desc-title">
          <el-icon><Microphone /></el-icon>
          <span>语音模式说明</span>
        </div>
        <ul class="desc-list">
          <li>系统会自动播报每个页面的主要文字内容</li>
          <li>点击选项时会播报选项内容</li>
          <li>适合视力不佳或更喜欢语音交互的用户</li>
        </ul>

        <div class="volume-control">
          <div class="volume-label">
            <el-icon><MuteNotification /></el-icon>
            <span>语音音量</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            v-model.number="volume"
            class="volume-slider"
            @change="onVolumeChange"
          />
          <span class="volume-value">{{ volume }}%</span>
          <button class="test-voice-btn" @click="testVolume">
            <el-icon><MuteNotification /></el-icon> 试听
          </button>
        </div>
      </div>

      <div v-if="selectedMode === 'text'" class="mode-description">
        <div class="desc-title">
          <el-icon><Document /></el-icon>
          <span>文字模式说明</span>
        </div>
        <ul class="desc-list">
          <li>系统不会进行自动播报</li>
          <li>纯文字阅读体验</li>
          <li>适合喜欢安静阅读的用户</li>
        </ul>
      </div>

      <div class="accessibility-row">
        <button class="text-link" @click="toggleAccessibilityMode">
          <el-icon><ZoomIn /></el-icon>
          {{ isElderlyMode ? '切换到标准模式' : '切换到老年人模式' }}
        </button>
      </div>

      <div class="confirm-section">
        <button class="confirm-btn" @click="confirmMode">
          确认进入
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Microphone, Document, MuteNotification, ZoomIn } from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'
import { useAccessibility } from '@/composables/useAccessibility'

const router = useRouter()
const selectedMode = ref('voice')
const volume = ref(80)
const currentSavedMode = ref(null)
const { speak, stop } = useSpeech()
const { toggleMode, isElderlyMode } = useAccessibility()

const currentModeLabel = computed(() => {
  if (currentSavedMode.value === 'voice') return '语音模式'
  if (currentSavedMode.value === 'text') return '文字模式'
  return '未设置'
})

function toggleAccessibilityMode() {
  toggleMode()
}

onMounted(() => {
  const savedMode = localStorage.getItem('user-mode')
  if (savedMode) {
    currentSavedMode.value = savedMode
    selectedMode.value = savedMode
  }

  const savedVolume = localStorage.getItem('speech-volume')
  if (savedVolume) {
    volume.value = Math.round(parseFloat(savedVolume) * 100)
  }

  if (selectedMode.value === 'voice') {
    setTimeout(() => {
      speak('欢迎使用老年人内在能力减退管理支持系统。请选择您的使用模式。我们推荐使用语音模式，系统将为您提供语音播报服务。')
    }, 500)
  }
})

function selectMode(mode) {
  selectedMode.value = mode
  if (mode === 'voice') {
    speak('已选择语音模式。系统将自动播报页面内容。您可以调节下方音量滑块来调整语音音量。')
  } else {
    stop()
  }
}

function onVolumeChange() {
  localStorage.setItem('speech-volume', (volume.value / 100).toString())
}

function testVolume() {
  speak('您好，这是语音播报测试。')
}

function confirmMode() {
  localStorage.setItem('user-mode', selectedMode.value)
  localStorage.setItem('speech-volume', (volume.value / 100).toString())
  setTimeout(() => {
    router.replace('/home')
  }, 500)
}
</script>

<style scoped>
.mode-select-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
  padding: 20px;
}

.mode-select-box {
  background: white;
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
  animation: slideIn 0.5s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.title {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.current-mode-hint {
  text-align: center;
  margin-bottom: 30px;
  font-size: 15px;
  color: #666;
}

.mode-badge {
  display: inline-block;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  font-weight: 600;
  margin-left: 8px;
}

.mode-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 30px;
}

.mode-button {
  flex: 1;
  height: 100px;
  font-size: 18px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 2px solid #e0e0e0;
  background: #fafafa;
  color: #555;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.mode-button.is-active {
  background: linear-gradient(135deg, #757575 0%, #9e9e9e 100%);
  border-color: transparent;
  color: white;
}

.mode-description {
  background: #f8f9fa;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}

.desc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #333;
}

.desc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.desc-list li {
  padding: 8px 0 8px 24px;
  position: relative;
  color: #666;
  line-height: 1.6;
}

.desc-list li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #67c23a;
  font-weight: bold;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  flex-wrap: wrap;
}

.volume-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #666;
  min-width: 80px;
}

.volume-slider {
  flex: 1;
  min-width: 120px;
  height: 6px;
  border-radius: 3px;
  background: #e0e0e0;
  outline: none;
  -webkit-appearance: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #757575;
  cursor: pointer;
}

.volume-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #757575;
  cursor: pointer;
  border: none;
}

.volume-value {
  font-size: 14px;
  color: #666;
  min-width: 45px;
  text-align: right;
}

.test-voice-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border: 1px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
}

.accessibility-row {
  text-align: center;
  margin-bottom: 20px;
}

.text-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  text-decoration: underline;
}

.confirm-section {
  text-align: center;
}

.confirm-btn {
  width: 200px;
  height: 48px;
  font-size: 16px;
  border: none;
  border-radius: 12px;
  background: #409eff;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.confirm-btn:hover {
  background: #66b1ff;
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .mode-select-container {
    padding: 16px;
    align-items: stretch;
  }

  .mode-select-box {
    padding: 24px 20px;
    margin: auto 0;
  }

  .title {
    font-size: 26px;
  }

  .mode-buttons {
    flex-direction: column;
    gap: 12px;
  }

  .mode-button {
    height: 80px;
    font-size: 17px;
  }

  .volume-control {
    flex-direction: column;
    align-items: stretch;
  }

  .volume-slider {
    width: 100%;
  }

  .confirm-btn {
    width: 100%;
    height: 52px;
    font-size: 18px;
  }
}
</style>
