-- 健康档案表
CREATE TABLE IF NOT EXISTS `health_record` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `name` VARCHAR(100) NOT NULL COMMENT '姓名',
    `birth_date` VARCHAR(20) NOT NULL COMMENT '出生年月',
    `gender` VARCHAR(10) NOT NULL COMMENT '性别',
    `height` FLOAT DEFAULT NULL COMMENT '身高(cm)',
    `weight` FLOAT DEFAULT NULL COMMENT '体重(kg)',
    `bmi` VARCHAR(10) DEFAULT NULL COMMENT 'BMI',
    `waist` FLOAT DEFAULT NULL COMMENT '腰围(cm)',
    `abdomen` FLOAT DEFAULT NULL COMMENT '腹围(cm)',
    `systolic_bp` INT DEFAULT NULL COMMENT '收缩压(mmHg)',
    `diastolic_bp` INT DEFAULT NULL COMMENT '舒张压(mmHg)',
    `heart_rate` INT DEFAULT NULL COMMENT '心率(次/min)',

    -- 睡眠状况
    `sleep_good` BOOLEAN DEFAULT FALSE COMMENT '睡眠良好',
    `sleep_difficulty_falling` BOOLEAN DEFAULT FALSE COMMENT '入睡困难',
    `sleep_easily_wake` BOOLEAN DEFAULT FALSE COMMENT '易醒',
    `sleep_early_wake` BOOLEAN DEFAULT FALSE COMMENT '早醒',
    `sleep_daytime_sleepiness` BOOLEAN DEFAULT FALSE COMMENT '白天犯困',
    `sleep_other` BOOLEAN DEFAULT FALSE COMMENT '其他睡眠问题',
    `sleep_other_desc` TEXT DEFAULT NULL COMMENT '其他睡眠问题描述',

    -- 慢性病情况
    `disease_hypertension` BOOLEAN DEFAULT FALSE COMMENT '高血压',
    `disease_diabetes` BOOLEAN DEFAULT FALSE COMMENT '糖尿病',
    `disease_dyslipidemia` BOOLEAN DEFAULT FALSE COMMENT '血脂异常',
    `disease_coronary` BOOLEAN DEFAULT FALSE COMMENT '冠心病',
    `disease_angina` BOOLEAN DEFAULT FALSE COMMENT '心绞痛',
    `disease_myocardial_infarction` BOOLEAN DEFAULT FALSE COMMENT '心肌梗死',
    `disease_stroke` BOOLEAN DEFAULT FALSE COMMENT '脑卒中',
    `disease_copd` BOOLEAN DEFAULT FALSE COMMENT '慢阻肺',
    `disease_gout` BOOLEAN DEFAULT FALSE COMMENT '痛风',
    `disease_kidney` BOOLEAN DEFAULT FALSE COMMENT '慢性肾病',
    `disease_hypothyroidism` BOOLEAN DEFAULT FALSE COMMENT '甲减',
    `disease_hyperthyroidism` BOOLEAN DEFAULT FALSE COMMENT '甲亢',
    `disease_osteoporosis` BOOLEAN DEFAULT FALSE COMMENT '骨质疏松',
    `disease_parkinsons` BOOLEAN DEFAULT FALSE COMMENT '帕金森',
    `disease_alzheimers` BOOLEAN DEFAULT FALSE COMMENT '阿尔茨海默',
    `disease_tumor` BOOLEAN DEFAULT FALSE COMMENT '肿瘤病史',
    `disease_tumor_site` VARCHAR(200) DEFAULT NULL COMMENT '肿瘤部位',
    `disease_other` BOOLEAN DEFAULT FALSE COMMENT '其他慢性病',
    `disease_other_desc` VARCHAR(200) DEFAULT NULL COMMENT '其他慢性病名称',
    `disease_none` BOOLEAN DEFAULT FALSE COMMENT '无慢性病',

    -- 用药情况
    `is_medication` BOOLEAN DEFAULT FALSE COMMENT '是否用药',
    `medication_names` TEXT DEFAULT NULL COMMENT '药物名称',

    -- 生活习惯 - 吸烟
    `smoking_status` VARCHAR(50) DEFAULT NULL COMMENT '吸烟状态',
    `smoking_count` INT DEFAULT NULL COMMENT '每天吸烟支数',

    -- 生活习惯 - 喝酒
    `drinking_status` VARCHAR(50) DEFAULT NULL COMMENT '喝酒状态',
    `drinking_frequency` INT DEFAULT NULL COMMENT '每周饮酒次数',
    `drinking_amount` INT DEFAULT NULL COMMENT '每次饮酒两数',

    -- 运动偏好
    `exercise_walking` BOOLEAN DEFAULT FALSE COMMENT '散步/健走',
    `exercise_jogging` BOOLEAN DEFAULT FALSE COMMENT '慢跑',
    `exercise_square_dance` BOOLEAN DEFAULT FALSE COMMENT '广场舞',
    `exercise_tai_chi` BOOLEAN DEFAULT FALSE COMMENT '太极拳/八段锦',
    `exercise_swimming` BOOLEAN DEFAULT FALSE COMMENT '游泳',
    `exercise_cycling` BOOLEAN DEFAULT FALSE COMMENT '骑车',
    `exercise_racket` BOOLEAN DEFAULT FALSE COMMENT '乒乓/羽毛球',
    `exercise_hiking` BOOLEAN DEFAULT FALSE COMMENT '爬山/爬楼梯',
    `exercise_gardening` BOOLEAN DEFAULT FALSE COMMENT '园艺',
    `exercise_fishing` BOOLEAN DEFAULT FALSE COMMENT '钓鱼',
    `exercise_gym` BOOLEAN DEFAULT FALSE COMMENT '健身房器械',
    `exercise_yoga` BOOLEAN DEFAULT FALSE COMMENT '瑜伽/普拉提',
    `exercise_no_preference` BOOLEAN DEFAULT FALSE COMMENT '无运动偏好',
    `exercise_other` BOOLEAN DEFAULT FALSE COMMENT '其他运动',
    `exercise_other_desc` VARCHAR(200) DEFAULT NULL COMMENT '其他运动描述',

    -- 社会支持
    `support_equipment` BOOLEAN DEFAULT FALSE COMMENT 'A.场地/器材支持',
    `support_organization` BOOLEAN DEFAULT FALSE COMMENT 'B.组织/人群支持',
    `support_info` BOOLEAN DEFAULT FALSE COMMENT 'C.信息/指导支持',
    `support_policy` BOOLEAN DEFAULT FALSE COMMENT 'D.政策/费用支持',
    `support_none` BOOLEAN DEFAULT FALSE COMMENT '无支持',
    `support_other` VARCHAR(500) DEFAULT NULL COMMENT '其他支持描述',

    -- 社会人口学信息
    `marital_status` VARCHAR(50) DEFAULT NULL COMMENT '婚姻状态',
    `address` VARCHAR(500) DEFAULT NULL COMMENT '居住地址',
    `work_status` VARCHAR(50) DEFAULT NULL COMMENT '工作状态',
    `education` VARCHAR(50) DEFAULT NULL COMMENT '文化程度',
    `ethnicity` VARCHAR(50) DEFAULT NULL COMMENT '民族',
    `religion` VARCHAR(50) DEFAULT NULL COMMENT '宗教信仰',
    `residence_type` VARCHAR(50) DEFAULT NULL COMMENT '居住地类型',
    `co_residents` VARCHAR(50) DEFAULT NULL COMMENT '共同居住者',
    `insurance_type` VARCHAR(50) DEFAULT NULL COMMENT '医保类型',
    `occupation` VARCHAR(100) DEFAULT NULL COMMENT '职业',
    `income` VARCHAR(50) DEFAULT NULL COMMENT '家庭人均月收入',

    -- 状态字段
    `is_draft` BOOLEAN DEFAULT TRUE NOT NULL COMMENT '是否为草稿',
    `is_completed` BOOLEAN DEFAULT FALSE NOT NULL COMMENT '是否已完成',

    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_is_draft` (`is_draft`),
    INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康档案表';
