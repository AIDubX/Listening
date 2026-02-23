from app.config import settings
from app.services.speaker import SpeakerManager
import os
from pathlib import Path
from app.services.tts import TTS
from app.model.api import Params
import numpy as np
import httpx
import io
import asyncio
import tempfile
from loguru import logger

speaker_manager = SpeakerManager()

def i18n(text):
    return text


dict_language = {
    i18n("不用选"): "all_zh",  # 全部按中文识别
    i18n("英文"): "en",  # 全部按英文识别#######不变
}
async def text_to_speech(text: str, spk: str = settings.DEFAULT_VOICE, speed: float = 1.0, language: str = "中文", emotion: str = settings.DEFAULT_EMOTION):
    """
    文本转语音服务
    
    Args:
        text: 要转换的文本
        voice: 使用的音色
        speed: 语速倍率，1.0为正常速度
        pitch: 音调倍率，1.0为正常音调
        emotion: 情感类型
        
    Returns:
        临时文件路径
    """
    tts = TTS()
    params = Params(
        text=text,
        spk=spk,
        speed=speed,
        emotion=emotion
    )
    # logger.debug(f"text_to_speech: {params}")
    
    # 确保TEMP目录存在
    temp_dir = Path('TEMP')
    temp_dir.mkdir(exist_ok=True)
    
    # 获取音频流响应并正确处理async generator
    
    # 在当前目录下创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False, dir=temp_dir) as temp_file:
        
        # 收集async generator的数据
        audio_data = b""
        async for chunk in tts.infer(params):
            audio_data += chunk
    
        temp_file.write(audio_data)
        
        # 返回临时文件路径
        return temp_file.name

def get_available_voices():
    """
    获取所有可用的音色
    
    Returns:
        List[str]: 音色名称列表
    """
    return speaker_manager.get_speaker_names()

def get_voice_emotions(voice):
    """
    获取指定音色支持的情感列表
    
    Args:
        voice: 音色名称
        
    Returns:
        List[str]: 情感名称列表
    """
    emotions = speaker_manager.get_speaker_emotions(voice)
    
    # 如果没有找到情感或情感列表为空，返回默认情感列表
    if not emotions:
        return [settings.DEFAULT_EMOTION]
    
    return emotions

def get_default_emotion_for_voice(voice):
    """
    获取指定音色的默认情感
    
    Args:
        voice: 音色名称
        
    Returns:
        str: 默认情感名称
    """
    emotions = get_voice_emotions(voice)
    if not emotions:
        return settings.DEFAULT_EMOTION
    
    # 如果有"正常"情感，优先使用
    if "正常" in emotions:
        return "正常"
    
    # 否则使用第一个情感
    return emotions[0]

def get_speaker_details(voice):
    """
    获取指定音色的详细信息
    
    Args:
        voice: 音色名称
        
    Returns:
        dict: 音色详细信息
    """
    
    speaker = speaker_manager.get_speaker(voice)
    
    if not speaker:
        return {
            "name": voice,
            "emotions": [],
            "ref_wav_path": None,
            "text": "",
            "text_lang": "",
            "desc": ""
        }
    
    return speaker

def get_reference_audio_path(voice, emotion=None):
    """
    获取指定音色和情感的参考音频路径
    
    Args:
        voice: 音色名称
        emotion: 情感名称，如果为None则使用默认情感
        
    Returns:
        str: 音频文件的绝对路径，如果不存在则返回None
    """

    speaker = speaker_manager.get_speaker(voice)
    
    if not speaker:
        return None
    
    # 如果没有指定情感，使用默认情感或第一个可用情感
    if emotion is None:
        ref_wav_path = speaker.get("ref_wav_path")
    else:
        # 获取指定情感的音频路径
        emotion_data = speaker.get("emotion", {}).get(emotion, {})
        ref_wav_path = emotion_data.get("ref_wav_path")
        
        # 如果指定情感没有音频，使用默认音频
        if not ref_wav_path:
            ref_wav_path = speaker.get("ref_wav_path")
    
    # 如果路径是相对路径，转换为绝对路径
    if ref_wav_path and not os.path.isabs(ref_wav_path):
        ref_wav_path = os.path.join(settings.SPEAKER_PATH, ref_wav_path)
    
    # 检查文件是否存在
    if ref_wav_path and os.path.exists(ref_wav_path):
        return ref_wav_path
    
    return None

def get_reference_text(voice, emotion=None):
    """
    获取指定音色和情感的参考文本
    
    Args:
        voice: 音色名称
        emotion: 情感名称，如果为None则使用默认情感
        
    Returns:
        str: 参考文本
    """
    
    speaker = speaker_manager.get_speaker(voice)
    
    if not speaker:
        return ""
    
    # 如果没有指定情感，使用默认文本
    if emotion is None:
        return speaker.get("text", "")
    
    # 获取指定情感的文本
    emotion_data = speaker.get("emotion", {}).get(emotion, {})
    text = emotion_data.get("text")
    
    # 如果指定情感没有文本，使用默认文本
    if not text:
        text = speaker.get("text", "")
    
    return text

def refresh_speakers():
    """
    刷新音色列表
    
    Returns:
        List[str]: 更新后的音色名称列表
    """
    speaker_manager.refresh()
    return speaker_manager.get_speaker_names()