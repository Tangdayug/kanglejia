<template>
  <div class="modern-health-record">
    <div class="modern-page-header">
      <div class="header-content">
        <h2 class="giant-page-title">健康档案信息录入</h2>
        <div class="save-info-pill">
          <el-icon v-if="isSaving" class="is-loading"><Loading /></el-icon>
          <span v-if="lastSaveTime">上次保存: {{ lastSaveTime }}</span>
          <span v-if="!isSaving && !lastSaveTime" class="unsaved">未保存状态</span>
        </div>
      </div>
    </div>

    <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" class="figma-form-style">
      <div class="modern-card">
        <div class="card-header-flex">
          <span class="card-title">基本信息</span>
          <span class="required-tip">* 为必填项</span>
        </div>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="姓名" prop="basicInfo.name" required>
              <el-input v-model="formData.basicInfo.name" placeholder="请输入您的姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="出生年月" prop="basicInfo.birthDate" required>
              <el-date-picker
                v-model="formData.basicInfo.birthDate"
                type="date"
                placeholder="选择出生日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="性别" prop="basicInfo.gender" required>
              <el-radio-group v-model="formData.basicInfo.gender" class="custom-radio-group">
                <el-radio value="male" border>男</el-radio>
                <el-radio value="female" border>女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="身高 (cm)" prop="basicInfo.height" required>
              <el-input-number v-model="formData.basicInfo.height" :min="0" :max="300" :precision="1" style="width: 100%" @change="calculateBMI" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="体重 (kg)" prop="basicInfo.weight" required>
              <el-input-number v-model="formData.basicInfo.weight" :min="0" :max="300" :precision="1" style="width: 100%" @change="calculateBMI" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="BMI" prop="basicInfo.bmi">
              <el-input v-model="formData.basicInfo.bmi" disabled placeholder="自动计算" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="腰围 (cm)" prop="basicInfo.waist">
              <el-input-number v-model="formData.basicInfo.waist" :min="0" :max="200" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="腹围 (cm)" prop="basicInfo.abdomen">
              <el-input-number v-model="formData.basicInfo.abdomen" :min="0" :max="200" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="收缩压 (mmHg)" prop="basicInfo.systolicBp" required>
              <el-input-number v-model="formData.basicInfo.systolicBp" :min="0" :max="300" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="舒张压 (mmHg)" prop="basicInfo.diastolicBp" required>
              <el-input-number v-model="formData.basicInfo.diastolicBp" :min="0" :max="200" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="心率 (次/min)" prop="basicInfo.heartRate" required>
              <el-input-number v-model="formData.basicInfo.heartRate" :min="0" :max="200" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">睡眠状况</span></div>
        <div class="question-box">
          <div class="question-text">过去 1 个月，您是否存在以下睡眠问题？</div>
          <el-checkbox-group v-model="formData.sleepStatus.sleepIssues" class="custom-checkbox-group">
            <el-checkbox value="good" border>睡眠良好</el-checkbox>
            <el-checkbox value="difficulty_falling_asleep" border>入睡困难</el-checkbox>
            <el-checkbox value="easily_wake" border>易醒</el-checkbox>
            <el-checkbox value="early_wake" border>早醒（无法再睡）</el-checkbox>
            <el-checkbox value="daytime_sleepiness" border>白天犯困</el-checkbox>
            <el-checkbox value="other" border>其他问题</el-checkbox>
          </el-checkbox-group>
          <transition name="fade-in">
            <el-input
              v-if="formData.sleepStatus.sleepIssues.includes('other')"
              v-model="formData.sleepStatus.otherSleepIssue"
              placeholder="请详细说明其他睡眠问题..."
              class="sub-input"
            />
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">慢性病情况</span></div>
        <div class="question-box">
          <div class="question-text">您是否患有或曾患有以下哪些慢性病？</div>
          <el-checkbox-group v-model="formData.chronicDisease.diseases" @change="handleChronicDiseaseChange" class="custom-checkbox-group">
            <el-checkbox value="hypertension" border>高血压</el-checkbox>
            <el-checkbox value="diabetes" border>糖尿病</el-checkbox>
            <el-checkbox value="dyslipidemia" border>血脂异常</el-checkbox>
            <el-checkbox value="coronary_heart_disease" border>冠心病</el-checkbox>
            <el-checkbox value="angina" border>心绞痛</el-checkbox>
            <el-checkbox value="myocardial_infarction" border>心肌梗死</el-checkbox>
            <el-checkbox value="stroke" border>脑卒中（中风）</el-checkbox>
            <el-checkbox value="copd" border>慢阻肺</el-checkbox>
            <el-checkbox value="gout" border>痛风</el-checkbox>
            <el-checkbox value="chronic_kidney_disease" border>慢性肾病</el-checkbox>
            <el-checkbox value="hypothyroidism" border>甲减</el-checkbox>
            <el-checkbox value="hyperthyroidism" border>甲亢</el-checkbox>
            <el-checkbox value="osteoporosis" border>骨质疏松</el-checkbox>
            <el-checkbox value="parkinsons" border>帕金森</el-checkbox>
            <el-checkbox value="alzheimers" border>阿尔茨海默</el-checkbox>
            <el-checkbox value="tumor_history" border>肿瘤病史</el-checkbox>
            <el-checkbox value="other" border>其他</el-checkbox>
            <el-checkbox value="none" border class="highlight-none">无任何上述疾病</el-checkbox>
          </el-checkbox-group>

          <transition name="fade-in">
            <div v-if="formData.chronicDisease.diseases.includes('tumor_history')" class="sub-field-group">
              <span class="sub-label">请填写肿瘤部位：</span>
              <el-input v-model="formData.chronicDisease.tumorHistory" placeholder="如：肺部、乳腺等" />
            </div>
          </transition>
          <transition name="fade-in">
            <div v-if="formData.chronicDisease.diseases.includes('other')" class="sub-field-group">
              <span class="sub-label">请填写其他疾病名称：</span>
              <el-input v-model="formData.chronicDisease.otherDisease" placeholder="请填写病名" />
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">用药情况</span></div>
        <div class="question-box">
          <div class="question-text">您现在在用什么药吗？</div>
          <el-radio-group v-model="formData.medication.isMedication" class="custom-radio-group">
            <el-radio :value="true" border>正在用药</el-radio>
            <el-radio :value="false" border>未用药</el-radio>
          </el-radio-group>
          <transition name="fade-in">
            <div v-if="formData.medication.isMedication" class="sub-field-group">
              <span class="sub-label">请填写正在服用的药物名称：</span>
              <el-input v-model="formData.medication.medicationNames" placeholder="如：缬沙坦、阿托伐他汀" style="max-width: 600px;" />
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">生活习惯</span></div>
        <div class="question-box">
          <div class="question-text">您现在的吸烟情况？</div>
          <el-radio-group v-model="formData.lifestyle.smokingStatus" class="custom-radio-group">
            <el-radio value="never" border>从不吸</el-radio>
            <el-radio value="quit_over_1_year" border>已戒烟 > 1年</el-radio>
            <el-radio value="quit_within_1_year" border>已戒烟 ≤ 1年</el-radio>
            <el-radio value="occasional" border>偶尔吸</el-radio>
            <el-radio value="daily" border>每天吸</el-radio>
          </el-radio-group>
          <transition name="fade-in">
            <div v-if="formData.lifestyle.smokingStatus === 'daily'" class="inline-sub-inputs">
              <span class="sub-label">每天平均吸：</span>
              <el-input-number v-model="formData.lifestyle.smokingCount" :min="0" :max="100" />
              <span class="sub-label">支</span>
            </div>
          </transition>
        </div>

        <div class="modern-divider"></div>

        <div class="question-box">
          <div class="question-text">您现在的饮酒情况？</div>
          <el-radio-group v-model="formData.lifestyle.drinkingStatus" class="custom-radio-group">
            <el-radio value="never" border>从不喝</el-radio>
            <el-radio value="quit_over_1_year" border>已戒酒 > 1年</el-radio>
            <el-radio value="quit_within_1_year" border>已戒酒 ≤ 1年</el-radio>
            <el-radio value="occasional" border>偶尔喝（＜1次/周）</el-radio>
            <el-radio value="weekly" border>每周喝</el-radio>
          </el-radio-group>
          <transition name="fade-in">
            <div v-if="formData.lifestyle.drinkingStatus === 'weekly'" class="inline-sub-inputs">
              <span class="sub-label">每周饮酒：</span>
              <el-input-number v-model="formData.lifestyle.drinkingFrequency" :min="0" :max="7" />
              <span class="sub-label">次，每次约</span>
              <el-input-number v-model="formData.lifestyle.drinkingAmount" :min="0" :max="100" />
              <span class="sub-label">两</span>
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">运动偏好</span></div>
        <div class="question-box">
          <div class="question-text">平时您最喜欢、且愿意坚持做的运动或活动是？（最多选3项）</div>
          <el-checkbox-group v-model="formData.exercise.preferredExercises" @change="handleExerciseChange" class="custom-checkbox-group">
            <el-checkbox value="walking" border>散步/健走</el-checkbox>
            <el-checkbox value="jogging" border>慢跑</el-checkbox>
            <el-checkbox value="square_dance" border>广场舞</el-checkbox>
            <el-checkbox value="tai_chi" border>太极拳/八段锦</el-checkbox>
            <el-checkbox value="swimming" border>游泳</el-checkbox>
            <el-checkbox value="cycling" border>骑车</el-checkbox>
            <el-checkbox value="racket_sports" border>乒乓/羽毛球</el-checkbox>
            <el-checkbox value="hiking" border>爬山/爬楼梯</el-checkbox>
            <el-checkbox value="gardening" border>园艺</el-checkbox>
            <el-checkbox value="fishing" border>钓鱼</el-checkbox>
            <el-checkbox value="gym" border>健身房器械</el-checkbox>
            <el-checkbox value="yoga" border>瑜伽/普拉提</el-checkbox>
            <el-checkbox value="no_preference" border class="highlight-none">无偏好（很少动）</el-checkbox>
            <el-checkbox value="other" border>其他</el-checkbox>
          </el-checkbox-group>
          <transition name="fade-in">
            <el-input
              v-if="formData.exercise.preferredExercises.includes('other')"
              v-model="formData.exercise.otherExercise"
              placeholder="请说明其他运动"
              class="sub-input"
            />
          </transition>
        </div>

        <div class="modern-divider"></div>

        <div class="question-box">
          <div class="question-text">在您家附近，能获得以下哪些支持？</div>
          <div class="support-grid">
            <div class="support-group">
              <div class="support-label">A. 场地/器材</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="fitness_equipment">免费户外健身器材</el-checkbox>
                <el-checkbox value="park">公园/广场</el-checkbox>
                <el-checkbox value="fitness_trail">小区健身步道</el-checkbox>
                <el-checkbox value="community_room">小区活动室</el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="support-group">
              <div class="support-label">B. 组织/人群</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="dance_team">广场舞队</el-checkbox>
                <el-checkbox value="fitness_team">健身队</el-checkbox>
                <el-checkbox value="sports_club">跑团/骑行团</el-checkbox>
                <el-checkbox value="interest_group">棋牌/兴趣小组</el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="support-group">
              <div class="support-label">C. 信息/指导</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="health_lecture">健康讲座</el-checkbox>
                <el-checkbox value="fitness_guidance">健身指导</el-checkbox>
                <el-checkbox value="digital_push">网络/手机推送</el-checkbox>
                <el-checkbox value="poster">宣传栏/海报</el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="support-group">
              <div class="support-label">D. 政策/费用</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="free_facilities">免费/优惠开放场馆</el-checkbox>
                <el-checkbox value="insurance_benefit">医保/社保优惠</el-checkbox>
                <el-checkbox value="subsidy">补贴/奖励</el-checkbox>
                <el-checkbox value="none">无</el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
          <div class="sub-field-group" style="margin-top: 24px;">
            <span class="sub-label">其他支持：</span>
            <el-input v-model="formData.exercise.otherSupport" placeholder="请说明其他支持" style="max-width: 600px" />
          </div>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">社会人口学信息</span></div>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="婚姻状态">
              <el-select v-model="formData.demographic.maritalStatus" placeholder="请选择">
                <el-option label="未婚" value="unmarried" />
                <el-option label="已婚" value="married" />
                <el-option label="丧偶" value="widowed" />
                <el-option label="离婚" value="divorced" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="居住地址">
              <el-input v-model="formData.demographic.address" placeholder="请输入居住地址" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="工作状态">
              <el-select v-model="formData.demographic.workStatus" placeholder="请选择">
                <el-option label="在职" value="employed" />
                <el-option label="退休" value="retired" />
                <el-option label="待业" value="unemployed" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="文化程度">
              <el-select v-model="formData.demographic.education" placeholder="请选择">
                <el-option label="未上过学" value="none" />
                <el-option label="小学" value="primary" />
                <el-option label="初中" value="junior" />
                <el-option label="高中/中专" value="senior" />
                <el-option label="大专/本科" value="college" />
                <el-option label="研究生及以上" value="postgraduate" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="民族">
              <el-radio-group v-model="formData.demographic.ethnicity" class="custom-radio-group">
                <el-radio value="han" border>汉族</el-radio>
                <el-radio value="minority" border>少数民族</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="宗教信仰">
              <el-select v-model="formData.demographic.religion" placeholder="请选择">
                <el-option label="无宗教信仰" value="none" />
                <el-option label="佛教" value="buddhism" />
                <el-option label="基督教" value="christianity" />
                <el-option label="天主教" value="catholicism" />
                <el-option label="伊斯兰教" value="islam" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="居住地类型">
              <el-radio-group v-model="formData.demographic.residenceType" class="custom-radio-group">
                <el-radio value="urban" border>城市</el-radio>
                <el-radio value="rural" border>农村</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="共同居住者">
              <el-select v-model="formData.demographic.coResidents" placeholder="请选择">
                <el-option label="独居" value="alone" />
                <el-option label="与配偶同住" value="spouse" />
                <el-option label="与子女同住" value="children" />
                <el-option label="与父母同住" value="parents" />
                <el-option label="三代同堂" value="three_generations" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="医保类型">
              <el-select v-model="formData.demographic.insuranceType" placeholder="请选择">
                <el-option label="城镇职工医保" value="employee" />
                <el-option label="城镇居民医保" value="resident" />
                <el-option label="新农合" value="rural_cooperative" />
                <el-option label="自费" value="self_pay" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="12">
            <el-form-item label="职业">
              <el-select v-model="formData.demographic.occupation" placeholder="请选择" style="width: 100%">
                <el-option label="机关/企事业单位负责人" value="executive" />
                <el-option label="专业技术人员" value="professional" />
                <el-option label="办事人员和有关人员" value="clerical" />
                <el-option label="商业/服务业人员" value="service" />
                <el-option label="农林牧渔水利生产人员" value="agricultural" />
                <el-option label="生产运输设备操作人员" value="production" />
                <el-option label="军人" value="military" />
                <el-option label="家务" value="homemaker" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="家庭人均月收入">
              <el-select v-model="formData.demographic.income" placeholder="请选择" style="width: 100%">
                <el-option label="<2000元" value="less_2000" />
                <el-option label="2000-4000元" value="2000_4000" />
                <el-option label="4001-6000元" value="4001_6000" />
                <el-option label="6001-8000元" value="6001_8000" />
                <el-option label="8001-10000元" value="8001_10000" />
                <el-option label=">10000元" value="over_10000" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-form>

    <div class="modern-bottom-actions">
      <div class="action-inner">
        <button class="cta-black-giant" :class="{ 'is-loading': isSaving }" @click="handleSave(true)">
          <el-icon v-if="!isSaving" class="icon-space"><Select /></el-icon>
          <el-icon v-else class="icon-space is-spinning"><Loading /></el-icon>
          {{ isSaving ? '保存中...' : '提交健康档案数据' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// ---- 脚本逻辑未做任何修改，保持功能完全一致 ----
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Select } from '@element-plus/icons-vue'
import { saveHealthRecord, getDraft } from '@/api/healthRecord'

const user = JSON.parse(localStorage.getItem('student-user') || '{}')
const formRef = ref(null)
const isSaving = ref(false)
const lastSaveTime = ref('')
const currentRecordId = ref(null)
let autoSaveTimer = null

// 表单验证规则
const rules = {
  'basicInfo.name': [{ required: true, message: '请填写姓名', trigger: 'blur' }],
  'basicInfo.birthDate': [{ required: true, message: '请填写出生年月', trigger: 'change' }],
  'basicInfo.gender': [{ required: true, message: '请选择性别', trigger: 'change' }],
  'basicInfo.height': [{ required: true, message: '请填写身高', trigger: 'blur' }],
  'basicInfo.weight': [{ required: true, message: '请填写体重', trigger: 'blur' }],
  'basicInfo.systolicBp': [{ required: true, message: '请填写收缩压', trigger: 'blur' }],
  'basicInfo.diastolicBp': [{ required: true, message: '请填写舒张压', trigger: 'blur' }],
  'basicInfo.heartRate': [{ required: true, message: '请填写心率', trigger: 'blur' }]
}

// Initial form data structure
const initialFormData = {
  basicInfo: {
    name: '', birthDate: '', gender: '', height: null, weight: null, bmi: '',
    waist: null, abdomen: null, systolicBp: null, diastolicBp: null, heartRate: null
  },
  sleepStatus: { sleepIssues: [], otherSleepIssue: '' },
  chronicDisease: { diseases: [], tumorHistory: '', otherDisease: '' },
  medication: { isMedication: false, medicationNames: '' },
  lifestyle: { smokingStatus: 'never', smokingCount: null, drinkingStatus: 'never', drinkingFrequency: null, drinkingAmount: null },
  exercise: { preferredExercises: [], otherExercise: '', socialSupport: [], otherSupport: '' },
  demographic: { maritalStatus: '', address: '', workStatus: '', education: '', ethnicity: 'han', religion: 'none', residenceType: 'urban', coResidents: '', insuranceType: '', occupation: '', income: '' }
}

const formData = reactive(JSON.parse(JSON.stringify(initialFormData)))

function calculateBMI() {
  const height = formData.basicInfo.height
  const weight = formData.basicInfo.weight
  if (height && weight) {
    const heightInMeters = height / 100
    formData.basicInfo.bmi = (weight / (heightInMeters * heightInMeters)).toFixed(2)
  } else { formData.basicInfo.bmi = '' }
}

function handleChronicDiseaseChange(value) {
  if (value.includes('none')) {
    const index = value.indexOf('none')
    if (index > -1 && value.length > 1) {
      formData.chronicDisease.diseases = ['none']
      formData.chronicDisease.tumorHistory = ''
      formData.chronicDisease.otherDisease = ''
    }
  }
}

function handleExerciseChange(value) {
  if (value.length > 3 && !value.includes('no_preference')) {
    ElMessage.warning('最多只能选择3项运动')
    formData.exercise.preferredExercises = value.slice(0, 3)
  }
  if (value.includes('no_preference')) { formData.exercise.preferredExercises = ['no_preference'] }
}

async function handleSave(isDraft = true) {
  try { await formRef.value.validate() } catch (error) { return }
  isSaving.value = true
  try {
    const response = await saveHealthRecord({ record_id: currentRecordId.value, data: formData, is_draft: isDraft })
    if (response.code === '200') {
      currentRecordId.value = response.data.record_id
      lastSaveTime.value = formatTime(new Date())
      saveToLocalStorage()
      ElMessage.success('保存成功')
    } else { ElMessage.error(response.msg || '保存失败') }
  } catch (error) { ElMessage.error('保存失败，请稍后重试') } finally { isSaving.value = false }
}

function formatTime(date) { return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}` }

const LOCAL_STORAGE_KEY = `health-record-draft-${user.id || 'guest'}`
function saveToLocalStorage() { localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify({ formData: formData, recordId: currentRecordId.value, savedAt: new Date().toISOString() })) }
function loadFromLocalStorage() { const saved = localStorage.getItem(LOCAL_STORAGE_KEY); return saved ? JSON.parse(saved) : null }

async function loadServerDraft() {
  try {
    const response = await getDraft()
    if (response.code === '200' && response.data) return response.data
  } catch (error) { console.error('Load draft error:', error) }
  return null
}

async function restoreDraft() {
  const localDraft = loadFromLocalStorage()
  const user = JSON.parse(localStorage.getItem('student-user') || '{}')
  let serverDraft = null
  if (user.token) { serverDraft = await loadServerDraft() }

  let shouldRestore = false; let draftSource = null
  if (localDraft && serverDraft) {
    if (new Date(serverDraft.updated_at) > new Date(localDraft.savedAt)) {
      try {
        await ElMessageBox.confirm('服务器上有更新的草稿，是否恢复？', '发现草稿', { confirmButtonText: '恢复服务器草稿', cancelButtonText: '使用本地草稿', distinguishCancelAndClose: true, type: 'info' })
        shouldRestore = true; draftSource = 'server'
      } catch (action) { if (action === 'cancel') { shouldRestore = true; draftSource = 'local' } }
    } else { shouldRestore = true; draftSource = 'local' }
  } else if (localDraft) { shouldRestore = true; draftSource = 'local' } else if (serverDraft) { shouldRestore = true; draftSource = 'server' }

  if (shouldRestore && draftSource) {
    const draft = draftSource === 'server' ? serverDraft : localDraft.formData
    const recordId = draftSource === 'server' ? draft.id : localDraft.recordId
    Object.keys(formData).forEach(key => { if (draft[key]) formData[key] = { ...formData[key], ...draft[key] } })
    if (recordId) currentRecordId.value = recordId
    lastSaveTime.value = formatTime(new Date(draftSource === 'server' ? draft.updated_at : localDraft.savedAt))
    ElMessage.success(`已恢复${draftSource === 'server' ? '服务器' : '本地'}草稿`)
  }
}

function startAutoSave() {
  autoSaveTimer = setInterval(() => {
    if (currentRecordId.value || Object.values(formData).some(section => Object.values(section).some(v => v !== '' && v !== null && v !== undefined))) { handleSave(true) }
  }, 60000)
}
function stopAutoSave() { if (autoSaveTimer) { clearInterval(autoSaveTimer); autoSaveTimer = null } }

watch(() => formData, () => { saveToLocalStorage() }, { deep: true })
onMounted(async () => { await restoreDraft(); startAutoSave() })
onUnmounted(() => { stopAutoSave() })
</script>

<style scoped>
/* Figma 现代沉浸式表单样式 */
.modern-health-record {
  padding: 0 40px 120px 40px;
  max-width: 1280px;
  margin: 0 auto;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
}

/* 页面大标题区 */
.modern-page-header {
  padding: 40px 0;
}
.giant-page-title {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -1.5px;
  color: var(--sn-text);
  margin: 0 0 12px 0;
}
.save-info-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--sn-slate-light);
  border-radius: 100px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sn-text-secondary);
}
.save-info-pill .unsaved { color: var(--sn-danger); }

/* 现代卡片覆盖 el-card */
.modern-card {
  background: var(--sn-surface);
  border-radius: 32px;
  padding: 40px;
  margin-bottom: 32px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.02);
  border: 1px solid var(--sn-border);
}
.card-header-flex {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}
.card-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--sn-text);
  letter-spacing: -0.5px;
}
.required-tip {
  font-size: 14px;
  font-weight: 600;
  color: var(--sn-text-muted);
  background: var(--sn-slate-light);
  padding: 4px 12px;
  border-radius: 10px;
}

/* 问卷标题 */
.question-box { margin-bottom: 24px; }
.question-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--sn-text);
  margin-bottom: 20px;
}

/* --- Element Plus 控件深度覆写 --- */
.figma-form-style :deep(.el-form-item__label) {
  font-size: 15px;
  font-weight: 700;
  color: var(--sn-text);
  padding-bottom: 10px;
}
/* 统一大尺寸输入框 */
.figma-form-style :deep(.el-input__wrapper),
.figma-form-style :deep(.el-select__wrapper) {
  background-color: var(--sn-slate-light);
  border-radius: 16px;
  height: 52px;
  box-shadow: none !important;
  padding: 0 20px;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}
.figma-form-style :deep(.el-input__wrapper.is-focus),
.figma-form-style :deep(.el-select__wrapper.is-focus) {
  background-color: var(--sn-surface);
  box-shadow: 0 0 0 2px var(--sn-text) !important; /* 纯黑高亮边框 */
}

/* 选择按钮阵列重排 */
.custom-radio-group, .custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.figma-form-style :deep(.el-radio.is-bordered), 
.figma-form-style :deep(.el-checkbox.is-bordered) {
  height: 52px;
  padding: 0 24px;
  border-radius: 16px;
  border: 2px solid var(--sn-border);
  background: var(--sn-surface);
  margin-right: 0;
}
.figma-form-style :deep(.el-radio.is-bordered.is-checked), 
.figma-form-style :deep(.el-checkbox.is-bordered.is-checked) {
  border-color: var(--sn-primary);
  background: var(--sn-primary);
}
.figma-form-style :deep(.el-radio.is-bordered.is-checked .el-radio__label),
.figma-form-style :deep(.el-checkbox.is-bordered.is-checked .el-checkbox__label) {
  color: var(--sn-surface);
  font-weight: 700;
}
.figma-form-style :deep(.el-radio__input), .figma-form-style :deep(.el-checkbox__inner) {
  display: none; /* 隐藏原生圈圈，做成纯 Button 质感 */
}
.highlight-none {
  border-color: var(--sn-danger-border) !important;
}

/* 子问题与补充输入 */
.sub-field-group { margin-top: 16px; display: flex; align-items: center; gap: 12px; }
.inline-sub-inputs { margin-top: 16px; display: flex; align-items: center; gap: 12px; background: var(--sn-slate-light); padding: 16px; border-radius: 16px;}
.sub-label { font-weight: 600; color: var(--sn-text-secondary); }
.sub-input { margin-top: 16px; max-width: 600px; }

/* 选项组栅格 */
.support-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}
.support-group {
  background: var(--sn-slate-light);
  padding: 24px;
  border-radius: 20px;
}
.support-label {
  font-weight: 800;
  color: var(--sn-text);
  margin-bottom: 16px;
  font-size: 16px;
}
.compact-checkboxes { display: flex; flex-direction: column; gap: 12px; }
.modern-divider { height: 1px; background: var(--sn-border); margin: 40px 0; }

/* 底部操作悬浮栏 */
.modern-bottom-actions {
  position: fixed;
  bottom: 0;
  left: 260px; /* 避开 Manager 侧边栏的宽度 */
  right: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--sn-border);
  padding: 24px;
  z-index: 900;
  display: flex;
  justify-content: center;
  transition: left 0.3s ease;
}
html[data-accessibility="elderly"] .modern-bottom-actions { left: 320px; } /* 老年人模式偏移适配 */

.cta-black-giant {
  background: transparent;
  color: var(--sn-primary);
  border: 1px solid var(--sn-primary);
  height: 64px;
  padding: 0 64px;
  border-radius: 20px;
  font-size: 20px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1);
}
.cta-black-giant:hover { background: rgba(13, 148, 136, 0.06); transform: translateY(-2px); }
.icon-space { margin-right: 12px; font-size: 24px; }
.is-spinning { animation: rotating 2s linear infinite; }
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 动效 */
.fade-in-enter-active, .fade-in-leave-active { transition: opacity 0.3s, transform 0.3s; }
.fade-in-enter-from, .fade-in-leave-to { opacity: 0; transform: translateY(-10px); }
</style>