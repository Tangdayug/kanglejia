/**
 * 引导弹窗状态管理
 * 用于控制首次使用引导弹窗的显示和状态
 */
const ONBOARDING_KEY = 'onboarding-completed'

export function useOnboarding() {
  /**
   * 检查引导状态
   * @returns {Object} { completed: boolean, userId?: string, timestamp?: number }
   */
  const checkOnboardingStatus = () => {
    const saved = localStorage.getItem(ONBOARDING_KEY)
    if (!saved) return { completed: false }

    try {
      const status = JSON.parse(saved)

      // 验证用户ID是否匹配
      const user = JSON.parse(localStorage.getItem('student-user') || '{}')
      const currentUserId = user.id || user.username

      if (status.userId !== currentUserId) {
        // 用户ID不匹配，需要重新显示引导
        return { completed: false }
      }

      return status
    } catch (e) {
      console.error('检查引导状态出错:', e)
      return { completed: false }
    }
  }

  /**
   * 标记引导完成
   */
  const markOnboardingComplete = () => {
    try {
      const user = JSON.parse(localStorage.getItem('student-user') || '{}')
      const status = {
        userId: user?.id || user?.username || 'unknown',
        completed: true,
        timestamp: Date.now()
      }
      localStorage.setItem(ONBOARDING_KEY, JSON.stringify(status))
    } catch (e) {
      console.error('标记引导完成出错:', e)
    }
  }

  /**
   * 重置引导状态
   * 用于测试或允许用户重新查看引导
   */
  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY)
  }

  return {
    checkOnboardingStatus,
    markOnboardingComplete,
    resetOnboarding
  }
}
