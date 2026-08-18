<template>
  <div class="sn-subpage health-education-page">
    
    <div class="sn-subpage-header">
      <div class="sn-subpage-header-inner">
        <button class="sn-back-btn" @click="goHome">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
      </div>
    </div>

    <div class="sn-subpage-body">
      
      <div class="sn-page-header">
        <div class="sn-page-header-main">
          <h1 class="sn-page-title">健康科普</h1>
        </div>
        <div class="sn-page-header-actions">
          <button class="cta-black-btn" @click="showUploadDialog">
            <el-icon><Plus /></el-icon>
            发布内容
          </button>
        </div>
      </div>

      <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange" class="modern-tabs">
        <el-tab-pane label="全部推荐" name="all" />
        <el-tab-pane label="慢病管理" name="chronic" />
        <el-tab-pane label="运动指导" name="exercise" />
        <el-tab-pane label="营养饮食" name="nutrition" />
        <el-tab-pane label="心理健康" name="mental" />
        <el-tab-pane label="康复训练" name="rehabilitation" />
      </el-tabs>

      <el-empty v-if="!loading && filteredArticles.length === 0" description="暂无科普内容" class="modern-empty" />

      <div v-loading="loading" class="modern-article-grid">
        <div
          v-for="article in filteredArticles"
          :key="article.id"
          class="modern-card"
          @click="viewArticle(article); speakArticle(article)"
        >
          <div class="card-cover" v-if="article.coverImage || article.type === 'video'">
            <img v-if="article.coverImage" :src="article.coverImage" :alt="article.title" />
            <div v-else-if="article.type === 'video'" class="video-placeholder">
              <el-icon :size="48"><VideoPlay /></el-icon>
            </div>
            <div class="type-badge" :class="article.type">
              {{ getTypeText(article.type) }}
            </div>
          </div>
          <div class="card-body">
            <div class="meta-row">
              <span class="category-pill">{{ categoryLabel(article.category) }}</span>
              <span class="date-text">{{ formatDate(article.createdAt) }}</span>
            </div>
            <h3 class="card-title">{{ article.title }}</h3>
            <p class="card-summary">{{ article.summary }}</p>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="uploadDialogVisible" title="发布科普" width="600px" class="modern-dialog" :close-on-click-modal="false">
      <el-form :model="uploadForm" label-position="top" class="modern-form">
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="输入吸引人的标题..." />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="类型" required>
              <el-radio-group v-model="uploadForm.type">
                <el-radio value="article">图文</el-radio>
                <el-radio value="video">视频</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" required>
              <el-select v-model="uploadForm.category" placeholder="选择标签" style="width: 100%">
                <el-option label="慢病管理" value="chronic" />
                <el-option label="运动指导" value="exercise" />
                <el-option label="营养饮食" value="nutrition" />
                <el-option label="心理健康" value="mental" />
                <el-option label="康复训练" value="rehabilitation" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="封面图">
          <el-upload class="modern-cover-uploader" action="#" :show-file-list="false" :before-upload="handleCoverUpload" accept="image/*">
            <img v-if="uploadForm.coverImage" :src="uploadForm.coverImage" class="cover-preview" />
            <div v-else class="uploader-placeholder">
              <el-icon><Plus /></el-icon><span>点击上传封面</span>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="uploadForm.summary" type="textarea" :rows="3" placeholder="一句话概括重点..." />
        </el-form-item>
        <el-form-item label="正文内容" required>
          <el-input v-model="uploadForm.content" type="textarea" :rows="8" placeholder="编写正文..." />
        </el-form-item>
        <el-form-item label="上传视频" v-if="uploadForm.type === 'video'">
          <el-upload
            class="modern-video-uploader"
            action="#"
            :show-file-list="false"
            :before-upload="handleVideoUpload"
            accept="video/*"
          >
            <video v-if="uploadForm.videoUrl && uploadForm.videoUrl.startsWith('data:video')" :src="uploadForm.videoUrl" class="video-preview" controls />
            <div v-else class="uploader-placeholder">
              <el-icon><Plus /></el-icon><span>点击上传视频</span>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="或填写视频地址" v-if="uploadForm.type === 'video'">
          <el-input v-model="uploadForm.videoUrl" placeholder="https://..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false" class="modern-btn-cancel">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading" class="modern-btn-submit">确认发布</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="articleDialogVisible" :title="currentArticle?.title" width="800px" class="modern-dialog">
      <div class="modern-article-detail" v-if="currentArticle">
        <div class="speech-floater" v-if="speechEnabled">
          <button class="speech-btn" @click="isSpeaking ? stopSpeaking() : speakArticleDetail()" :class="{ 'is-playing': isSpeaking }">
            <el-icon><component :is="isSpeaking ? 'VideoPause' : 'Microphone'" /></el-icon>
            {{ isSpeaking ? '停止播报' : '语音朗读' }}
          </button>
        </div>
        <div class="detail-cover" v-if="currentArticle.coverImage">
          <img :src="currentArticle.coverImage" :alt="currentArticle.title" />
        </div>
        <div class="detail-content" v-html="currentArticle.content"></div>
        <div class="detail-video" v-if="currentArticle.type === 'video' && currentArticle.videoUrl">
          <video :src="currentArticle.videoUrl" controls style="width: 100%; border-radius: var(--sn-radius-md);"></video>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router' // 引入路由用于返回
import { ElMessage } from 'element-plus'
import { Plus, Microphone, VideoPause, ArrowLeft, VideoPlay } from '@element-plus/icons-vue' // 引入 ArrowLeft
import { useSpeech } from '@/composables/useSpeech'
import request from '@/utils/request'

const router = useRouter()
const { speak, stop, speakPageTitle, isEnabled: speechEnabled } = useSpeech()
const loading = ref(false)
const isSpeaking = ref(false)

function goHome() {
  router.push('/home')
}

function speakArticle(article) {
  if (!speechEnabled.value) return
  stop()
  const typeText = getTypeText(article.type)
  const text = `${article.title}。${typeText}。${article.summary || ''}`
  isSpeaking.value = true
  speak(text, { onEnd: () => { isSpeaking.value = false }})
}

function stopSpeaking() { stop(); isSpeaking.value = false }

function speakArticleDetail() {
  if (!speechEnabled.value || !currentArticle.value) return
  stop()
  const article = currentArticle.value
  let text = `${article.title}。${article.summary || ''}`
  if (article.content) {
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = article.content
    text += ' ' + (tempDiv.textContent || tempDiv.innerText || '')
  }
  isSpeaking.value = true
  speak(text, { onEnd: () => { isSpeaking.value = false }})
}

const activeCategory = ref('all')
const uploadDialogVisible = ref(false)
const articleDialogVisible = ref(false)
const uploading = ref(false)
const articles = ref([])
const currentArticle = ref(null)

const uploadForm = ref({ title: '', type: 'article', category: '', coverImage: '', summary: '', content: '', videoUrl: '', tags: '' })

onMounted(() => { speakPageTitle('健康科普'); loadArticles() })
onUnmounted(() => { stop() })

async function loadArticles() {
  loading.value = true
  try {
    const res = await request.get('/health-education/list')
    articles.value = res || []
  } catch (error) {
    console.error('[HealthEducation] 加载科普内容失败:', error)
    ElMessage.error('加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const filteredArticles = computed(() => {
  if (activeCategory.value === 'all') return articles.value
  return articles.value.filter(article => article.category === activeCategory.value)
})

function handleCategoryChange() {}
function getTypeText(type) { const types = { article: '图文阅读', video: '视频解说' }; return types[type] || '图文' }
function categoryLabel(category) {
  const labels = {
    all: '全部推荐',
    chronic: '慢病管理',
    exercise: '运动指导',
    nutrition: '营养饮食',
    mental: '心理健康',
    rehabilitation: '康复训练'
  }
  return labels[category] || category
}
function formatDate(dateStr) { if (!dateStr) return ''; const date = new Date(dateStr); return date.toLocaleDateString('zh-CN') }

function showUploadDialog() {
  uploadForm.value = { title: '', type: 'article', category: '', coverImage: '', summary: '', content: '', videoUrl: '', tags: '' }
  uploadDialogVisible.value = true
}

function handleCoverUpload(file) {
  const reader = new FileReader()
  reader.onload = (e) => { uploadForm.value.coverImage = e.target.result }
  reader.readAsDataURL(file)
  return false 
}

function handleVideoUpload(file) {
  if (!file.type.startsWith('video/')) {
    ElMessage.warning('请选择视频文件')
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.warning('视频文件大小不能超过 50MB')
    return false
  }
  const reader = new FileReader()
  reader.onload = (e) => { uploadForm.value.videoUrl = e.target.result }
  reader.readAsDataURL(file)
  return false
}

async function handleUpload() {
  if (!uploadForm.value.title || !uploadForm.value.category || !uploadForm.value.content) { ElMessage.warning('请填写必填项'); return }
  uploading.value = true
  try {
    const newArticle = { id: Date.now(), ...uploadForm.value, tags: uploadForm.value.tags ? uploadForm.value.tags.split(',').map(t => t.trim()) : [], createdAt: new Date().toISOString() }
    articles.value.unshift(newArticle)
    ElMessage.success('发布成功')
    uploadDialogVisible.value = false
  } catch (error) { ElMessage.error('上传失败') } finally { uploading.value = false }
}

async function viewArticle(article) {
  if (article.type === 'article') {
    try {
      loading.value = true
      const res = await request.get(`/health-education/article/${article.id}`)
      currentArticle.value = res
      articleDialogVisible.value = true
    } catch (error) {
      console.error('加载文章详情失败:', error); ElMessage.error('加载文章详情失败')
    } finally { loading.value = false }
  } else {
    currentArticle.value = article; articleDialogVisible.value = true
  }
}
</script>

<style scoped>
/* =========================================
全屏突破层 (关键)：让组件霸占整个浏览器窗口
========================================= */


@media (max-width: 992px) {
  .sn-subpage-body { padding: 0 24px 80px 24px; }
  .sn-subpage-header { padding: 16px 24px; }
  .modern-article-grid { grid-template-columns: repeat(2, 1fr); gap: 20px; }
}

@media (max-width: 576px) {
  .sn-subpage-body { padding: 0 16px 60px 16px; }
  .sn-subpage-header { padding: 12px 16px; }
  .modern-article-grid { grid-template-columns: 1fr; }
  .cta-black-btn { width: 100%; justify-content: center; }
}

.cta-black-btn {
  background: transparent;
  color: var(--sn-primary);
  border: 1px solid var(--sn-primary);
  height: 48px;
  padding: 0 24px;
  border-radius: var(--sn-radius-md);
  font-weight: 700;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s;
}
.cta-black-btn:hover { background: rgba(23, 114, 246, 0.06); transform: translateY(-2px); }

/* 深度重写 Tabs (变成胶囊形式) */
.modern-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.modern-tabs :deep(.el-tabs__active-bar) { display: none; }
.modern-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
  color: #666;
  padding: 0 20px !important;
  height: 44px;
  line-height: 44px;
  border-radius: var(--sn-radius-md);
  transition: all 0.3s;
  margin-right: 8px;
}
.modern-tabs :deep(.el-tabs__item.is-active) { color: var(--sn-primary-dark); background: var(--sn-primary-light); }
.modern-tabs :deep(.el-tabs__item:hover) { color: var(--sn-primary-dark); }

.modern-loading, .modern-empty { padding: 100px 0; text-align: center; }

/* 现代化卡片网格 */
.modern-article-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 32px;
  margin-top: 24px;
}

.modern-card {
  background: #FFFFFF;
  border-radius: var(--sn-radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.2, 0, 0, 1);
  border: 1px solid #F0F0F0;
}
.modern-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.06);
  border-color: #EAEAEA;
}

.card-cover {
  width: 100%;
  height: 220px;
  position: relative;
  background: #F9F9F9;
}
.card-cover img { width: 100%; height: 100%; object-fit: cover; }
.type-badge {
  position: absolute;
  top: 16px; left: 16px;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
  color: #111;
  padding: 6px 12px;
  border-radius: var(--sn-radius-sm);
  font-size: 12px;
  font-weight: 700;
}
.type-badge.video { background: var(--sn-primary); color: #FFF; }

.card-body { padding: 24px; }
.meta-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.category-pill { font-size: 13px; font-weight: 700; color: var(--sn-primary-dark); background: var(--sn-primary-light); padding: 4px 10px; border-radius: 6px; }
.date-text { font-size: 13px; color: #999; font-weight: 500; }
.card-title { font-size: 20px; font-weight: 800; color: #111; margin: 0 0 12px 0; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-summary { font-size: 15px; color: #666; line-height: 1.6; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* 弹窗与表单全局样式化 */
:deep(.modern-dialog) { border-radius: var(--sn-radius-xl) !important; }
.modern-form :deep(.el-form-item__label) { font-weight: 700; color: #111; }
.modern-form :deep(.el-input__wrapper), .modern-form :deep(.el-textarea__inner) { background: #F5F5F5; border-radius: var(--sn-radius-md); box-shadow: none; border: 2px solid transparent; transition: 0.3s; }
.modern-form :deep(.el-input__wrapper.is-focus), .modern-form :deep(.el-textarea__inner:focus) { background: #FFF; border-color: var(--sn-primary); }

.modern-cover-uploader { width: 100%; }
.uploader-placeholder { height: 160px; background: #F5F5F5; border-radius: var(--sn-radius-md); display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; gap: 8px; transition: 0.3s; cursor: pointer; }
.uploader-placeholder:hover { background: #EAEAEA; color: #111; }
.cover-preview { width: 100%; height: 160px; border-radius: var(--sn-radius-md); object-fit: cover; }

.modern-video-uploader { width: 100%; }
.modern-video-uploader .uploader-placeholder { height: 200px; }
.video-preview { width: 100%; height: 200px; border-radius: var(--sn-radius-md); object-fit: cover; }
.video-placeholder {
  width: 100%;
  height: 220px;
  background: #F5F5F5;
  border-radius: var(--sn-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.modern-btn-submit { background: var(--sn-primary); border: none; border-radius: var(--sn-radius-md); font-weight: 700; }
.modern-btn-cancel { border-radius: var(--sn-radius-md); font-weight: 600; }

/* 详情面板 */
.modern-article-detail { position: relative; }
.speech-floater { position: absolute; top: -60px; right: 0; }
.speech-btn { background: #F5F5F5; border: none; padding: 10px 20px; border-radius: var(--sn-radius-md); font-weight: 700; display: flex; align-items: center; gap: 8px; cursor: pointer; transition: 0.3s; }
.speech-btn.is-playing { background: var(--sn-primary); color: #FFF; }
.detail-cover img { width: 100%; border-radius: var(--sn-radius-lg); margin-bottom: 24px; }
.detail-content { font-size: 16px; line-height: 1.8; color: #333; }
.detail-content :deep(img) { max-width: 100%; border-radius: var(--sn-radius-md); margin: 24px 0; }

html[data-accessibility="elderly"] .sn-page-title { font-size: 48px; }
html[data-accessibility="elderly"] .card-title { font-size: 24px; }
html[data-accessibility="elderly"] .card-summary { font-size: 18px; }
</style>