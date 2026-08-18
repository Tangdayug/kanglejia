<template>
  <div class="health-record-container">
    <el-card class="welcome-card">
      <div class="welcome-content">
        <el-icon class="welcome-icon" :size="60"><Folder /></el-icon>
        <h2>健康档案管理</h2>
        <p>请选择您要使用的功能</p>
      </div>
    </el-card>

    <div class="feature-grid">
      <el-card
        class="feature-card"
        shadow="hover"
        @click="navigateTo('/health-record/info')"
      >
        <div class="card-content">
          <div class="card-icon feature-icon">
            <el-icon :size="40"><Edit /></el-icon>
          </div>
          <h3>信息录入</h3>
          <p>填写和管理个人基本信息、慢性病情况、生活习惯等健康档案</p>
          <el-button type="primary" round>进入</el-button>
        </div>
      </el-card>

      <el-card
        class="feature-card"
        shadow="hover"
        @click="navigateTo('/health-record/history')"
      >
        <div class="card-content">
          <div class="card-icon feature-icon">
            <el-icon :size="40"><Clock /></el-icon>
          </div>
          <h3>历史评估</h3>
          <p>查看历次健康测试结果，AI分析您的健康变化趋势</p>
          <el-button type="primary" round>进入</el-button>
        </div>
      </el-card>

      <el-card
        class="feature-card"
        shadow="hover"
        @click="navigateTo('/health-record/intervention')"
      >
        <div class="card-content">
          <div class="card-icon feature-icon">
            <el-icon :size="40"><Document /></el-icon>
          </div>
          <h3>干预日志</h3>
          <p>查看系统建议的健康干预措施和执行情况记录</p>
          <el-button type="primary" round>进入</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Folder, Edit, Clock, Document } from '@element-plus/icons-vue'
import { useSpeech } from '@/composables/useSpeech'

const router = useRouter()
const { speakPageTitle, speakOption, stop } = useSpeech()

// 页面加载时播报
import { onMounted, onUnmounted } from 'vue'
onMounted(() => {
  speakPageTitle('健康档案管理，请选择功能')
})

// 组件卸载时停止语音播报
onUnmounted(() => {
  stop()
})

function navigateTo(path) {
  speakOption('正在进入')
  setTimeout(() => {
    router.push(path)
  }, 300)
}
</script>

<style scoped>
.health-record-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 30px;
  background: linear-gradient(135deg, var(--sn-primary) 0%, var(--sn-primary-dark) 100%);
  border: none;
}

.welcome-card :deep(.el-card__body) {
  padding: 40px;
}

.welcome-content {
  text-align: center;
  color: white;
}

.welcome-icon {
  color: white;
  margin-bottom: 20px;
}

.welcome-content h2 {
  font-size: 32px;
  margin: 0 0 10px 0;
  color: white;
}

.welcome-content p {
  font-size: 18px;
  margin: 0;
  opacity: 0.9;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.feature-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.feature-card :deep(.el-card__body) {
  padding: 30px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.card-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.feature-icon {
  background: transparent;
  color: var(--sn-text-secondary);
  border: 2px solid var(--sn-border);
}

.card-content h3 {
  font-size: 24px;
  margin: 0 0 15px 0;
  color: var(--sn-text);
}

.card-content p {
  font-size: 14px;
  color: var(--sn-text-secondary);
  line-height: 1.6;
  margin: 0 0 20px 0;
  flex: 1;
}

.card-content .el-button {
  width: 120px;
}
</style>
