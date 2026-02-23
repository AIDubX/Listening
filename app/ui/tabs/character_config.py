import gradio as gr
import json
import os
from pathlib import Path
from app.utils.character_recognition import diyList
from app.services.tts_service import (
    get_available_voices,
    get_voice_emotions,
    get_default_emotion_for_voice
)
from loguru import logger

default_character_config = {
    "默认对话": {
        "emotion": "",
        "pitch": "1",
        "role": "",
        "speed": "1",
        "spk": "",
        "tag": "dialogue",
        "regex": ""
    },
    "旁白": {
        "emotion": "",
        "pitch": "1",
        "role": "",
        "speed": "1",
        "spk": "",
        "tag": "narration",
        "regex": ""
    }
}

def load_config_files():
    """Load all JSON config files from configs/listening directory"""
    config_dir = Path("configs/listening")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # If no config files exist, create a default one
    if not list(config_dir.glob("*.json")):
        default_config = {
            "默认对话": {
                "emotion": "",
                "pitch": "1",
                "role": "",
                "speed": "1",
                "spk": "",
                "tag": "dialogue",
                "regex": ""
            },
            "旁白": {
                "emotion": "",
                "pitch": "1",
                "role": "",
                "speed": "1",
                "spk": "",
                "tag": "narration",
                "regex": ""
            }
        }
        with open(config_dir / "default.json", "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    l = [f.name for f in config_dir.glob("*.json")]
    return l
    # return gr.update(choices=l)

def load_config(filename):
    """Load a specific config file"""
    config_path = Path("configs/listening") / filename
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(filename, data):
    """Save config to file"""
    config_path = Path("configs/listening") / filename
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return "配置已保存"

def create_character_config_tab():
    """Create character configuration tab"""
    # 创建标签选项列表，每个选项是(key, display_name)的元组
    tag_choices = [(diyList[key]["name"], key) for key in diyList.keys()]
    
    # 获取可用的说话人列表
    available_voices = get_available_voices()
    default_voice = available_voices[0] if available_voices else None
    
    # 获取初始配置文件列表和默认配置
    initial_configs = load_config_files()
    default_config = initial_configs[0] if initial_configs else None
    
    # 获取默认配置的角色列表
    initial_characters = list(load_config(default_config).keys()) if default_config else []
    
    with gr.Column():
        gr.Markdown("## 角色配置")
        
        # 配置文件选择区域
        with gr.Row():
            with gr.Column(scale=4):
                with gr.Row():
                    config_dropdown = gr.Dropdown(
                        choices=initial_configs,
                        label="配置文件",
                        value=default_config,
                        scale=3
                    )
                    new_config_name = gr.Textbox(
                        label="新配置文件名",
                        placeholder="输入新配置文件名 (不需要.json后缀)",
                        scale=2
                    )
            
            with gr.Column(scale=1):
                with gr.Row():
                    create_config_btn = gr.Button("📝 创建", variant="secondary", min_width=50)
                    refresh_config_btn = gr.Button("🔄 刷新", variant="secondary", min_width=50)
                with gr.Row():
                    delete_config_btn = gr.Button("🗑️ 删除", variant="secondary", min_width=50)
                    read_config_btn = gr.Button("📖 导入到阅读", variant="secondary", min_width=50,link=f"/import/legado/redirect/tts?id={default_config[0:-5]}")

        
        # 角色配置区域
        with gr.Row():
            # 左侧 - 角色列表
            with gr.Column(scale=1):
                gr.Markdown("### 角色列表")
                character_list = gr.Radio(
                    choices=initial_characters,
                    label=None,
                    interactive=True
                )
                
                with gr.Row():
                    new_character_name = gr.Textbox(
                        label="新角色名称",
                        placeholder="输入新角色名称",
                        scale=2
                    )
                    add_character_btn = gr.Button("➕ 添加", variant="secondary", scale=1)
             
            
            # 右侧 - 角色属性
            with gr.Column(scale=2):
                gr.Markdown("### 角色属性")
                with gr.Group():
                    with gr.Row():
                        spk = gr.Dropdown(
                            choices=available_voices,
                            label="说话人",
                            value=default_voice,
                            allow_custom_value=True,
                            scale=2
                        )
                        emotion = gr.Dropdown(
                            choices=get_voice_emotions(default_voice) if default_voice else [],
                            label="情绪",
                            allow_custom_value=True,
                            value=get_default_emotion_for_voice(default_voice) if default_voice else None,
                            scale=2
                        )
                    
                    with gr.Row():
                        speed = gr.Slider(
                            minimum=0.5,
                            maximum=2.0,
                            value=1.0,
                            step=0.1,
                            label="语速"
                        )
                        pitch = gr.Slider(
                            minimum=0.5,
                            maximum=2.0,
                            value=1.0,
                            step=0.1,
                            label="音调"
                        )
                    
                    with gr.Row():
                        role = gr.Textbox(
                            label="角色名称",
                            scale=2
                        )
                        tag = gr.Dropdown(
                            label="标签类型", 
                            choices=tag_choices,
                            value="dialogue",
                            allow_custom_value=True,
                            scale=2
                        )
                    
                    regex = gr.Textbox(
                        label="正则表达式",
                        placeholder="用于匹配对话文本的正则表达式"
                    )
                    
                    with gr.Row():
                        save_btn = gr.Button("💾 保存更改", variant="primary", scale=2)
                        delete_btn = gr.Button("🗑️ 删除角色", variant="secondary", scale=1)
                    status = gr.Text(label="状态")

        def update_character_list(filename,request:gr.Request):
                
            link = f"/import/legado/redirect/tts?id={filename[0:-5]}"
            if not filename:
                return [[], gr.update(link="")]
            config = load_config(filename)
            characters = list(config.keys())
            return [gr.update(choices=characters, value=characters[0] if characters else None), gr.update(link=link)]
        
        def load_character_properties(filename, character_name):
            if not filename or not character_name:
                return [""]*7
            config = load_config(filename)
            # 处理character_name可能是列表的情况
            if isinstance(character_name, list):
                character_name = character_name[0] if character_name else ""
            char_config = config.get(character_name, {})

            spk_list = get_available_voices()
            
            # 先获取说话人
            spk_value = char_config.get("spk", default_voice)
            # 根据说话人获取可用的情绪列表
            available_emotions = get_voice_emotions(spk_value)
            # 获取保存的情绪值，如果不在可用列表中，使用默认情绪
            emotion_value = char_config.get("emotion", "")
            if emotion_value not in available_emotions:
                emotion_value = get_default_emotion_for_voice(spk_value)
            
            return [
                gr.update(choices=spk_list, value=spk_value),
                gr.update(choices=available_emotions, value=emotion_value),
                float(char_config.get("pitch", "1")),
                char_config.get("role", ""),
                float(char_config.get("speed", "1")),
                char_config.get("tag", "dialogue"),
                char_config.get("regex", "")
            ]
        
        def save_character_properties(filename, character_name, spk_value, emotion_value, pitch, role, speed, tag, regex):
            if not filename or not character_name:
                return "请选择配置文件和角色"
            # 处理character_name可能是列表的情况
            if isinstance(character_name, list):
                character_name = character_name[0] if character_name else ""
            config = load_config(filename)
            config[character_name] = {
                "spk": spk_value,
                "emotion": emotion_value,
                "pitch": pitch,
                "role": role,
                "speed": speed,
                "tag": tag,
                "regex": regex
            }
            save_config(filename, config)
            return "保存成功"
        
        def delete_character(filename, character_name):
            if not filename or not character_name:
                return [[], "请选择要删除的角色"]
            # 处理character_name可能是列表的情况
            if isinstance(character_name, list):
                character_name = character_name[0] if character_name else ""
            
            config = load_config(filename)
            if character_name not in config:
                return [list(config.keys()), "角色不存在"]
            
            # 删除角色
            del config[character_name]
            save_config(filename, config)
            
            # 更新角色列表
            characters = list(config.keys())
            return [gr.update(choices=characters, value=characters[0] if characters else None), "角色已删除"]
        
        def create_new_config(new_name):
            if not new_name:
                return [None, "请输入配置文件名"]
            filename = f"{new_name}.json" if not new_name.endswith(".json") else new_name
            config_path = Path("configs/listening") / filename
            if config_path.exists():
                return [None, "配置文件已存在"]
            
            # Create empty config
            save_config(filename, default_character_config)
            configs = load_config_files()
            return [filename, "新配置文件已创建"]

        def add_new_character(filename, char_name):
            if not filename or not char_name:
                return [[], "请选择配置文件并输入角色名称"]
            config = load_config(filename)
            if char_name in config:
                return [list(config.keys()), "角色已存在"]
            
            config[char_name] = {
                "spk": default_voice,
                "emotion": get_default_emotion_for_voice(default_voice) if default_voice else "",
                "pitch": 1,
                "role": "",
                "speed": 1,
                "tag": "dialogue",
                "regex": ""
            }
            save_config(filename, config)
            characters = list(config.keys())
            return [gr.update(choices=characters, value=char_name), "角色已添加"]

        def update_emotions(voice):
            emotions = get_voice_emotions(voice)
            default_emotion = get_default_emotion_for_voice(voice)
            return gr.update(choices=emotions, value=default_emotion)

        def refresh_configs():
            configs = load_config_files()
            current_value = config_dropdown.value
            # 如果当前选中的配置文件仍然存在，保持选中，否则选择第一个配置
            new_value = current_value if current_value in configs else (configs[0] if configs else None)
            # 更新角色列表
            characters = list(load_config(new_value).keys()) if new_value else []
            return [
                gr.update(choices=configs, value=new_value),
                gr.update(choices=characters, value=characters[0] if characters else None),
                "配置列表已刷新"
            ]

        def delete_config(filename):
            if not filename:
                return [None, [], "请选择要删除的配置文件"]
            
            config_path = Path("configs/listening") / filename
            try:
                if config_path.exists():
                    config_path.unlink()  # 删除文件
                
                # 重新加载配置文件列表
                configs = load_config_files()
                new_value = configs[0] if configs else None
                
                # 如果有新的配置文件，加载其角色列表
                characters = list(load_config(new_value).keys()) if new_value else []
                
                return [
                    gr.update(choices=configs, value=new_value),
                    gr.update(choices=characters, value=characters[0] if characters else None),
                    "配置文件已删除"
                ]
            except Exception as e:
                return [
                    gr.update(choices=configs, value=filename),
                    gr.update(),
                    f"删除配置文件失败: {str(e)}"
                ]

        # Event handlers
        config_dropdown.change(
            fn=update_character_list,
            inputs=[config_dropdown],
            outputs=[character_list, read_config_btn]
        )
        
        character_list.change(
            fn=load_character_properties,
            inputs=[config_dropdown, character_list],
            outputs=[spk, emotion, pitch, role, speed, tag, regex]
        )
        
        spk.change(
            fn=update_emotions,
            inputs=[spk],
            outputs=[emotion]
        )
        
        save_btn.click(
            fn=save_character_properties,
            inputs=[config_dropdown, character_list, spk, emotion, pitch, role, speed, tag, regex],
            outputs=[status]
        )
        
        delete_btn.click(
            fn=delete_character,
            inputs=[config_dropdown, character_list],
            outputs=[character_list, status]
        )
        
        def update_config_dropdown():
            configs = load_config_files()
            return gr.update(choices=configs)
        
        create_config_btn.click(
            fn=create_new_config,
            inputs=[new_config_name],
            outputs=[config_dropdown, status]
        ).then(
            fn=update_config_dropdown,
            inputs=[],
            outputs=[config_dropdown]
        ).then(
            fn=update_character_list,
            inputs=[config_dropdown],
            outputs=[character_list, read_config_btn]
        )
        
        refresh_config_btn.click(
            fn=refresh_configs,
            inputs=[],
            outputs=[config_dropdown, character_list, status]
        )
        
        add_character_btn.click(
            fn=add_new_character,
            inputs=[config_dropdown, new_character_name],
            outputs=[character_list, status]
        )
    
        
        delete_config_btn.click(
            fn=delete_config,
            inputs=[config_dropdown],
            outputs=[config_dropdown, character_list, status]
        )
        

    return [config_dropdown, character_list, status] 