/**
 * 语音播报 Hook
 * 基于 Edge TTS，支持队列管理和回调机制
 */
import { ref } from 'vue'
import tts from '@/utils/tts'

export function useSpeech() {
  const isVoiceMode = ref(false)
  const isEnabled = ref(false)
  const ttsInitialized = ref(false)

  // 组件挂载时初始化语音模式
  ;(async () => {
    const userMode = localStorage.getItem('user-mode')
    isVoiceMode.value = userMode === 'voice'
    isEnabled.value = isVoiceMode.value && tts.isAvailable()

    if (isEnabled.value) {
      try {
        await tts.init()
        ttsInitialized.value = true
      } catch (error) {
        // 初始化失败时降级到浏览器语音
      }
    }
  })()

  /** 播报文字 */
  function speak(text, delay = 0) {
    if (!isEnabled.value) return

    const doSpeak = () => tts.speak(text)

    if (delay > 0) {
      setTimeout(doSpeak, delay)
    } else {
      doSpeak()
    }
  }

  /** 停止播报 */
  function stop() {
    tts.stop()
  }

  /** 播报选项文字 */
  function speakOption(optionText) {
    if (!isEnabled.value) return
    tts.speak(optionText)
  }

  /** 播报页面标题（延迟300ms） */
  function speakPageTitle(title) {
    speak(title, 300)
  }

  /** 播报列表项文字 */
  function speakListItem(itemText) {
    if (!isEnabled.value) return
    tts.speak(itemText)
  }

  /** 播报文字并执行回调 */
  function speakWithCallback(text, callback, delay = 0) {
    if (!isEnabled.value) {
      if (callback) callback()
      return
    }

    const doSpeak = () => tts.speak(text, { onEnd: callback })

    if (delay > 0) {
      setTimeout(doSpeak, delay)
    } else {
      doSpeak()
    }
  }

  return {
    isVoiceMode,
    isEnabled,
    speak,
    stop,
    speakOption,
    speakPageTitle,
    speakListItem,
    speakWithCallback
  }
}
