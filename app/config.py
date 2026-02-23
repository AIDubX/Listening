from dataclasses import dataclass, field
from typing import List, Dict, Any
import os
import json
from pathlib import Path
# from dotenv import load_dotenv
import os
# 加载.env文件
# load_dotenv()
from loguru import logger

@dataclass
class Settings:
    """应用配置类"""
    
    # 应用信息
    APP_TITLE: str = "AI听书 优云智算版本"
    APP_VERSION: str = "2.0"
    TTS_ENGINE: str = "IndexTTS"
    APP_SUMMARY: str = "只需要阅读+AI听书，就能实现多角色AI听书"
    TERMS_OF_SERVICE: str = "https://aidub.pro"
    CONTACT: Dict[str, str] = field(default_factory=lambda: {
        "name": "CyberWon",
        "url": "https://aidub.pro",
        "email": "mail@berstar.cn",
    })
    DEBUG = True
    # 服务器设置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # CORS设置
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = field(default_factory=lambda: ["*"])
    
    # Gradio设置
    GRADIO_PATH: str = "/ui"
    
    # TTS设置
    DEFAULT_VOICE: str = "默认"
    AVAILABLE_VOICES: List[str] = field(default_factory=lambda: ["默认", "女声", "男声", "童声"])
    
    # 情感设置
    DEFAULT_EMOTION: str = "正常"
    AVAILABLE_EMOTIONS: List[str] = field(default_factory=lambda: ["正常", "开心", "悲伤", "愤怒", "惊讶", "恐惧", "温柔", "激动"])
    
    # 内网穿透设置
    ENABLE_NAT: bool = False
    NAT_TYPE: str = "ssh"  # 支持的类型：ssh, frp, ngrok
    NAT_SERVER: str = ""  # 内网穿透服务器地址
    NAT_PORT: int = 7860  # 本地服务端口
    NAT_REMOTE_PORT: int = 60080  # 远程服务端口，0表示随机
    NAT_TOKEN: str = "aidub"  # 认证token (用于frp/ngrok)
    NAT_CUSTOM_DOMAIN: str = ""  # 自定义域名
    NAT_USERNAME: str = ""  # SSH用户名
    NAT_PASSWORD: str = ""  # SSH密码
    NAT_SSH_PORT: int = 22  # SSH端口号
    
    # 路径设置
    BASE_DIR: Path = os.getcwd()
    SPEAKER_PATH: Path = field(init=False)
    OUTPUT_DIR: Path = field(init=False)
    
    # 分桶设置
    split_bucket: bool = True
    batch_size: int = 1
    batch_threshold: float = 0.75
    text_split_method: str = "cut2"
    temperature: float = 1
    top_k: int = 15
    top_p: float = 1
    repetition_penalty: float = 1.35
    parallel_infer: bool = True
    fragment_interval: float = 0.01

    # 认证设置
    ENABLE_AUTH: bool = False
    AUTH_USERNAME: str = ""
    AUTH_PASSWORD: str = ""

    def __post_init__(self):
        # 加载JSON配置
        self.load_config()
        
        # 初始化路径
        self.SPEAKER_PATH = self.get_config("paths.speaker_path", os.environ.get("AIDUB_SPEAKER_PATH", "models"))
        self.MODEL_PATH = self.get_config("paths.model_path", os.environ.get("AIDUB_MODEL_PATH", "models2"))
        logger.info(f"音模路径1: {self.SPEAKER_PATH}")
        logger.info(f"音模路径2: {self.MODEL_PATH}")
        # self.OUTPUT_DIR = self.get_config("paths.output_dir", "output")
        
        # 确保必要的目录存在
        os.makedirs(self.SPEAKER_PATH, exist_ok=True)
        os.makedirs(self.MODEL_PATH, exist_ok=True)
        # os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def load_config(self):
        """从JSON文件加载配置"""
        config_path = "configs/config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 更新应用信息
            
            # 更新服务器设置
            self.SERVER_HOST = config.get("server", {}).get("host", self.SERVER_HOST)
            self.SERVER_PORT = config.get("server", {}).get("port", self.SERVER_PORT)
            
            # 更新路径设置
            # self.SPEAKER_PATH = config.get("paths", {}).get("speaker_path", self.SPEAKER_PATH)
            # self.MODEL_PATH = config.get("paths", {}).get("model_path", self.MODEL_PATH)
            # self.OUTPUT_DIR = config.get("paths", {}).get("output_dir", self.OUTPUT_DIR)
            
            # 更新CORS设置
            cors_config = config.get("cors", {})
            self.CORS_ORIGINS = cors_config.get("origins", self.CORS_ORIGINS)
            self.CORS_ALLOW_CREDENTIALS = cors_config.get("allow_credentials", self.CORS_ALLOW_CREDENTIALS)
            self.CORS_ALLOW_METHODS = cors_config.get("allow_methods", self.CORS_ALLOW_METHODS)
            self.CORS_ALLOW_HEADERS = cors_config.get("allow_headers", self.CORS_ALLOW_HEADERS)
            
            # 更新Gradio设置
            self.GRADIO_PATH = config.get("gradio", {}).get("path", self.GRADIO_PATH)
            
            # 更新TTS设置
            tts_config = config.get("tts", {})
            self.DEFAULT_VOICE = tts_config.get("default_voice", self.DEFAULT_VOICE)
            self.AVAILABLE_VOICES = tts_config.get("available_voices", self.AVAILABLE_VOICES)
            
            # 更新情感设置
            emotion_config = config.get("emotion", {})
            self.DEFAULT_EMOTION = emotion_config.get("default_emotion", self.DEFAULT_EMOTION)
            self.AVAILABLE_EMOTIONS = emotion_config.get("available_emotions", self.AVAILABLE_EMOTIONS)
            
            # 更新内网穿透设置
            nat_config = config.get("nat", {})
            self.ENABLE_NAT = nat_config.get("enable", self.ENABLE_NAT)
            self.NAT_TYPE = nat_config.get("type", self.NAT_TYPE)
            self.NAT_SERVER = nat_config.get("server", self.NAT_SERVER)
            self.NAT_PORT = nat_config.get("port", self.NAT_PORT)
            self.NAT_REMOTE_PORT = nat_config.get("remote_port", self.NAT_REMOTE_PORT)
            self.NAT_TOKEN = nat_config.get("token", self.NAT_TOKEN)
            self.NAT_CUSTOM_DOMAIN = nat_config.get("custom_domain", self.NAT_CUSTOM_DOMAIN)
            self.NAT_USERNAME = nat_config.get("username", self.NAT_USERNAME)
            self.NAT_PASSWORD = nat_config.get("password", self.NAT_PASSWORD)
            self.NAT_SSH_PORT = nat_config.get("ssh_port", self.NAT_SSH_PORT)
            
            # 更新分桶设置
            bucket_config = config.get("bucket", {})
            self.split_bucket = bucket_config.get("split_bucket", self.split_bucket)
            self.batch_size = bucket_config.get("batch_size", self.batch_size)
            self.batch_threshold = bucket_config.get("batch_threshold", self.batch_threshold)
            self.text_split_method = bucket_config.get("text_split_method", self.text_split_method)
            self.temperature = bucket_config.get("temperature", self.temperature)
            self.top_k = bucket_config.get("top_k", self.top_k)
            self.top_p = bucket_config.get("top_p", self.top_p)
            self.repetition_penalty = bucket_config.get("repetition_penalty", self.repetition_penalty)
            self.parallel_infer = bucket_config.get("parallel_infer", self.parallel_infer)
            self.fragment_interval = bucket_config.get("fragment_interval", self.fragment_interval)

            # 加载认证设置
            self.ENABLE_AUTH = config.get("auth", {}).get("enable", False)
            self.AUTH_USERNAME = config.get("auth", {}).get("username", "")
            self.AUTH_PASSWORD = config.get("auth", {}).get("password", "")

        else:
            logger.warning(f"配置文件 {config_path} 不存在，已创建默认配置")
            self.save_config()

    def save_config(self):
        """保存配置到JSON文件"""
        config = {
            "server": {
                "host": self.SERVER_HOST,
                "port": self.SERVER_PORT
            },
            "cors": {
                "origins": self.CORS_ORIGINS,
                "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
                "allow_methods": self.CORS_ALLOW_METHODS,
                "allow_headers": self.CORS_ALLOW_HEADERS
            },
            "gradio": {
                "path": self.GRADIO_PATH
            },
            "tts": {
                "default_voice": self.DEFAULT_VOICE,
                "available_voices": self.AVAILABLE_VOICES
            },
            "emotion": {
                "default_emotion": self.DEFAULT_EMOTION,
                "available_emotions": self.AVAILABLE_EMOTIONS
            },
            "nat": {
                "enable": self.ENABLE_NAT,
                "type": self.NAT_TYPE,
                "server": self.NAT_SERVER,
                "port": self.NAT_PORT,
                "remote_port": self.NAT_REMOTE_PORT,
                "token": self.NAT_TOKEN,
                "custom_domain": self.NAT_CUSTOM_DOMAIN,
                "username": self.NAT_USERNAME,
                "password": self.NAT_PASSWORD,
                "ssh_port": self.NAT_SSH_PORT
            },
            "bucket": {
                "split_bucket": self.split_bucket,
                "batch_size": self.batch_size,
                "batch_threshold": self.batch_threshold,
                "text_split_method": self.text_split_method,
                "temperature": self.temperature,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty,
                "parallel_infer": self.parallel_infer,
                "fragment_interval": self.fragment_interval
            },
            "auth": {
                "enable": self.ENABLE_AUTH,
                "username": self.AUTH_USERNAME,
                "password": self.AUTH_PASSWORD
            }
        }
        
        config_path = "configs/config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def get_config(self, path: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            if '.' in path:
                section, key = path.split('.', 1)
                if section == 'nat':
                    return getattr(self, f'NAT_{key.upper()}', default)
                return default
            return getattr(self, path.upper(), default)
        except AttributeError:
            return default

    def update_config(self, path: str, value: Any):
        """更新配置值"""
        try:
            if '.' in path:
                section, key = path.split('.', 1)
                if section == 'nat':
                    attr_name = f'NAT_{key.upper()}'
                    if hasattr(self, attr_name):
                        setattr(self, attr_name, value)
                        self.save_config()
                    else:
                        raise AttributeError(f"Unknown configuration: {path}")
            else:
                attr_name = path.upper()
                if hasattr(self, attr_name):
                    setattr(self, attr_name, value)
                    self.save_config()
                else:
                    raise AttributeError(f"Unknown configuration: {path}")
        except Exception as e:
            raise Exception(f"Failed to update configuration: {str(e)}")

# 创建全局设置实例
settings = Settings() 
