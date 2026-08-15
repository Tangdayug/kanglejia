<template>
  <div class="mobile-chat-input">
    <div v-if="isRecording" class="recording-bar">
      <span class="recording-dot"></span>
      <span>正在听… {{ recordingText }}</span>
    </div>
    <div class="input-row">
      <a-button
        type="default"
        shape="circle"
        class="voice-btn"
        :class="{ recording: isRecording }"
        :disabled="disabled || isLoading"
        @click="toggleVoice"
      >
        <audio-outlined />
      </a-button>
      <a-textarea
        v-model:value="inputText"
        :rows="1"
        :auto-size="{ minRows: 1, maxRows: 4 }"
        placeholder="输入您的健康问题，或点击话筒说话"
        :disabled="disabled || isLoading"
        @pressEnter="handleSend"
        class="message-textarea"
      />
      <a-button
        type="primary"
        shape="circle"
        class="send-btn"
        :disabled="!inputText.trim() || disabled || isLoading"
        :loading="isLoading"
        @click="handleSend"
      >
        <send-outlined />
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { AudioOutlined, SendOutlined } from '@ant-design/icons-vue'
import { startSpeechRecognition } from '@shared/api/chatAI'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  isLoading: { type: Boolean, default: false }
})

const emit = defineEmits(['send'])

const inputText = ref('')
const isRecording = ref(false)
const recordingText = ref('')
let stopRecognition = null

function handleSend(e) {
  if (e && e.shiftKey) return
  const text = inputText.value.trim()
  if (text && !props.disabled && !props.isLoading) {
    emit('send', text)
    inputText.value = ''
  }
}

function toggleVoice() {
  if (isRecording.value) {
    stopVoice()
  } else {
    startVoice()
  }
}

function startVoice() {
  isRecording.value = true
  recordingText.value = ''
  stopRecognition = startSpeechRecognition({
    lang: 'zh-CN',
    onResult: (text) => { recordingText.value = text },
    onFinal: (text) => {
      inputText.value = text
      recordingText.value = ''
      isRecording.value = false
    },
    onError: () => {
      isRecording.value = false
      recordingText.value = ''
    }
  })
}

function stopVoice() {
  if (stopRecognition) {
    stopRecognition()
    stopRecognition = null
  }
  isRecording.value = false
  recordingText.value = ''
}
</script>

<style scoped>
.mobile-chat-input {
  background: #fff;
  border-top: 1px solid #eee;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
}

.recording-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff2f0;
  color: #ff4d4f;
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 14px;
}

.recording-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4d4f;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.voice-btn {
  width: 52px;
  height: 52px;
  min-height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.voice-btn.recording {
  background: #ff4d4f;
  color: #fff;
  border-color: #ff4d4f;
}

.message-textarea {
  flex: 1;
  font-size: 18px;
}

.message-textarea :deep(.ant-input) {
  font-size: 18px !important;
  min-height: 52px;
  padding: 12px 14px;
}

.send-btn {
  width: 52px;
  height: 52px;
  min-height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
</style>
