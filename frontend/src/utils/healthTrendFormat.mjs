export function cleanAnalysisMarkdown(text = '') {
  return String(text)
    .replace(/```[\s\S]*?```/g, '')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/[*_`>]/g, '')
    .replace(/^\s*[-+]\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

export function escapeHtml(text = '') {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function formatAnalysisHtml(text = '') {
  return escapeHtml(cleanAnalysisMarkdown(text)).replace(/\n/g, '<br>')
}

export function formatTrendDate(dateStr) {
  if (!dateStr) return '未知'
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(dateStr)
  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) return '未知'

  if (!hasTimezone) {
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }

  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).formatToParts(date).reduce((acc, part) => {
    acc[part.type] = part.value
    return acc
  }, {})

  return `${parts.year}年${parts.month}月${parts.day}日 ${parts.hour}:${parts.minute}`
}

export function riskLevelFromRisks(risks = {}) {
  const riskCount = [
    risks.cognitive,
    risks.motor,
    risks.vitality,
    risks.vision,
    risks.hearing,
    risks.psychological
  ].filter(Boolean).length

  if (riskCount >= 3) return 'high'
  if (riskCount >= 1) return 'medium'
  return 'low'
}

export function getDimensionStatusLabel(hasRisk) {
  return hasRisk ? '风险' : '正常'
}
