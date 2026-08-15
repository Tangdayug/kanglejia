"""
数据初始化脚本
创建默认用户（20260101）和测试数据
所有数据存储在 /mnt/workspace 目录（持久化卷）
"""
import os
import sys
from pathlib import Path

# 添加父目录到路径以导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from model import get_db_session, Base, engine
from model.user import User
from model.healthRecord import HealthRecord
from model.healthTest import HealthTest
from model.chatHistory import ChatSession, ChatMessage


def init_default_user():
    """初始化默认用户 20260101"""
    db_gen = get_db_session()
    db = next(db_gen)

    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.id == 20260101).first()
        if existing_user:
            print("✅ 默认用户 20260101 已存在")
            return existing_user

        # 生成密码哈希
        from common.auth import AuthHandler
        auth_handler = AuthHandler()
        password_hash = auth_handler.get_password_hash("123456")  # 默认密码: 123456

        # 创建默认用户
        user = User()
        user.id = 20260101
        user.username = "testuser"
        user.password = password_hash
        user.name = "测试用户"
        user.gender = "男"
        user.role = "USER"

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✅ 创建默认用户: ID={user.id}, 用户名={user.username}, 密码=123456")
        return user

    except Exception as e:
        db.rollback()
        print(f"❌ 创建默认用户失败: {e}")
        raise
    finally:
        db.close()


def init_health_record(user_id):
    """初始化健康档案"""
    db_gen = get_db_session()
    db = next(db_gen)

    try:
        # 检查是否已有健康档案
        existing = db.query(HealthRecord).filter(HealthRecord.user_id == user_id).first()
        if existing:
            print("✅ 健康档案已存在")
            return

        # 创建示例健康档案
        record = HealthRecord()
        record.user_id = user_id
        record.name = "测试用户"
        record.birth_date = "1960-01-01"
        record.gender = "男"
        record.height = 170.0
        record.weight = 70.0
        record.bmi = "24.2"
        record.waist = 85.0
        record.abdomen = 90.0
        record.systolic_bp = 120
        record.diastolic_bp = 80
        record.heart_rate = 72

        # 睡眠状况
        record.sleep_good = True
        record.sleep_difficulty_falling = False
        record.sleep_easily_wake = False

        # 慢性疾病
        record.disease_hypertension = False
        record.disease_diabetes = False
        record.disease_none = True

        # 生活习惯
        record.smoking_status = "never"
        record.drinking_status = "never"

        # 运动偏好
        record.exercise_walking = True
        record.exercise_tai_chi = True

        # 社会支持
        record.support_organization = True

        # 社会信息
        record.marital_status = "married"
        record.work_status = "retired"
        record.education = "undergraduate"
        record.residence_type = "urban"
        record.co_residents = "spouse"

        record.is_draft = False
        record.is_completed = True
        record.created_at = datetime.now(timezone.utc)
        record.updated_at = datetime.now(timezone.utc)

        db.add(record)
        db.commit()

        print("✅ 创建示例健康档案")

    except Exception as e:
        db.rollback()
        print(f"❌ 创建健康档案失败: {e}")
        raise
    finally:
        db.close()


def init_health_test(user_id):
    """初始化健康测试"""
    db_gen = get_db_session()
    db = next(db_gen)

    try:
        # 检查是否已有健康测试
        existing = db.query(HealthTest).filter(HealthTest.user_id == user_id).first()
        if existing:
            print("✅ 健康测试已存在")
            return

        # 创建示例健康测试
        test = HealthTest()
        test.user_id = user_id

        # 认知功能测试
        test.q1_memory_issue = False
        test.q1_2_today_date = "2026-02-10"
        test.q1_2_correct = True
        test.q1_3_correct = True
        test.q1_4_correct = True

        # 运动功能测试
        test.q2_completed = True
        test.q2_time_seconds = 12.5

        # 其他风险评估
        test.q3_fatigued = False
        test.q4_health_poor = False
        test.q5_vision_issue = False
        test.q6_reading_issue = False
        test.q7_hearing_issue = False
        test.q8_depressed = False
        test.q9_anxious = False

        # 协助模式
        test.assistance_mode = "alone"

        # 评分（示例数据）
        test.score_cognitive = 100
        test.score_motor = 95
        test.score_vitality = 90
        test.score_vision = 100
        test.score_hearing = 100
        test.score_psychological = 95
        test.score_total = 97

        # 风险评估
        test.risk_cognitive = False
        test.risk_motor = False
        test.risk_vitality = False
        test.risk_vision = False
        test.risk_hearing = False
        test.risk_psychological = False

        # 建议
        test.recommendations = {
            "overall": "您的健康状况良好，继续保持！",
            "tips": [
                "保持每天30分钟的中等强度运动",
                "注意饮食均衡，多吃蔬菜水果",
                "保持良好的睡眠习惯"
            ]
        }

        test.facilities = {
            "equipment": ["步行路径", "健身器材"],
            "organization": ["社区活动中心"],
            "info": ["健康宣传栏"],
            "policy": ["老年人健康补贴"]
        }

        test.created_at = datetime.now(timezone.utc)
        test.updated_at = datetime.now(timezone.utc)

        db.add(test)
        db.commit()

        print("✅ 创建示例健康测试")

    except Exception as e:
        db.rollback()
        print(f"❌ 创建健康测试失败: {e}")
        raise
    finally:
        db.close()


def init_sample_chat(user_id):
    """初始化示例对话"""
    db_gen = get_db_session()
    db = next(db_gen)

    try:
        # 检查是否已有对话
        existing = db.query(ChatSession).filter(ChatSession.user_id == user_id).first()
        if existing:
            print("✅ 示例对话已存在")
            return

        # 创建示例会话
        session = ChatSession()
        session.user_id = user_id
        session.title = "关于健康饮食的咨询"
        session.created_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        db.add(session)
        db.commit()
        db.refresh(session)

        # 创建示例消息
        user_message = ChatMessage()
        user_message.session_id = session.id
        user_message.role = "user"
        user_message.content = "请问老年人日常饮食应该注意什么？"
        user_message.created_at = datetime.now(timezone.utc)

        db.add(user_message)
        db.commit()

        assistant_message = ChatMessage()
        assistant_message.session_id = session.id
        assistant_message.role = "assistant"
        assistant_message.content = """老年人日常饮食应注意以下几点：

1. **营养均衡**
   - 保证蛋白质摄入：每天摄入优质蛋白质（鱼、肉、蛋、奶、豆制品）
   - 适量碳水化合物：选择粗粮、杂粮，减少精米白面

2. **控制油盐糖**
   - 低盐：每天食盐摄入量不超过6克
   - 低油：选择植物油，少吃动物油脂
   - 低糖：少吃甜食，控制添加糖摄入

3. **多吃蔬菜水果**
   - 每天摄入300-500克蔬菜
   - 每天摄入200-350克水果
   - 深色蔬菜占一半以上

4. **适量饮水**
   - 每天饮水1500-1700毫升
   - 少量多次，主动饮水
   - 可选择淡茶水、白开水

5. **饮食习惯**
   - 定时定量，细嚼慢咽
   - 三餐规律，不暴饮暴食
   - 食物多样化，不挑食偏食

6. **特殊注意事项**
   - 根据自身健康状况调整饮食
   - 有慢性病的老人遵医嘱饮食
   - 服药时注意与饮食的相互作用

📚 来源：健康饮食指南.md"""
        assistant_message.created_at = datetime.now(timezone.utc)

        db.add(assistant_message)
        db.commit()

        print("✅ 创建示例对话")

    except Exception as e:
        db.rollback()
        print(f"❌ 创建示例对话失败: {e}")
        raise
    finally:
        db.close()


def ensure_persistent_directories():
    """确保持久化目录存在"""
    dirs = [
        "/mnt/workspace/backend/data",
        "/mnt/workspace/backend/rag/data",
        "/mnt/workspace/backend/rag/data/chroma",
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 确保目录存在: {dir_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("初始化默认数据")
    print("=" * 60)

    try:
        # 1. 确保持久化目录存在
        print("\n步骤 1: 创建持久化目录")
        ensure_persistent_directories()

        # 2. 初始化数据库表
        print("\n步骤 2: 初始化数据库表")
        from model import init_db
        init_db()

        # 3. 创建默认用户
        print("\n步骤 3: 创建默认用户")
        user = init_default_user()

        # 4. 创建健康档案
        print("\n步骤 4: 创建健康档案")
        init_health_record(user.id)

        # 5. 创建健康测试
        print("\n步骤 5: 创建健康测试")
        init_health_test(user.id)

        # 6. 创建示例对话
        print("\n步骤 6: 创建示例对话")
        init_sample_chat(user.id)

        print("\n" + "=" * 60)
        print("✅ 数据初始化完成！")
        print("=" * 60)
        print("\n默认测试用户:")
        print(f"  用户ID: {user.id}")
        print(f"  用户名: {user.username}")
        print(f"  密码: 123456")
        print(f"  姓名: {user.name}")
        print(f"  性别: {user.gender}")
        print(f"  角色: {user.role}")
        print("\n💡 提示: 所有数据已存储在 /mnt/workspace 目录")
        print("   即使 Docker 容器重启，数据也不会丢失")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 数据初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
