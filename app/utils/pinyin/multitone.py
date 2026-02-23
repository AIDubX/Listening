from pypinyin import lazy_pinyin, Style
import yaml
from .pinyin2ph import pinyin2ph_dict,py_errors
import os

# 全局变量用于跟踪窗口实例
_instance = None


class MultiToneManager:
    _instance = None
    multi_tone = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self.multi_tone is None:
            self.multi_tone = {}
            self.phoneme = {}
            self.multi_tone_gsv = {}

    def pinyin2gsv(self,src):

        out = ""
        for py in src:
            phs = []
            # logger.debug(f"py: {py}")
            if py in self.phoneme:
                ph = self.phoneme[py].split()
                phs.extend(ph)
            elif py in pinyin2ph_dict:
                ph = pinyin2ph_dict[py].split()
                phs.extend(ph)
            else:
                for w in py:
                    ph = py_errors(w)
                    phs.extend(ph)

            if len(phs[0]) > 1 and phs[0][0] == ph[0][1]:
                # 改成大写
                phs[0] = phs[0].upper()
            p = ''.join(phs[1:])
            out += f'{phs[0]} {p} '
        return out[:-1]

    def load(self,data:dict,phoneme:dict = {}):
        self.multi_tone = data
        self.phoneme = phoneme
        self.multi_tone_gsv = {k:self.pinyin2gsv(v.split(" ")) for k,v in self.multi_tone.items()}
  

    def set(self, key, value):
        self.multi_tone[key] = value
        self.save()

    def get(self, key):
        return self.multi_tone.get(key)

    def save(self):
        with open(self.path, "w+", encoding="utf-8") as f:
            yaml.dump(self.multi_tone, f, default_flow_style=False, allow_unicode=True)

    def to_gpt_sovits(self):
        return self.multi_tone_gsv

    def to_f5tts(self):
        return {k:v.split(" ") for k,v in self.multi_tone.items()}
    
def multi_tone_manager():
    global _instance
    if _instance is None:
        _instance = MultiToneManager()
    return _instance
