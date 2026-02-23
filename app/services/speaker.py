import os
import yaml
import copy
from loguru import logger
from pathlib import Path
from app.config import settings
import shutil

def dynamic_load_speaker(path):
    """使用pathlib加载音色文件"""
    path = Path(path)
    logger.debug(f"开始加载{path}")
    speakers = {}
    
    if not path.exists():
        return speakers

    # 初始化 _config 对象，确保 category 是字典
    if not hasattr(dynamic_load_speaker, "_config"):
        dynamic_load_speaker._config = type('Config', (object,), {})()
        dynamic_load_speaker._config.category = {}
    
    for m_dir in path.iterdir():
        if not m_dir.is_dir() or m_dir.name in [".DS_Store", "rvctts"]:
            continue
            
        spk = m_dir.name
        dir_name = str(m_dir)
        
        if speakers.get(spk) is None:
            speakers[spk] = {"emotion": {}, "tags": [dir_name], "desc": path.name}
            # 新增分类功能
            if dir_name not in dynamic_load_speaker._config.category:
                dynamic_load_speaker._config.category[dir_name] = []
            dynamic_load_speaker._config.category[dir_name].append(spk)
            
        for wav in m_dir.iterdir():
            if not wav.is_file():
                continue
                
            prompt = wav.stem
            suffix = wav.suffix.lower()
            
            if suffix == ".ckpt":
                speakers[spk]["gpt_path"] = wav.absolute().as_posix()
            elif suffix == ".pth":
                speakers[spk]["sovits_path"] = wav.absolute().as_posix()
            elif suffix.lower() in ['.wav', ".wav"]:
                if speakers[spk].get("path") is None:
                    speakers[spk]["path"] = str(wav.parent)
                    
                nprompt = wav.stem.split("#")
                if len(nprompt) > 2:
                    prompt = nprompt
                else:
                    logger.error(f"{m_dir.name}/{wav.name} 音色文件命名格式有误，请按照格式：语气#语言#内容.wav")
                    continue
                    
                if speakers[spk].get("ref_wav_path") is None:
                    speakers[spk]["ref_wav_path"] = wav.absolute().as_posix()
                    speakers[spk]["text"] = prompt[2]
                    speakers[spk]["text_lang"] = prompt[1]
                    
                speakers[spk]["emotion"][prompt[0]] = {
                    "ref_wav_path": wav.absolute().as_posix(),
                    "text": prompt[2],
                    "text_lang": prompt[1],
                }
            elif suffix.lower() in ['.png', '.jpg']:
                speakers[spk]["avatar"] = wav.absolute().as_posix()
            elif wav.stem == "metadata":
                try:
                    with open(wav, "r", encoding="utf-8") as f:
                        speakers[spk]["metadata"] = yaml.load(f, Loader=yaml.FullLoader)
                except:
                    speakers[spk]["metadata"] = {}
    return speakers

def dynamic_load_model1(path):
    """使用pathlib加载模型"""
    path = Path(path)
    speakers = {}
    
    for m_dir in path.iterdir():
        if not m_dir.is_dir():
            continue
            
        category = m_dir.name
        # gpt_path,sovits_path = get_default_model()
        category_configs = {
            # "sovits_path": sovits_path,
            # "gpt_path": gpt_path,
        }
        
        # 查找模型文件
        for c in m_dir.iterdir():
            if c.is_file():
                suffix = c.suffix.lower()
                if suffix == ".ckpt":
                    # 使用postfix路径
                    rel_path = c.relative_to(path) if c.is_absolute() else c
                    category_configs["gpt_path"] = c.absolute().as_posix()
                elif suffix == ".pth":
                    # 使用postfix路径
                    category_configs["sovits_path"] = c.absolute().as_posix()
        
        # 处理情感文件夹
        emotions_dir = m_dir / "reference_audios" / "emotions"
        if emotions_dir.exists():
            for spk in emotions_dir.iterdir():
                if not spk.is_dir():
                    continue
                    
                speakers[spk.name] = copy.deepcopy(category_configs)
                speakers[spk.name].update({
                    "ref_wav_path": None,
                    "text": "",
                    "text_lang": "",
                    "desc": category,
                    "emotion": {}
                })
                
                for lang in spk.iterdir():
                    if not lang.is_dir():
                        continue
                        
                    language = "auto"
                    if lang.name == "中文":
                        language = "zh"
                    elif lang.name == "日语":
                        language = "ja"
                    elif lang.name in ["英语", "英文"]:
                        language = "en"
                    
                    for wav in lang.iterdir():
                        if not wav.is_file() or wav.suffix.lower() not in ['.wav', '.mp3']:
                            continue
                            
                        info = wav.stem.split("】")
                        if len(info) < 2:
                            continue
                            
                        emotion = info[0][1:]
                        speakers[spk.name]["emotion"][emotion] = {
                            "ref_wav_path": wav.absolute().as_posix(),
                            "text": info[1],
                            "text_lang": language,
                        }
                        
                        if speakers[spk.name].get("ref_wav_path") is None:
                            speakers[spk.name]["ref_wav_path"] = wav.absolute().as_posix()
                            speakers[spk.name]["text"] = info[1]
                            speakers[spk.name]["text_lang"] = language
    return speakers

class SpeakerManager:
    _instance = None
    _speakers = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpeakerManager, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if self._speakers is None:
            self.refresh()
            
    def refresh(self):
        """刷新speaker配置"""
        self._speakers = dynamic_load_model1(settings.SPEAKER_PATH)
        self._speakers.update(dynamic_load_speaker(settings.MODEL_PATH))
        
    def get_speakers(self):
        """获取所有speaker配置"""
        self.refresh()
        return self._speakers
        
    def get_speaker(self, name):
        """获取指定speaker配置"""
        return self._speakers.get(name)
        
    def get_speaker_names(self):
        """获取所有speaker名称"""
        self.refresh()
        return list(self._speakers.keys())
        
    def get_speaker_emotions(self, name):
        """获取指定speaker的情感列表"""
        speaker = self.get_speaker(name)
        if speaker:
            return list(speaker["emotion"].keys())
        return []

    def create_speaker(self,name,emotion,ref_wav_path,text,text_lang):
        """创建新的speaker"""
        voice_path = Path(settings.MODEL_PATH) / name
        voice_path.mkdir(parents=True, exist_ok=True)
        # 检查一下是否存在旧的，存在旧的删掉
        if emotion_path := self._speakers.get(name,{}).get("emotion",{}).get(emotion,{}).get("ref_wav_path",""):
            os.remove(emotion_path)
        # 复制参考音频到新文件夹
        if not ref_wav_path.lower().endswith(".wav"):
            os.system(f"ffmpeg -i {ref_wav_path} -acodec pcm_s16le -ac 1 -ar 16000 {voice_path / f'{emotion}#{text_lang}#{text}.wav'}")
        else:
            shutil.copy(ref_wav_path, voice_path / f"{emotion}#{text_lang}#{text}.wav")
        
        return f"音色 {name} 已创建"
    
    def delete_speaker(self,name):
        """删除指定speaker"""
        voice_path = Path(settings.MODEL_PATH) / name
        if voice_path.exists():
            shutil.rmtree(voice_path)
        return f"音色 {name} 已删除"
    
    def delete_emotion(self,name,emotion):
        """删除指定speaker的情感"""
        emotion_path = self._speakers.get(name,{}).get("emotion",{}).get(emotion,{}).get("ref_wav_path","")
        if emotion_path:
            os.remove(emotion_path)
        return f"音色 {name} 的情感 {emotion} 已删除"