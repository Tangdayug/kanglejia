<template>
  <Teleport to="body">
    <Transition name="tour-fade">
      <div v-if="visible" class="spotlight-tour" @click="handleBackdropClick">
        <!-- 高亮框：镂空目标元素 -->
        <div
          v-if="currentStep.target && targetRect"
          class="spotlight-hole"
          :style="holeStyle"
          @click.stop
        >
          <div class="spotlight-pulse"></div>
        </div>

        <!-- 教程卡片 -->
        <div
          class="tour-card"
          :class="{ 'is-centered': !currentStep.target || !targetRect }"
          :style="cardStyle"
          @click.stop
        >
          <div class="tour-progress">
            <div
              v-for="i in steps.length"
              :key="i"
              class="progress-dot"
              :class="{ 'is-active': activeIndex >= (i - 1), 'is-current': activeIndex === (i - 1) }"
            ></div>
          </div>

          <div class="tour-body">
            <div class="tour-icon" v-if="currentStep.icon">
              <component :is="currentStep.icon" v-bind="currentStep.iconProps || {}" />
            </div>
            <h3 class="tour-title">{{ currentStep.title }}</h3>
            <p class="tour-description">{{ currentStep.description }}</p>
          </div>

          <div class="tour-footer">
            <button class="tour-btn tour-btn--text" @click="handleSkip">
              {{ isLastStep ? '' : '跳过' }}
            </button>
            <div class="tour-actions">
              <button
                v-if="activeIndex > 0"
                class="tour-btn tour-btn--secondary"
                @click="handlePrev"
              >
                上一步
              </button>
              <button class="tour-btn tour-btn--primary" @click="handleNext">
                {{ isLastStep ? '立即体验' : '下一步' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import {
  DocumentCopy, ChatDotRound, ZoomIn, Microphone, Document,
  User, Calendar, House, Reading, DataLine, Check
} from '@element-plus/icons-vue'
import SpeakerIcon from '@/components/SpeakerIcon.vue'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'complete'])

const activeIndex = ref(0)
const targetRect = ref(null)
const cardRect = ref({ width: 360, height: 240 })
const viewport = ref({ width: 0, height: 0 })
const moveDirection = ref(1)

let resizeObserver = null
let mutationObserver = null
let targetResizeObserver = null

const steps = [
  {
    icon: House,
    title: '欢迎使用康乐家',
    description: '接下来用一分钟带您了解首页与左侧导航的作用。您可以随时跳过。',
    position: 'center'
  },
  {
    target: '.saas-floating-sidebar',
    icon: Reading,
    title: '左侧导航栏',
    description: '通过这里可以快速回到首页、查看健康趋势、获取今日建议、管理个人档案和浏览健康科普内容。',
    position: 'right'
  },
  {
    target: '.hero-card',
    icon: Calendar,
    title: '每日问候与档案入口',
    description: '这里显示当前日期和专属问候，点击「完善健康档案」可快速录入您的健康信息。',
    position: 'right'
  },
  {
    target: '.ai-chat-card',
    icon: ChatDotRound,
    title: 'AI 智能问答',
    description: '点击这里即可向 AI 健康管家咨询健康问题，获取个性化的健康指导。',
    position: 'bottom'
  },
  {
    target: '.health-test-card',
    icon: DocumentCopy,
    title: '健康能力评估',
    description: '定期完成测试，从多维度了解您的内在能力水平与变化趋势。',
    position: 'bottom'
  },
  {
    target: '.toggle-row-btn',
    icon: ZoomIn,
    title: '长辈模式',
    description: '一键放大字体、按钮和间距，让长辈也能轻松看清、轻松操作。',
    position: 'left'
  },
  {
    target: '.segment-toggle',
    icon: Microphone,
    title: '语音 / 文字切换',
    description: '选择您喜欢的交互方式。语音模式下系统会自动播报页面内容。',
    position: 'left'
  },
  {
    target: '.volume-row',
    icon: SpeakerIcon,
    iconProps: { level: 3 },
    title: '语音音量调节',
    description: '在语音模式下拖动滑块，即可调整语音播报的音量大小，图标会随音量变化。',
    position: 'left'
  },
  {
    target: '.account-settings-btn',
    icon: User,
    title: '账户与安全',
    description: '在这里可以切换账号、修改密码或安全退出系统。',
    position: 'left'
  },
  {
    icon: Document,
    title: '开始您的健康之旅',
    description: '教程结束。点击立即体验，进入康乐家系统。',
    position: 'center'
  }
]

const currentStep = computed(() => steps[activeIndex.value] || steps[0])
const isLastStep = computed(() => activeIndex.value === steps.length - 1)

function updateViewport() {
  viewport.value = {
    width: window.innerWidth,
    height: window.innerHeight
  }
}

function measureTarget() {
  if (!props.visible) return
  const step = currentStep.value
  if (!step.target) {
    targetRect.value = null
    observeTarget(null)
    return
  }
  const el = document.querySelector(step.target)
  if (!el) {
    targetRect.value = null
    observeTarget(null)
    return
  }
  const rect = el.getBoundingClientRect()
  targetRect.value = {
    left: rect.left - 12,
    top: rect.top - 12,
    width: rect.width + 24,
    height: rect.height + 24
  }
  // 尝试滚动到可视区域
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  observeTarget(el)
}

function measureCard(el) {
  if (!el) {
    const cardEl = document.querySelector('.tour-card')
    el = cardEl
  }
  if (!el) return
  cardRect.value = {
    width: el.offsetWidth,
    height: el.offsetHeight
  }
}

function observeTarget(el) {
  if (targetResizeObserver) {
    targetResizeObserver.disconnect()
    targetResizeObserver = null
  }
  if (!el || !window.ResizeObserver) return
  targetResizeObserver = new ResizeObserver(() => {
    nextTick(refreshLayout)
  })
  targetResizeObserver.observe(el)
}

function observeCard(el) {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (!el || !window.ResizeObserver) return
  resizeObserver = new ResizeObserver(() => {
    measureCard(el)
  })
  resizeObserver.observe(el)
}

function observeAccessibility() {
  if (!window.MutationObserver) return
  const html = document.documentElement
  mutationObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'data-accessibility') {
        // 模式切换后布局会变化，等待过渡完成再重新定位
        setTimeout(refreshLayout, 400)
      }
    }
  })
  mutationObserver.observe(html, { attributes: true })
}

function waitForLayoutStable(callback) {
  // 等待 CSS 过渡（0.35s）完成后再测量，提高长辈模式下的定位精度
  nextTick(() => {
    setTimeout(callback, 50)
  })
}

const holeStyle = computed(() => {
  if (!targetRect.value) return {}
  return {
    left: `${targetRect.value.left}px`,
    top: `${targetRect.value.top}px`,
    width: `${targetRect.value.width}px`,
    height: `${targetRect.value.height}px`,
    borderRadius: 'var(--sn-radius-lg)'
  }
})

const cardStyle = computed(() => {
  if (!currentStep.value.target || !targetRect.value) {
    return {
      left: '50%',
      top: '50%',
      transform: 'translate(-50%, -50%)'
    }
  }
  const rect = targetRect.value
  const cw = Math.max(cardRect.value.width, 320)
  const ch = Math.max(cardRect.value.height, 180)
  const vw = viewport.value.width
  const vh = viewport.value.height
  const isElderly = document.documentElement.getAttribute('data-accessibility') === 'elderly'
  const gap = isElderly ? 24 : 16
  const minMargin = isElderly ? 20 : 16
  let pos = currentStep.value.position || 'bottom'

  let left, top

  if (pos === 'left') {
    left = rect.left - cw - gap
    top = rect.top + (rect.height - ch) / 2
    if (left < minMargin) {
      left = rect.left + rect.width + gap
      pos = 'right'
    }
  } else if (pos === 'right') {
    left = rect.left + rect.width + gap
    top = rect.top + (rect.height - ch) / 2
    if (left + cw > vw - minMargin) {
      left = rect.left - cw - gap
      pos = 'left'
    }
  } else if (pos === 'top') {
    left = rect.left + (rect.width - cw) / 2
    top = rect.top - ch - gap
    if (top < minMargin) {
      top = rect.top + rect.height + gap
      pos = 'bottom'
    }
  } else {
    left = rect.left + (rect.width - cw) / 2
    top = rect.top + rect.height + gap
    if (top + ch > vh - minMargin) {
      top = rect.top - ch - gap
      pos = 'top'
    }
  }

  // 边界修正
  left = Math.max(minMargin, Math.min(left, vw - cw - minMargin))
  top = Math.max(minMargin, Math.min(top, vh - ch - minMargin))

  return {
    left: `${left}px`,
    top: `${top}px`
  }
})

function refreshLayout() {
  updateViewport()
  waitForLayoutStable(() => {
    const cardEl = document.querySelector('.tour-card')
    measureCard(cardEl)
    observeCard(cardEl)
    measureTarget()
    // 目标元素不存在时自动跳过（如文字模式下没有音量条）
    if (currentStep.value.target && !targetRect.value) {
      if (moveDirection.value === 1 && activeIndex.value < steps.length - 1) {
        activeIndex.value++
        refreshLayout()
      } else if (moveDirection.value === -1 && activeIndex.value > 0) {
        activeIndex.value--
        refreshLayout()
      }
    }
  })
}

function handleNext() {
  if (activeIndex.value < steps.length - 1) {
    moveDirection.value = 1
    activeIndex.value++
    refreshLayout()
  } else {
    closeTour(true)
  }
}

function handlePrev() {
  if (activeIndex.value > 0) {
    moveDirection.value = -1
    activeIndex.value--
    refreshLayout()
  }
}

function handleSkip() {
  closeTour(true)
}

function closeTour(completed) {
  emit('update:visible', false)
  if (completed) emit('complete')
  activeIndex.value = 0
  targetRect.value = null
}

function handleBackdropClick() {
  closeTour(false)
}

function handleKeydown(e) {
  if (!props.visible) return
  if (e.key === 'Escape') closeTour(false)
  if (e.key === 'ArrowRight') handleNext()
  if (e.key === 'ArrowLeft') handlePrev()
}

watch(() => props.visible, (val) => {
  if (val) {
    activeIndex.value = 0
    refreshLayout()
  }
})

onMounted(() => {
  updateViewport()
  window.addEventListener('resize', refreshLayout)
  window.addEventListener('keydown', handleKeydown)
  observeAccessibility()
})

onUnmounted(() => {
  window.removeEventListener('resize', refreshLayout)
  window.removeEventListener('keydown', handleKeydown)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (targetResizeObserver) {
    targetResizeObserver.disconnect()
    targetResizeObserver = null
  }
  if (mutationObserver) {
    mutationObserver.disconnect()
    mutationObserver = null
  }
})
</script>

<style scoped>
.spotlight-tour {
  position: fixed;
  inset: 0;
  z-index: 9999;
  overflow: hidden;
}

.spotlight-hole {
  position: absolute;
  z-index: 1;
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.62),
    0 0 0 4px rgba(23, 114, 246, 0.35),
    0 8px 32px rgba(23, 114, 246, 0.18);
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.spotlight-pulse {
  position: absolute;
  inset: -4px;
  border-radius: inherit;
  border: 2px solid rgba(23, 114, 246, 0.5);
  animation: pulse-ring 2s ease-out infinite;
  pointer-events: none;
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.08); opacity: 0; }
}

.tour-card {
  position: absolute;
  z-index: 2;
  width: 360px;
  max-width: calc(100vw - 32px);
  background: #FFFFFF;
  border-radius: var(--sn-radius-xl);
  padding: 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.tour-card.is-centered {
  text-align: center;
}

.tour-progress {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #E5E7EB;
  transition: all 0.3s ease;
}

.progress-dot.is-active {
  background: var(--sn-primary-light);
}

.progress-dot.is-current {
  width: 24px;
  border-radius: 100px;
  background: var(--sn-primary);
}

.tour-body {
  margin-bottom: 24px;
}

.tour-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px auto;
  font-size: 32px;
  color: var(--sn-primary);
}

.tour-title {
  font-size: 22px;
  font-weight: 800;
  color: #111;
  margin: 0 0 10px 0;
  line-height: 1.3;
}

.tour-description {
  font-size: 15px;
  color: #6B7280;
  line-height: 1.7;
  margin: 0;
}

.tour-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.tour-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.tour-btn {
  height: 42px;
  padding: 0 20px;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.tour-btn--primary {
  background: var(--sn-primary);
  color: #FFF;
  box-shadow: 0 4px 12px rgba(23, 114, 246, 0.2);
}

.tour-btn--primary:hover {
  background: var(--sn-primary-dark);
  transform: translateY(-1px);
}

.tour-btn--secondary {
  background: #F3F4F6;
  color: #374151;
}

.tour-btn--secondary:hover {
  background: #E5E7EB;
}

.tour-btn--text {
  background: transparent;
  color: #9CA3AF;
  padding: 0 10px;
}

.tour-btn--text:hover {
  color: #374151;
}

.tour-fade-enter-active,
.tour-fade-leave-active {
  transition: opacity 0.3s ease;
}

.tour-fade-enter-from,
.tour-fade-leave-to {
  opacity: 0;
}

/* 长辈模式适配 */
html[data-accessibility="elderly"] .tour-card {
  width: min(520px, calc(100vw - 40px));
  max-width: min(520px, calc(100vw - 40px));
  padding: 36px;
  border-radius: var(--sn-radius-xl);
}

html[data-accessibility="elderly"] .tour-title {
  font-size: 30px;
}

html[data-accessibility="elderly"] .tour-description {
  font-size: 20px;
}

html[data-accessibility="elderly"] .tour-btn {
  height: 54px;
  padding: 0 28px;
  font-size: 18px;
}

html[data-accessibility="elderly"] .tour-icon {
  width: 84px;
  height: 84px;
  font-size: 44px;
}

html[data-accessibility="elderly"] .spotlight-hole {
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.68),
    0 0 0 5px rgba(23, 114, 246, 0.45),
    0 8px 32px rgba(23, 114, 246, 0.22);
}

html[data-accessibility="elderly"] .spotlight-pulse {
  inset: -6px;
  border-width: 3px;
}

@media (max-width: 480px) {
  .tour-card {
    width: calc(100vw - 32px);
    padding: 22px;
  }

  .tour-title {
    font-size: 20px;
  }

  .tour-description {
    font-size: 14px;
  }

  .tour-footer {
    flex-wrap: wrap;
  }

  .tour-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
