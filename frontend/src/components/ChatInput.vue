<template>
  <div class="chat-input-container">
    <div v-if="isRecording" class="recording-indicator">
      <div class="recording-dot"></div>
      <span>正在录音... {{ recordingText }}</span>
      <el-button type="danger" size="small" @click="stopRecording">停止</el-button>
    </div>
    <div class="input-wrapper">
      <button
        class="voice-button"
        :class="{ 'is-recording': isRecording }"
        :disabled="disabled || isLoading"
        @click="toggleVoiceInput"
      >
        <el-icon><Microphone /></el-icon>
        <span class="voice-text">{{ isRecording ? '说完点这里' : '说话' }}</span>
      </button>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="输入您的健康问题，或点击左侧“说话”"
        :disabled="disabled || isLoading"
        @keydown.enter.exact="handleSend"
        @keydown.enter.shift.prevent
        class="message-input"
      />
      <el-button
        type="primary"
        :disabled="!inputText.trim() || disabled || isLoading"
        :loading="isLoading"
        @click="handleSend"
        class="send-button"
      >
        发送
      </el-button>
    </div>
    <div class="input-hint">
      点击“说话”可以直接语音提问
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Microphone } from '@element-plus/icons-vue'
import { startSpeechRecognition } from '@/api/chatAI'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

const inputText = ref('')
const isRecording = ref(false)
const recordingText = ref('')
const stopRecognition = ref(null)

function handleSend() {
  const text = inputText.value.trim()
  if (text && !props.disabled && !props.isLoading) {
    emit('send', text)
    inputText.value = ''
  }
}

function toggleVoiceInput() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startVoiceInput()
  }
}

function startVoiceInput() {
  isRecording.value = true
  recordingText.value = ''

  stopRecognition.value = startSpeechRecognition({
    lang: 'zh-CN',
    onResult: (text) => {
      recordingText.value = text
    },
    onFinal: (text) => {
      inputText.value = text
      recordingText.value = ''
      isRecording.value = false
    },
    onError: (error) => {
      console.error('Voice recognition error:', error)
      isRecording.value = false
      recordingText.value = ''
    }
  })
}

function stopRecording() {
  if (stopRecognition.value) {
    stopRecognition.value()
    stopRecognition.value = null
  }
  isRecording.value = false
  recordingText.value = ''
}

// Expose methods
defineExpose({
  focus: () => {
    // Could add focus logic here
  }
})
</script>

<style scoped>
.chat-input-container {
  border-top: 1px solid #e0e0e0;
  padding: 16px;
  background-color: #fff;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #fff3f3;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #f56c6c;
}

.recording-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #f56c6c;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.voice-button {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 56px;
  height: 56px;
  padding: 0;
  border-radius: 16px;
  background: #FFF;
  border: 2px solid #E5E7EB;
  color: #333;
  cursor: pointer;
  transition: 0.2s;
}

.voice-button:hover {
  border-color: var(--sn-primary);
  color: var(--sn-primary);
}

.voice-button .el-icon {
  font-size: 22px;
}

.voice-text {
  font-size: 11px;
  font-weight: 700;
}

.voice-button.is-recording {
  background-color: #f56c6c;
  color: white;
  border-color: #f56c6c;
}

.voice-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 20px;
  padding: 14px 18px;
  resize: none;
  font-size: 16px;
  min-height: 56px !important;
}

.send-button {
  flex-shrink: 0;
  border-radius: 20px;
  padding: 12px 28px;
  height: 56px;
  font-size: 16px;
  font-weight: 700;
}

.send-button:disabled {
  background: #D1D5DB !important;
  border-color: #D1D5DB !important;
  color: #FFF !important;
}

.input-hint {
  font-size: 13px;
  color: #666;
  margin-top: 8px;
  text-align: center;
  font-weight: 600;
}
</style>
