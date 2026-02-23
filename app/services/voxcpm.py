from voxcpm import VoxCPM
import os

model = VoxCPM(r"ckpts")
from app.utils.pack_audio import pack_ogg,speed_change,pack_wav,read_clean_buffer
from loguru import logger
from io import BytesIO


def get_tts_wav(text, ref_audio, ref_text, infer_timestep=32, p_w=1.6, t_w=2.5,stream=False,format="ogg",speed=1.0):
    wav_data = model.generate(
        text=text,
        prompt_wav_path=ref_audio,      # optional: path to a prompt speech for voice cloning
        prompt_text=ref_text,          # optional: reference text
        cfg_value=2.0,             # LM guidance on LocDiT, higher for better adherence to the prompt, but maybe worse
        inference_timesteps=10,   # LocDiT inference timesteps, higher for better result, lower for fast speed
        normalize=True,           # enable external TN tool
        denoise=True,             # enable external Denoise tool
        retry_badcase=True,        # enable retrying mode for some bad cases (unstoppable)
        retry_badcase_max_times=3,  # maximum retrying times
        retry_badcase_ratio_threshold=6.0, # maximum length restriction for bad case detection (simple but effective), it could be adjusted for slow pace speech
    )
    if speed != 1.0:
        wav_data = speed_change(wav_data,speed,16000)
    audio_bytes = BytesIO()
    audio_bytes = pack_ogg(audio_bytes,wav_data,16000)
    # audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
    yield audio_bytes.getvalue()
    