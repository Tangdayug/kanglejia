from common.datetime_utils import get_now_naive
"""AI 聊天服务"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Iterator
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from model.chatHistory import ChatSession, ChatMessage
from model.interventionLog import InterventionLog
from model.healthRecord import HealthRecord
from model.healthTest import HealthTest
from common.deepseek_client import get_deepseek_client
from common.constant import CHAT_MAX_HISTORY_ROUNDS
from rag.retriever_faiss import get_rag_retriever


class ChatService:
    """AI 聊天服务类"""

    FALLBACK_RECOMMENDATIONS = [
        "如何改善睡眠质量？",
        "老年人适合哪些运动？",
        "怎样保持健康饮食？",
        "如何预防跌倒？",
        "高血压患者需要注意什么？",
    ]

    @staticmethod
    def create_session(user_id: int, title: str = None, db_session: Session = None) -> ChatSession:
        session = ChatSession()
        session.user_id = user_id
        session.title = title or "新对话"

        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        return session

    @staticmethod
    def get_user_sessions(user_id: int, db_session: Session) -> List[ChatSession]:
        # 只返回有实际对话内容的会话，过滤掉未发送任何消息的空白会话
        has_messages = select(ChatMessage).where(
            ChatMessage.session_id == ChatSession.id
        ).exists()
        query = select(ChatSession).where(
            ChatSession.user_id == user_id,
            has_messages
        ).order_by(desc(ChatSession.updated_at))
        result = db_session.execute(query).scalars().all()
        return list(result)

    @staticmethod
    def get_session_messages(session_id: int, user_id: int, db_session: Session) -> List[ChatMessage]:
        session_query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        session = db_session.execute(session_query).scalar_one_or_none()

        if not session:
            raise ValueError("Session not found or access denied")

        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at)
        result = db_session.execute(query).scalars().all()
        return list(result)

    @staticmethod
    def get_user_health_context(user_id: int, db_session: Session) -> Dict[str, Any]:
        context = {
            'healthRecord': None,
            'healthTest': None
        }

        # Get latest health record (any non-empty record)
        record_query = select(HealthRecord).where(
            HealthRecord.user_id == user_id
        ).order_by(desc(HealthRecord.updated_at)).limit(1)
        record = db_session.execute(record_query).scalar_one_or_none()

        # Use the record if it exists (even partially filled)
        if record:
            # Collect all available basic info
            basic_info = {}
            if record.name:
                basic_info['name'] = record.name
            if record.birth_date:
                basic_info['birthDate'] = record.birth_date
                basic_info['age'] = ChatService._calculate_age(record.birth_date)
            if record.gender:
                basic_info['gender'] = record.gender
            if record.height:
                basic_info['height'] = record.height
            if record.weight:
                basic_info['weight'] = record.weight
            if record.bmi:
                basic_info['bmi'] = record.bmi
            if record.waist:
                basic_info['waist'] = record.waist
            if record.abdomen:
                basic_info['abdomen'] = record.abdomen
            if record.systolic_bp:
                basic_info['systolic_bp'] = record.systolic_bp
            if record.diastolic_bp:
                basic_info['diastolic_bp'] = record.diastolic_bp
            if record.heart_rate:
                basic_info['heart_rate'] = record.heart_rate

            # Collect sleep information
            sleep_info = []
            if record.sleep_good:
                sleep_info.append('睡眠良好')
            if record.sleep_difficulty_falling:
                sleep_info.append('入睡困难')
            if record.sleep_easily_wake:
                sleep_info.append('易醒')
            if record.sleep_early_wake:
                sleep_info.append('早醒')
            if record.sleep_daytime_sleepiness:
                sleep_info.append('白天犯困')
            if record.sleep_other and record.sleep_other_desc:
                sleep_info.append(f'其他: {record.sleep_other_desc}')

            # Collect diseases
            diseases = ChatService._get_diseases_list(record)

            # Collect medication info
            medication_info = None
            if record.is_medication and record.medication_names:
                medication_info = record.medication_names

            # Collect lifestyle habits
            lifestyle = {}
            if record.smoking_status:
                lifestyle['smoking'] = {
                    'status': record.smoking_status,
                    'count': record.smoking_count if record.smoking_count else None
                }
            if record.drinking_status:
                lifestyle['drinking'] = {
                    'status': record.drinking_status,
                    'frequency': record.drinking_frequency if record.drinking_frequency else None,
                    'amount': record.drinking_amount if record.drinking_amount else None
                }

            # Collect exercise preferences
            exercise_prefs = []
            exercise_map = {
                'exercise_walking': '散步/健走',
                'exercise_jogging': '慢跑',
                'exercise_square_dance': '广场舞',
                'exercise_tai_chi': '太极拳/八段锦',
                'exercise_swimming': '游泳',
                'exercise_cycling': '骑车',
                'exercise_racket': '乒乓球/羽毛球',
                'exercise_hiking': '爬山/爬楼梯',
                'exercise_gardening': '园艺',
                'exercise_fishing': '钓鱼',
                'exercise_gym': '健身房器械',
                'exercise_yoga': '瑜伽/普拉提'
            }
            for field, name in exercise_map.items():
                if getattr(record, field):
                    exercise_prefs.append(name)
            if record.exercise_other and record.exercise_other_desc:
                exercise_prefs.append(f'其他: {record.exercise_other_desc}')
            if record.exercise_no_preference:
                exercise_prefs.append('无运动偏好')

            # Collect social support
            social_support = []
            support_map = {
                'support_equipment': '场地/器材支持',
                'support_organization': '组织/人群支持',
                'support_info': '信息/指导支持',
                'support_policy': '政策/费用支持'
            }
            for field, name in support_map.items():
                if getattr(record, field):
                    social_support.append(name)
            if record.support_other:
                social_support.append(f'其他: {record.support_other}')
            if record.support_none:
                social_support.append('无支持')

            # Collect demographic info
            demographic = {}
            if record.marital_status:
                demographic['marital_status'] = record.marital_status
            if record.work_status:
                demographic['work_status'] = record.work_status
            if record.education:
                demographic['education'] = record.education
            if record.residence_type:
                demographic['residence_type'] = record.residence_type
            if record.co_residents:
                demographic['co_residents'] = record.co_residents

            # Only add healthRecord if we have at least some data
            if basic_info or diseases or sleep_info or lifestyle or exercise_prefs:
                record_data = {
                    'basicInfo': basic_info,
                    'chronicDisease': {
                        'diseases': diseases
                    }
                }

                if sleep_info:
                    record_data['sleep'] = sleep_info
                if medication_info:
                    record_data['medication'] = medication_info
                if lifestyle:
                    record_data['lifestyle'] = lifestyle
                if exercise_prefs:
                    record_data['exercise'] = exercise_prefs
                if social_support:
                    record_data['socialSupport'] = social_support
                if demographic:
                    record_data['demographic'] = demographic

                context['healthRecord'] = record_data

        # Get latest health test
        test_query = select(HealthTest).where(
            HealthTest.user_id == user_id
        ).order_by(desc(HealthTest.created_at)).limit(1)
        test = db_session.execute(test_query).scalar_one_or_none()

        if test:
            # Calculate risk level based on risk fields
            risk_count = sum([
                test.risk_cognitive, test.risk_motor, test.risk_vitality,
                test.risk_vision, test.risk_hearing, test.risk_psychological
            ])
            if risk_count >= 3:
                risk_level = 'high'
            elif risk_count >= 1:
                risk_level = 'medium'
            else:
                risk_level = 'low'

            context['healthTest'] = {
                'overallScore': test.score_total,
                'riskLevel': risk_level,
                'dimensions': {
                    'cognitive': test.score_cognitive,
                    'motor': test.score_motor,
                    'vitality': test.score_vitality,
                    'vision': test.score_vision,
                    'hearing': test.score_hearing,
                    'psychological': test.score_psychological,
                }
            }

        return context

    @staticmethod
    def _calculate_age(birth_date: str) -> int:
        try:
            from datetime import datetime
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            today = get_now_naive()
            age = today.year - birth.year
            if (today.month, today.day) < (birth.month, birth.day):
                age -= 1
            return age
        except:
            return None

    @staticmethod
    def _get_diseases_list(record: HealthRecord) -> List[str]:
        diseases = []
        disease_fields = [
            ('disease_hypertension', 'hypertension'),
            ('disease_diabetes', 'diabetes'),
            ('disease_dyslipidemia', 'dyslipidemia'),
            ('disease_coronary', 'coronary_heart_disease'),
            ('disease_stroke', 'stroke'),
            ('disease_copd', 'copd'),
            ('disease_gout', 'gout'),
            ('disease_osteoporosis', 'osteoporosis'),
            ('disease_parkinsons', 'parkinsons'),
            ('disease_alzheimers', 'alzheimers'),
        ]

        for field, code in disease_fields:
            if getattr(record, field):
                diseases.append(code)

        return diseases

    @staticmethod
    def save_message(
        session_id: int,
        role: str,
        content: str,
        sources: Dict[str, Any] = None,
        db_session: Session = None
    ) -> ChatMessage:
        message = ChatMessage()
        message.session_id = session_id
        message.role = role
        message.content = content
        message.sources = sources

        # 防御纵深：从聊天会话继承用户ID，确保消息按账号隔离
        session = db_session.get(ChatSession, session_id)
        if session:
            message.user_id = session.user_id
            session.updated_at = get_now_naive()

        db_session.add(message)

        db_session.commit()
        db_session.refresh(message)

        return message

    @staticmethod
    def generate_chat_response(
        user_id: int,
        session_id: int,
        user_message: str,
        db_session: Session,
        subject_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成聊天回复。

        Args:
            user_id: 当前会话所属用户ID（用于鉴权和聊天记录归属）
            session_id: 聊天会话ID
            user_message: 用户消息
            db_session: 数据库会话
            subject_user_id: 健康上下文所属用户ID；当 A 描述 B 时，传入 B 的 user_id，
                            使系统基于 B 的健康档案回答，而聊天记录仍归属 A。
        """
        ChatService.save_message(session_id, 'user', user_message, db_session=db_session)

        messages = ChatService.get_session_messages(session_id, user_id, db_session)
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in messages[-CHAT_MAX_HISTORY_ROUNDS:]
        ]

        # 健康上下文优先使用 subject_user_id（被描述对象），否则回退到说话人
        health_context_user_id = subject_user_id if subject_user_id is not None else user_id
        health_context = ChatService.get_user_health_context(health_context_user_id, db_session)

        retriever = get_rag_retriever()
        retrieval_results = retriever.retrieve(
            query=user_message,
            user_profile=health_context.get('healthRecord'),
            health_record=health_context.get('healthRecord'),
            health_test=health_context.get('healthTest'),
            n_results=3
        )

        system_prompt = ChatService._build_system_prompt(
            health_context, retrieval_results
        )

        client = get_deepseek_client()
        response = client.generate_chat_response(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history[:-1],
            temperature=0.7
        )

        sources = None
        if retrieval_results:
            avg_relevance = sum(r.relevance_score for r in retrieval_results) / len(retrieval_results)
            # 修复后 relevance_score ∈ [0, 1]，阈值设为 0.3 更合理
            has_relevant_results = any(r.relevance_score > 0.3 for r in retrieval_results)

            if has_relevant_results and avg_relevance > 0.3:
                sources = {
                    'type': 'knowledge_base',
                    'sources': [
                        {
                            'source': r.source,
                            'filename': r.metadata.get('filename', '未知')
                        }
                        for r in retrieval_results if r.relevance_score > 0.5
                    ]
                }

        ChatService.save_message(
            session_id, 'assistant', response, sources=sources, db_session=db_session
        )

        return {
            'response': response,
            'sources': sources
        }

    @staticmethod
    def stream_chat_response(
        user_id: int,
        session_id: int,
        user_message: str,
        db_session: Session
    ) -> Iterator[str]:
        ChatService.save_message(session_id, 'user', user_message, db_session=db_session)

        messages = ChatService.get_session_messages(session_id, user_id, db_session)
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in messages[-CHAT_MAX_HISTORY_ROUNDS:]
        ]

        health_context = ChatService.get_user_health_context(user_id, db_session)

        retriever = get_rag_retriever()
        retrieval_results = retriever.retrieve(
            query=user_message,
            user_profile=health_context.get('healthRecord'),
            health_record=health_context.get('healthRecord'),
            health_test=health_context.get('healthTest'),
            n_results=3
        )

        system_prompt = ChatService._build_system_prompt(
            health_context, retrieval_results
        )

        client = get_deepseek_client()
        full_response = ""

        messages_for_api = [{"role": "system", "content": system_prompt}]

        if len(conversation_history) > 1:
            messages_for_api.extend(conversation_history[:-1])

        messages_for_api.append({"role": "user", "content": user_message})

        try:
            for chunk in client.stream_chat_completion(
                messages=messages_for_api,
                temperature=0.7
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            yield "抱歉，我遇到了一些问题，请稍后再试。"
            return

        sources = None
        if retrieval_results:
            avg_relevance = sum(r.relevance_score for r in retrieval_results) / len(retrieval_results)
            # 修复后 relevance_score ∈ [0, 1]，阈值设为 0.3 更合理
            has_relevant_results = any(r.relevance_score > 0.3 for r in retrieval_results)

            if has_relevant_results and avg_relevance > 0.3:
                sources = {
                    'type': 'knowledge_base',
                    'sources': [
                        {
                            'source': r.source,
                            'filename': r.metadata.get('filename', '未知')
                        }
                        for r in retrieval_results if r.relevance_score > 0.5
                    ]
                }

        ChatService.save_message(
            session_id, 'assistant', full_response, sources=sources, db_session=db_session
        )

    @staticmethod
    def _build_system_prompt(
        health_context: Dict[str, Any],
        retrieval_results: List
    ) -> str:

        prompt = """你是一个专业、友善的老年人健康咨询助手。你的职责是为老年人提供健康建议和指导。

# 回答原则
1. 使用简洁、清晰、易懂的语言
2. 对老年人保持耐心和尊重
3. 基于循证医学知识提供建议
4. 对于紧急或严重症状，建议及时就医
5. 不要提供确定的诊断，始终建议咨询专业医生
6. **重要**：如果系统提供了用户的基本信息（年龄、性别、慢性病等），请在回答时直接使用这些信息
7. 如果某些信息未提供，不要特意提及，只基于已知信息回答
"""

        # Add health context (only add the section if we have some data)
        if health_context.get('healthRecord'):
            basic_info = health_context['healthRecord'].get('basicInfo', {})
            diseases = health_context['healthRecord'].get('chronicDisease', {}).get('diseases', [])

            # Only add the section if we have at least some info
            if basic_info or diseases:
                prompt += "\n# 用户基本信息\n"

                if basic_info.get('name'):
                    prompt += f"- 姓名: {basic_info['name']}\n"
                if basic_info.get('age'):
                    prompt += f"- 年龄: {basic_info['age']}岁\n"
                if basic_info.get('gender'):
                    prompt += f"- 性别: {basic_info['gender']}\n"
                if basic_info.get('height'):
                    prompt += f"- 身高: {basic_info['height']}cm\n"
                if basic_info.get('weight'):
                    prompt += f"- 体重: {basic_info['weight']}kg\n"
                if basic_info.get('bmi'):
                    prompt += f"- BMI: {basic_info['bmi']}\n"
                if basic_info.get('waist'):
                    prompt += f"- 腰围: {basic_info['waist']}cm\n"
                if basic_info.get('abdomen'):
                    prompt += f"- 腹围: {basic_info['abdomen']}cm\n"
                if basic_info.get('systolic_bp') and basic_info.get('diastolic_bp'):
                    prompt += f"- 血压: {basic_info['systolic_bp']}/{basic_info['diastolic_bp']} mmHg\n"
                if basic_info.get('heart_rate'):
                    prompt += f"- 静息心率: {basic_info['heart_rate']} 次/分\n"

                if diseases:
                    prompt += f"- 患有疾病: {', '.join(diseases)}\n"

                sleep_info = health_context['healthRecord'].get('sleep')
                if sleep_info:
                    prompt += f"- 睡眠状况: {', '.join(sleep_info)}\n"

                medication = health_context['healthRecord'].get('medication')
                if medication:
                    prompt += f"- 用药情况: {medication}\n"

                lifestyle = health_context['healthRecord'].get('lifestyle', {})
                if lifestyle:
                    prompt += "- 生活习惯:\n"
                    if lifestyle.get('smoking'):
                        smoking = lifestyle['smoking']
                        prompt += f"  - 吸烟: {smoking['status']}"
                        if smoking.get('count'):
                            prompt += f" ({smoking['count']}支/天)"
                        prompt += "\n"
                    if lifestyle.get('drinking'):
                        drinking = lifestyle['drinking']
                        prompt += f"  - 饮酒: {drinking['status']}"
                        if drinking.get('frequency'):
                            prompt += f" ({drinking['frequency']}次/周)"
                        if drinking.get('amount'):
                            prompt += f" ({drinking['amount']}两/次)"
                        prompt += "\n"

                exercise = health_context['healthRecord'].get('exercise')
                if exercise:
                    prompt += f"- 运动偏好: {', '.join(exercise)}\n"

                social_support = health_context['healthRecord'].get('socialSupport')
                if social_support:
                    prompt += f"- 社会支持: {', '.join(social_support)}\n"

                demographic = health_context['healthRecord'].get('demographic', {})
                if demographic:
                    prompt += "- 社会信息:\n"
                    if demographic.get('marital_status'):
                        prompt += f"  - 婚姻状况: {demographic['marital_status']}\n"
                    if demographic.get('work_status'):
                        prompt += f"  - 工作状态: {demographic['work_status']}\n"
                    if demographic.get('education'):
                        prompt += f"  - 教育程度: {demographic['education']}\n"
                    if demographic.get('residence_type'):
                        prompt += f"  - 居住地类型: {demographic['residence_type']}\n"
                    if demographic.get('co_residents'):
                        prompt += f"  - 共同居住者: {demographic['co_residents']}\n"

        if health_context.get('healthTest'):
            test = health_context['healthTest']
            prompt += f"\n# 最近健康测试\n"
            prompt += f"- 综合得分: {test.get('overallScore', 'N/A')}\n"
            prompt += f"- 风险等级: {test.get('riskLevel', 'N/A')}\n"

        if retrieval_results:
            avg_relevance = sum(r.relevance_score for r in retrieval_results) / len(retrieval_results)

            if avg_relevance > 0.5:
                retriever = get_rag_retriever()
                formatted_context = retriever.format_context_for_llm(retrieval_results)

                prompt += "\n# 相关知识库内容\n"
                prompt += formatted_context
                prompt += "\n请优先参考上述知识库内容回答问题。\n"
                prompt += "\n# 来源标注\n"
                prompt += "如果你的回答主要基于上述知识库内容，请在回答末尾标注：📚 来源：[文件名]\n"

        return prompt

    @staticmethod
    def generate_recommendations(
        user_id: int,
        session_id: int,
        db_session: Session
    ) -> List[str]:
        try:
            health_context = ChatService.get_user_health_context(user_id, db_session)

            messages = ChatService.get_session_messages(session_id, user_id, db_session)
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in messages[-CHAT_MAX_HISTORY_ROUNDS:]
            ]

            user_profile = {}
            if health_context.get('healthRecord'):
                user_profile.update(health_context['healthRecord'])
            if health_context.get('healthTest'):
                user_profile.update(health_context['healthTest'])

            client = get_deepseek_client()
            recommendations = client.generate_recommendations(
                user_profile=user_profile,
                conversation_history=conversation_history,
                count=3
            )

            return recommendations if recommendations else ChatService.FALLBACK_RECOMMENDATIONS[:3]

        except Exception as e:
            return ChatService.FALLBACK_RECOMMENDATIONS[:3]

    @staticmethod
    def check_user_readiness(user_id: int, db_session: Session) -> Dict[str, bool]:
        record_query = select(HealthRecord).where(
            HealthRecord.user_id == user_id
        ).order_by(desc(HealthRecord.updated_at)).limit(1)
        record = db_session.execute(record_query).scalar_one_or_none()

        has_health_record = record is not None

        test_query = select(HealthTest).where(
            HealthTest.user_id == user_id
        )
        has_health_test = db_session.execute(test_query).first() is not None

        return {
            'hasHealthRecord': has_health_record,
            'hasHealthTest': has_health_test,
            'isReady': has_health_record and has_health_test
        }

    @staticmethod
    def extract_and_save_intervention(
        user_id: int,
        session_id: int,
        user_message: str,
        assistant_response: str,
        db_session: Session
    ) -> Optional[InterventionLog]:
        try:
            extraction_prompt = f"""分析以下健康咨询对话，判断是否需要为用户记录健康干预建议。

用户问题：{user_message}

AI回复：{assistant_response[:500]}

请分析并判断：
1. AI是否给出了具体的、可执行的健康建议或干预措施？
2. 这些建议是否需要用户在日常生活中长期执行？（如运动、饮食、睡眠习惯等）

如果需要记录干预，请按以下JSON格式输出：
{{
    "needs_intervention": true,
    "problem": "简要描述用户的问题或健康关注点（30字以内）",
    "suggestion": "具体的干预建议内容（100字以内）"
}}

如果不需要记录（例如：只是一般性问答、紧急就医建议、一次性建议等），请输出：
{{
    "needs_intervention": false,
    "reason": "原因说明"
}}

请直接输出JSON，不要包含其他解释文字。
"""

            client = get_deepseek_client()
            response = client.generate_chat_response(
                system_prompt="你是一个健康咨询分析专家，擅长从对话中识别需要长期跟踪的健康干预建议。",
                user_message=extraction_prompt,
                temperature=0.3
            )

            import json
            import re

            json_match = re.search(r'\{[^}]*\}', response, re.DOTALL)
            if not json_match:
                return None

            json_str = json_match.group(0)
            result = json.loads(json_str)

            if not result.get('needs_intervention', False):
                return None

            problem = result.get('problem', '').strip()
            suggestion = result.get('suggestion', '').strip()

            if not suggestion:
                return None

            intervention = InterventionLog()
            intervention.user_id = user_id
            intervention.session_id = session_id
            intervention.intervention_suggestion = suggestion
            intervention.execution_status = 'pending'
            intervention.created_at = get_now_naive()
            intervention.updated_at = get_now_naive()

            db_session.add(intervention)
            db_session.commit()
            db_session.refresh(intervention)

            return intervention

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_user_interventions(
        user_id: int,
        db_session: Session,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[InterventionLog]:
        query = select(InterventionLog).where(
            InterventionLog.user_id == user_id
        )

        if status:
            query = query.where(InterventionLog.execution_status == status)

        query = query.order_by(desc(InterventionLog.created_at)).limit(limit)

        return list(db_session.execute(query).scalars().all())

    @staticmethod
    def analyze_health_history(history: List[Dict[str, Any]]) -> str:
        """分析健康历史记录"""
        if not history:
            return "暂无健康历史记录可供分析。"

        # 构建分析提示
        history_text = "\n".join([
            f"日期: {h['date']} | 总分: {h['totalScore']} | 风险等级: {h['riskLevel']} | "
            f"认知: {h['cognitive']} | 运动: {h['motor']} | 活力: {h['vitality']}"
            for h in history
        ])

        prompt = f"""请分析以下健康历史记录数据，提供专业的健康趋势分析和建议：

健康历史记录：
{history_text}

请提供以下分析：
1. 健康趋势分析（分数变化、风险等级变化）
2. 各维度的变化趋势（认知、运动、活力）
3. 主要健康风险点和改善建议
4. 后续健康管理的重点建议

请用简洁、专业的语言进行分析，使用markdown格式。"""

        client = get_deepseek_client()
        analysis = client.generate_chat_response(
            system_prompt="你是一个专业的健康分析师，擅长分析健康数据趋势并提供专业的健康建议。",
            user_message=prompt,
            temperature=0.7
        )

        return analysis
