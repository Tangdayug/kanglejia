/**
 * 文字转语音工具类
 * 使用 Edge TTS API 实现语音合成，支持队列管理和浏览器降级
 */
import request from '@/utils/request'

class EdgeTTS {
  constructor() {
    this.speechQueue = []
    this.isProcessing = false
    this.currentAudio = null
    this.voice = 'xiaoxiao' // 默认女声
    this.fallbackToBrowser = true // API 失败时降级到浏览器语音
    this.browserSpeech = null
    this.userInteracted = false // 用户是否已交互页面
    this.forceStopped = false // 强制停止标志

    // 初始化浏览器语音作为降级方案
    if ('speechSynthesis' in window) {
      this.browserSpeech = window.speechSynthesis
    }

    this._setupInteractionListener()
  }

  /**
   * 设置用户交互监听器以解锁音频播放
   */
  _setupInteractionListener() {
    const unlockAudio = () => {
      this.userInteracted = true

      const dummyAudio = new Audio()
      dummyAudio.play().then(() => {
        dummyAudio.pause()
      }).catch(() => {})

      document.removeEventListener('click', unlockAudio)
      document.removeEventListener('touchstart', unlockAudio)
      document.removeEventListener('keydown', unlockAudio)
    }

    document.addEventListener('click', unlockAudio, { once: true })
    document.addEventListener('touchstart', unlockAudio, { once: true })
    document.addEventListener('keydown', unlockAudio, { once: true })
  }

  /**
   * 初始化 TTS 服务，获取推荐的语音配置
   */
  async init() {
    try {
      const res = await request.get('/tts/recommended')
      if (res.code === '200' && res.data.available) {
        this.voice = res.data.voice
      }
    } catch (error) {
      // 使用默认语音
    }
  }

  /**
   * 语音播报（带队列管理）
   * @param {string} text - 待播报文本
   * @param {Object} options - 配置选项
   * @param {number} options.volume - 音量 (0-1)
   * @param {number} options.rate - 语速 (0.5-2)
   * @param {Function} options.onEnd - 播报完成回调
   * @param {Function} options.onError - 错误回调
   */
  async speak(text, options = {}) {
    return new Promise((resolve, reject) => {
      this.speechQueue.push({ text, options, resolve, reject })
      if (!this.isProcessing) {
        this._processQueue()
      }
    })
  }

  /**
   * 处理语音队列
   */
  async _processQueue() {
    if (this.isProcessing || this.speechQueue.length === 0) {
      return
    }

    this.isProcessing = true

    while (this.speechQueue.length > 0) {
      if (!this.isProcessing) {
        return
      }

      const item = this.speechQueue.shift()
      try {
        await this._speakNow(item.text, item.options)

        if (!this.isProcessing) {
          return
        }

        if (item.resolve) item.resolve()
      } catch (error) {
        if (item.reject) item.reject(error)
        if (item.options.onError) item.options.onError(error)
      }
    }

    this.isProcessing = false
  }

  /**
   * 执行语音播报（内部方法）
   */
  async _speakNow(text, options = {}) {
    const {
      volume = 1,
      rate = 1,
      onEnd = null,
      onError = null
    } = options

    if (this.forceStopped) {
      return
    }

    const cleanText = this._cleanText(text)

    if (!cleanText) {
      throw new Error('Empty text')
    }

    try {
      const audioBlob = await request({
        url: '/tts/speak',
        method: 'post',
        data: {
          text: cleanText,
          voice: this.voice,
          rate: this._convertRate(rate),
          volume: this._convertVolume(volume)
        },
        responseType: 'blob'
      })

      if (this.forceStopped) {
        return
      }

      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)

      await new Promise((resolve, reject) => {
        let thisAudioStopped = false
        let checkInterval = null

        audio.onloadeddata = () => {
          if (this.forceStopped) {
            thisAudioStopped = true
            cleanup()
            resolve()
            return
          }
        }

        audio.onended = () => {
          cleanup()

          if (thisAudioStopped || this.forceStopped) {
            resolve()
            return
          }
          if (onEnd) onEnd()
          resolve()
        }

        audio.onerror = (error) => {
          cleanup()
          if (onError && !this.forceStopped) onError(error)
          resolve()
        }

        const cleanup = () => {
          if (checkInterval) {
            clearInterval(checkInterval)
            checkInterval = null
          }
          if (audioUrl) {
            URL.revokeObjectURL(audioUrl)
          }
          this.currentAudio = null
        }

        this.currentAudio = audio
        if (this.forceStopped) {
          cleanup()
          resolve()
          return
        }

        checkInterval = setInterval(() => {
          if (this.forceStopped) {
            thisAudioStopped = true
            audio.pause()
            audio.currentTime = 0
            cleanup()
            resolve()
          }
        }, 50)

        const playPromise = audio.play()

        if (this.forceStopped) {
          cleanup()
          resolve()
          return
        }

        playPromise.catch((error) => {
          cleanup()
          if (this.forceStopped || thisAudioStopped) {
            resolve()
            return
          }
          reject(error)
        })
      })

    } catch (error) {
      if (error.name === 'NotAllowedError') {
        return
      }

      if (this.fallbackToBrowser && this.browserSpeech) {
        await this._speakWithBrowser(cleanText, options)
      } else {
        throw error
      }
    }
  }

  /**
   * 停止当前播报并清空队列
   */
  stop() {
    this.forceStopped = true
    this.speechQueue = []

    if (this.currentAudio) {
      try {
        this.currentAudio.pause()
        this.currentAudio.currentTime = 0
        this.currentAudio.src = ''
        this.currentAudio.load()
        this.currentAudio = null
      } catch (error) {
        this.currentAudio = null
      }
    }

    if (this.browserSpeech) {
      this.browserSpeech.cancel()
    }

    this.isProcessing = false

    setTimeout(() => {
      this.forceStopped = false
    }, 200)
  }

  /**
   * 检查 TTS 是否可用
   */
  isAvailable() {
    return true
  }

  /**
   * 清理文本（移除 markdown 格式、多余空格等）
   */
  _cleanText(text) {
    if (!text) return ''

    let cleaned = text
      .replace(/^#{1,6}\s+/gm, '')
      .replace(/\*\*/g, '').replace(/__/g, '')
      .replace(/\*/g, '').replace(/_/g, '')
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
      .replace(/\s+/g, ' ')
      .trim()

    // 将长数字序列拆分以便更好的发音
    cleaned = cleaned.replace(/\d{8,}/g, (match) => {
      return match.split('').join(' ')
    })

    return cleaned
  }

  /**
   * 转换语速格式 (0.5-2 → -50% ~ +100%)
   */
  _convertRate(rate) {
    if (rate === 1) return '+0%'
    if (rate < 1) return `${Math.round((rate - 1) * 50)}%`
    return `+${Math.round((rate - 1) * 100)}%`
  }

  /**
   * 转换音量格式 (0-1 → -50% ~ +50%)
   */
  _convertVolume(volume) {
    if (volume === 1) return '+0%'
    return `${Math.round((volume - 1) * 50)}%`
  }

  /**
   * 降级方案：使用浏览器语音合成
   */
  _speakWithBrowser(text, options) {
    return new Promise((resolve, reject) => {
      if (!this.browserSpeech) {
        reject(new Error('Browser speech not available'))
        return
      }

      this.browserSpeech.cancel()

      const utterance = new SpeechSynthesisUtterance(text)

      const voices = this.browserSpeech.getVoices()
      const chineseVoice = voices.find(v => v.lang.startsWith('zh')) || voices[0]
      if (chineseVoice) utterance.voice = chineseVoice

      utterance.rate = options.rate || 1
      utterance.volume = options.volume || 1
      utterance.pitch = 1.0

      utterance.onend = () => {
        if (options.onEnd) options.onEnd()
        resolve()
      }

      utterance.onerror = (error) => {
        if (options.onError) options.onError(error)
        reject(error)
      }

      this.browserSpeech.speak(utterance)
    })
  }
}

// 创建单例实例
const tts = new EdgeTTS()

export default tts
