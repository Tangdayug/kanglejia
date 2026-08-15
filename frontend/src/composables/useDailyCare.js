/**
 * Daily Care Hook - Manages daily care popup logic
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getDailyCareMessage } from '@/api/care'
import { useSpeech } from '@/composables/useSpeech'

export function useDailyCare() {
  const router = useRouter()
  const { speak, stop } = useSpeech()

  const visible = ref(false)
  const careMessage = ref('您好，今天感觉怎么样？来和我聊一聊吧')
  const interventionId = ref(null)

  // Load care message (LLM generated)
  const loadCareMessage = async () => {
    try {
      const res = await getDailyCareMessage()
      if (res.data && res.data.message) {
        careMessage.value = res.data.message
        interventionId.value = res.data.interventionId
        visible.value = true

        // Speech synthesis (delay 300ms)
        const userMode = localStorage.getItem('user-mode')
        if (userMode === 'voice') {
          setTimeout(() => {
            speak(careMessage.value, 300)
          }, 300)
        }
      }
    } catch (error) {
      console.error('Failed to load care message:', error)
      // Use default message on error
      careMessage.value = '您好，今天感觉怎么样？来和我聊一聊吧'
      visible.value = true
    }
  }

  // Show care bubble (called from mode select page)
  const showCare = async () => {
    await loadCareMessage()
  }

  // Handle "AI Chat" button click
  const handleChat = () => {
    stop() // Stop any ongoing speech
    visible.value = false

    // Navigate to AI chat with care context
    router.push({
      path: '/chat-ai',
      query: {
        careMessage: careMessage.value,
        interventionId: interventionId.value || ''
      }
    })
  }

  // Handle "Skip for today" button click - navigate to home
  const handleLater = () => {
    stop() // Stop any ongoing speech
    visible.value = false

    // Navigate to home page
    router.push('/home')
  }

  return {
    visible,
    careMessage,
    showCare,
    handleChat,
    handleLater
  }
}
