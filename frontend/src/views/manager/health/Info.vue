<template>
 <div class="sn-subpage info-page">

    <div class="sn-subpage-header">
      <div class="sn-subpage-header-inner">
        <button class="sn-back-btn" @click="goHome">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
      </div>
    </div>
  <div class="sn-subpage-body modern-health-record">
    <div class="sn-page-header">
      <div class="sn-page-header-main">
        <h2 class="sn-page-title giant-page-title">健康档案信息录入</h2>
        <div class="sn-page-header-meta">
          <div class="save-info-pill">
            <el-icon v-if="isSaving" class="is-loading"><Loading /></el-icon>
            <span v-if="lastSaveTime">上次保存: {{ lastSaveTime }}</span>
            <span v-if="!isSaving && !lastSaveTime" class="unsaved">未保存状态</span>
          </div>
        </div>
      </div>
    </div>

    <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" class="figma-form-style">

      <div class="modern-card ocr-card">
        <div class="card-header-flex">
          <span class="card-title">智能识别档案</span>
          <span class="required-tip">拍照或上传体检报告/病历，自动识别文字</span>
        </div>
        <div class="ocr-body">
          <input
            ref="ocrFileInput"
            type="file"
            accept="image/*"
            capture="environment"
            style="display: none"
            @change="handleOcrFileChange"
          />
          <div class="ocr-actions">
            <button type="button" class="ocr-btn" @click="triggerOcrCamera">
              <el-icon><Camera /></el-icon>
              <span>拍照识别</span>
            </button>
            <button type="button" class="ocr-btn ocr-btn-secondary" @click="triggerOcrUpload">
              <el-icon><Upload /></el-icon>
              <span>上传图片</span>
            </button>
          </div>
          <div v-if="ocrLoading" class="ocr-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在识别文字，请稍候…</span>
          </div>
          <el-form-item label="识别结果" class="ocr-result-item">
            <el-input
              v-model="formData.ocrText"
              type="textarea"
              :rows="4"
              placeholder="识别结果将显示在这里，您可以直接修改或补充"
            />
          </el-form-item>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex">
          <span class="card-title">基本信息</span>
          <span class="required-tip">* 为必填项</span>
        </div>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="姓名" prop="basicInfo.name" required>
              <el-input v-model="formData.basicInfo.name" placeholder="请输入姓名" @focus="speakFieldLabel('姓名', '请输入您的姓名')" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="出生年月" prop="basicInfo.birthDate" required>
              <el-date-picker
                v-model="formData.basicInfo.birthDate"
                type="date"
                placeholder="选择日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
                :teleported="false"
                @focus="speakFieldLabel('出生年月', '请选择您的出生年月')"
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
              <el-input-number
                v-model="formData.basicInfo.height"
                :min="0" :max="300" :precision="1"
                style="width: 100%"
                @change="calculateBMI"
                @focus="speakFieldLabel('身高', '请输入您的身高，单位厘米')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="体重 (kg)" prop="basicInfo.weight" required>
              <el-input-number
                v-model="formData.basicInfo.weight"
                :min="0" :max="300" :precision="1"
                style="width: 100%"
                @change="calculateBMI"
                @focus="speakFieldLabel('体重', '请输入您的体重，单位千克')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="BMI" prop="basicInfo.bmi">
              <el-input v-model="formData.basicInfo.bmi" disabled placeholder="系统自动计算" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="腰围 (cm)" prop="basicInfo.waist">
              <el-input-number
                v-model="formData.basicInfo.waist"
                :min="0" :max="200" :precision="1"
                style="width: 100%"
                @focus="speakFieldLabel('腰围', '请输入您的腰围，单位厘米')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="腹围 (cm)" prop="basicInfo.abdomen">
              <el-input-number
                v-model="formData.basicInfo.abdomen"
                :min="0" :max="200" :precision="1"
                style="width: 100%"
                @focus="speakFieldLabel('腹围', '请输入您的腹围，单位厘米')"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="收缩压 (mmHg)" prop="basicInfo.systolicBp" required>
              <el-input-number
                v-model="formData.basicInfo.systolicBp"
                :min="0" :max="300"
                style="width: 100%"
                @focus="speakFieldLabel('收缩压', '请输入您的收缩压，单位毫米汞柱')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="舒张压 (mmHg)" prop="basicInfo.diastolicBp" required>
              <el-input-number
                v-model="formData.basicInfo.diastolicBp"
                :min="0" :max="200"
                style="width: 100%"
                @focus="speakFieldLabel('舒张压', '请输入您的舒张压，单位毫米汞柱')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="心率 (次/min)" prop="basicInfo.heartRate" required>
              <el-input-number
                v-model="formData.basicInfo.heartRate"
                :min="0" :max="200"
                style="width: 100%"
                @focus="speakFieldLabel('心率', '请输入您的心率，单位每分钟次数')"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">睡眠状况</span></div>
        <div class="question-box">
          <div class="question-text" @click="speakQuestion('过去 1 个月，您是否存在睡眠问题？')">
            过去 1 个月，您是否存在睡眠问题？
          </div>
          <el-checkbox-group v-model="formData.sleepStatus.sleepIssues" class="custom-checkbox-group">
            <el-checkbox value="good" border @click="speakOption('睡眠良好')">睡眠良好</el-checkbox>
            <el-checkbox value="difficulty_falling_asleep" border @click="speakOption('入睡困难')">入睡困难</el-checkbox>
            <el-checkbox value="easily_wake" border @click="speakOption('易醒')">易醒</el-checkbox>
            <el-checkbox value="early_wake" border @click="speakOption('早醒，比打算早1小时且无法再睡')">早醒（比打算早≥1h 且无法再睡）</el-checkbox>
            <el-checkbox value="daytime_sleepiness" border @click="speakOption('白天犯困')">白天犯困</el-checkbox>
            <el-checkbox value="other" border @click="speakOption('其他')">其他</el-checkbox>
          </el-checkbox-group>
          <transition name="fade-in">
            <div v-if="formData.sleepStatus.sleepIssues.includes('other')" class="sub-field-group">
              <span class="sub-label">请说明：</span>
              <el-input
                v-model="formData.sleepStatus.otherSleepIssue"
                placeholder="请说明其他睡眠问题"
                @focus="speakFieldLabel('其他睡眠问题', '请输入具体问题')"
              />
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">慢性病情况</span></div>
        <div class="question-box">
          <div class="question-text" @click="speakQuestion('您是否患有或曾患有以下哪些慢性病？')">
            您是否患有或曾患有以下哪些慢性病？
          </div>
          <el-checkbox-group v-model="formData.chronicDisease.diseases" @change="handleChronicDiseaseChange" class="custom-checkbox-group">
            <el-checkbox value="hypertension" border @click="speakOption('高血压')">高血压</el-checkbox>
            <el-checkbox value="diabetes" border @click="speakOption('糖尿病')">糖尿病</el-checkbox>
            <el-checkbox value="dyslipidemia" border @click="speakOption('血脂异常')">血脂异常</el-checkbox>
            <el-checkbox value="coronary_heart_disease" border @click="speakOption('冠心病')">冠心病</el-checkbox>
            <el-checkbox value="angina" border @click="speakOption('心绞痛')">心绞痛</el-checkbox>
            <el-checkbox value="myocardial_infarction" border @click="speakOption('心肌梗死')">心肌梗死</el-checkbox>
            <el-checkbox value="stroke" border @click="speakOption('脑卒中')">脑卒中（中风）</el-checkbox>
            <el-checkbox value="copd" border @click="speakOption('慢阻肺')">慢阻肺</el-checkbox>
            <el-checkbox value="gout" border @click="speakOption('痛风')">痛风</el-checkbox>
            <el-checkbox value="chronic_kidney_disease" border @click="speakOption('慢性肾病')">慢性肾病</el-checkbox>
            <el-checkbox value="hypothyroidism" border @click="speakOption('甲减')">甲减</el-checkbox>
            <el-checkbox value="hyperthyroidism" border @click="speakOption('甲亢')">甲亢</el-checkbox>
            <el-checkbox value="osteoporosis" border @click="speakOption('骨质疏松')">骨质疏松</el-checkbox>
            <el-checkbox value="parkinsons" border @click="speakOption('帕金森')">帕金森</el-checkbox>
            <el-checkbox value="alzheimers" border @click="speakOption('阿尔茨海默')">阿尔茨海默</el-checkbox>
            <el-checkbox value="tumor_history" border @click="speakOption('肿瘤病史')">肿瘤病史</el-checkbox>
            <el-checkbox value="other" border @click="speakOption('其他')">其他</el-checkbox>
            <el-checkbox value="none" border class="highlight-none" @click="speakOption('无')">无任何疾病</el-checkbox>
          </el-checkbox-group>

          <transition name="fade-in">
            <div v-if="formData.chronicDisease.diseases.includes('tumor_history')" class="sub-field-group">
              <span class="sub-label">请填写肿瘤部位：</span>
              <el-input
                v-model="formData.chronicDisease.tumorHistory"
                placeholder="如：肺部、乳腺等"
                style="max-width: 400px;"
                @focus="speakFieldLabel('肿瘤部位', '请填写肿瘤部位，如肺部、乳腺等')"
              />
            </div>
          </transition>
          <transition name="fade-in">
            <div v-if="formData.chronicDisease.diseases.includes('other')" class="sub-field-group">
              <span class="sub-label">请填写其他疾病名称：</span>
              <el-input
                v-model="formData.chronicDisease.otherDisease"
                placeholder="请填写病名"
                style="max-width: 400px;"
                @focus="speakFieldLabel('其他疾病名称', '请填写具体的疾病名称')"
              />
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">用药情况</span></div>
        <div class="question-box">
          <div class="question-text" @click="speakQuestion('您现在在用什么药吗？')">
            您现在在用什么药吗？
          </div>
          <el-radio-group v-model="formData.medication.isMedication" class="custom-radio-group">
            <el-radio :value="true" border @click="speakOption('是')">正在用药</el-radio>
            <el-radio :value="false" border @click="speakOption('否')">未用药</el-radio>
          </el-radio-group>
          <transition name="fade-in">
            <div v-if="formData.medication.isMedication" class="sub-field-group">
              <span class="sub-label">正在服用的药物名称：</span>
              <el-input
                v-model="formData.medication.medicationNames"
                placeholder="如：缬沙坦、阿托伐他汀"
                style="max-width: 500px;"
                @focus="speakFieldLabel('药物名称', '请填写正在服用的药物名称')"
              />
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">生活习惯</span></div>
        <div class="question-box">
          <div class="question-text" @click="speakQuestion('您现在吸烟吗？')">
            您现在吸烟吗？
          </div>
          <el-radio-group v-model="formData.lifestyle.smokingStatus" class="custom-radio-group">
            <el-radio value="never" border @click="speakOption('从不吸')">从不吸</el-radio>
            <el-radio value="quit_over_1_year" border @click="speakOption('已戒烟超过1年')">已戒烟 > 1年</el-radio>
            <el-radio value="quit_within_1_year" border @click="speakOption('已戒烟1年以内')">已戒烟 ≤ 1年</el-radio>
            <el-radio value="occasional" border @click="speakOption('偶尔吸')">偶尔吸</el-radio>
            <el-radio value="daily" border @click="speakOption('每天吸')">每天吸</el-radio>
          </el-radio-group>
          <transition name="fade-in">
            <div v-if="formData.lifestyle.smokingStatus === 'daily'" class="inline-sub-inputs">
              <span class="sub-label">每天平均吸：</span>
              <el-input-number
                v-model="formData.lifestyle.smokingCount"
                :min="0" :max="100"
                @focus="speakFieldLabel('每天吸烟支数', '请输入每天吸烟的数量')"
              />
              <span class="sub-label">支</span>
            </div>
          </transition>
        </div>

        <div class="modern-divider"></div>

        <div class="question-box">
          <div class="question-text" @click="speakQuestion('您现在喝酒吗？')">
            您现在喝酒吗？
          </div>
          <el-radio-group v-model="formData.lifestyle.drinkingStatus" class="custom-radio-group">
            <el-radio value="never" border @click="speakOption('从不喝')">从不喝</el-radio>
            <el-radio value="quit_over_1_year" border @click="speakOption('已戒酒超过1年')">已戒酒 > 1年</el-radio>
            <el-radio value="quit_within_1_year" border @click="speakOption('已戒酒1年以内')">已戒酒 ≤ 1年</el-radio>
            <el-radio value="occasional" border @click="speakOption('偶尔喝')">偶尔喝（＜1次/周）</el-radio>
            <el-radio value="weekly" border @click="speakOption('每周喝')">每周喝</el-radio>
          </el-radio-group>
          <transition name="fade-in">
            <div v-if="formData.lifestyle.drinkingStatus === 'weekly'" class="inline-sub-inputs">
              <span class="sub-label">每周饮酒：</span>
              <el-input-number
                v-model="formData.lifestyle.drinkingFrequency"
                :min="0" :max="7"
                @focus="speakFieldLabel('每周饮酒次数', '请输入每周饮酒的次数')"
              />
              <span class="sub-label">次，每次约</span>
              <el-input-number
                v-model="formData.lifestyle.drinkingAmount"
                :min="0" :max="100"
                @focus="speakFieldLabel('每次饮酒量', '请输入每次饮酒的量')"
              />
              <span class="sub-label">两</span>
            </div>
          </transition>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">运动偏好</span></div>
        <div class="question-box">
          <div class="question-text" @click="speakQuestion('平时您最喜欢、且愿意坚持做的运动或活动是？最多选3项')">
            平时您最喜欢、且愿意坚持做的运动或活动是？（多选，最多 3 项）
          </div>
          <el-checkbox-group v-model="formData.exercise.preferredExercises" @change="handleExerciseChange" class="modern-exercise-grid">
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('walking') }">
              <el-checkbox value="walking" @click="speakOption('散步健走')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/walk.jpg" alt="散步/健走" />
                  <span>散步/健走</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('jogging') }">
              <el-checkbox value="jogging" @click="speakOption('慢跑')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/run.jpg" alt="慢跑" />
                  <span>慢跑</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('swimming') }">
              <el-checkbox value="swimming" @click="speakOption('游泳')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/swim.jpg" alt="游泳" />
                  <span>游泳</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('tai_chi') }">
              <el-checkbox value="tai_chi" @click="speakOption('太极拳八段锦')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/taiji.jpg" alt="太极拳/八段锦" />
                  <span>太极拳/八段锦</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('square_dance') }">
              <el-checkbox value="square_dance" @click="speakOption('广场舞')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/dance.jpg" alt="广场舞" />
                  <span>广场舞</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('yoga') }">
              <el-checkbox value="yoga" @click="speakOption('瑜伽普拉提')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/yoga.jpg" alt="瑜伽/普拉提" />
                  <span>瑜伽/普拉提</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('racket_sports') }">
              <el-checkbox value="racket_sports" @click="speakOption('乒乓羽毛球')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/ping-pong.jpg" alt="乒乓/羽毛球" />
                  <span>乒乓/羽毛球</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('gardening') }">
              <el-checkbox value="gardening" @click="speakOption('园艺')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/gardening.jpg" alt="园艺" />
                  <span>园艺</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('fishing') }">
              <el-checkbox value="fishing" @click="speakOption('钓鱼')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/fishing.jpg" alt="钓鱼" />
                  <span>钓鱼</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('cycling') }">
              <el-checkbox value="cycling" @click="speakOption('骑车')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/ride.jpg" alt="骑车" />
                  <span>骑车</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('hiking') }">
              <el-checkbox value="hiking" @click="speakOption('爬山爬楼梯')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/climb.jpg" alt="爬山/爬楼梯" />
                  <span>爬山/楼梯</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card" :class="{ 'is-active': formData.exercise.preferredExercises.includes('gym') }">
              <el-checkbox value="gym" @click="speakOption('健身房器械')">
                <div class="exercise-inner">
                  <img src="@/assets/imgs/exercise.jpg" alt="健身房器械" />
                  <span>健身房器械</span>
                </div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card text-only" :class="{ 'is-active': formData.exercise.preferredExercises.includes('no_preference') }">
              <el-checkbox value="no_preference" @click="speakOption('无偏好或很少动')">
                <div class="exercise-inner"><span>无偏好/很少动</span></div>
              </el-checkbox>
            </div>
            <div class="modern-exercise-card text-only" :class="{ 'is-active': formData.exercise.preferredExercises.includes('other') }">
              <el-checkbox value="other" @click="speakOption('其他')">
                <div class="exercise-inner"><span>其他运动</span></div>
              </el-checkbox>
            </div>
          </el-checkbox-group>

          <transition name="fade-in">
            <el-input
              v-if="formData.exercise.preferredExercises.includes('other')"
              v-model="formData.exercise.otherExercise"
              placeholder="请说明其他运动"
              class="sub-input-mt"
              @focus="speakFieldLabel('其他运动', '请说明您喜欢的其他运动')"
            />
          </transition>
        </div>

        <div class="modern-divider"></div>

        <div class="question-box">
          <div class="question-text" @click="speakQuestion('在您家附近，能获得以下哪些支持？')">
            在您家附近，能获得以下哪些支持？
          </div>
          <div class="support-grid">
            <div class="support-group">
              <div class="support-label">A 场地/器材</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="fitness_trail" @click="speakOption('小区健身步道')">小区健身步道</el-checkbox>
                <el-checkbox value="park" @click="speakOption('公园广场')">公园/广场</el-checkbox>
                <el-checkbox value="fitness_equipment" @click="speakOption('免费户外健身器材')">免费户外健身器材</el-checkbox>
                <el-checkbox value="swimming_pool" @click="speakOption('公共游泳场馆')">公共游泳场馆</el-checkbox>
                <el-checkbox value="community_gym" @click="speakOption('社区健身房')">社区健身房（低收费）</el-checkbox>
                <el-checkbox value="rehab_room" @click="speakOption('社区康复室')">社区卫生服务中心康复室</el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="support-group">
              <div class="support-label">B 组织/人群</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="sports_team" @click="speakOption('老年运动队社团')">有老年运动队/社团</el-checkbox>
                <el-checkbox value="family_accompany" @click="speakOption('家人可陪同一起运动')">家人可陪同一起运动</el-checkbox>
                <el-checkbox value="friends_exercise" @click="speakOption('邻里朋友常约锻炼')">邻里朋友常约锻炼</el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="support-group">
              <div class="support-label">C 信息指导/设备</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="health_lecture" @click="speakOption('社区定期开健康讲座')">社区定期健康讲座</el-checkbox>
                <el-checkbox value="coach" @click="speakOption('有康复师教练')">有康复师/教练</el-checkbox>
                <el-checkbox value="app_device" @click="speakOption('已在使用运动App或手环')">已使用运动 App/手环</el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="support-group">
              <div class="support-label">D 政策/费用</div>
              <el-checkbox-group v-model="formData.exercise.socialSupport" class="compact-checkboxes">
                <el-checkbox value="elderly_card" @click="speakOption('凭老年卡可免费或优惠进场馆')">凭老年卡优惠进场馆</el-checkbox>
                <el-checkbox value="subsidy_coupon" @click="speakOption('社区提供运动项目补贴券')">社区提供运动补贴券</el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
          <div class="support-extras">
            <div class="sub-field-group">
              <span class="sub-label">E 其他：</span>
              <el-input
                v-model="formData.exercise.otherSupport"
                placeholder="请填写其他支持"
                style="max-width: 400px;"
                @focus="speakFieldLabel('其他支持', '请填写其他类型的支持')"
              />
            </div>
            <div class="sub-field-group" style="margin-top: 16px;">
              <el-checkbox
                v-model="formData.exercise.noSupport"
                @change="handleNoSupportChange"
                border
                class="highlight-none"
                @click="speakOption('以上皆无，将自动清空其余选项')"
              >F 以上皆无（自动清空其余选项）</el-checkbox>
            </div>
          </div>
        </div>
      </div>

      <div class="modern-card">
        <div class="card-header-flex"><span class="card-title">社会人口学信息</span></div>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="婚姻状态" prop="demographic.maritalStatus" required>
              <el-select v-model="formData.demographic.maritalStatus" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="未婚" value="unmarried" />
                <el-option label="已婚" value="married" />
                <el-option label="丧偶" value="widowed" />
                <el-option label="离婚" value="divorced" />
                <el-option label="分居" value="separated" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="居住地址">
              <el-input v-model="formData.demographic.address" placeholder="请输入居住地址" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="工作状态" prop="demographic.workStatus" required>
              <el-select v-model="formData.demographic.workStatus" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="在职" value="employed" />
                <el-option label="退休" value="retired" />
                <el-option label="待业" value="unemployed" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <transition name="fade-in">
          <el-row v-if="formData.demographic.workStatus === 'other'" :gutter="32">
            <el-col :span="8">
              <el-form-item label="工作状态说明" prop="demographic.workStatusOther" required>
                <el-input v-model="formData.demographic.workStatusOther" placeholder="请说明工作状态" />
              </el-form-item>
            </el-col>
          </el-row>
        </transition>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="文化程度">
              <el-select v-model="formData.demographic.education" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="小学及以下" value="primary_or_below" />
                <el-option label="初中" value="junior" />
                <el-option label="高中/中专" value="senior" />
                <el-option label="大专" value="college" />
                <el-option label="本科" value="undergraduate" />
                <el-option label="研究生及以上" value="postgraduate" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="民族">
              <el-select v-model="formData.demographic.ethnicity" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="汉族" value="han" />
                <el-option label="壮族" value="zhuang" />
                <el-option label="维吾尔族" value="uyghur" />
                <el-option label="回族" value="hui" />
                <el-option label="苗族" value="miao" />
                <el-option label="满族" value="manchu" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="宗教信仰">
              <el-select v-model="formData.demographic.religion" placeholder="请选择" style="width: 100%" :teleported="false">
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
        <transition name="fade-in">
          <el-row v-if="formData.demographic.ethnicity === 'other' || formData.demographic.religion === 'other'" :gutter="32">
            <el-col :span="8" v-if="formData.demographic.ethnicity === 'other'">
              <el-form-item label="民族说明">
                <el-input v-model="formData.demographic.ethnicityOther" placeholder="请填写民族" />
              </el-form-item>
            </el-col>
            <el-col :span="8" v-if="formData.demographic.religion === 'other'">
              <el-form-item label="宗教信仰说明">
                <el-input v-model="formData.demographic.religionOther" placeholder="请填写宗教信仰" />
              </el-form-item>
            </el-col>
          </el-row>
        </transition>
        <el-row :gutter="32">
          <el-col :span="8">
            <el-form-item label="居住地类型">
              <el-select v-model="formData.demographic.residenceType" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="城市" value="urban" />
                <el-option label="城镇" value="town" />
                <el-option label="农村" value="rural" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="医保类型">
              <el-select v-model="formData.demographic.insuranceType" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="城镇职工医保" value="employee" />
                <el-option label="城乡居民医保" value="resident" />
                <el-option label="公费医疗" value="free_medical" />
                <el-option label="仅商业保险" value="commercial" />
                <el-option label="暂无医保（全自费）" value="self_pay" />
                <el-option label="不清楚" value="unknown" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="职业">
              <el-select v-model="formData.demographic.occupation" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="行政机关、企事业单位" value="government" />
                <el-option label="专业技术人员" value="professional" />
                <el-option label="离退休人员" value="retired" />
                <el-option label="销售、服务业人员" value="service" />
                <el-option label="自由职业者" value="freelancer" />
                <el-option label="农民" value="farmer" />
                <el-option label="工人" value="worker" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <transition name="fade-in">
          <el-row v-if="formData.demographic.residenceType === 'other' || formData.demographic.insuranceType === 'other' || formData.demographic.occupation === 'other'" :gutter="32">
            <el-col :span="8" v-if="formData.demographic.residenceType === 'other'">
              <el-form-item label="居住地类型说明">
                <el-input v-model="formData.demographic.residenceTypeOther" placeholder="说明居住地" />
              </el-form-item>
            </el-col>
            <el-col :span="8" v-if="formData.demographic.insuranceType === 'other'">
              <el-form-item label="医保类型说明">
                <el-input v-model="formData.demographic.insuranceTypeOther" placeholder="说明医保" />
              </el-form-item>
            </el-col>
            <el-col :span="8" v-if="formData.demographic.occupation === 'other'">
              <el-form-item label="职业说明">
                <el-input v-model="formData.demographic.occupationOther" placeholder="说明职业" />
              </el-form-item>
            </el-col>
          </el-row>
        </transition>
        <el-row :gutter="32">
          <el-col :span="12">
            <el-form-item label="家庭人均月收入">
              <el-select v-model="formData.demographic.income" placeholder="请选择" style="width: 100%" :teleported="false">
                <el-option label="＜1000元" value="less_1000" />
                <el-option label="1000-5000元" value="1000_5000" />
                <el-option label="5001-10000元" value="5001_10000" />
                <el-option label="10001-20000元" value="10001_20000" />
                <el-option label="20001-30000元" value="20001_30000" />
                <el-option label="＞30000元" value="over_30000" />
                <el-option label="不清楚" value="unknown" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <transition name="fade-in">
          <el-row v-if="formData.demographic.income === 'unknown'" :gutter="32">
            <el-col :span="12">
              <el-form-item label="收入情况说明">
                <el-input v-model="formData.demographic.incomeOther" placeholder="请说明收入情况" />
              </el-form-item>
            </el-col>
          </el-row>
        </transition>
        <el-row :gutter="32">
          <el-col :span="24">
            <el-form-item label="共同居住者">
              <el-checkbox-group v-model="formData.demographic.coResidents" class="custom-checkbox-group">
                <el-checkbox value="alone" border>独居</el-checkbox>
                <el-checkbox value="parents" border>父母</el-checkbox>
                <el-checkbox value="children" border>子女</el-checkbox>
                <el-checkbox value="spouse" border>配偶</el-checkbox>
                <el-checkbox value="friends" border>朋友</el-checkbox>
                <el-checkbox value="other" border>其他</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>
        <transition name="fade-in">
          <el-row v-if="formData.demographic.coResidents?.includes('other')" :gutter="32">
            <el-col :span="24">
              <el-form-item label="共同居住者说明">
                <el-input v-model="formData.demographic.coResidentsOther" placeholder="请填写共同居住者" style="width: 100%; max-width: 600px;" />
              </el-form-item>
            </el-col>
          </el-row>
        </transition>
      </div>
    </el-form>

    <div class="modern-bottom-actions">
      <div class="action-inner">
        <button class="cta-black-giant" :class="{ 'is-loading': isSaving }" @click="handleSave(true)">
          <el-icon v-if="!isSaving" class="icon-space"><Select /></el-icon>
          <el-icon v-else class="icon-space is-spinning"><Loading /></el-icon>
          {{ isSaving ? '保存数据中...' : '保存健康档案数据' }}
        </button>
      </div>
    </div>
  </div>
 </div>
</template>

<script setup>
// ---- 这里所有的 Script 逻辑与你提供的原版代码 100% 保持一致，绝对未做删改 ----
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Select, Camera, Upload } from '@element-plus/icons-vue'
import { saveHealthRecord, getDraft, ocrHealthRecordImage } from '@/api/healthRecord'
import { useSpeech } from '@/composables/useSpeech'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('student-user') || '{}')
const formRef = ref(null)
const isSaving = ref(false)
const lastSaveTime = ref('')
const currentRecordId = ref(null)
const ocrFileInput = ref(null)
const ocrLoading = ref(false)
let autoSaveTimer = null

const { speak, stop, speakPageTitle, isEnabled: speechEnabled } = useSpeech()
let speechDebounceTimer = null

function checkVoiceModeEnabled() {
  const userMode = localStorage.getItem('user-mode')
  return userMode === 'voice' && speechEnabled.value
}

function speakOption(optionText) {
  if (!checkVoiceModeEnabled()) return
  stop()
  speak(optionText)
}

function speakFieldLabel(labelText, hint = '') {
  if (!checkVoiceModeEnabled()) return
  if (speechDebounceTimer) clearTimeout(speechDebounceTimer)
  speechDebounceTimer = setTimeout(() => {
    stop()
    const text = hint ? `${labelText}，${hint}` : labelText
    speak(text)
  }, 300)
}

function speakQuestion(questionText) {
  if (!checkVoiceModeEnabled()) return
  if (speechDebounceTimer) clearTimeout(speechDebounceTimer)
  speechDebounceTimer = setTimeout(() => {
    stop()
    speak(questionText)
  }, 500)
}

const rules = {
  'basicInfo.name': [{ required: true, message: '请填写姓名', trigger: 'blur' }],
  'basicInfo.birthDate': [{ required: true, message: '请填写出生年月', trigger: 'change' }],
  'basicInfo.gender': [{ required: true, message: '请选择性别', trigger: 'change' }],
  'basicInfo.height': [{ required: true, message: '请填写身高', trigger: 'blur' }],
  'basicInfo.weight': [{ required: true, message: '请填写体重', trigger: 'blur' }],
  'basicInfo.systolicBp': [{ required: true, message: '请填写收缩压', trigger: 'blur' }],
  'basicInfo.diastolicBp': [{ required: true, message: '请填写舒张压', trigger: 'blur' }],
  'basicInfo.heartRate': [{ required: true, message: '请填写心率', trigger: 'blur' }],
  'demographic.maritalStatus': [{ required: true, message: '请选择婚姻状态', trigger: 'change' }],
  'demographic.workStatus': [
    { required: true, message: '请选择工作状态', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (value === 'other' && !formData.demographic.workStatusOther) {
          callback(new Error('选择"其他"时必须填写说明'))
        } else { callback() }
      },
      trigger: 'blur'
    }
  ]
}

const initialFormData = {
  basicInfo: { name: '', birthDate: '', gender: '', height: null, weight: null, bmi: '', waist: null, abdomen: null, systolicBp: null, diastolicBp: null, heartRate: null },
  sleepStatus: { sleepIssues: [], otherSleepIssue: '' },
  chronicDisease: { diseases: [], tumorHistory: '', otherDisease: '' },
  medication: { isMedication: false, medicationNames: '' },
  lifestyle: { smokingStatus: 'never', smokingCount: null, drinkingStatus: 'never', drinkingFrequency: null, drinkingAmount: null },
  exercise: { preferredExercises: [], otherExercise: '', socialSupport: [], otherSupport: '', noSupport: false },
  demographic: { maritalStatus: '', address: '', workStatus: '', workStatusOther: '', education: '', ethnicity: 'han', ethnicityOther: '', religion: 'none', religionOther: '', residenceType: 'urban', residenceTypeOther: '', coResidents: [], coResidentsOther: '', insuranceType: '', insuranceTypeOther: '', occupation: '', occupationOther: '', income: '', incomeOther: '' },
  ocrText: ''
}

const formData = reactive(JSON.parse(JSON.stringify(initialFormData)))

function calculateBMI() {
  const height = formData.basicInfo.height
  const weight = formData.basicInfo.weight
  if (height && weight) {
    const heightInMeters = height / 100
    const bmi = weight / (heightInMeters * heightInMeters)
    formData.basicInfo.bmi = bmi.toFixed(2)
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

function handleNoSupportChange(checked) {
  if (checked) {
    formData.exercise.socialSupport = []
    formData.exercise.otherSupport = ''
  }
}

watch(() => formData.exercise.socialSupport, (newVal) => {
  if (newVal.length > 0 && formData.exercise.noSupport) {
    formData.exercise.noSupport = false
  }
})

function goHome() {
  // 关闭所有弹窗后再跳转
  ElMessage.closeAll()
  ElMessageBox.close()
  router.push('/home')
}

// 路由离开守卫：关闭所有弹窗
onBeforeRouteLeave((to, from, next) => {
  ElMessage.closeAll()
  ElMessageBox.close()
  next()
})

function triggerOcrCamera() {
  if (ocrFileInput.value) {
    ocrFileInput.value.removeAttribute('capture')
    ocrFileInput.value.setAttribute('capture', 'environment')
    ocrFileInput.value.click()
  }
}
function triggerOcrUpload() {
  if (ocrFileInput.value) {
    ocrFileInput.value.removeAttribute('capture')
    ocrFileInput.value.click()
  }
}
async function handleOcrFileChange(event) {
  const file = event.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请上传图片文件')
    return
  }
  if (file.size > 4 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 4MB')
    return
  }
  ocrLoading.value = true
  try {
    const response = await ocrHealthRecordImage(file)
    if (response.code === '200') {
      formData.ocrText = response.data.text || ''
      ElMessage.success('识别完成，已附加到档案')
    } else {
      ElMessage.error(response.msg || '识别失败')
    }
  } catch (error) {
    console.error('OCR error:', error)
    ElMessage.error('识别请求失败，请检查网络')
  } finally {
    ocrLoading.value = false
    event.target.value = ''
  }
}

async function handleSave(isDraft = true) {
  console.log('[handleSave] 开始保存, isDraft:', isDraft)
  try { await formRef.value.validate() } catch (error) { 
    console.log('[handleSave] 表单验证失败:', error)
    return 
  }
  isSaving.value = true
  try {
    console.log('[handleSave] 开始调用API')
    const response = await saveHealthRecord({ record_id: currentRecordId.value, data: formData, is_draft: isDraft })
    console.log('[handleSave] API响应:', response)
    if (response.code === '200') {
      currentRecordId.value = response.data.record_id
      lastSaveTime.value = formatTime(new Date())
      saveToLocalStorage()
      console.log('[handleSave] 准备显示成功消息')
      ElMessage.success({
        message: '保存成功',
        duration: 3000,
        showClose: true
      })
      
      console.log('[handleSave] 成功消息已显示，准备显示确认对话框')
      // 延迟显示确认对话框
// 找到这部分并修改 👇
      setTimeout(() => {
        console.log('[handleSave] 显示确认对话框')
        ElMessageBox.confirm(
          '健康档案已保存，是否前往 AI 问答获取个性化健康建议？', 
          '保存成功', 
          { 
            confirmButtonText: '前往 AI 问答', 
            cancelButtonText: '继续编辑', 
            customClass: 'modern-confirm-dialog', // 引入现代弹窗样式
            closeOnClickModal: false,
            closeOnPressEscape: false,
            showClose: false,
            center: true // 居中排版更好看
          }
        )
        .then(() => { 
          ElMessage.closeAll()
          router.push('/chat-ai') 
        })
        .catch(() => {})
      }, 500)
    } else { ElMessage.error(response.msg || '保存失败') }
  } catch (error) {
    console.error('Save error:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally { isSaving.value = false }
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

  let shouldRestore = false
  let draftSource = null

  if (localDraft && serverDraft) {
    const localTime = new Date(localDraft.savedAt)
    const serverTime = new Date(serverDraft.updated_at)
    if (serverTime > localTime) {
      try {
        await ElMessageBox.confirm('服务器上有更新的草稿，是否恢复？', '发现草稿', { confirmButtonText: '恢复服务器草稿', cancelButtonText: '使用本地草稿', distinguishCancelAndClose: true, type: 'info' })
        shouldRestore = true; draftSource = 'server'
      } catch (action) { if (action === 'cancel') { shouldRestore = true; draftSource = 'local' } }
    } else { shouldRestore = true; draftSource = 'local' }
  } else if (localDraft) { shouldRestore = true; draftSource = 'local' } else if (serverDraft) { shouldRestore = true; draftSource = 'server' }

  if (shouldRestore && draftSource) {
    const draft = draftSource === 'server' ? serverDraft : localDraft.formData
    const recordId = draftSource === 'server' ? draft.id : localDraft.recordId
    Object.keys(formData).forEach(key => {
      if (draft[key] !== undefined && draft[key] !== null) {
        if (typeof formData[key] === 'string') {
          formData[key] = draft[key]
        } else {
          formData[key] = { ...formData[key], ...draft[key] }
          if (key === 'demographic' && draft[key].coResidents) {
            if (typeof draft[key].coResidents === 'string') { formData[key].coResidents = draft[key].coResidents ? [draft[key].coResidents] : [] }
            else if (!Array.isArray(formData[key].coResidents)) { formData[key].coResidents = [] }
          }
        }
      }
    })
    if (recordId) { currentRecordId.value = recordId }
    lastSaveTime.value = formatTime(new Date(draftSource === 'server' ? draft.updated_at : localDraft.savedAt))
    ElMessage.success(`已恢复${draftSource === 'server' ? '服务器' : '本地'}草稿`)
  }
}

function startAutoSave() {
  autoSaveTimer = setInterval(() => {
    if (currentRecordId.value || Object.values(formData).some(section => Object.values(section).some(value => value !== '' && value !== null && value !== undefined))) { handleSave(true) }
  }, 60000)
}
function stopAutoSave() { if (autoSaveTimer) { clearInterval(autoSaveTimer); autoSaveTimer = null } }

watch(() => formData, () => { saveToLocalStorage() }, { deep: true })

onMounted(async () => {
  const userMode = localStorage.getItem('user-mode')
  if (userMode === 'voice') {
    speak('健康档案信息录入', { onEnd: () => { setTimeout(() => { speak('请填写您的健康档案信息。标有星号的为必填项。点击问题可以听到问题内容。') }, 500) }})
  }
  await restoreDraft()
  startAutoSave()
})
onUnmounted(() => { stopAutoSave(); stop() })
</script>

<style scoped>
/* Figma / SaaS 沉浸式表单容器 */

.sn-page-title {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -1.5px;
  color: #111;
  margin: 0 0 12px 0;
}
.save-info-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #F5F5F5;
  border-radius: var(--sn-radius-md);
  font-size: 14px;
  font-weight: 600;
  color: #666;
}
.save-info-pill .unsaved { color: #FF4D4F; }

/* 现代卡片覆盖原生的 el-card */
.modern-card {
  background: #FFFFFF;
  border-radius: var(--sn-radius-lg);
  padding: 40px;
  margin-bottom: 32px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.02);
  border: 1px solid #F0F0F0;
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
  color: #111;
  letter-spacing: -0.5px;
}
.required-tip {
  font-size: 14px;
  font-weight: 600;
  color: #999;
  background: #F9F9F9;
  padding: 4px 12px;
  border-radius: 10px;
}

/* OCR 智能识别 */
.ocr-card { background: linear-gradient(135deg, #F0F7FF 0%, #FFFFFF 100%); border-color: #D9E9FD; }
.ocr-body { display: flex; flex-direction: column; gap: 20px; }
.ocr-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.ocr-btn {
  height: 48px; padding: 0 24px;
  background: transparent; color: var(--sn-primary); border: 1px solid var(--sn-primary);
  border-radius: var(--sn-radius-md);
  font-size: 15px; font-weight: 700;
  display: inline-flex; align-items: center; gap: 8px;
  cursor: pointer; transition: 0.2s;
}
.ocr-btn:hover { background: rgba(23, 114, 246, 0.06); transform: translateY(-1px); }
.ocr-btn-secondary { background: #FFF; color: #111; border: 1px solid #E5E7EB; }
.ocr-btn-secondary:hover { background: #F9FAFB; border-color: #D1D5DB; }
.ocr-loading { display: flex; align-items: center; gap: 10px; color: var(--sn-primary); font-weight: 600; }
.ocr-result-item { margin-bottom: 0; }
.ocr-result-item :deep(.el-textarea__inner) { background: #FFFFFF; border-radius: var(--sn-radius-md); min-height: 120px; }

/* 问卷标题 */
.question-box { margin-bottom: 24px; }
.question-text {
  font-size: 18px;
  font-weight: 700;
  color: #111;
  margin-bottom: 20px;
  cursor: pointer;
  display: inline-block;
  padding: 4px 8px;
  margin-left: -8px;
  border-radius: 8px;
  transition: 0.2s;
}
.question-text:hover { background: #F5F5F5; }

/* --- Element Plus 控件深度覆写 --- */
.figma-form-style :deep(.el-form-item__label) {
  font-size: 15px;
  font-weight: 700;
  color: #111;
  padding-bottom: 10px;
}

/* 统一大尺寸输入框 (Typeform/Stripe 风格) */
.figma-form-style :deep(.el-input__wrapper),
.figma-form-style :deep(.el-select__wrapper) {
  background-color: #F5F5F5;
  border-radius: var(--sn-radius-md);
  height: 52px;
  box-shadow: none !important;
  padding: 0 20px;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}
.figma-form-style :deep(.el-input__wrapper.is-focus),
.figma-form-style :deep(.el-select__wrapper.is-focus) {
  background-color: #FFFFFF;
  box-shadow: 0 0 0 2px #000000 !important; /* 纯黑高亮边框 */
}
/* 修复日期面板弹出层层级问题 */
:deep(.el-picker__popper) { z-index: 9999 !important; }

/* 选择按钮阵列重排 (去掉原生的圆点和方块) */
.custom-radio-group, .custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.figma-form-style :deep(.el-radio.is-bordered), 
.figma-form-style :deep(.el-checkbox.is-bordered) {
  height: 52px;
  padding: 0 24px;
  border-radius: var(--sn-radius-md);
  border: 2px solid #F0F0F0;
  background: #FFFFFF;
  margin-right: 0;
  transition: all 0.2s;
}
.figma-form-style :deep(.el-radio.is-bordered.is-checked), 
.figma-form-style :deep(.el-checkbox.is-bordered.is-checked) {
  border-color: var(--sn-primary);
  background: var(--sn-primary);
}
.figma-form-style :deep(.el-radio.is-bordered.is-checked .el-radio__label),
.figma-form-style :deep(.el-checkbox.is-bordered.is-checked .el-checkbox__label) {
  color: #FFF;
  font-weight: 700;
}
.figma-form-style :deep(.el-radio__input), .figma-form-style :deep(.el-checkbox__input) {
  display: none; /* 隐藏原生圈圈/勾勾 */
}
/* --- 统一 el-select 触发器样式 --- */
.figma-form-style :deep(.el-select__wrapper) {
  background-color: #F5F5F5 !important;
  border-radius: var(--sn-radius-md) !important;
  height: 52px !important; /* 必须与输入框高度一致 */
  box-shadow: none !important;
  padding: 0 20px !important;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

/* 选中后的文字颜色 */
.figma-form-style :deep(.el-select__placeholder) {
  color: #111;
  font-weight: 600;
}

/* 聚焦状态：纯黑边框 */
.figma-form-style :deep(.el-select__wrapper.is-focused) {
  background-color: #FFFFFF !important;
  box-shadow: 0 0 0 2px var(--sn-primary) !important;
}

/* --- 重构下拉菜单弹出层 (Popper) --- */
/* 因为使用了 :teleported="false"，我们可以直接深度控制 */
.figma-form-style :deep(.el-select__popper) {
  border-radius: var(--sn-radius-md) !important;
  border: 1px solid #F0F0F0 !important;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
  overflow: hidden;
  margin-top: 8px !important;
}

.figma-form-style :deep(.el-select-dropdown__list) {
  padding: 6px !important;
}

/* --- 统一选项 (Option) 样式 --- */
.figma-form-style :deep(.el-select-dropdown__item) {
  height: 44px !important;
  line-height: 44px !important;
  border-radius: 10px !important;
  margin-bottom: 2px;
  font-weight: 600;
  color: #666;
  padding: 0 16px !important;
}

/* 选项悬停：浅灰背景 */
.figma-form-style :deep(.el-select-dropdown__item.is-hovering) {
  background-color: #F5F5F5 !important;
  color: #111;
}

/* 选项选中：品牌蓝背景，白字 */
.figma-form-style :deep(.el-select-dropdown__item.is-selected) {
  background-color: var(--sn-primary) !important;
  color: #FFFFFF !important;
}

/* 隐藏下拉菜单自带的小箭头，让视觉更干净 */
.figma-form-style :deep(.el-popper__arrow) {
  display: none !important;
}
.highlight-none { border-color: #FFCCC7 !important; }

/* 运动图文卡片重写 (Airbnb 风格) */
.modern-exercise-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
  width: 100%;
}
.modern-exercise-card {
  position: relative;
  background: #FFFFFF;
  border: 2px solid #F0F0F0;
  border-radius: var(--sn-radius-md);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
  cursor: pointer;
}
.modern-exercise-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.06);
  border-color: #CCC;
}
.modern-exercise-card.is-active {
  border-color: #000;
  background: #FAFAFA;
}
/* 强行掩盖原生 checkbox 影响 */
.modern-exercise-card :deep(.el-checkbox) { display: flex; width: 100%; height: 100%; margin: 0; padding: 0; }
.modern-exercise-card :deep(.el-checkbox__input) { display: none; }
.modern-exercise-card :deep(.el-checkbox__label) { width: 100%; padding: 0; }

.exercise-inner {
  display: flex;
  flex-direction: column;
  width: 100%;
}
.exercise-inner img {
  width: 100%;
  height: 120px;
  object-fit: cover;
}
.exercise-inner span {
  padding: 16px 12px;
  font-size: 15px;
  font-weight: 700;
  color: #111;
  text-align: center;
}
.text-only .exercise-inner {
  height: 100%;
  justify-content: center;
  min-height: 80px;
  background: #F9F9F9;
}

/* 子问题与补充输入 */
.sub-field-group { margin-top: 16px; display: flex; align-items: center; gap: 12px; }
.inline-sub-inputs { margin-top: 16px; display: flex; align-items: center; gap: 12px; background: #FAFAFA; padding: 16px; border-radius: var(--sn-radius-md); width: fit-content; }
.sub-label { font-weight: 600; color: #666; }
.sub-input-mt { margin-top: 16px; max-width: 600px; }

/* 选项组栅格 */
.support-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
.support-group { background: #FAFAFA; padding: 24px; border-radius: var(--sn-radius-lg); }
.support-label { font-weight: 800; color: #111; margin-bottom: 16px; font-size: 16px; }
.compact-checkboxes { display: flex; flex-direction: column; gap: 12px; }
/* 在 support 里面的 checkbox 稍微保留原生形态，避免信息密度过高 */
.support-group :deep(.el-checkbox__inner) { display: inline-block; width: 20px; height: 20px; border-radius: 6px; }
.support-group :deep(.el-checkbox__label) { font-size: 15px; color: #333; font-weight: 500; }
.support-extras { margin-top: 24px; }
.modern-divider { height: 1px; background: #F0F0F0; margin: 40px 0; }

/* 底部保存操作区 */
.modern-bottom-actions {
  position: sticky;
  bottom: 24px;
  margin-top: 40px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: var(--sn-radius-lg);
  padding: 20px 24px;
  display: flex;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0,0,0,0.04);
  z-index: 10;
}

.cta-black-giant {
  background: transparent;
  color: var(--sn-primary);
  border: 1px solid var(--sn-primary);
  height: 52px;
  padding: 0 48px;
  border-radius: var(--sn-radius-md);
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1);
}
.cta-black-giant:hover { background: rgba(23, 114, 246, 0.06); transform: translateY(-2px); }
.icon-space { margin-right: 12px; font-size: 24px; }
.is-spinning { animation: rotating 2s linear infinite; }
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 动效 */
.fade-in-enter-active, .fade-in-leave-active { transition: opacity 0.3s, transform 0.3s; }
.fade-in-enter-from, .fade-in-leave-to { opacity: 0; transform: translateY(-10px); }

/* --- 老年人模式放大适配 --- */
html[data-accessibility="elderly"] .sn-page-title { font-size: 44px; }
html[data-accessibility="elderly"] .card-title { font-size: 28px; }
html[data-accessibility="elderly"] .question-text { font-size: 24px; padding: 8px 12px; }
html[data-accessibility="elderly"] .figma-form-style :deep(.el-form-item__label) { font-size: 20px; }
html[data-accessibility="elderly"] .figma-form-style :deep(.el-radio.is-bordered), html[data-accessibility="elderly"] .figma-form-style :deep(.el-checkbox.is-bordered) { height: 64px; font-size: 20px; }
html[data-accessibility="elderly"] .exercise-inner span { font-size: 18px; }

</style>
<style>
/* 现代确认弹窗全局样式覆盖 */
.modern-confirm-dialog.el-message-box {
  border-radius: var(--sn-radius-xl) !important;
  padding: 40px 32px !important;
  background: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12) !important;
  max-width: 420px !important;
  width: 90% !important;
  font-family: AlibabaHealthFont, 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif !important;
}

/* 隐藏自带的丑陋 icon */
.modern-confirm-dialog .el-message-box__status {
  display: none !important;
}

/* 标题样式 */
.modern-confirm-dialog .el-message-box__header {
  padding: 0 !important;
  margin-bottom: 16px !important;
}
.modern-confirm-dialog .el-message-box__title {
  font-size: 24px !important;
  font-weight: 800 !important;
  color: #111 !important;
  text-align: center !important;
  letter-spacing: -0.5px !important;
}

/* 内容样式 */
.modern-confirm-dialog .el-message-box__content {
  padding: 0 !important;
  margin-bottom: 32px !important;
}
.modern-confirm-dialog .el-message-box__message {
  font-size: 16px !important;
  font-weight: 500 !important;
  color: #666 !important;
  line-height: 1.6 !important;
  text-align: center !important;
}

/* 按钮组样式 */
.modern-confirm-dialog .el-message-box__btns {
  padding: 0 !important;
  display: flex !important;
  gap: 12px !important;
  justify-content: center !important;
}
.modern-confirm-dialog .el-button {
  flex: 1 !important;
  height: 48px !important;
  border-radius: var(--sn-radius-md) !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  border: none !important;
  transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1) !important;
}

/* 取消/次级按钮 */
.modern-confirm-dialog .el-button--default {
  background: #F4F5F7 !important;
  color: #333 !important;
}
.modern-confirm-dialog .el-button--default:hover {
  background: #EAEAEA !important;
  transform: translateY(-2px) !important;
}

/* 确认/主级按钮 */
.modern-confirm-dialog .el-button--primary {
  background: var(--sn-primary) !important;
  color: #FFF !important;
  box-shadow: 0 4px 12px rgba(23,114,246,0.15) !important;
}
.modern-confirm-dialog .el-button--primary:hover {
  background: var(--sn-primary-dark) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(23,114,246,0.2) !important;
}

/* 针对危险操作（如删除）的特殊颜色 */
.modern-confirm-dialog.danger-action .el-button--primary {
  background: #EF4444 !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
}
.modern-confirm-dialog.danger-action .el-button--primary:hover {
  background: #DC2626 !important;
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3) !important;
}
</style>