import soundfile as sf
import ffmpeg
import numpy as np
from loguru import logger
import io
from scipy.io import wavfile

def read_clean_buffer(audio_bytes):
    audio_chunk = audio_bytes.getvalue()
    audio_bytes.truncate(0)
    audio_bytes.seek(0)

    return audio_bytes, audio_chunk


def pack_wav(bytes_io,wav, sr):
    wavfile.write(bytes_io, sr, wav)
    return bytes_io

def speed_change(input_audio: np.ndarray, speed: float, sr: int):
    # 将 NumPy 数组转换为原始 PCM 流
    raw_audio = input_audio.tobytes()

    # 设置 ffmpeg 输入流
    input_stream = ffmpeg.input('pipe:', format='s16le', acodec='pcm_s16le', ar=str(sr), ac=1)

    # 变调
    output_stream = input_stream.filter("atempo", speed)

    try:
        # 输出流到管道
        out, err = (
            output_stream.output('pipe:', format='s16le', acodec='pcm_s16le')
            .run(input=raw_audio, capture_stdout=True, capture_stderr=True)
        )
        # 将管道输出解码为 NumPy 数组
        processed_audio = np.frombuffer(out, np.int16)

        return processed_audio
    except Exception as e:
        logger.error(e)
        return input_stream


def read_clean_buffer(audio_bytes):
    audio_chunk = audio_bytes.getvalue()
    audio_bytes.truncate(0)
    audio_bytes.seek(0)

    return audio_bytes, audio_chunk

def pack_ogg(audio_bytes, data, rate):
 
    def handle_pack_ogg():
        with sf.SoundFile(audio_bytes, mode='w', samplerate=rate, channels=1, format='ogg') as audio_file:
            audio_file.write(data)

    import threading
    # See: https://docs.python.org/3/library/threading.html
    # The stack size of this thread is at least 32768
    # If stack overflow error still occurs, just modify the `stack_size`.
    # stack_size = n * 4096, where n should be a positive integer.
    # Here we chose n = 4096.
    stack_size = 4096 * 4096
    try:
        threading.stack_size(stack_size)
        pack_ogg_thread = threading.Thread(target=handle_pack_ogg)
        pack_ogg_thread.start()
        pack_ogg_thread.join()
    except RuntimeError as e:
        # If changing the thread stack size is unsupported, a RuntimeError is raised.
        print("RuntimeError: {}".format(e))
        print("Changing the thread stack size is unsupported.")
    except ValueError as e:
        # If the specified stack size is invalid, a ValueError is raised and the stack size is unmodified.
        print("ValueError: {}".format(e))
        print("The specified stack size is invalid.")

    return audio_bytes
