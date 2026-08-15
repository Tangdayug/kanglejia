"""基于 Microsoft Edge TTS 的语音合成服务"""
import io
import asyncio
from typing import Optional

_edge_tts_module = None

def _get_edge_tts():
    global _edge_tts_module
    if _edge_tts_module is None:
        try:
            import edge_tts
            _edge_tts_module = edge_tts
        except ImportError:
            _edge_tts_module = False
    return _edge_tts_module if _edge_tts_module is not False else None


class EdgeTTSService:
    """语音合成服务类"""

    WARM_VOICES = {
        'xiaoxiao': 'zh-CN-XiaoxiaoNeural',
        'xiaoyi': 'zh-CN-XiaoyiNeural',
        'yunjian': 'zh-CN-YunjianNeural',
        'xiaochen': 'zh-CN-XiaochenNeural',
    }

    DEFAULT_VOICE = 'xiaoxiao'

    @staticmethod
    def is_available() -> bool:
        edge_tts = _get_edge_tts()
        return edge_tts is not None

    @staticmethod
    async def synthesize_async(
        text: str,
        voice: str = None,
        rate: str = '+0%',
        pitch: str = '+0Hz',
        volume: str = '+0%'
    ) -> Optional[bytes]:
        edge_tts = _get_edge_tts()

        if edge_tts is None:
            return None

        if voice is None or voice not in EdgeTTSService.WARM_VOICES:
            voice = EdgeTTSService.DEFAULT_VOICE

        voice_id = EdgeTTSService.WARM_VOICES[voice]

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            audio_buffer = io.BytesIO()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

            audio_data = audio_buffer.getvalue()
            return audio_data

        except Exception as e:
            return None

    @staticmethod
    def synthesize(
        text: str,
        voice: str = None,
        rate: str = '+0%',
        pitch: str = '+0Hz',
        volume: str = '+0%'
    ) -> Optional[bytes]:
        if not EdgeTTSService.is_available():
            return None

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        EdgeTTSService.synthesize_async(text, voice, rate, pitch, volume)
                    )
                    return future.result()
            else:
                return asyncio.run(EdgeTTSService.synthesize_async(text, voice, rate, pitch, volume))
        except Exception as e:
            return None

    @staticmethod
    def get_available_voices() -> dict:
        return {
            'xiaoxiao': {
                'id': 'zh-CN-XiaoxiaoNeural',
                'name': '晓筱',
                'description': '温柔女声，适合日常关怀',
                'gender': 'female',
                'style': 'warm'
            },
            'xiaoyi': {
                'id': 'zh-CN-XiaoyiNeural',
                'name': '晓伊',
                'description': '温暖女声，亲切自然',
                'gender': 'female',
                'style': 'warm'
            },
            'yunjian': {
                'id': 'zh-CN-YunjianNeural',
                'name': '云健',
                'description': '温暖男声，稳重可靠',
                'gender': 'male',
                'style': 'calm'
            },
            'xiaochen': {
                'id': 'zh-CN-XiaochenNeural',
                'name': '晓辰',
                'description': '友好女声，活泼亲切',
                'gender': 'female',
                'style': 'friendly'
            }
        }

    @staticmethod
    def get_recommended_voice(user_gender: str = None) -> str:
        if user_gender == 'male':
            return 'xiaoxiao'
        elif user_gender == 'female':
            return 'xiaoyi'
        else:
            return 'xiaoxiao'


_tts_service: Optional[EdgeTTSService] = None


def get_edge_tts_service() -> EdgeTTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = EdgeTTSService()
    return _tts_service
