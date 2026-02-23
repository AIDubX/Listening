from indextts.infer_v2 import IndexTTS2,QwenEmotion
from app.utils.pack_audio import pack_ogg,speed_change,pack_wav,read_clean_buffer
from loguru import logger
from io import BytesIO
import gc
from pathlib import Path
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

tts = IndexTTS2(cfg_path="IndexTTS-2/config.yaml",
    model_dir="IndexTTS-2",
    is_fp16=True,
    device=device,
    use_cuda_kernel=False)

def get_tts_wav(text, ref_audio, vec=None,stream=False,format="ogg",speed=1.0):
    (sampling_rate,wav_data) = tts.infer(spk_audio_prompt=ref_audio,
     text=text, output_path=None,emo_vector=vec, verbose=True)
    if speed != 1.0:
        wav_data = speed_change(wav_data,speed,sampling_rate)
    audio_bytes = BytesIO()
    audio_bytes = pack_ogg(audio_bytes,wav_data,sampling_rate)
    # audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
    yield audio_bytes.getvalue()
    
