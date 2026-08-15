<template>
  <div class="mobile-tab-bar">
    <router-link
      v-for="item in tabs"
      :key="item.path"
      :to="item.path"
      class="tab-item"
      :class="{ active: route.path === item.path, center: item.center }"
    >
      <div class="tab-icon-wrap">
        <component :is="item.icon" class="tab-icon" />
      </div>
      <span class="tab-label">{{ item.label }}</span>
    </router-link>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import {
  HomeOutlined,
  FormOutlined,
  MessageOutlined,
  ReadOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

const route = useRoute()

const tabs = [
  { path: '/home', label: '首页', icon: HomeOutlined },
  { path: '/test', label: '测试', icon: FormOutlined },
  { path: '/chat-ai', label: '咨询', icon: MessageOutlined, center: true },
  { path: '/health-education', label: '科普', icon: ReadOutlined },
  { path: '/profile', label: '我的', icon: UserOutlined }
]
</script>

<style scoped>
.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(78px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-around;
  align-items: flex-start;
  padding-top: 6px;
  z-index: 100;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 3px;
  color: #999;
  text-decoration: none;
  min-height: 60px;
  padding-top: 4px;
  transition: all 0.2s ease;
}

.tab-item.active {
  color: #047857;
}

.tab-icon-wrap {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.tab-item.active .tab-icon-wrap {
  background: #e6f4f0;
}

.tab-item.center .tab-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #047857;
  color: #fff;
  margin-top: -16px;
  box-shadow: 0 4px 14px rgba(4, 120, 87, 0.35);
}

.tab-item.center.active .tab-icon-wrap {
  background: #065f46;
}

.tab-icon {
  font-size: 22px;
}

.tab-item.center .tab-icon {
  font-size: 24px;
}

.tab-label {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

/* 长辈模式 */
html[data-accessibility="elderly"] .mobile-tab-bar {
  height: calc(88px + env(safe-area-inset-bottom));
  padding-top: 8px;
}

html[data-accessibility="elderly"] .tab-icon-wrap {
  width: 46px;
  height: 46px;
}

html[data-accessibility="elderly"] .tab-item.center .tab-icon-wrap {
  width: 58px;
  height: 58px;
}

html[data-accessibility="elderly"] .tab-icon {
  font-size: 24px;
}

html[data-accessibility="elderly"] .tab-item.center .tab-icon {
  font-size: 28px;
}

html[data-accessibility="elderly"] .tab-label {
  font-size: 15px;
}
</style>
