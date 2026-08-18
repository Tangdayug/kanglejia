<template>
  <div class="register-container">
    <div class="register-card">

      <div class="register-left">
        <img src="@/assets/imgs/grandma_illustration.png" alt="活力老人插画" class="illustration-img" />
      </div>

      <div class="register-right">
        <div class="form-container">
          <div class="brand-container">
            <div class="brand-name">康乐家</div>
            <div class="brand-slogan">内在力量，活力人生</div>
          </div>

          <el-form :model="data.form" ref="formRef" :rules="rules" class="register-form">
            <el-form-item prop="username">
              <el-input
                class="capsule-input"
                prefix-icon="Avatar"
                v-model="data.form.username"
                placeholder="请输入账号"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                class="capsule-input"
                show-password
                prefix-icon="Lock"
                v-model="data.form.password"
                placeholder="请输入密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                class="capsule-button"
                style="width: 100%;"
                @click="register"
              >
                注 册
              </el-button>
            </el-form-item>
          </el-form>

          <div class="login-link">
            已有账号？<el-button type="primary" link @click="goToLogin">请登录</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {reactive, ref} from 'vue'
import request from "@/utils/request";
import {ElMessage} from "element-plus";
import router from "@/router";

const data = reactive({
  form: {}
})

const rules = reactive({
  username: [
    {required: true, message: '请输入账号', trigger: 'blur'}
  ],
  password: [
    {required: true, message: '请输入密码', trigger: 'blur'}
  ]
})

const formRef = ref()

const register = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      request.post('/register', data.form).then(res => {
        if (res.code === '200') {
          ElMessage.success('注册成功')
          // 保存用户信息到 localStorage
          localStorage.setItem('student-user', JSON.stringify(res.data))

          // 设置默认模式为语音模式
          localStorage.setItem('user-mode', 'voice')

          // 直接跳转到主页面
          router.push('/test')
        } else {
          ElMessage.error(res.msg)
        }
      }).catch(err => {
        ElMessage.error(err.response?.data?.msg || err.message)
      })
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
/* 1. 最外层容器：加上 box-sizing 防止内边距撑出滚动条 */
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, var(--sn-primary-soft) 0%, var(--sn-primary-light) 100%);
  padding: 20px;
  box-sizing: border-box; /* 🌟 防止出现外层滚动条 */
}

/* 2. 深色卡片：极致缩小版 (600x360) 适配在线 IDE 预览窗 */
.register-card {
  display: flex;
  width: 100%;
  max-width: 600px;
  height: 360px;
  background: linear-gradient(180deg, var(--sn-primary) 0%, var(--sn-primary-dark) 100%);
  border-radius: 20px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
  position: relative;
}

/* 3. 左侧插画区域 */
.register-left {
  flex: 1.1;
}

/* 4. 插画图片：破框偏移量按缩小比例重算 */
.illustration-img {
  position: absolute;
  z-index: 10;
  pointer-events: none; /* 防止图片遮挡右侧的点击事件 */

  height: 105%;
  bottom: -82px;
  left: -320px;

  width: auto;
  object-fit: contain;
  object-position: left bottom;
  filter: drop-shadow(-4px 6px 10px rgba(0,0,0,0.3));
}

/* 右侧表单区域 */
.register-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  z-index: 20; /* 确保层级高于图片，保证能点击 */
}

.form-container {
  width: 100%;
  max-width: 280px;
  transform: translateX(-30px);
}

.brand-container {
  text-align: center;
  margin-bottom: 25px;
}

/* 标题字体自适应 */
.brand-name {
  font-weight: bold;
  font-size: 26px;
  color: var(--sn-surface);
  letter-spacing: 3px;
  margin-bottom: 6px;
}

.brand-slogan {
  font-size: 12px;
  color: var(--sn-surface);
  letter-spacing: 1px;
  opacity: 0.9;
}

/* --- 输入框样式 (稍微调矮以适应小卡片) --- */
.capsule-input :deep(.el-input__wrapper) {
  height: 36px !important;
  border-radius: 40px !important;
  padding: 0 15px !important;
  background-color: var(--sn-surface) !important;
  box-shadow: none !important;
}

.capsule-input :deep(.el-input__inner) {
  background-color: transparent !important;
  color: var(--sn-text) !important;
  font-size: 14px !important;
}
/* 🌟 新增代码：专门缩小“请输入账号/密码”提示文字的大小 */
.capsule-input :deep(input::placeholder) {
  font-size: 12px !important; /* 字体缩小到 12px，您可以根据需要调整为 12px 或 13px */
}
/* --- 注册按钮样式 --- */
.capsule-button {
  height: 38px !important;
  border-radius: 40px !important;
  background-color: var(--sn-white) !important;
  border-color: var(--sn-white) !important;
  color: var(--sn-primary) !important;
  font-size: 15px !important;
  font-weight: 600;
  transition: all 0.3s ease;
}

.capsule-button:hover {
  background-color: var(--sn-primary-light) !important;
  border-color: var(--sn-primary-light) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
}

/* --- 其他排版 --- */
.register-form {
  margin-top: 10px;
}

.register-form :deep(.el-form-item) {
  margin-bottom: 16px; /* 表单项间距调小 */
}

.login-link {
  text-align: center;
  font-size: 13px;
  color: var(--sn-white);
  margin-top: 15px;
}

.login-link :deep(.el-button--primary.link) {
  color: var(--sn-primary-light);
  font-weight: 600;
}

/* 响应式：移动端隐藏插画区域并居中表单 */
@media (max-width: 768px) {
  .register-container {
    padding: 16px;
  }

  .register-card {
    height: auto;
    padding: 32px 20px;
    flex-direction: column;
    max-width: 100%;
  }

  .register-left {
    display: none;
  }

  .register-right {
    padding: 0;
    transform: none;
  }

  .form-container {
    max-width: 100%;
    transform: none;
    padding: 0 8px;
  }

  .brand-name {
    font-size: 28px;
  }

  .brand-slogan {
    font-size: 14px;
  }

  .capsule-input :deep(.el-input__wrapper) {
    height: 48px !important;
  }

  .capsule-button {
    height: 48px !important;
    font-size: 16px !important;
  }
}
</style>