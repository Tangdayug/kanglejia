from common.datetime_utils import get_now_naive
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from datetime import datetime

from model.healthTest import HealthTest
from exception.customException import NotFoundException


class HealthTestService:
    """健康测试服务 - 内在能力减退初筛"""

    @staticmethod
    def calculate_scores(data: dict) -> dict:
        scores = {
            'cognitive': 0,
            'motor': 0,
            'vitality': 0,
            'vision': 0,
            'hearing': 0,
            'psychological': 0
        }

        # 认知维度评分 (总分>0=有风险)
        q1_memory_issue = data.get('q1MemoryIssue')
        if q1_memory_issue:  # Q1: 是有记忆问题
            scores['cognitive'] += 1

        # Q1.2-Q1.4 仅当Q1=否时回答并参与评分。
        if q1_memory_issue is False:
            if data.get('q1_2Correct') is False:  # 日期错误
                scores['cognitive'] += 1
            if data.get('q1_3Correct') is False:  # 位置错误
                scores['cognitive'] += 1

            # Q1.4: 回忆三个词 (flower_door_rice是正确答案)
            q1_4_recall = data.get('q1_4Recall', '')
            if q1_4_recall != 'flower_door_rice':  # 不是"花、门、米饭"
                scores['cognitive'] += 1

        # 运动维度评分 (>0=有风险)
        # Q2: 否(不能完成)=1分
        if data.get('q2Completed') is False:
            scores['motor'] = 1

        # 活力维度评分 (>0=有风险, 营养不良风险)
        # Q3: 是(体重下降)=1分
        if data.get('q3WeightLoss'):
            scores['vitality'] += 1
        # Q4: 是(食欲减退)=1分
        if data.get('q4AppetiteLoss'):
            scores['vitality'] += 1

        # 视力维度评分 (>0=有风险)
        # Q5: 是(眼睛问题)=1分
        if data.get('q5VisionIssue'):
            scores['vision'] += 1
        # Q6: 是(糖尿病/高血压)=1分
        if data.get('q6DiabetesHypertension'):
            scores['vision'] += 1

        # 听力维度评分 (>0=有风险)
        # Q7: 是(听不清)=1分
        if data.get('q7HearingIssue'):
            scores['hearing'] = 1

        # 心理维度评分 (>0=有抑郁症状)
        # Q8: 是(情绪低落)=1分
        if data.get('q8Depressed'):
            scores['psychological'] += 1
        # Q9: 是(兴趣减退)=1分
        if data.get('q9InterestLoss'):
            scores['psychological'] += 1

        # 计算总分
        scores['total'] = sum(scores.values())

        return scores

    @staticmethod
    def determine_risks(scores: dict) -> dict:
        return {
            'cognitive': scores.get('cognitive', 0) > 0,
            'motor': scores.get('motor', 0) > 0,
            'vitality': scores.get('vitality', 0) > 0,
            'vision': scores.get('vision', 0) > 0,
            'hearing': scores.get('hearing', 0) > 0,
            'psychological': scores.get('psychological', 0) > 0
        }

    @staticmethod
    def generate_recommendations(scores: dict, risks: dict, data: dict) -> dict:
        recommendations = {
            'cognitive': [],
            'motor': [],
            'vitality': [],
            'vision': [],
            'hearing': [],
            'psychological': [],
            'overall': []
        }

        # 认知维度建议
        if risks.get('cognitive'):
            recommendations['cognitive'].extend([
                '建议进行认知功能详细评估',
                '保持社交活动，多与人交流',
                '进行益智类游戏和活动',
                '保证充足睡眠，维持规律作息'
            ])
            if scores.get('cognitive', 0) >= 3:
                recommendations['cognitive'].append('风险较高，建议尽快就医咨询神经内科')

        # 运动维度建议
        if risks.get('motor'):
            recommendations['motor'].extend([
                '建议进行平衡能力和步态评估',
                '进行适度的肌肉力量训练',
                '注意居家环境防跌倒改造',
                '可考虑使用助行器具'
            ])
            q2_time = data.get('q2TimeSeconds')
            if q2_time is not None and q2_time > 14:
                recommendations['motor'].append('起立测试时间超过14秒，建议咨询康复科医生')

        # 活力维度建议 (营养不良风险)
        if risks.get('vitality'):
            recommendations['vitality'].extend([
                '建议进行营养状况评估',
                '增加优质蛋白质摄入',
                '保证规律三餐，定时定量',
                '适当增加户外活动'
            ])
            if scores.get('vitality', 0) >= 2:
                recommendations['vitality'].append('体重下降和食欲减退较明显，建议咨询营养科或老年科医生')

        # 视力维度建议
        if risks.get('vision'):
            recommendations['vision'].extend([
                '建议到眼科进行全面检查',
                '定期检查眼底、眼压等',
                '如有糖尿病或高血压，注意控制血糖血压',
                '注意阅读光线充足，避免用眼过度'
            ])
            if scores.get('vision', 0) >= 2:
                recommendations['vision'].append('视力风险因素较多，建议尽快就医')

        # 听力维度建议
        if risks.get('hearing'):
            recommendations['hearing'].extend([
                '建议到耳鼻喉科进行听力检查',
                '排除耳部疾病',
                '必要时配戴助听器',
                '交流时注意面对面，语速适中'
            ])

        # 心理维度建议
        if risks.get('psychological'):
            recommendations['psychological'].extend([
                '建议关注心理健康状况',
                '多参加社区活动和社交互动',
                '与家人朋友多交流沟通',
                '培养兴趣爱好，保持积极心态'
            ])
            if scores.get('psychological', 0) >= 2:
                recommendations['psychological'].append('情绪和兴趣问题较明显，建议咨询心理医生或精神科医生')

        # 总体建议
        if scores.get('total', 0) == 0:
            recommendations['overall'].append('您的各项功能状态良好，请继续保持健康的生活方式！')
        else:
            recommendations['overall'].append('建议根据上述具体建议，对有风险的方面进行关注和干预')
            recommendations['overall'].append('定期复查，监测功能状态变化')

        return recommendations

    @staticmethod
    def get_nearby_facilities(location: str = None) -> list:
        facilities = [
            {
                'name': '市人民医院',
                'address': '市中心大街123号',
                'distance': '1.2km',
                'phone': '010-12345678',
                'type': '综合医院'
            },
            {
                'name': '社区卫生服务中心',
                'address': '建设路456号',
                'distance': '0.5km',
                'phone': '010-87654321',
                'type': '社区医院'
            },
            {
                'name': '中医院',
                'address': '健康路789号',
                'distance': '2.1km',
                'phone': '010-11112222',
                'type': '专科医院'
            },
            {
                'name': '康复医院',
                'address': '康复路321号',
                'distance': '3.5km',
                'phone': '010-33334444',
                'type': '专科医院'
            },
            {
                'name': '老年病医院',
                'address': '长寿路654号',
                'distance': '4.2km',
                'phone': '010-55556666',
                'type': '专科医院'
            }
        ]
        return facilities

    @staticmethod
    def save_test(user_id: int, data: dict, db_session: Session) -> HealthTest:
        try:
            test = HealthTest()
            test.user_id = user_id

            test.q1_memory_issue = data.get('q1MemoryIssue')
            test.q1_1_recall_name = data.get('q1_1Remembered')
            test.q1_2_today_date = data.get('q1_2TodayDate')
            test.q1_2_correct = data.get('q1_2Correct')
            test.q1_3_home_address = data.get('q1_3Location')
            test.q1_3_correct = data.get('q1_3Correct')
            test.q1_4_current_location = data.get('q1_4Recall')
            q1_4_recall = data.get('q1_4Recall', '')
            test.q1_4_correct = (q1_4_recall == 'flower_door_rice')
            test.q2_completed = data.get('q2Completed')
            test.q2_time_seconds = data.get('q2TimeSeconds')
            test.q3_fatigued = data.get('q3WeightLoss')
            test.q4_health_poor = data.get('q4AppetiteLoss')
            test.q5_vision_issue = data.get('q5VisionIssue')
            test.q6_reading_issue = data.get('q6DiabetesHypertension')
            test.q7_hearing_issue = data.get('q7HearingIssue')
            test.q8_depressed = data.get('q8Depressed')
            test.q9_anxious = data.get('q9InterestLoss')
            test.assistance_mode = data.get('assistanceMode')

            scores = HealthTestService.calculate_scores(data)
            test.score_cognitive = scores.get('cognitive', 0)
            test.score_motor = scores.get('motor', 0)
            test.score_vitality = scores.get('vitality', 0)
            test.score_vision = scores.get('vision', 0)
            test.score_hearing = scores.get('hearing', 0)
            test.score_psychological = scores.get('psychological', 0)
            test.score_total = scores.get('total', 0)

            risks = HealthTestService.determine_risks(scores)
            test.risk_cognitive = risks.get('cognitive', False)
            test.risk_motor = risks.get('motor', False)
            test.risk_vitality = risks.get('vitality', False)
            test.risk_vision = risks.get('vision', False)
            test.risk_hearing = risks.get('hearing', False)
            test.risk_psychological = risks.get('psychological', False)

            recommendations = HealthTestService.generate_recommendations(scores, risks, data)
            test.recommendations = recommendations

            db_session.add(test)
            db_session.commit()
            db_session.refresh(test)
            return test
        except Exception as e:
            db_session.rollback()
            import traceback
            traceback.print_exc()
            raise e

    @staticmethod
    def get_user_tests(user_id: int, db_session: Session) -> list:
        query = select(HealthTest).where(
            HealthTest.user_id == user_id
        ).order_by(desc(HealthTest.created_at))
        result = db_session.execute(query).scalars().all()
        return list(result)

    @staticmethod
    def get_test_by_id(test_id: int, user_id: int, db_session: Session) -> HealthTest:
        query = select(HealthTest).where(
            HealthTest.id == test_id,
            HealthTest.user_id == user_id
        )
        test = db_session.execute(query).scalar()
        if not test:
            raise NotFoundException("健康测试记录不存在")
        return test
