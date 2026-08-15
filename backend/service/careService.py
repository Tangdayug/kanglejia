from common.datetime_utils import get_now_naive
"""日常关怀服务"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from model.chatHistory import ChatSession, ChatMessage
from model.interventionLog import InterventionLog
from service.chatService import ChatService
from common.deepseek_client import get_deepseek_client


class CareService:
    """日常关怀服务类"""

    @staticmethod
    def generate_daily_care(user_id: int, db_session: Session) -> Dict[str, Any]:
        interventions = CareService._get_recent_interventions(user_id, db_session)
        recent_conversations = CareService._get_recent_conversations(user_id, db_session)
        health_context = ChatService.get_user_health_context(user_id, db_session)

        prompt = CareService._build_care_prompt(interventions, recent_conversations, health_context)

        try:
            llm_client = get_deepseek_client()
            care_message = llm_client.generate_chat_response(
                system_prompt="你是一个温暖、专业的老年人健康关怀助手。",
                user_message=prompt,
                temperature=0.8
            )

            care_message = care_message.strip()
            for prefix in ["好的，", "好的。", "嗯，", "嗯。", "您好，", "您好。"]:
                if care_message.startswith(prefix):
                    care_message = care_message[len(prefix):].strip()

        except Exception as e:
            if interventions and interventions[0].execution_status == 'pending':
                care_message = f"上次提到的{interventions[0].intervention_suggestion[:20]}...您尝试了吗？来和我聊一聊吧"
            else:
                care_message = "您好，今天感觉怎么样？来和我聊一聊吧"

        intervention_id = None
        if interventions:
            pending_interventions = [i for i in interventions if i.execution_status == 'pending']
            if pending_interventions:
                intervention_id = pending_interventions[0].id
            else:
                intervention_id = interventions[0].id

        return {
            'message': care_message,
            'interventionId': intervention_id
        }

    @staticmethod
    def _get_recent_interventions(user_id: int, db_session: Session) -> List[InterventionLog]:
        seven_days_ago = get_now_naive() - timedelta(days=7)

        query = select(InterventionLog).where(
            InterventionLog.user_id == user_id,
            InterventionLog.created_at >= seven_days_ago,
            InterventionLog.execution_status.in_(['pending', 'completed'])
        ).order_by(desc(InterventionLog.created_at)).limit(3)

        return list(db_session.execute(query).scalars().all())

    @staticmethod
    def _get_recent_conversations(user_id: int, db_session: Session) -> List[Dict[str, Any]]:
        three_days_ago = get_now_naive() - timedelta(days=3)

        sessions_query = select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.updated_at >= three_days_ago
        ).order_by(desc(ChatSession.updated_at)).limit(5)

        sessions = list(db_session.execute(sessions_query).scalars().all())

        conversations = []
        for session in sessions:
            messages_query = select(ChatMessage).where(
                ChatMessage.session_id == session.id,
                ChatMessage.role == 'user'
            ).order_by(desc(ChatMessage.created_at)).limit(3)

            messages = list(db_session.execute(messages_query).scalars().all())
            for msg in messages:
                conversations.append({
                    'session_id': session.id,
                    'content': msg.content[:100] if len(msg.content) > 100 else msg.content,
                    'created_at': msg.created_at
                })

        return conversations

    @staticmethod
    def _build_care_prompt(
        interventions: List[InterventionLog],
        conversations: List[Dict[str, Any]],
        health_context: Dict[str, Any]
    ) -> str:
        prompt = """请生成一句简短、亲切的关怀问候（20-50字）。

要求：
1. 语气温暖、自然，像朋友聊天一样
2. 简洁明了，不超过50字
3. 如果用户有未完成的健康建议，优先提及
4. 鼓励用户分享最近的状况
5. 结尾引导对话："来和我聊一聊吧"

"""

        if interventions:
            prompt += "\n最近的健康建议：\n"
            for intervention in interventions[:2]:
                prompt += f"- {intervention.intervention_suggestion}\n"
                if intervention.execution_status == 'pending':
                    prompt += "  状态：尚未开始执行\n"
                elif intervention.execution_status == 'completed' and not intervention.user_feedback:
                    prompt += "  状态：已完成，等待反馈\n"

        if conversations:
            prompt += "\n最近的对话话题：\n"
            for conv in conversations[:2]:
                prompt += f"- {conv['content']}\n"

        health_record = health_context.get('healthRecord', {})
        if health_record:
            prompt += "\n用户健康信息（仅供参考）：\n"
            basic_info = health_record.get('basicInfo', {})
            if basic_info.get('age'):
                prompt += f"- 年龄：{basic_info['age']}岁\n"
            if health_record.get('exercise'):
                prompt += f"- 运动偏好：{', '.join(health_record['exercise'])}\n"
            if basic_info.get('sleepStatus'):
                prompt += f"- 睡眠状况：{basic_info['sleepStatus']}\n"

        prompt += """
请直接输出关怀问候，不要任何解释和标点符号之外的符号。

示例：
1. "您最近感觉怎么样？来和我聊一聊吧"
2. "您昨晚的拉伸做了吗？来和我分享一下吧！"
3. "上次推荐给您的饭后散步30分钟您感觉怎么样？来和我聊一聊吧"

请生成：
"""

        return prompt

    @staticmethod
    def save_feedback(
        user_id: int,
        intervention_id: int,
        feedback: str,
        session_id: int,
        db_session: Session
    ) -> bool:
        try:
            query = select(InterventionLog).where(
                InterventionLog.id == intervention_id,
                InterventionLog.user_id == user_id
            )
            intervention = db_session.execute(query).scalar_one_or_none()

            if intervention:
                intervention.user_feedback = feedback
                intervention.execution_status = 'completed'
                intervention.session_id = session_id
                intervention.updated_at = get_now_naive()
                db_session.commit()
                return True

            return False
        except Exception as e:
            db_session.rollback()
            return False
