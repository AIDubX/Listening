from pydantic import BaseModel
from fastapi import Query
from typing import Union, Optional
from enum import Enum
from app.config import settings

class ImportLegadoTTSRequest(BaseModel):
    id: str = Query("default", description="要使用的作品ID")

class ReaderRequest(BaseModel):
    text: str = Query("", description="text内容")
    id: str = Query("", description="要使用的作品ID")
    narration: bool = Query(True, description="启用旁白，默认为启用")
    dialogue: bool = Query(True, description="启用对话，默认为启用")
    stream: bool = Query(False, description="是否启用流式返回")

class SplitMethod(str, Enum):
    # cut0 = "不切"
    # cut1 = "凑4句一切"
    # cut2 = "凑50字一切"
    # cut3 = "中文句号。切"
    # cut4 = "英文句号.切"
    # cut5 = "按标点符号切"
    cut0 = "cut0"
    cut1 = "cut1"
    cut2 = "cut2"
    cut3 = "cut3"
    cut4 = "cut4"
    cut5 = "cut5"


class TextLang(str, Enum):
    all_zh = "all_zh"
    en = "en"
    all_ja = "all_ja"
    zh = "zh"
    ja = "ja"
    all_yue = "all_yue"
    yue = "yue"
    ko = "ko"
    all_ko = "all_ko"
    auto = "auto"

class AudioFormat(str, Enum):
    WAV = "wav"
    OGG = "ogg"
    AAC = "aac"
    MP3 = "mp3"


class Params(BaseModel):
    text: Union[str, None] = Query(None, description="文本内容", title="文本内容")
    spk: Union[str, None] = Query(
        None, description="发音人,不设置走默认的。", title="发音人"
    )
    emotion: Union[str, None] = Query(
        None, description="情感,不设置走默认的", title="情感"
    )
    role: Optional[str] = Query(
        "", description="角色,不设置走默认的", title="角色"
    )
    # engine: Optional[str] = Query("GPT-SoVITS", description="引擎名，默认是GPT-SoVITS", title="引擎")
    speed: float = Query(1.0, description="语速", title="语速")
    format: AudioFormat = Query(
        AudioFormat.WAV, description="输出文件格式", title="输出音频格式"
    )
    text_lang: TextLang = Query(TextLang.zh, description="文本语言", title="文本语言")
    split_bucket: bool = Query(settings.split_bucket, description="是否启用分桶")
    batch_size: int = Query(settings.batch_size, description="分桶大小")
    batch_threshold: float = Query(settings.batch_threshold, description="分桶阈值")
    text_split_method: SplitMethod = Query(
        settings.text_split_method,
        description="文本切割方式.cut0(不切),cut1(凑4句一切),cut2(凑50字一切),cut3(中文句号。切),cut4(英文句号.切),cut5(按标点符号切)",
    )
    temperature: float = Query(settings.temperature, description="temperature")
    top_k: int = Query(settings.top_k, description="top_k")
    top_p: float = Query(settings.top_p, description="top_p")
    ref_wav_path: Union[str, None] = Query(
        None, description="参考音频路径,优先使用参数的"
    )

    prompt_text: Union[str, None] = Query(None, description="参考文本，优先使用参数的")
    prompt_language: Union[str, None] = Query(
        None, description="参考语言，优先使用参数的"
    )
    return_fragment: bool = Query(False, description="分段返回，默认不启用")
    fragment_interval: float = Query(settings.fragment_interval, description="分段时间间隔")
    seed: int = Query(-1, description="随机种子，-1为不固定")
    stream: bool = Query(False, description="是否为流式语音")
    parallel_infer: bool = Query(settings.parallel_infer, description="是否启用并行推理")
    repetition_penalty: float = Query(settings.repetition_penalty, description="重复惩罚")
    pitch: float = Query(1.0, description="音高")
    volume: float = Query(1.0, description="音量")
    duration: Union[float, None] = Query(None, description="固定时长")
    instruct_text: Union[str, None] = Query(None, description="指令文本,仅CosyVoice有效")
    # sr: bool = Query(False, description="是否语音增强。")