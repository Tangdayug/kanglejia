<template>
  <div class="mobile-register">
    <div class="register-content">
      <div class="brand-header">
        <img src="@shared/assets/imgs/logo2.png" alt="Logo" class="brand-logo" />
        <h1 class="brand-name">注册康乐家</h1>
        <p class="brand-slogan">开启您的健康之旅</p>
      </div>

      <a-form :model="form" class="register-form">
        <a-form-item>
          <a-input
            v-model:value="form.username"
            placeholder="请输入账号"
            size="large"
          >
            <template #prefix><user-outlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item>
          <a-input-password
            v-model:value="form.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix><lock-outlined /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            size="large"
            block
            :loading="loading"
            @click="register"
            class="register-btn"
          >
            注册并登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="auth-footer">
        <span>已有账号？</span>
        <a @click="goLogin">去登录</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import request from '@shared/utils/request'
import { useSpeech } from '@shared/composables/useSpeech'

const router = useRouter()
const { speakPageTitle } = useSpeech()

const form = reactive({ username: '', password: '', role: 'USER' })
const loading = ref(false)

onMounted(() => {
  const user = localStorage.getItem('student-user')
  if (user) {
    router.replace('/home')
    return
  }
  speakPageTitle('注册')
})

function register() {
  if (!form.username || !form.password) {
    message.warning('请输入账号和密码')
    return
  }
  loading.value = true
  request.post('/register', form).then(res => {
    loading.value = false
    if (res.code === '200') {
      localStorage.setItem('student-user', JSON.stringify(res.data))
      localStorage.setItem('user-mode', 'voice')
      message.success('注册成功')
      router.push('/mode-select')
    } else {
      message.error(res.msg || '注册失败')
    }
  }).catch(err => {
    loading.value = false
    message.error(err?.response?.data?.msg || err?.message || '网络异常')
  })
}

function goLogin() {
  router.push('/login')
}
</script>

<style scoped>
.mobile-register {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(180deg, #f0f9ff 0%, #fff 100%);
}

.register-content {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.brand-header {
  text-align: center;
  margin-bottom: 40px;
}

.brand-logo {
  width: 80px;
  height: 80px;
  object-fit: contain;
  margin-bottom: 16px;
}

.brand-name {
  font-size: 28px;
  font-weight: 800;
  color: #111;
  margin: 0 0 8px 0;
}

.brand-slogan {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.register-form :deep(.ant-input-affix-wrapper) {
  min-height: 52px;
  border-radius: 12px;
}

.register-form :deep(.ant-input) {
  font-size: 16px;
}

.register-btn {
  min-height: 52px;
  font-size: 18px;
  border-radius: 12px;
  margin-top: 8px;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  color: #666;
  font-size: 15px;
}

.auth-footer a {
  color: #1890ff;
  margin-left: 4px;
  min-height: auto;
}
</style>
