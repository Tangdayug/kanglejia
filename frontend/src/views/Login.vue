<template>
  <div class="figma-pure-landing">
    <div class="case-background" :class="{ 'is-expanded': isExpanded }" @click="toggleLayout">
      <div class="case-track">
        <div v-for="(col, index) in caseData" :key="index" class="case-column" :class="getColClass(index)">
          <div v-for="(img, i) in col" :key="i" class="case-card" :style="{ backgroundImage: `url(${img})` }"></div>
        </div>
      </div>
    </div>

    <header class="site-header">
      <div class="header-container floating-nav-capsule">
        
        <div class="header-left">
          <div class="brand-group">
            <img src="@/assets/imgs/logo2.png" alt="Logo" class="main-logo" />
            <span class="brand-name">康乐家</span>
          </div>
        </div>

        <div class="header-right">
          <button class="nav-action-btn mode-toggle-pill" @click="toggleAccessibilityMode">
            <el-icon><ZoomIn /></el-icon>
            <span>{{ isElderlyMode ? '标准模式' : '长辈模式' }}</span>
          </button>
          
          <div class="auth-group">
            <button class="nav-action-btn login-btn" @click.stop="openAuth('login')">登录</button>
            <button class="nav-action-btn cta-black" @click.stop="openAuth('register')">免费开启评估</button>
          </div>
        </div>

      </div>
    </header>

    <main class="hero-interface">
      <div class="input-focus-area">
        <div class="giant-prompt-box" :class="{ 'is-active': isInputFocused }">
          <div class="placeholder-animation" v-if="!isInputFocused && !userInput">
            {{ typedText }}<span class="cursor">|</span>
          </div>
          
          <textarea 
            class="main-prompt-input"
            v-model="userInput"
            @focus="isInputFocused = true"
            @blur="handleBlur"
            @keyup.enter.prevent="handleStart"
            spellcheck="false"
            :placeholder="isInputFocused ? '' : ''"
          ></textarea>

          <div class="prompt-actions">
            <button class="start-text-btn" @click.stop="handleStart">
              {{ userInput.length > 0 ? '开始评估' : '点击开始' }}
            </button>
            <button class="submit-action-btn" :class="{ 'ready': userInput.length > 0 }" @click.stop="handleStart">
              <el-icon><Right /></el-icon>
            </button>
          </div>
        </div>
      </div>
    </main>

    <footer class="footer-slogan">
      <span>康乐家：AI赋能的个性化内在能力健康管家</span>
      <nav class="footer-links">
        <a href="javascript:void(0)" @click="showAbout">关于系统</a>
        <a href="javascript:void(0)" @click="showPrivacy">隐私政策</a>
      </nav>
    </footer>

    <el-dialog v-model="authVisible" width="400px" :show-close="false" align-center class="auth-dialog">
      <div class="auth-box">
        <h3>{{ isLogin ? '欢迎回来' : '开启健康评估' }}</h3>
        <el-form :model="authForm" ref="formRef" @keyup.enter="doAuth">
          <el-form-item><el-input v-model="authForm.username" placeholder="账号名称" class="auth-field" /></el-form-item>
          <el-form-item><el-input v-model="authForm.password" type="password" show-password placeholder="安全密码" class="auth-field" /></el-form-item>
          <el-button class="auth-submit-btn" :loading="loading" @click="doAuth">
            {{ isLogin ? '立即登录' : '注册并开始测试' }}
          </el-button>
        </el-form>
        <div class="auth-toggle" @click="isLogin = !isLogin">{{ isLogin ? '没有账号？点击注册' : '已有账号？去登录' }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Right, ZoomIn } from '@element-plus/icons-vue' // 引入所需的 Icon
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from "@/utils/request"
import { useAccessibility } from '@/composables/useAccessibility' // 引入无障碍模式钩子

// 引入本地图片资源
import imgGrandparents from '@/assets/imgs/p1_1.jpg'
import imgWalk from '@/assets/imgs/p1_2.jpg'
import imgSwim from '@/assets/imgs/p1_3.jpg'
import imgTaiji from '@/assets/imgs/p1_4.jpg'
import imgExercise from '@/assets/imgs/p1_5.jpg'
import imgYoga from '@/assets/imgs/p1_6.jpg'
import imgRide from '@/assets/imgs/p1_7.jpg'
import imgRun from '@/assets/imgs/p1_8.jpg'
import imgDance from '@/assets/imgs/p1_9.jpg'
import imgClimb from '@/assets/imgs/p1_10.jpg'

const router = useRouter()
const userInput = ref('')
const isInputFocused = ref(false)
const isExpanded = ref(false)

// 无障碍模式切换逻辑
const { toggleMode } = useAccessibility()
const toggleAccessibilityMode = () => {
  toggleMode()
}

// 顶部链接点击提示（已移除顶部弹窗）
const showAbout = () => {}
const showPrivacy = () => {}

// 布局切换逻辑
const toggleLayout = () => { isExpanded.value = !isExpanded.value }
const getColClass = (index) => index === 2 ? 'center-col' : 'side-col'

// 5 列案例数据排布
const caseData = [
  [imgWalk, imgSwim],
  [imgTaiji, imgExercise],
  [imgGrandparents, imgYoga], // 中间列
  [imgRide, imgRun],
  [imgDance, imgClimb]
]

// 打字机逻辑
const typedText = ref('')
const prompts = ['衰老只是个数字!', '点击开始，','轻松测试内在能力!']
let pIdx = 0, cIdx = 0, isDeleting = false

const runTypewriter = () => {
  const current = prompts[pIdx]
  typedText.value = isDeleting ? current.substring(0, cIdx--) : current.substring(0, cIdx++)
  let speed = isDeleting ? 30 : 100
  if (!isDeleting && cIdx === current.length) { speed = 2500; isDeleting = true }
  else if (isDeleting && cIdx === 0) { isDeleting = false; pIdx = (pIdx + 1) % prompts.length; speed = 500 }
  setTimeout(runTypewriter, speed)
}

onMounted(runTypewriter)
const handleBlur = () => { isInputFocused.value = false; if(!userInput.value) cIdx = 0 }

// 业务逻辑
const authVisible = ref(false)
const isLogin = ref(false)
const loading = ref(false)
const authForm = reactive({ username: '', password: '', role: 'USER' })

const openAuth = (mode) => { isLogin.value = mode === 'login'; authVisible.value = true }
const handleStart = () => {
  if (!userInput.value && typedText.value) userInput.value = typedText.value
  if (!userInput.value) return
  isLogin.value = false
  authVisible.value = true
}

const doAuth = () => {
  if (!authForm.username || !authForm.password) {
    return
  }
  loading.value = true
  const api = isLogin.value ? '/login' : '/register'
  request.post(api, authForm).then(res => {
    loading.value = false
    if (res.code === '200') {
      localStorage.setItem('student-user', JSON.stringify(res.data))
      // 未选择使用模式时给一个默认值，避免 /home 跳走
      if (!localStorage.getItem('user-mode')) {
        localStorage.setItem('user-mode', 'text')
      }
      const target = isLogin.value ? '/home' : '/test'
      router.push(target)
    } else {
      ElMessage.error(res.msg || '请求失败')
    }
  }).catch(err => {
    loading.value = false
    const msg = err?.response?.data?.msg || err?.message || '网络异常，请检查网络或服务器地址'
    ElMessage.error(msg)
  })
}
</script>

<style scoped>
.figma-pure-landing {
  min-height: 100vh;
  background-color: var(--sn-bg); /* 官方浅色底 */
  position: relative;
  overflow: hidden;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
}

/* 1. 案例背景重排系统 */
.case-background {
  position: absolute; inset: 0; z-index: 0;
  padding: 140px 4% 0 4%; cursor: pointer;
}
.case-track { display: flex; gap: 24px; height: 100%; justify-content: center; }
.case-column {
  display: flex; flex-direction: column; gap: 24px;
  transition: all 0.7s cubic-bezier(0.19, 1, 0.22, 1);
}
.case-column.side-col { flex: 0 0 160px; }
.case-column.center-col { flex: 0 0 580px; }
.is-expanded .case-column { flex: 1 !important; }

.case-card {
  width: 100%; height: 440px; background-size: cover; background-position: center;
  border-radius: 28px; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  border: 1px solid rgba(0,0,0,0.05);
}

/* 2. 导航栏 (顶部通栏，仅底部圆角) */
.site-header { 
  position: fixed; top: 0; width: 100%; padding: 0 60px; z-index: 100; 
  pointer-events: none;
}
.header-container { 
  display: flex; justify-content: space-between; align-items: center; 
  max-width: 1440px; margin: 0 auto; 
  pointer-events: auto;
}

.floating-nav-capsule {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 14px 40px;
  border-radius: 0 0 24px 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-top: none;
}

.header-left { display: flex; align-items: center; }
.brand-group { display: flex; align-items: center; gap: 14px; }
.main-logo { height: 44px; mix-blend-mode: darken; }
.brand-name { font-size: 26px; font-weight: 800; color: var(--sn-text); letter-spacing: -1.2px; }

.header-right { display: flex; align-items: center; gap: 12px; }

/* 导航按钮统一样式 */
.nav-action-btn {
  height: 44px;
  padding: 0 24px;
  border-radius: var(--sn-radius-md);
  font-size: 15px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}
.nav-action-btn:hover { transform: translateY(-1px); }

.mode-toggle-pill {
  background: var(--sn-slate-light);
  color: var(--sn-text);
  border-color: transparent;
}
.mode-toggle-pill:hover { background: var(--sn-border); color: var(--sn-text); }

.login-btn { background: var(--sn-surface); color: var(--sn-text); border-color: var(--sn-border); }
.login-btn:hover { background: var(--sn-slate-light); border-color: var(--sn-border); }

.cta-black { 
  background: transparent; color: var(--sn-primary); border-color: var(--sn-primary);
}
.cta-black:hover { background: rgba(10, 127, 206, 0.06); border-color: var(--sn-primary-dark); color: var(--sn-primary-dark); }

.auth-group { display: flex; align-items: center; gap: 12px; }

/* 3. 中央巨幕输入区 */
.hero-interface {
  position: relative; z-index: 10; height: 100vh;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none;
}
.input-focus-area { width: 100%; max-width: 1000px; text-align: center; pointer-events: auto; }

.giant-prompt-box {
  width: 100%; height: 300px; 
  background: var(--sn-surface); 
  border: 1px solid var(--sn-border); border-radius: 48px; padding: 60px; position: relative;
  transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}
.giant-prompt-box.is-active {
  border-color: var(--sn-primary); transform: translateY(-10px);
  box-shadow: 0 40px 100px rgba(10, 127, 206,0.12);
}

.main-prompt-input {
  width: 100%; height: 100%; border: none; outline: none; resize: none;
  font-size: 64px; font-weight: 700; color: var(--sn-text); line-height: 1.1; 
  letter-spacing: -3px; background: transparent;
}
.placeholder-animation { position: absolute; top: 60px; left: 60px; font-size: 64px; font-weight: 700; color: var(--sn-text); pointer-events: none; letter-spacing: -3px; text-align: left; }
.cursor { color: var(--sn-text); animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }

.prompt-actions {
  position: absolute; right: 40px; bottom: 40px;
  display: flex; align-items: center; gap: 16px;
}
.start-text-btn {
  background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary);
  padding: 14px 28px; border-radius: 100px;
  font-size: 16px; font-weight: 700; cursor: pointer;
  transition: 0.3s;
}
.start-text-btn:hover { background: rgba(10, 127, 206, 0.06); transform: translateY(-2px); }
.submit-action-btn {
  width: 76px; height: 76px; border-radius: 50%;
  border: 1px solid var(--sn-border); background: var(--sn-surface); color: var(--sn-text); font-size: 32px; cursor: pointer; transition: 0.3s;
}
.submit-action-btn.ready { background: transparent; color: var(--sn-primary); border-color: var(--sn-primary); transform: scale(1.1); }
.submit-action-btn.ready:hover { background: rgba(10, 127, 206, 0.06); }

/* 4. 底部品牌宣言 */
.footer-slogan {
  position: absolute; bottom: 40px; width: 100%;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  font-size: 16px; color: var(--sn-text); font-weight: 600; letter-spacing: 1px;
  text-shadow: 0 1px 0 rgba(255,255,255,0.8), 0 0 12px rgba(255,255,255,0.7);
  padding: 8px 16px;
}
.footer-links { display: flex; gap: 24px; }
.footer-links a { 
  text-decoration: none; color: var(--sn-text-secondary); font-weight: 600; font-size: 14px; 
  transition: color 0.2s; 
}
.footer-links a:hover { color: var(--sn-text); }

/* 认证弹窗 */
:deep(.auth-dialog) { border-radius: 32px !important; }
.auth-box { padding: 30px; text-align: center; }
.auth-field :deep(.el-input__wrapper) { background: var(--sn-slate-light); border-radius: 12px; height: 52px; box-shadow: none !important; }
.auth-submit-btn { width: 100%; height: 52px; background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary); border-radius: 12px; font-weight: 700; margin-top: 20px; }
.auth-submit-btn:hover { background: rgba(10, 127, 206, 0.06); }
.auth-toggle { margin-top: 24px; color: var(--sn-text); font-weight: 700; cursor: pointer; text-decoration: underline; }

.mobile-auth-card {
  display: none;
}

/* 模式切换时的平滑过渡 */
.main-logo, .brand-name, .nav-action-btn, .footer-links a {
  transition: font-size 0.35s ease, height 0.35s ease, padding 0.35s ease, transform 0.3s ease, background-color 0.25s ease, color 0.25s ease;
}

/* 老年人模式下导航栏的放大适配 */
html[data-accessibility="elderly"] .main-logo { height: 60px; }
html[data-accessibility="elderly"] .brand-name { font-size: 34px; letter-spacing: -0.5px; }

/* 长辈模式：高对比、低干扰、易识别 */
html[data-accessibility="elderly"] .case-background { opacity: 0.12; filter: grayscale(0.4); }
html[data-accessibility="elderly"] .floating-nav-capsule {
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
  border-color: rgba(10, 127, 206, 0.15);
}
html[data-accessibility="elderly"] .nav-action-btn {
  height: 60px;
  padding: 0 34px;
  font-size: 19px;
  border-radius: 16px;
}
html[data-accessibility="elderly"] .mode-toggle-pill {
  background: var(--sn-primary);
  color: var(--sn-surface);
  font-weight: 800;
}
html[data-accessibility="elderly"] .mode-toggle-pill:hover {
  background: var(--sn-primary-dark);
}
html[data-accessibility="elderly"] .login-btn {
  background: var(--sn-surface);
  color: var(--sn-text);
  border: 2px solid var(--sn-text);
  font-weight: 800;
}
html[data-accessibility="elderly"] .login-btn:hover {
  background: var(--sn-slate-light);
}
html[data-accessibility="elderly"] .cta-black {
  background: transparent;
  color: var(--sn-primary);
  border: 2px solid var(--sn-primary);
  font-weight: 800;
}
html[data-accessibility="elderly"] .cta-black:hover {
  background: rgba(10, 127, 206, 0.06);
}

/* 中央输入区长辈模式强化 */
html[data-accessibility="elderly"] .input-focus-area { max-width: 1100px; }
html[data-accessibility="elderly"] .giant-prompt-box {
  height: 360px;
  border: 3px solid var(--sn-border);
  border-radius: 56px;
  padding: 70px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
}
html[data-accessibility="elderly"] .giant-prompt-box.is-active {
  border-color: var(--sn-primary);
  box-shadow: 0 40px 100px rgba(10, 127, 206, 0.18);
}
html[data-accessibility="elderly"] .main-prompt-input,
html[data-accessibility="elderly"] .placeholder-animation {
  font-size: 78px;
  letter-spacing: -2px;
  line-height: 1.05;
}
html[data-accessibility="elderly"] .placeholder-animation { color: var(--sn-text); }
html[data-accessibility="elderly"] .start-text-btn {
  padding: 18px 36px;
  font-size: 20px;
  border-radius: 100px;
  font-weight: 800;
  background: transparent;
  color: var(--sn-primary);
  border: 2px solid var(--sn-primary);
}
html[data-accessibility="elderly"] .start-text-btn:hover {
  background: rgba(10, 127, 206, 0.06);
}
html[data-accessibility="elderly"] .submit-action-btn {
  width: 88px;
  height: 88px;
  font-size: 36px;
  background: transparent;
  color: var(--sn-primary);
  border: 2px solid var(--sn-primary);
}
html[data-accessibility="elderly"] .submit-action-btn.ready:hover {
  background: rgba(10, 127, 206, 0.06);
}

/* 底部品牌宣言长辈模式 */
html[data-accessibility="elderly"] .footer-slogan {
  font-size: 20px;
  gap: 18px;
  line-height: 1.6;
}
html[data-accessibility="elderly"] .footer-links { gap: 32px; }
html[data-accessibility="elderly"] .footer-links a {
  font-size: 19px;
  color: var(--sn-text);
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 4px;
}

/* 认证弹窗长辈模式 */
html[data-accessibility="elderly"] .auth-box { padding: 36px; }
html[data-accessibility="elderly"] .auth-box h3 { font-size: 26px; margin-bottom: 24px; }
html[data-accessibility="elderly"] .auth-field :deep(.el-input__wrapper) {
  height: 64px;
  border-radius: 16px;
}
html[data-accessibility="elderly"] .auth-field :deep(.el-input__inner) {
  font-size: 20px;
}
html[data-accessibility="elderly"] .auth-submit-btn {
  height: 60px;
  font-size: 20px;
  border-radius: 16px;
  font-weight: 800;
  background: transparent;
  color: var(--sn-primary);
  border: 2px solid var(--sn-primary);
}
html[data-accessibility="elderly"] .auth-submit-btn:hover {
  background: rgba(10, 127, 206, 0.06);
}
html[data-accessibility="elderly"] .auth-toggle {
  font-size: 18px;
  margin-top: 28px;
}
</style>