import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { message } from 'ant-design-vue'

import './assets/mobile.css'
import './assets/elderly-overrides.css'
import { initAccessibility } from '@shared/composables/useAccessibility'

initAccessibility()

const app = createApp(App)

app.use(router)
app.config.globalProperties.$message = message

app.mount('#app')
