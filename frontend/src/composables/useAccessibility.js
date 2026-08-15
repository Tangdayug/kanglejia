import { reactive, toRefs } from 'vue'

const ACCESSIBILITY_KEY = 'accessibility-mode'
const ELDERLY_MODE = 'elderly'
const STANDARD_MODE = 'standard'

// 全局响应式状态
const state = reactive({
  isElderlyMode: false
})

/**
 * 无障碍模式管理 Composable
 * 用于切换老年人模式和标准模式
 */
export function useAccessibility() {
  /**
   * 设置无障碍模式
   * @param {string} mode - 'elderly' 或 'standard'
   */
  const setMode = (mode) => {
    if (mode === ELDERLY_MODE) {
      document.documentElement.setAttribute('data-accessibility', ELDERLY_MODE)
      state.isElderlyMode = true
      console.log('[Accessibility] 已切换到老年人模式')
    } else {
      document.documentElement.removeAttribute('data-accessibility')
      state.isElderlyMode = false
      console.log('[Accessibility] 已切换到标准模式')
    }
    // 保存到 localStorage
    localStorage.setItem(ACCESSIBILITY_KEY, mode)
    console.log('[Accessibility] 当前模式:', mode, '属性值:', document.documentElement.getAttribute('data-accessibility'))
  }

  /**
   * 切换模式
   * @returns {string} 新模式
   */
  const toggleMode = () => {
    const newMode = state.isElderlyMode ? STANDARD_MODE : ELDERLY_MODE
    setMode(newMode)
    return newMode
  }

  /**
   * 从 localStorage 恢复模式设置
   */
  const restoreMode = () => {
    const savedMode = localStorage.getItem(ACCESSIBILITY_KEY)
    if (savedMode) {
      setMode(savedMode)
    }
  }

  /**
   * 初始化 - 在组件 onMounted 时调用
   */
  const init = () => {
    restoreMode()
  }

  // 返回响应式状态（使用 toRefs 确保响应式）
  return {
    ...toRefs(state),
    setMode,
    toggleMode,
    init,
    ELDERLY_MODE,
    STANDARD_MODE
  }
}

/**
 * 全局初始化函数 - 在应用启动时调用
 */
export function initAccessibility() {
  const savedMode = localStorage.getItem(ACCESSIBILITY_KEY)
  console.log('[Accessibility] 初始化，保存的模式:', savedMode)

  if (savedMode === ELDERLY_MODE) {
    document.documentElement.setAttribute('data-accessibility', ELDERLY_MODE)
    state.isElderlyMode = true
    console.log('[Accessibility] 已恢复老年人模式')
  } else if (savedMode === STANDARD_MODE) {
    document.documentElement.removeAttribute('data-accessibility')
    state.isElderlyMode = false
    console.log('[Accessibility] 已恢复标准模式')
  } else {
    // 首次使用，默认启用老年人模式
    document.documentElement.setAttribute('data-accessibility', ELDERLY_MODE)
    state.isElderlyMode = true
    localStorage.setItem(ACCESSIBILITY_KEY, ELDERLY_MODE)
    console.log('[Accessibility] 首次使用，已启用老年人模式（默认）')
  }

  console.log('[Accessibility] HTML元素属性:', document.documentElement.getAttribute('data-accessibility'))
}

