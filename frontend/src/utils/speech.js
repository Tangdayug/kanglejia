/**
 * 语音播报工具类
 * 使用 Web Speech API 实现文字转语音功能
 */

class SpeechService {
  constructor() {
    this.synth = window.speechSynthesis
    this.volume = 1.0
    this.rate = 1.0
    this.pitch = 1.0
    this.voice = null
    this.isSpeaking = false

    this.voices = []
    if (this.synth) {
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => {
          this.voices = this.synth.getVoices()
          this.voice = this.voices.find(voice =>
            voice.lang.includes('zh') || voice.lang.includes('CN')
          ) || this.voices[0] || null
        }
      }
    }
  }

  /**
   * 设置音量
   * @param {number} volume - 音量值 0-1
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume))
    localStorage.setItem('speech-volume', this.volume.toString())
  }

  /**
   * 获取当前音量
   */
  getVolume() {
    return this.volume
  }

  /**
   * 播报文字
   * @param {string} text - 要播报的文字
   * @param {Object} options - 可选参数
   * @param {Function} options.onEnd - 播报完成时的回调函数
   */
  speak(text, options = {}) {
    if (!this.synth || !text) {
      return
    }

    this.stop()

    const maxLength = 200
    const cleanText = text.trim()

    if (cleanText.length <= maxLength) {
      this._speakSingle(cleanText, options)
    } else {
      this._speakLongText(cleanText, maxLength, options)
    }
  }

  /**
   * 播报单段文本
   */
  _speakSingle(text, options) {
    const { onEnd, ...speechOptions } = options
    const utterance = new SpeechSynthesisUtterance(text)

    utterance.volume = speechOptions.volume !== undefined ? speechOptions.volume : this.volume
    utterance.rate = speechOptions.rate || this.rate
    utterance.pitch = speechOptions.pitch || this.pitch
    utterance.lang = speechOptions.lang || 'zh-CN'

    if (this.voice) {
      utterance.voice = this.voice
    }

    utterance.onstart = () => {
      this.isSpeaking = true
    }

    utterance.onend = () => {
      this.isSpeaking = false
      if (onEnd) onEnd()
    }

    utterance.onerror = (event) => {
      this.isSpeaking = false
      if (onEnd) onEnd()
    }

    this.synth.speak(utterance)
  }

  /**
   * 播报长文本
   * @param {string} text - 要播报的文字
   * @param {number} maxLength - 每段最大长度
   * @param {Object} options - 可选参数
   * @param {Function} options.onEnd - 播报完成时的回调函数
   */
  _speakLongText(text, maxLength, options) {
    const { onEnd, ...speechOptions } = options
    const segments = []

    let remainingText = text
    while (remainingText.length > 0) {
      if (remainingText.length <= maxLength) {
        segments.push(remainingText)
        break
      }

      let splitPos = maxLength
      const punctuation = ['。', '！', '？', '.', '!', '?', '；', ';', '，', ',', '、', '\n']

      for (let i = 0; i < 30 && i < maxLength; i++) {
        const pos = maxLength - i
        if (punctuation.includes(remainingText[pos])) {
          splitPos = pos + 1
          break
        }
      }

      segments.push(remainingText.substring(0, splitPos))
      remainingText = remainingText.substring(splitPos)
    }

    let index = 0
    const speakNext = () => {
      if (index < segments.length) {
        const utterance = new SpeechSynthesisUtterance(segments[index])

        utterance.volume = speechOptions.volume !== undefined ? speechOptions.volume : this.volume
        utterance.rate = speechOptions.rate || this.rate
        utterance.pitch = speechOptions.pitch || this.pitch
        utterance.lang = speechOptions.lang || 'zh-CN'

        if (this.voice) {
          utterance.voice = this.voice
        }

        utterance.onstart = () => {
          this.isSpeaking = true
        }

        utterance.onend = () => {
          index++
          if (index < segments.length) {
            setTimeout(() => speakNext(), 300)
          } else {
            this.isSpeaking = false
            if (onEnd) onEnd()
          }
        }

        utterance.onerror = (event) => {
          index++
          this.isSpeaking = false
          if (index >= segments.length && onEnd) onEnd()
        }

        this.synth.speak(utterance)
      } else {
        this.isSpeaking = false
      }
    }

    if (segments.length > 0) {
      speakNext()
    }
  }

  /**
   * 强制分割长文本
   */
  _splitText(text, maxLength) {
    const chunks = []
    for (let i = 0; i < text.length; i += maxLength) {
      chunks.push(text.substring(i, i + maxLength))
    }
    return chunks
  }

  /**
   * 停止播报
   */
  stop() {
    if (this.synth) {
      this.synth.cancel()
      this.isSpeaking = false
    }
  }

  /**
   * 暂停播报
   */
  pause() {
    if (this.synth && this.isSpeaking) {
      this.synth.pause()
    }
  }

  /**
   * 恢复播报
   */
  resume() {
    if (this.synth) {
      this.synth.resume()
    }
  }

  /**
   * 是否正在播报
   */
  isActive() {
    return this.isSpeaking
  }

  /**
   * 检查浏览器是否支持语音播报
   */
  isSupported() {
    return !!this.synth
  }
}

// 创建单例实例
const speechService = new SpeechService()

// 从 localStorage 恢复音量设置
const savedVolume = localStorage.getItem('speech-volume')
if (savedVolume !== null) {
  speechService.setVolume(parseFloat(savedVolume))
}

export default speechService
