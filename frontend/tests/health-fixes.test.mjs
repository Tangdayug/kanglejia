import assert from 'node:assert/strict'
import {
  getNextHealthTestStep,
  getPreviousHealthTestStep,
  isCorrectRecallAnswer,
  toHealthTestSubmitPayload
} from '../src/utils/healthTestFlow.mjs'
import {
  cleanAnalysisMarkdown,
  formatTrendDate,
  riskLevelFromRisks
} from '../src/utils/healthTrendFormat.mjs'

assert.equal(getNextHealthTestStep('q1', { q1MemoryIssue: true }), 'q2')
assert.equal(getNextHealthTestStep('q1', { q1MemoryIssue: false }), 'q1_1')
assert.equal(getPreviousHealthTestStep('q2', { q1MemoryIssue: false }), 'q1_4')
assert.equal(getPreviousHealthTestStep('q2', { q1MemoryIssue: true }), 'q1')

assert.equal(isCorrectRecallAnswer('flower_door_rice'), true)
assert.equal(isCorrectRecallAnswer('flower_table_window'), false)

assert.deepEqual(
  toHealthTestSubmitPayload(
    {
      q1MemoryIssue: false,
      q1_2TodayDate: '2026-06-28',
      q1_3Location: '上海',
      q1_4Recall: 'flower_door_rice',
      q2Completed: true,
      q2TimeSeconds: 12.4
    },
    'alone',
    new Date('2026-06-28T09:00:00+08:00')
  ),
  {
    q1MemoryIssue: false,
    q1_2TodayDate: '2026-06-28',
    q1_2Correct: true,
    q1_3Location: '上海',
    q1_3Correct: true,
    q1_4Recall: 'flower_door_rice',
    q2Completed: true,
    q2TimeSeconds: 12.4,
    assistanceMode: 'alone'
  }
)

assert.equal(
  cleanAnalysisMarkdown('# 趋势\n**重点**：*保持运动*\n- 每天散步'),
  '趋势\n重点：保持运动\n每天散步'
)
assert.equal(formatTrendDate('2026-06-28T01:30:00+00:00'), '2026年6月28日 09:30')
assert.equal(
  riskLevelFromRisks({
    cognitive: false,
    motor: true,
    vitality: false,
    vision: true,
    hearing: true,
    psychological: false
  }),
  'high'
)

console.log('health fixes logic tests passed')
