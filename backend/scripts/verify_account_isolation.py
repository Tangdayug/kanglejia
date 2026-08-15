"""
账号隔离验证脚本
创建两个临时用户并验证：
1. 用户只能看到自己的设备
2. 已绑定到 A 的声纹，B 无法接入
3. 健康观察写入正确的 user_id
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base, USE_SQLITE, database_url
from model.user import User
from model.xiaozhiSession import XiaozhiVoiceprint, XiaozhiVoiceSession, HealthObservation
from common.auth import auth_handler
from service.xiaozhiService import (
    register_voiceprint,
    recognize_voiceprint,
    is_voiceprint_allowed,
    record_health_observation,
    get_recent_health_observations,
    dialogue_manager,
)


def main():
    engine = create_engine(database_url, connect_args={"check_same_thread": False} if USE_SQLITE else {})
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 先清理可能残留的测试数据
        db.query(XiaozhiVoiceprint).filter(
            XiaozhiVoiceprint.voiceprint_id.in_(["iso_vp_a_001", "iso_vp_b_001"])
        ).delete(synchronize_session=False)
        db.query(XiaozhiVoiceSession).filter(
            XiaozhiVoiceSession.voiceprint_id.in_(["iso_vp_a_001", "iso_vp_b_001"])
        ).delete(synchronize_session=False)
        db.query(HealthObservation).filter(
            HealthObservation.subject_voiceprint_id.in_(["iso_vp_a_001", "iso_vp_b_001"])
        ).delete(synchronize_session=False)
        db.query(User).filter(User.username.in_(["iso_test_user_a", "iso_test_user_b"])).delete(synchronize_session=False)
        db.commit()

        # 创建两个测试账号
        u1 = User(
            username="iso_test_user_a",
            password=auth_handler.get_password_hash("test123"),
            name="测试甲",
            gender="male",
            role="user",
        )
        u2 = User(
            username="iso_test_user_b",
            password=auth_handler.get_password_hash("test123"),
            name="测试乙",
            gender="female",
            role="user",
        )
        db.add_all([u1, u2])
        db.commit()
        db.refresh(u1)
        db.refresh(u2)
        print(f"✅ 创建测试用户 A={u1.id}, B={u2.id}")

        # 分别为 A、B 注册声纹
        vp_a = register_voiceprint("iso_vp_a_001", u1.id, db, current_user_id=u1.id)
        vp_b = register_voiceprint("iso_vp_b_001", u2.id, db, current_user_id=u2.id)
        print(f"✅ 声纹绑定: A->{vp_a.voiceprint_id}, B->{vp_b.voiceprint_id}")

        # 验证设备列表按用户隔离
        devices_a = db.query(XiaozhiVoiceprint).filter(XiaozhiVoiceprint.user_id == u1.id).all()
        devices_b = db.query(XiaozhiVoiceprint).filter(XiaozhiVoiceprint.user_id == u2.id).all()
        assert len(devices_a) == 1 and devices_a[0].voiceprint_id == "iso_vp_a_001"
        assert len(devices_b) == 1 and devices_b[0].voiceprint_id == "iso_vp_b_001"
        print("✅ 设备列表按用户隔离正确")

        # A 的声纹，B 无法接入
        try:
            dialogue_manager.get_or_create_voice_session(
                voiceprint_id="iso_vp_a_001",
                db_session=db,
                fallback_user_id=u2.id,
                token=None,
                agent_name="second-nature",
            )
            print("❌ 跨账号声纹接入未被拦截")
            return False
        except PermissionError as e:
            print(f"✅ 跨账号声纹接入被拦截: {e}")

        # B 使用自己的声纹可以接入
        session_id, is_new = dialogue_manager.get_or_create_voice_session(
            voiceprint_id="iso_vp_b_001",
            db_session=db,
            fallback_user_id=u2.id,
            token=None,
            agent_name="second-nature",
        )
        print(f"✅ B 使用自己的声纹接入成功，session_id={session_id}, is_new={is_new}")

        # 健康观察写入 B 的账号
        obs = record_health_observation(
            observer_voiceprint_id="iso_vp_b_001",
            subject_voiceprint_id="iso_vp_b_001",
            content="今天头有点晕",
            db_session=db,
            subject_user_id=u2.id,
        )
        assert obs.user_id == u2.id
        print(f"✅ 健康观察写入正确的 user_id={obs.user_id}")

        # A 查不到 B 的健康观察
        obs_a = get_recent_health_observations("iso_vp_b_001", db, current_user_id=u1.id, limit=5)
        obs_b = get_recent_health_observations("iso_vp_b_001", db, current_user_id=u2.id, limit=5)
        assert len(obs_a) == 0
        assert len(obs_b) == 1
        print("✅ 健康观察按 user_id 隔离正确")

        # is_voiceprint_allowed 校验
        assert is_voiceprint_allowed("iso_vp_a_001", db, current_user_id=u1.id) is True
        assert is_voiceprint_allowed("iso_vp_a_001", db, current_user_id=u2.id) is False
        print("✅ is_voiceprint_allowed 按当前用户隔离正确")

        print("\n🎉 账号隔离验证全部通过")
        return True

    finally:
        # 清理测试数据
        try:
            db.query(XiaozhiVoiceprint).filter(
                XiaozhiVoiceprint.voiceprint_id.in_(["iso_vp_a_001", "iso_vp_b_001"])
            ).delete(synchronize_session=False)
            db.query(XiaozhiVoiceSession).filter(
                XiaozhiVoiceSession.voiceprint_id.in_(["iso_vp_a_001", "iso_vp_b_001"])
            ).delete(synchronize_session=False)
            db.query(User).filter(User.username.in_(["iso_test_user_a", "iso_test_user_b"])).delete(synchronize_session=False)
            db.commit()
            print("✅ 测试数据已清理")
        except Exception as e:
            print(f"⚠️ 测试数据清理失败: {e}")
        db.close()


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
