"""
从旧数据库迁移用户 20260101 的数据到持久化存储

旧数据库位置: backend/data/secondnature.db
新数据库位置: /mnt/workspace/backend/data/secondnature.db

用户信息:
- 用户名: 20260101
- 姓名: 李秀
- ID: 将保持为 1（或可以改为 20260101）
"""
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from sqlalchemy import create_engine, text


def migrate_user_data():
    """迁移用户 20260101 的数据"""

    # 旧数据库路径
    old_db_path = Path(__file__).parent.parent / "data" / "secondnature.db"

    if not old_db_path.exists():
        print(f"❌ 旧数据库不存在: {old_db_path}")
        return False

    print("=" * 60)
    print("迁移用户 20260101 数据")
    print("=" * 60)

    # 连接旧数据库
    old_engine = create_engine(f"sqlite:///{old_db_path}")

    try:
        with old_engine.connect() as old_conn:
            # 1. 查询用户信息
            print("\n步骤 1: 读取用户信息")
            result = old_conn.execute(text("SELECT * FROM user WHERE username = '20260101'"))
            user_row = result.fetchone()

            if not user_row:
                print("❌ 未找到用户 20260101")
                return False

            print(f"✅ 找到用户: ID={user_row[0]}, 用户名={user_row[1]}, 姓名={user_row[3]}")

            # 2. 查询健康档案
            print("\n步骤 2: 读取健康档案")
            result = old_conn.execute(text("SELECT * FROM health_record WHERE user_id = 1"))
            health_record = result.fetchone()

            if health_record:
                print(f"✅ 找到健康档案: {health_record[3]}")
            else:
                print("⚠️  未找到健康档案")

            # 3. 查询健康测试
            print("\n步骤 3: 读取健康测试")
            result = old_conn.execute(text("SELECT * FROM health_test WHERE user_id = 1"))
            health_tests = result.fetchall()

            print(f"✅ 找到 {len(health_tests)} 条健康测试记录")

            # 4. 查询对话记录
            print("\n步骤 4: 读取对话记录")
            result = old_conn.execute(text("""
                SELECT cs.id, cs.title, cs.created_at, cm.role, cm.content, cm.created_at as msg_created_at
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cm.session_id = cs.id
                WHERE cs.user_id = 1
                ORDER BY cs.id, cm.id
            """))
            chat_data = result.fetchall()

            if chat_data:
                print(f"✅ 找到对话记录")
            else:
                print("⚠️  未找到对话记录")

            # 5. 写入新数据库
            print("\n步骤 5: 写入新数据库")
            from model import get_db_session
            from model.user import User
            from model.healthRecord import HealthRecord
            from model.healthTest import HealthTest
            from model.chatHistory import ChatSession, ChatMessage

            db_gen = get_db_session()
            db = next(db_gen)

            try:
                # 检查新数据库中是否已存在该用户
                existing_user = db.query(User).filter(User.username == "20260101").first()

                if existing_user:
                    print("⚠️  新数据库中已存在用户 20260101，跳过迁移")
                    print("   如需强制迁移，请先删除新数据库中的该用户")
                    return False

                # 创建用户（保持原有 ID 或使用新 ID）
                new_user = User()
                new_user.id = user_row[0]  # 保持原有 ID: 1
                new_user.username = user_row[1]
                new_user.password = user_row[2]
                new_user.name = user_row[3]
                new_user.gender = user_row[4]
                new_user.role = user_row[5]

                db.add(new_user)
                db.flush()  # 获取分配的 ID
                print(f"✅ 创建用户: ID={new_user.id}, 用户名={new_user.username}")

                # 迁移健康档案
                if health_record:
                    # 将数据映射到模型字段
                    new_record = HealthRecord()
                    new_record.user_id = new_user.id
                    new_record.name = health_record[3]
                    new_record.birth_date = health_record[4]
                    new_record.gender = health_record[5]
                    new_record.height = health_record[6]
                    new_record.weight = health_record[7]
                    new_record.bmi = str(health_record[8]) if health_record[8] else None
                    new_record.waist = health_record[9]
                    new_record.abdomen = health_record[10]
                    new_record.systolic_bp = health_record[11]
                    new_record.diastolic_bp = health_record[12]
                    new_record.heart_rate = health_record[13]
                    new_record.sleep_good = bool(health_record[14])
                    new_record.sleep_difficulty_falling = bool(health_record[15])
                    new_record.sleep_easily_wake = bool(health_record[16])
                    new_record.sleep_early_wake = bool(health_record[17])
                    new_record.sleep_daytime_sleepiness = bool(health_record[18])
                    new_record.sleep_other = bool(health_record[19])
                    new_record.sleep_other_desc = health_record[20]
                    new_record.disease_hypertension = bool(health_record[21])
                    new_record.disease_diabetes = bool(health_record[22])
                    new_record.disease_dyslipidemia = bool(health_record[23])
                    new_record.disease_coronary = bool(health_record[24])
                    new_record.disease_angina = bool(health_record[25])
                    new_record.disease_myocardial_infarction = bool(health_record[26])
                    new_record.disease_stroke = bool(health_record[27])
                    new_record.disease_copd = bool(health_record[28])
                    new_record.disease_gout = bool(health_record[29])
                    new_record.disease_kidney = bool(health_record[30])
                    new_record.disease_hypothyroidism = bool(health_record[31])
                    new_record.disease_hyperthyroidism = bool(health_record[32])
                    new_record.disease_osteoporosis = bool(health_record[33])
                    new_record.disease_parkinsons = bool(health_record[34])
                    new_record.disease_alzheimers = bool(health_record[35])
                    new_record.disease_tumor = bool(health_record[36])
                    new_record.disease_tumor_site = health_record[37]
                    new_record.disease_other = bool(health_record[38])
                    new_record.disease_other_desc = health_record[39]
                    new_record.disease_none = bool(health_record[40])
                    new_record.is_medication = bool(health_record[41])
                    new_record.medication_names = health_record[42]
                    new_record.smoking_status = health_record[43]
                    new_record.smoking_count = health_record[44]
                    new_record.drinking_status = health_record[45]
                    new_record.drinking_frequency = health_record[46]
                    new_record.drinking_amount = health_record[47]
                    new_record.exercise_walking = bool(health_record[48])
                    new_record.exercise_jogging = bool(health_record[49])
                    new_record.exercise_square_dance = bool(health_record[50])
                    new_record.exercise_tai_chi = bool(health_record[51])
                    new_record.exercise_swimming = bool(health_record[52])
                    new_record.exercise_cycling = bool(health_record[53])
                    new_record.exercise_racket = bool(health_record[54])
                    new_record.exercise_hiking = bool(health_record[55])
                    new_record.exercise_gardening = bool(health_record[56])
                    new_record.exercise_fishing = bool(health_record[57])
                    new_record.exercise_gym = bool(health_record[58])
                    new_record.exercise_yoga = bool(health_record[59])
                    new_record.exercise_no_preference = bool(health_record[60])
                    new_record.exercise_other = bool(health_record[61])
                    new_record.exercise_other_desc = health_record[62]
                    new_record.support_equipment = bool(health_record[63])
                    new_record.support_organization = bool(health_record[64])
                    new_record.support_info = bool(health_record[65])
                    new_record.support_policy = bool(health_record[66])
                    new_record.support_none = bool(health_record[67])
                    new_record.support_other = health_record[68]
                    new_record.marital_status = health_record[69]
                    new_record.address = health_record[70]
                    new_record.work_status = health_record[71]
                    new_record.education = health_record[72]
                    new_record.ethnicity = health_record[73]
                    new_record.religion = health_record[74]
                    new_record.residence_type = health_record[75]
                    new_record.co_residents = health_record[76]
                    new_record.insurance_type = health_record[77]
                    new_record.occupation = health_record[78]
                    new_record.income = health_record[79]
                    new_record.is_draft = bool(health_record[80])
                    new_record.is_completed = bool(health_record[81])
                    new_record.created_at = datetime.fromisoformat(str(health_record[82]).replace('+00:00', '+00:00')) if health_record[82] else datetime.now(timezone.utc)
                    new_record.updated_at = datetime.fromisoformat(str(health_record[83]).replace('+00:00', '+00:00')) if health_record[83] else datetime.now(timezone.utc)

                    db.add(new_record)
                    print(f"✅ 创建健康档案")

                # 迁移健康测试
                session_id_map = {}  # 旧会话ID到新会话ID的映射

                for test_row in health_tests:
                    new_test = HealthTest()
                    new_test.user_id = new_user.id
                    new_test.q1_memory_issue = bool(test_row[2])
                    new_test.q1_1_recall_name = test_row[3]
                    new_test.q1_2_today_date = test_row[4]
                    new_test.q1_2_correct = bool(test_row[5])
                    new_test.q1_3_home_address = test_row[6]
                    new_test.q1_3_correct = bool(test_row[7])
                    new_test.q1_4_current_location = test_row[8]
                    new_test.q1_4_correct = bool(test_row[9])
                    new_test.q2_completed = bool(test_row[10])
                    new_test.q2_time_seconds = test_row[11]
                    new_test.q3_fatigued = bool(test_row[12])
                    new_test.q4_health_poor = bool(test_row[13])
                    new_test.q5_vision_issue = bool(test_row[14])
                    new_test.q6_reading_issue = bool(test_row[15])
                    new_test.q7_hearing_issue = bool(test_row[16])
                    new_test.q8_depressed = bool(test_row[17])
                    new_test.q9_anxious = bool(test_row[18])
                    new_test.assistance_mode = test_row[19]
                    new_test.score_cognitive = test_row[20]
                    new_test.score_motor = test_row[21]
                    new_test.score_vitality = test_row[22]
                    new_test.score_vision = test_row[23]
                    new_test.score_hearing = test_row[24]
                    new_test.score_psychological = test_row[25]
                    new_test.score_total = test_row[26]
                    new_test.risk_cognitive = bool(test_row[27])
                    new_test.risk_motor = bool(test_row[28])
                    new_test.risk_vitality = bool(test_row[29])
                    new_test.risk_vision = bool(test_row[30])
                    new_test.risk_hearing = bool(test_row[31])
                    new_test.risk_psychological = bool(test_row[32])

                    # JSON 字段
                    import json
                    try:
                        new_test.recommendations = json.loads(test_row[33]) if test_row[33] else None
                        new_test.facilities = json.loads(test_row[34]) if test_row[34] else None
                    except:
                        new_test.recommendations = None
                        new_test.facilities = None

                    new_test.created_at = datetime.fromisoformat(str(test_row[35]).replace('+00:00', '+00:00')) if test_row[35] else datetime.now(timezone.utc)
                    new_test.updated_at = datetime.fromisoformat(str(test_row[36]).replace('+00:00', '+00:00')) if test_row[36] else datetime.now(timezone.utc)

                    db.add(new_test)

                print(f"✅ 迁移 {len(health_tests)} 条健康测试记录")

                # 迁移对话记录（如果有）
                if chat_data:
                    current_session_id = None
                    current_session = None

                    for row in chat_data:
                        session_id = row[0]
                        session_title = row[1]
                        session_created = row[2]
                        role = row[3]
                        content = row[4]
                        msg_created = row[5]

                        # 创建新会话
                        if session_id != current_session_id:
                            current_session = ChatSession()
                            current_session.user_id = new_user.id
                            current_session.title = session_title
                            current_session.created_at = datetime.fromisoformat(str(session_created).replace('+00:00', '+00:00')) if session_created else datetime.now(timezone.utc)
                            current_session.updated_at = datetime.fromisoformat(str(session_created).replace('+00:00', '+00:00')) if session_created else datetime.now(timezone.utc)
                            db.add(current_session)
                            db.flush()  # 获取新会话 ID
                            session_id_map[session_id] = current_session.id
                            current_session_id = session_id

                        # 创建消息
                        if role and content:
                            new_message = ChatMessage()
                            new_message.session_id = current_session.id
                            new_message.role = role
                            new_message.content = content
                            new_message.created_at = datetime.fromisoformat(str(msg_created).replace('+00:00', '+00:00')) if msg_created else datetime.now(timezone.utc)
                            db.add(new_message)

                    print(f"✅ 迁移对话记录")

                db.commit()

                print("\n" + "=" * 60)
                print("✅ 数据迁移完成！")
                print("=" * 60)
                print(f"\n迁移的用户信息:")
                print(f"  用户ID: {new_user.id}")
                print(f"  用户名: {new_user.username}")
                print(f"  密码: (保持原密码)")
                print(f"  姓名: {new_user.name}")
                print(f"\n💡 提示: 数据已存储在 /mnt/workspace/backend/data/")
                print("=" * 60)

                return True

            except Exception as e:
                db.rollback()
                print(f"❌ 迁移失败: {e}")
                import traceback
                traceback.print_exc()
                return False
            finally:
                db.close()

    except Exception as e:
        print(f"❌ 读取旧数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    migrate_user_data()


if __name__ == "__main__":
    main()
