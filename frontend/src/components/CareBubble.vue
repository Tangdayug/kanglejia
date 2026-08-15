<template>
  <el-dialog
    v-model="dialogVisible"
    title=""
    width="480px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    class="care-bubble-dialog"
  >
    <div class="care-content">
      <!-- Icon -->
      <div class="care-icon">
        <el-icon :size="55"><ChatDotRound /></el-icon>
      </div>

      <!-- Care message -->
      <div class="care-message">{{ careMessage }}</div>

      <!-- Action buttons -->
      <div class="care-actions">
        <el-button type="primary" size="large" @click="handleChat">
          <el-icon><ChatLineRound /></el-icon>
          <span>AI智能问答</span>
        </el-button>
        <el-button size="large" @click="handleLater">
          今天先不聊
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { ChatDotRound, ChatLineRound } from '@element-plus/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  careMessage: {
    type: String,
    default: '您好，今天感觉怎么样？来和我聊一聊吧'
  }
})

const emit = defineEmits(['chat', 'later'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => {
    if (!val) {
      emit('later')
    }
  }
})

// Handle AI chat button click
const handleChat = () => {
  emit('chat')
}

// Handle "skip for today" button click
const handleLater = () => {
  emit('later')
}
</script>

<style scoped>
.care-bubble-dialog :deep(.el-dialog__header) {
  display: none;
}

.care-bubble-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.care-content {
  text-align: center;
  padding: 30px 20px;
}

.care-icon {
  color: #409eff;
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.care-message {
  font-size: 18px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 24px 0;
  padding: 0 20px;
  font-weight: 500;
}

.care-actions {
  display: flex;
  flex-direction: row;
  justify-content: center;
  gap: 16px;
  padding: 0 40px;
}

.care-actions .el-button {
  height: 48px;
  font-size: 16px;
  border-radius: 24px;
  flex: 1;
  max-width: 200px;
}

.care-actions .el-button :deep(.el-button__content) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.care-actions .el-button :deep(.el-icon) {
  font-size: 18px;
}

/* Elderly mode support */
html[data-accessibility="elderly"] .care-message {
  font-size: 22px;
}

html[data-accessibility="elderly"] .care-actions {
  gap: 20px;
}

html[data-accessibility="elderly"] .care-actions .el-button {
  height: 60px;
  font-size: 20px;
  max-width: 220px;
}

html[data-accessibility="elderly"] .care-actions .el-button :deep(.el-icon) {
  font-size: 22px;
}
</style>
