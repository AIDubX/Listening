from indextts.infer_vllm_v2 import IndexTTS2,QwenEmotion
from app.utils.pack_audio import pack_ogg,speed_change,pack_wav,read_clean_buffer
from loguru import logger
from io import BytesIO
import gc
from pathlib import Path
import torch
import asyncio
import traceback

class TTS(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        if not hasattr(self, "tts"):
            self.tts = IndexTTS2(
                model_dir=Path("checkpoints/IndexTTS-2-vLLM").as_posix(),
                is_fp16=True,
                gpu_memory_utilization=0.1)


async def get_tts_wav(text, ref_audio, vec=None,stream=False,format="ogg",speed=1.0):
    # logger.debug(f"text: {text}, ref_audio: {ref_audio}, vec: {vec}, stream: {stream}, format: {format}, speed: {speed}")
    try:
        (sampling_rate, wav_data) = await TTS().tts.infer(
                spk_audio_prompt=ref_audio,
                text=text,
                output_path=None,
                emo_vector=vec,
                verbose=False,
                interval_silence=0,
            )
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"TTS推理失败: {e}")
        yield b''
        return
    if format is None:
        yield (sampling_rate, wav_data)
    else:
        if speed != 1.0:
            wav_data = speed_change(wav_data,speed,sampling_rate)
        audio_bytes = BytesIO()
        if format == "ogg":
            audio_bytes = pack_ogg(audio_bytes,wav_data,sampling_rate)
        elif format == "wav":
            audio_bytes = pack_wav(audio_bytes,wav_data,sampling_rate)
        # audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
        yield (sampling_rate, audio_bytes.getvalue())

async def get_tts_wav2(text, ref_audio, vec=None,stream=False,format="ogg",speed=1.0):
    # logger.debug(f"text: {text}, ref_audio: {ref_audio}, vec: {vec}, stream: {stream}, format: {format}, speed: {speed}")
    try:
        (sampling_rate, wav_data) = await TTS().tts.infer(
                spk_audio_prompt=ref_audio,
                text=text,
                output_path=None,
                emo_vector=vec,
                verbose=False,
                interval_silence=0,
                # verbose=True,
            )
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"TTS推理失败: {e}")
        yield b''
        return
    if format is None:
        yield (sampling_rate, wav_data)
    else:
        if speed != 1.0:
            wav_data = speed_change(wav_data,speed,sampling_rate)
        audio_bytes = BytesIO()
        if format == "ogg":
            audio_bytes = pack_ogg(audio_bytes,wav_data,sampling_rate)
        elif format == "wav":
            audio_bytes = pack_wav(audio_bytes,wav_data,sampling_rate)
        # audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
        yield (sampling_rate, audio_bytes.getvalue())
    
