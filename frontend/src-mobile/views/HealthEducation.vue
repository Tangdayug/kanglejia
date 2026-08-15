<template>
  <div class="mobile-health-edu page-padding">
    <div class="page-header">
      <a-button type="text" class="back-btn" @click="goBack">
        <left-outlined /> 返回
      </a-button>
      <h1 class="page-title">健康科普</h1>
      <a-button type="primary" size="small" @click="showUploadDialog">
        <plus-outlined /> 发布
      </a-button>
    </div>

    <a-tabs v-model:activeKey="activeCategory" centered class="edu-tabs">
      <a-tab-pane key="all" tab="全部"></a-tab-pane>
      <a-tab-pane key="chronic" tab="慢病"></a-tab-pane>
      <a-tab-pane key="exercise" tab="运动"></a-tab-pane>
      <a-tab-pane key="nutrition" tab="营养"></a-tab-pane>
      <a-tab-pane key="mental" tab="心理"></a-tab-pane>
    </a-tabs>

    <a-spin v-if="loading" class="loading-spin" />

    <a-empty v-else-if="filteredArticles.length === 0" description="暂无科普内容" />

    <div v-else class="article-list">
      <div
        v-for="article in filteredArticles"
        :key="article.id"
        class="article-card"
        @click="viewArticle(article)"
      >
        <div v-if="article.coverImage" class="article-cover">
          <img :src="article.coverImage" :alt="article.title" />
          <span class="type-badge" :class="article.type">{{ getTypeText(article.type) }}</span>
        </div>
        <div class="article-body">
          <div class="article-meta">
            <a-tag size="small">{{ article.category }}</a-tag>
            <span class="article-date">{{ formatDate(article.createdAt) }}</span>
          </div>
          <h3 class="article-title">{{ article.title }}</h3>
          <p class="article-summary">{{ article.summary }}</p>
        </div>
      </div>
    </div>

    <a-modal v-model:open="articleVisible" :title="currentArticle?.title" :footer="null" width="100%">
      <div v-if="currentArticle" class="article-detail">
        <img v-if="currentArticle.coverImage" :src="currentArticle.coverImage" class="detail-cover" />
        <div class="detail-content" v-html="currentArticle.content"></div>
        <video v-if="currentArticle.type === 'video' && currentArticle.videoUrl" :src="currentArticle.videoUrl" controls class="detail-video"></video>
      </div>
    </a-modal>

    <a-modal v-model:open="uploadVisible" title="发布科普" @ok="handleUpload" :confirm-loading="uploading">
      <a-form layout="vertical">
        <a-form-item label="标题" required>
          <a-input v-model:value="uploadForm.title" placeholder="输入标题" />
        </a-form-item>
        <a-form-item label="类型" required>
          <a-radio-group v-model:value="uploadForm.type">
            <a-radio value="article">图文</a-radio>
            <a-radio value="video">视频</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="分类" required>
          <a-select v-model:value="uploadForm.category" placeholder="选择分类">
            <a-select-option value="chronic">慢病管理</a-select-option>
            <a-select-option value="exercise">运动指导</a-select-option>
            <a-select-option value="nutrition">营养饮食</a-select-option>
            <a-select-option value="mental">心理健康</a-select-option>
            <a-select-option value="rehabilitation">康复训练</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="摘要">
          <a-textarea v-model:value="uploadForm.summary" :rows="2" placeholder="一句话概括" />
        </a-form-item>
        <a-form-item label="正文内容" required>
          <a-textarea v-model:value="uploadForm.content" :rows="4" placeholder="编写正文" />
        </a-form-item>
        <a-form-item v-if="uploadForm.type === 'video'" label="视频地址">
          <a-input v-model:value="uploadForm.videoUrl" placeholder="https://..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, LeftOutlined } from '@ant-design/icons-vue'
import { useSpeech } from '@shared/composables/useSpeech'
import request from '@shared/utils/request'

const router = useRouter()
const { speak, stop, speakPageTitle, isEnabled: speechEnabled } = useSpeech()

function goBack() {
  router.back()
}

const loading = ref(false)
const activeCategory = ref('all')
const articles = ref([])
const currentArticle = ref(null)
const articleVisible = ref(false)
const uploadVisible = ref(false)
const uploading = ref(false)

const uploadForm = ref({
  title: '',
  type: 'article',
  category: '',
  coverImage: '',
  summary: '',
  content: '',
  videoUrl: ''
})

onMounted(() => {
  speakPageTitle('健康科普')
  loadArticles()
})
onUnmounted(() => stop())

async function loadArticles() {
  loading.value = true
  try {
    const res = await request.get('/health-education/list')
    articles.value = res || []
  } catch (error) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const filteredArticles = computed(() => {
  if (activeCategory.value === 'all') return articles.value
  return articles.value.filter(article => article.category === activeCategory.value)
})

function getTypeText(type) {
  const types = { article: '图文', video: '视频' }
  return types[type] || '图文'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

async function viewArticle(article) {
  if (article.type === 'article') {
    try {
      loading.value = true
      const res = await request.get(`/health-education/article/${article.id}`)
      currentArticle.value = res
      articleVisible.value = true
    } catch (error) {
      message.error('加载详情失败')
    } finally {
      loading.value = false
    }
  } else {
    currentArticle.value = article
    articleVisible.value = true
  }
  if (speechEnabled.value) {
    speak(`${article.title}。${article.summary || ''}`)
  }
}

function showUploadDialog() {
  uploadForm.value = { title: '', type: 'article', category: '', coverImage: '', summary: '', content: '', videoUrl: '' }
  uploadVisible.value = true
}

async function handleUpload() {
  if (!uploadForm.value.title || !uploadForm.value.category || !uploadForm.value.content) {
    message.warning('请填写必填项')
    return
  }
  uploading.value = true
  try {
    const newArticle = {
      id: Date.now(),
      ...uploadForm.value,
      createdAt: new Date().toISOString()
    }
    articles.value.unshift(newArticle)
    message.success('发布成功')
    uploadVisible.value = false
  } catch (error) {
    message.error('发布失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.mobile-health-edu {
  padding-bottom: 100px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.page-title {
  flex: 1;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}

.back-btn {
  padding: 0;
  font-size: 17px;
  color: #666;
}

.edu-tabs {
  margin-bottom: 12px;
}

.loading-spin {
  display: block;
  text-align: center;
  padding: 40px;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.article-cover {
  position: relative;
  width: 100%;
  height: 160px;
}

.article-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 12px;
}

.type-badge.video {
  background: #1890ff;
}

.article-body {
  padding: 14px;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.article-date {
  font-size: 12px;
  color: #999;
}

.article-title {
  margin: 0 0 8px 0;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.4;
  color: #111;
}

.article-summary {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-detail {
  padding: 8px 0;
}

.detail-cover {
  width: 100%;
  border-radius: 12px;
  margin-bottom: 16px;
}

.detail-content {
  font-size: 16px;
  line-height: 1.8;
  color: #333;
}

.detail-video {
  width: 100%;
  border-radius: 12px;
  margin-top: 16px;
}
</style>
