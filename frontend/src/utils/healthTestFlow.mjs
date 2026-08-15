export const HEALTH_TEST_STEPS = [
  'q1',
  'q1_1',
  'q1_2',
  'q1_3',
  'q1_4',
  'q2',
  'q3',
  'q4',
  'q5',
  'q6',
  'q7',
  'q8',
  'q9'
]

export const RECALL_OPTIONS = [
  { label: '花、桌子、窗户', value: 'flower_table_window' },
  { label: '花、门、米饭', value: 'flower_door_rice' },
  { label: '笔、柜子、门', value: 'pen_cabinet_door' },
  { label: '笔、门、米饭', value: 'pen_door_rice' }
]

export function getNextHealthTestStep(currentStep, answers = {}) {
  const flow = {
    q1: answers.q1MemoryIssue === true ? 'q2' : 'q1_1',
    q1_1: 'q1_2',
    q1_2: 'q1_3',
    q1_3: 'q1_4',
    q1_4: 'q2',
    q2: 'q2_result',
    q2_result: 'q3',
    q3: 'q4',
    q4: 'q5',
    q5: 'q6',
    q6: 'q7',
    q7: 'q8',
    q8: 'q9',
    q9: 'results'
  }

  return flow[currentStep]
}

export function getPreviousHealthTestStep(currentStep, answers = {}) {
  const prevMap = {
    q1: 'intro',
    q1_1: 'q1',
    q1_2: 'q1_1',
    q1_3: 'q1_2',
    q1_4: 'q1_3',
    q2: answers.q1MemoryIssue === false ? 'q1_4' : 'q1',
    q2_result: 'q2',
    q3: 'q2_result',
    q4: 'q3',
    q5: 'q4',
    q6: 'q5',
    q7: 'q6',
    q8: 'q7',
    q9: 'q8'
  }

  return prevMap[currentStep] || 'intro'
}

export function formatLocalDateValue(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function isCorrectRecallAnswer(value) {
  return value === 'flower_door_rice'
}

export function toHealthTestSubmitPayload(answers, assistanceMode, today = new Date()) {
  const payload = {
    q1MemoryIssue: answers.q1MemoryIssue,
    q2Completed: answers.q2Completed,
    q2TimeSeconds: answers.q2TimeSeconds ?? answers.q2TimeUsed ?? 0,
    q3WeightLoss: answers.q3WeightLoss,
    q4AppetiteLoss: answers.q4AppetiteLoss,
    q5VisionIssue: answers.q5VisionIssue,
    q6DiabetesHypertension: answers.q6DiabetesHypertension,
    q7HearingIssue: answers.q7HearingIssue,
    q8Depressed: answers.q8Depressed,
    q9InterestLoss: answers.q9InterestLoss,
    assistanceMode
  }

  if (answers.q1MemoryIssue === false) {
    const todayValue = formatLocalDateValue(today)
    payload.q1_2TodayDate = answers.q1_2TodayDate
    payload.q1_2Correct = answers.q1_2TodayDate === todayValue
    payload.q1_3Location = answers.q1_3Location
    payload.q1_3Correct = Boolean(String(answers.q1_3Location || '').trim())
    payload.q1_4Recall = answers.q1_4Recall
  }

  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== undefined)
  )
}
