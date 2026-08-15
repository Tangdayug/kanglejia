<template>
  <div class="mobile-health-info page-padding">
    <div class="page-header">
      <a-button type="text" class="back-btn" @click="goBack">
        <left-outlined /> 返回
      </a-button>
      <h1 class="page-title">健康档案</h1>
      <span v-if="lastSaveTime" class="save-hint">上次保存 {{ lastSaveTime }}</span>
    </div>

    <a-form :model="formData" layout="vertical" class="health-form">
      <div class="section-card">
        <h3 class="section-title">基本信息 <span class="required">* 必填</span></h3>
        <a-form-item label="姓名" required>
          <a-input v-model:value="formData.basicInfo.name" placeholder="请输入姓名" size="large" />
        </a-form-item>
        <a-form-item label="出生年月" required>
          <a-date-picker v-model:value="formData.basicInfo.birthDate" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" size="large" />
        </a-form-item>
        <a-form-item label="性别" required>
          <a-radio-group v-model:value="formData.basicInfo.gender" button-style="solid">
            <a-radio-button value="male">男</a-radio-button>
            <a-radio-button value="female">女</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="身高 (cm)" required>
          <a-input-number v-model:value="formData.basicInfo.height" :min="0" :max="300" :precision="1" style="width: 100%" size="large" @change="calculateBMI" />
        </a-form-item>
        <a-form-item label="体重 (kg)" required>
          <a-input-number v-model:value="formData.basicInfo.weight" :min="0" :max="300" :precision="1" style="width: 100%" size="large" @change="calculateBMI" />
        </a-form-item>
        <a-form-item label="BMI">
          <a-input v-model:value="formData.basicInfo.bmi" disabled placeholder="自动计算" size="large" />
        </a-form-item>
        <a-form-item label="收缩压 (mmHg)" required>
          <a-input-number v-model:value="formData.basicInfo.systolicBp" :min="0" :max="300" style="width: 100%" size="large" />
        </a-form-item>
        <a-form-item label="舒张压 (mmHg)" required>
          <a-input-number v-model:value="formData.basicInfo.diastolicBp" :min="0" :max="200" style="width: 100%" size="large" />
        </a-form-item>
        <a-form-item label="心率 (次/min)" required>
          <a-input-number v-model:value="formData.basicInfo.heartRate" :min="0" :max="200" style="width: 100%" size="large" />
        </a-form-item>
      </div>

      <div class="section-card">
        <h3 class="section-title">睡眠状况</h3>
        <a-form-item label="过去 1 个月，您是否存在睡眠问题？">
          <a-checkbox-group v-model:value="formData.sleepStatus.sleepIssues" class="checkbox-list">
            <a-checkbox value="good">睡眠良好</a-checkbox>
            <a-checkbox value="difficulty_falling_asleep">入睡困难</a-checkbox>
            <a-checkbox value="easily_wake">易醒</a-checkbox>
            <a-checkbox value="early_wake">早醒</a-checkbox>
            <a-checkbox value="daytime_sleepiness">白天犯困</a-checkbox>
            <a-checkbox value="other">其他</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        <a-form-item v-if="formData.sleepStatus.sleepIssues.includes('other')" label="请说明">
          <a-input v-model:value="formData.sleepStatus.otherSleepIssue" placeholder="请说明其他睡眠问题" size="large" />
        </a-form-item>
      </div>

      <div class="section-card">
        <h3 class="section-title">慢性病情况</h3>
        <a-form-item label="您是否患有或曾患有以下哪些慢性病？">
          <a-checkbox-group v-model:value="formData.chronicDisease.diseases" @change="handleChronicDiseaseChange" class="checkbox-list">
            <a-checkbox value="hypertension">高血压</a-checkbox>
            <a-checkbox value="diabetes">糖尿病</a-checkbox>
            <a-checkbox value="dyslipidemia">血脂异常</a-checkbox>
            <a-checkbox value="coronary_heart_disease">冠心病</a-checkbox>
            <a-checkbox value="stroke">脑卒中</a-checkbox>
            <a-checkbox value="copd">慢阻肺</a-checkbox>
            <a-checkbox value="osteoporosis">骨质疏松</a-checkbox>
            <a-checkbox value="alzheimers">阿尔茨海默</a-checkbox>
            <a-checkbox value="tumor_history">肿瘤病史</a-checkbox>
            <a-checkbox value="other">其他</a-checkbox>
            <a-checkbox value="none">无任何疾病</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        <a-form-item v-if="formData.chronicDisease.diseases.includes('tumor_history')" label="肿瘤部位">
          <a-input v-model:value="formData.chronicDisease.tumorHistory" placeholder="如：肺部、乳腺等" size="large" />
        </a-form-item>
        <a-form-item v-if="formData.chronicDisease.diseases.includes('other')" label="其他疾病名称">
          <a-input v-model:value="formData.chronicDisease.otherDisease" placeholder="请填写病名" size="large" />
        </a-form-item>
      </div>

      <div class="section-card">
        <h3 class="section-title">用药情况</h3>
        <a-form-item label="您现在正在用药吗？">
          <a-radio-group v-model:value="formData.medication.isMedication">
            <a-radio :value="true">正在用药</a-radio>
            <a-radio :value="false">未用药</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item v-if="formData.medication.isMedication" label="正在服用的药物">
          <a-input v-model:value="formData.medication.medicationNames" placeholder="如：缬沙坦、阿托伐他汀" size="large" />
        </a-form-item>
      </div>

      <div class="section-card">
        <h3 class="section-title">生活习惯</h3>
        <a-form-item label="您现在吸烟吗？">
          <a-radio-group v-model:value="formData.lifestyle.smokingStatus" class="radio-list">
            <a-radio value="never">从不吸</a-radio>
            <a-radio value="quit_over_1_year">已戒烟 &gt; 1年</a-radio>
            <a-radio value="quit_within_1_year">已戒烟 ≤ 1年</a-radio>
            <a-radio value="occasional">偶尔吸</a-radio>
            <a-radio value="daily">每天吸</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item v-if="formData.lifestyle.smokingStatus === 'daily'" label="每天平均吸多少支">
          <a-input-number v-model:value="formData.lifestyle.smokingCount" :min="0" :max="100" style="width: 100%" size="large" />
        </a-form-item>
        <a-form-item label="您现在喝酒吗？">
          <a-radio-group v-model:value="formData.lifestyle.drinkingStatus" class="radio-list">
            <a-radio value="never">从不喝</a-radio>
            <a-radio value="quit_over_1_year">已戒酒 &gt; 1年</a-radio>
            <a-radio value="quit_within_1_year">已戒酒 ≤ 1年</a-radio>
            <a-radio value="occasional">偶尔喝</a-radio>
            <a-radio value="weekly">每周喝</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item v-if="formData.lifestyle.drinkingStatus === 'weekly'" label="每周饮酒次数">
          <a-input-number v-model:value="formData.lifestyle.drinkingFrequency" :min="0" :max="7" style="width: 100%" size="large" />
        </a-form-item>
      </div>

      <div class="section-card">
        <h3 class="section-title">运动偏好</h3>
        <a-form-item label="平时您最喜欢、且愿意坚持做的运动（最多选3项）">
          <a-checkbox-group v-model:value="formData.exercise.preferredExercises" @change="handleExerciseChange" class="checkbox-list">
            <a-checkbox value="walking">散步/健走</a-checkbox>
            <a-checkbox value="jogging">慢跑</a-checkbox>
            <a-checkbox value="swimming">游泳</a-checkbox>
            <a-checkbox value="tai_chi">太极拳/八段锦</a-checkbox>
            <a-checkbox value="square_dance">广场舞</a-checkbox>
            <a-checkbox value="yoga">瑜伽/普拉提</a-checkbox>
            <a-checkbox value="racket_sports">乒乓/羽毛球</a-checkbox>
            <a-checkbox value="cycling">骑车</a-checkbox>
            <a-checkbox value="other">其他</a-checkbox>
            <a-checkbox value="no_preference">无偏好/很少动</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        <a-form-item v-if="formData.exercise.preferredExercises.includes('other')" label="请说明其他运动">
          <a-input v-model:value="formData.exercise.otherExercise" placeholder="请说明其他运动" size="large" />
        </a-form-item>
      </div>

      <div class="section-card">
        <h3 class="section-title">社会人口学信息</h3>
        <a-form-item label="婚姻状态" required>
          <a-select v-model:value="formData.demographic.maritalStatus" placeholder="请选择" size="large">
            <a-select-option value="unmarried">未婚</a-select-option>
            <a-select-option value="married">已婚</a-select-option>
            <a-select-option value="widowed">丧偶</a-select-option>
            <a-select-option value="divorced">离婚</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="工作状态" required>
          <a-select v-model:value="formData.demographic.workStatus" placeholder="请选择" size="large">
            <a-select-option value="employed">在职</a-select-option>
            <a-select-option value="retired">退休</a-select-option>
            <a-select-option value="unemployed">待业</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="formData.demographic.workStatus === 'other'" label="工作状态说明">
          <a-input v-model:value="formData.demographic.workStatusOther" placeholder="请说明工作状态" size="large" />
        </a-form-item>
        <a-form-item label="文化程度">
          <a-select v-model:value="formData.demographic.education" placeholder="请选择" size="large">
            <a-select-option value="primary_or_below">小学及以下</a-select-option>
            <a-select-option value="junior">初中</a-select-option>
            <a-select-option value="senior">高中/中专</a-select-option>
            <a-select-option value="college">大专</a-select-option>
            <a-select-option value="undergraduate">本科</a-select-option>
            <a-select-option value="postgraduate">研究生及以上</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="居住地类型">
          <a-select v-model:value="formData.demographic.residenceType" placeholder="请选择" size="large">
            <a-select-option value="urban">城市</a-select-option>
            <a-select-option value="town">城镇</a-select-option>
            <a-select-option value="rural">农村</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="医保类型">
          <a-select v-model:value="formData.demographic.insuranceType" placeholder="请选择" size="large">
            <a-select-option value="employee">城镇职工医保</a-select-option>
            <a-select-option value="resident">城乡居民医保</a-select-option>
            <a-select-option value="free_medical">公费医疗</a-select-option>
            <a-select-option value="commercial">商业保险</a-select-option>
            <a-select-option value="self_pay">暂无医保</a-select-option>
            <a-select-option value="unknown">不清楚</a-select-option>
          </a-select>
        </a-form-item>
      </div>
    </a-form>

    <div class="bottom-actions">
      <a-button type="primary" size="large" block :loading="isSaving" @click="handleSave" class="save-btn">
        保存健康档案
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { LeftOutlined } from '@ant-design/icons-vue'
import { saveHealthRecord, getDraft } from '@shared/api/healthRecord'
import { useSpeech } from '@shared/composables/useSpeech'

const router = useRouter()
const { speak, stop, speakPageTitle } = useSpeech()

function goBack() {
  router.back()
}

const user = JSON.parse(localStorage.getItem('student-user') || '{}')
const isSaving = ref(false)
const lastSaveTime = ref('')
const currentRecordId = ref(null)
let autoSaveTimer = null

const initialFormData = {
  basicInfo: { name: '', birthDate: '', gender: '', height: null, weight: null, bmi: '', waist: null, abdomen: null, systolicBp: null, diastolicBp: null, heartRate: null },
  sleepStatus: { sleepIssues: [], otherSleepIssue: '' },
  chronicDisease: { diseases: [], tumorHistory: '', otherDisease: '' },
  medication: { isMedication: false, medicationNames: '' },
  lifestyle: { smokingStatus: 'never', smokingCount: null, drinkingStatus: 'never', drinkingFrequency: null, drinkingAmount: null },
  exercise: { preferredExercises: [], otherExercise: '', socialSupport: [], otherSupport: '', noSupport: false },
  demographic: { maritalStatus: '', address: '', workStatus: '', workStatusOther: '', education: '', ethnicity: 'han', ethnicityOther: '', religion: 'none', religionOther: '', residenceType: 'urban', residenceTypeOther: '', coResidents: [], coResidentsOther: '', insuranceType: '', insuranceTypeOther: '', occupation: '', occupationOther: '', income: '', incomeOther: '' }
}

const formData = reactive(JSON.parse(JSON.stringify(initialFormData)))

function calculateBMI() {
  const h = formData.basicInfo.height
  const w = formData.basicInfo.weight
  if (h && w) {
    formData.basicInfo.bmi = (w / ((h / 100) ** 2)).toFixed(2)
  } else {
    formData.basicInfo.bmi = ''
  }
}

function handleChronicDiseaseChange(value) {
  if (value.includes('none') && value.length > 1) {
    formData.chronicDisease.diseases = ['none']
    formData.chronicDisease.tumorHistory = ''
    formData.chronicDisease.otherDisease = ''
  }
}

function handleExerciseChange(value) {
  if (value.length > 3 && !value.includes('no_preference')) {
    message.warning('最多只能选择3项运动')
    formData.exercise.preferredExercises = value.slice(0, 3)
  }
  if (value.includes('no_preference')) {
    formData.exercise.preferredExercises = ['no_preference']
  }
}

const LOCAL_STORAGE_KEY = `health-record-draft-${user.id || 'guest'}`
function saveToLocalStorage() {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify({ formData, recordId: currentRecordId.value, savedAt: new Date().toISOString() }))
}
function loadFromLocalStorage() {
  const saved = localStorage.getItem(LOCAL_STORAGE_KEY)
  return saved ? JSON.parse(saved) : null
}

async function restoreDraft() {
  const localDraft = loadFromLocalStorage()
  let serverDraft = null
  if (user.token) {
    try {
      const response = await getDraft()
      if (response.code === '200' && response.data) serverDraft = response.data
    } catch (error) {}
  }

  let draft = null
  let recordId = null
  if (serverDraft && (!localDraft || new Date(serverDraft.updated_at) > new Date(localDraft.savedAt))) {
    draft = serverDraft
    recordId = serverDraft.id
  } else if (localDraft) {
    draft = localDraft.formData
    recordId = localDraft.recordId
  }

  if (draft) {
    Object.keys(formData).forEach(key => {
      if (draft[key]) {
        formData[key] = { ...formData[key], ...draft[key] }
      }
    })
    if (recordId) currentRecordId.value = recordId
    lastSaveTime.value = formatTime(new Date())
  }
}

async function handleSave() {
  if (!formData.basicInfo.name || !formData.basicInfo.birthDate || !formData.basicInfo.gender ||
      !formData.basicInfo.height || !formData.basicInfo.weight ||
      !formData.basicInfo.systolicBp || !formData.basicInfo.diastolicBp || !formData.basicInfo.heartRate ||
      !formData.demographic.maritalStatus || !formData.demographic.workStatus) {
    message.warning('请填写所有必填项')
    return
  }
  isSaving.value = true
  try {
    const response = await saveHealthRecord({ record_id: currentRecordId.value, data: formData, is_draft: true })
    if (response.code === '200') {
      currentRecordId.value = response.data.record_id
      lastSaveTime.value = formatTime(new Date())
      saveToLocalStorage()
      message.success('保存成功')
      Modal.confirm({
        title: '保存成功',
        content: '是否前往 AI 问答获取个性化健康建议？',
        okText: '去咨询',
        cancelText: '继续编辑',
        onOk: () => router.push('/chat-ai')
      })
    } else {
      message.error(response.msg || '保存失败')
    }
  } catch (error) {
    message.error('保存失败，请稍后重试')
  } finally {
    isSaving.value = false
  }
}

function formatTime(date) {
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

watch(() => formData, () => saveToLocalStorage(), { deep: true })

onMounted(async () => {
  speakPageTitle('健康档案')
  await restoreDraft()
  autoSaveTimer = setInterval(() => {
    if (currentRecordId.value) handleSave()
  }, 60000)
})

onUnmounted(() => {
  if (autoSaveTimer) clearInterval(autoSaveTimer)
  stop()
})
</script>

<style scoped>
.mobile-health-info {
  padding-bottom: 100px;
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 800;
  margin: 0;
}

.save-hint {
  font-size: 13px;
  color: #999;
}

.section-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.page-title {
  flex: 1;
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.back-btn {
  padding: 0;
  font-size: 17px;
  color: #666;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 16px 0;
}

.required {
  font-size: 13px;
  color: #999;
  font-weight: 500;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bottom-actions {
  position: fixed;
  bottom: calc(64px + env(safe-area-inset-bottom));
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #eee;
  z-index: 10;
}

.save-btn {
  min-height: 52px;
  font-size: 18px;
  border-radius: 12px;
}
</style>
