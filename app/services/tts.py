import torch
import logging
from app.services.speaker import SpeakerManager
from app.model.api import Params
from app.utils.text_split import text_split_registry
import numpy as np
import io
import wave
from tqdm import tqdm
# todo: 增加调试模式，允许自定义加载
from .indextts_vllm import get_tts_wav,QwenEmotion

from app.services.listening import Listening
from pathlib import Path
import os
from loguru import logger

import random
def set_seed(seed):
    if seed == -1:
        seed = random.randint(0, 1000000)
    seed = int(seed)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)

class TTS:
    _instance = None
    _engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
         
        return cls._instance
    
    def __init__(self):
        ...

    async def infer(self, params: Params):
        """Perform TTS inference and save the generated audio."""
        speaker_manager = SpeakerManager()
        speaker = speaker_manager.get_speaker(params.spk)

        if params.ref_wav_path is not None:
            ref_wav_path = params.ref_wav_path
            ref_text = params.prompt_text
        elif params.emotion in speaker.get("emotion"):
            ref_wav_path = speaker.get("emotion", {}).get(params.emotion, {}).get("ref_wav_path")
            ref_text = speaker.get("emotion", {}).get(params.emotion, {}).get("text")
        else:
            ref_wav_path = speaker.get("ref_wav_path")
            ref_text = speaker.get("text")
        
        if params.seed != -1:
            set_seed(params.seed)
        else:
            set_seed(os.getenv("SEED",-1))
        async for (sampling_rate, wav_data) in get_tts_wav(params.text,ref_wav_path,
                                stream=params.stream,format=params.format.value,speed=params.speed):
            yield wav_data

    async def listening(self, params: Params):
        listening = Listening() 
        speaker_manager = SpeakerManager()
        for tts_params,role in listening.text_to_params(params.text, params.id):
            # logger.debug(tts_params)
            speaker = speaker_manager.get_speaker(tts_params.spk)
            # logger.debug(speaker)
            if role == "旁白" and not params.narration:
                continue
            elif role != "旁白" and not params.dialogue:
                continue
    
            if tts_params.ref_wav_path is not None:
                ref_wav_path = tts_params.ref_wav_path
                ref_text = tts_params.prompt_text
            elif tts_params.emotion in speaker.get("emotion"):
                ref_wav_path = speaker.get("emotion", {}).get(tts_params.emotion, {}).get("ref_wav_path")
                ref_text = speaker.get("emotion", {}).get(tts_params.emotion, {}).get("text")
            else:
                ref_wav_path = speaker.get("ref_wav_path")
                ref_text = speaker.get("text")
            vec = None
            if True and role != "旁白":
                (vec_dict,_) = QwenEmotion('').inference(params.text)
                vec = [v for k,v in vec_dict.items()]
  
            logger.debug(f"text: {tts_params.text}, role: {role} vec = {vec}") 
            
            async for (sampling_rate, chunk) in get_tts_wav(tts_params.text,ref_wav_path,
                                stream=params.stream,format="ogg",speed=tts_params.speed,vec=vec):
                yield chunk
