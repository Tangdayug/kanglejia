<template>
  <div class="mobile-app" :class="{ 'elderly-mode': isElderlyMode }">
    <div class="mobile-page">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
    <MobileTabBar v-if="showTabBar" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MobileTabBar from './components/MobileTabBar.vue'
import { useAccessibility } from '@shared/composables/useAccessibility'

const route = useRoute()
const { isElderlyMode } = useAccessibility()

const showTabBar = computed(() => {
  const noTabBarRoutes = ['/login', '/register', '/mode-select']
  return !noTabBarRoutes.includes(route.path)
})
</script>

<style scoped>
.mobile-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.mobile-page {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: calc(86px + env(safe-area-inset-bottom));
}

html[data-accessibility="elderly"] .mobile-page {
  padding-bottom: calc(98px + env(safe-area-inset-bottom));
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
