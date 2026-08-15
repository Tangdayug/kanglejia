/**
 * Chat AI API - API calls for AI chat functionality
 */
import request from '@/utils/request'

/**
 * Create a new chat session
 * @param {Object} data
 * @param {string} data.title - Optional session title
 * @returns {Promise}
 */
export function createSession(data = {}) {
  return request({
    url: '/chat/sessions',
    method: 'post',
    data
  })
}

/**
 * Get all chat sessions for current user
 * @returns {Promise}
 */
export function getSessions() {
  return request({
    url: '/chat/sessions',
    method: 'get'
  })
}

/**
 * Get a specific chat session by ID
 * @param {number} id - Session ID
 * @returns {Promise}
 */
export function getSession(id) {
  return request({
    url: `/chat/sessions/${id}`,
    method: 'get'
  })
}

/**
 * Get all messages for a session
 * @param {number} sessionId - Session ID
 * @returns {Promise}
 */
export function getMessages(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}/messages`,
    method: 'get'
  })
}

/**
 * Send a message and get a non-streaming response
 * @param {Object} data
 * @param {number} data.session_id - Session ID
 * @param {string} data.message - User message
 * @returns {Promise}
 */
export function sendMessage(data) {
  return request({
    url: '/chat/send',
    method: 'post',
    data
  })
}

/**
 * Get recommended questions for the user
 * @param {number} sessionId - Session ID
 * @returns {Promise}
 */
export function getRecommendations(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}/recommendations`,
    method: 'get'
  })
}

/**
 * Check user readiness (health record and health test completion)
 * @returns {Promise}
 */
export function checkReadiness() {
  return request({
    url: '/chat/readiness',
    method: 'get'
  })
}

/**
 * Delete a chat session
 * @param {number} sessionId - Session ID
 * @returns {Promise}
 */
export function deleteSession(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}`,
    method: 'delete'
  })
}

/**
 * Update session title
 * @param {number} sessionId - Session ID
 * @param {string} title - New title
 * @returns {Promise}
 */
export function updateSessionTitle(sessionId, title) {
  return request({
    url: `/chat/sessions/${sessionId}/title`,
    method: 'put',
    params: { title }
  })
}

/**
 * Stream chat response using Server-Sent Events (SSE)
 * @param {number} sessionId - Session ID
 * @param {string} message - User message
 * @param {Function} onMessage - Callback for each message chunk
 * @param {Function} onError - Callback for errors
 * @param {Function} onDone - Callback for completion
 * @returns {Function} - Abort function to cancel the stream
 */
export function streamMessage(sessionId, message, onMessage, onError, onDone) {
  const userStr = localStorage.getItem('student-user')
  let tokenValue = null
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      tokenValue = user?.token
    } catch (e) {
      console.error('Failed to parse user:', e)
    }
  }

  // Build URL with query parameters
  const baseUrl = import.meta.env.VITE_BASE_URL || 'http://localhost:9090'
  // Construct full URL - handle relative paths like '/api'
  const fullUrl = baseUrl.startsWith('http')
    ? `${baseUrl}/chat/stream/${sessionId}`
    : `${window.location.origin}${baseUrl}/chat/stream/${sessionId}`
  const url = new URL(fullUrl)
  url.searchParams.append('message', message)

  console.log('[SSE] Starting stream to:', url.toString())

  // Create EventSource with headers workaround (using fetch for SSE support)
  const controller = new AbortController()

  fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${tokenValue}`,
      'Accept': 'text/event-stream'
    },
    signal: controller.signal
  }).then(response => {
    console.log('[SSE] Response received:', response.status, response.headers.get('content-type'))

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) {
          console.log('[SSE] Stream completed')
          if (onDone) onDone()
          return
        }

        // Decode chunk immediately (no buffering)
        const chunk = decoder.decode(value, { stream: true })
        console.log('[SSE] Raw chunk received:', chunk.length, 'bytes')

        buffer += chunk

        // Process line by line (SSE format: data: {...}\n\n)
        const lines = buffer.split(/\n\n|\r\n\r\n/)
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.trim()) continue

          console.log('[SSE] Processing line:', line.substring(0, 50))

          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            try {
              const parsed = JSON.parse(data)
              console.log('[SSE] Parsed:', parsed)

              if (parsed.error) {
                console.error('[SSE] Error from server:', parsed.error)
                if (onError) onError(parsed.error)
              } else if (parsed.done) {
                console.log('[SSE] Done signal received, sources:', parsed.sources)
                // Pass sources to onDone callback
                if (onDone) onDone(parsed.sources)
                return
              } else if (parsed.content) {
                console.log('[SSE] Content chunk:', parsed.content.length, 'chars')
                if (onMessage) onMessage(parsed.content)
              }
            } catch (e) {
              console.error('[SSE] Failed to parse JSON:', e, 'Data:', data)
            }
          }
        }

        // Immediately read next chunk (don't wait)
        read()
      }).catch(error => {
        if (error.name !== 'AbortError') {
          console.error('[SSE] Read error:', error)
          if (onError) onError(error.message)
        }
      })
    }

    read()
  }).catch(error => {
    console.error('[SSE] Fetch error:', error)
    if (onError) onError(error.message)
  })

  // Return abort function
  return () => {
    console.log('[SSE] Aborting stream')
    controller.abort()
  }
}

/**
 * Speech to text using Web Speech API
 * @param {Object} options
 * @param {string} options.lang - Language code (default: zh-CN)
 * @param {Function} options.onResult - Callback for interim results
 * @param {Function} options.onFinal - Callback for final result
 * @param {Function} options.onError - Callback for errors
 * @returns {Function} - Stop function
 */
export function startSpeechRecognition(options = {}) {
  const {
    lang = 'zh-CN',
    onResult = null,
    onFinal = null,
    onError = null
  } = options

  // Check browser support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

  if (!SpeechRecognition) {
    if (onError) onError('浏览器不支持语音识别功能')
    return null
  }

  const recognition = new SpeechRecognition()
  recognition.lang = lang
  recognition.continuous = false
  recognition.interimResults = true

  recognition.onresult = (event) => {
    let finalTranscript = ''
    let interimTranscript = ''

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        finalTranscript += transcript
      } else {
        interimTranscript += transcript
      }
    }

    if (interimTranscript && onResult) {
      onResult(interimTranscript)
    }
    if (finalTranscript && onFinal) {
      onFinal(finalTranscript)
    }
  }

  recognition.onerror = (event) => {
    if (onError) onError(`语音识别错误: ${event.error}`)
  }

  recognition.onend = () => {
    // Recognition ended
  }

  recognition.start()

  // Return stop function
  return () => recognition.stop()
}
