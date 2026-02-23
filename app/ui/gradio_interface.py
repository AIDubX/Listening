import gradio as gr
from app.config import settings
import requests
from datetime import datetime

from app.ui.tabs import (
    create_speech_synthesis_tab,
    create_voice_config_tab,
    # create_listening_config_tab,
    create_audiobook_tab,
    create_nat_config_tab,
    create_about_tab,
    create_character_config_tab
)
from app.ui.tabs.book_tab import create_book_tab, CUSTOM_CSS
from app.ui.tabs.auth import create_auth_config_tab

def create_gradio_interface():
    """创建Gradio界面"""
    with gr.Blocks(title=settings.APP_TITLE, css=CUSTOM_CSS) as interface:
        gr.Markdown(f"# {settings.APP_TITLE} V{settings.APP_VERSION} By CyberWon X {settings.TTS_ENGINE} \n"
                    "CyberWon 出品，值得收藏使用")
        
        with gr.Tabs():

            # with gr.TabItem("有声"):
            #     create_audiobook_tab()
                
            with gr.TabItem("推书"):
                # update_fn, outputs = create_audiobook_tab()
                update_fn, outputs = create_book_tab()
                
            with gr.TabItem("语音合成"):
                create_speech_synthesis_tab()
            
            with gr.TabItem("音色"):
                create_voice_config_tab()
            
            # with gr.TabItem("畅听配置"):
            #     create_listening_config_tab()
            
            with gr.TabItem("角色"):
                create_character_config_tab()

            with gr.TabItem("有声"):
                create_audiobook_tab()
            
            with gr.TabItem("外网"):
                create_nat_config_tab()
            
            with gr.TabItem("安全"):
                create_auth_config_tab()
            
            with gr.TabItem("关于"):
                create_about_tab()
        
        # 页面加载时自动更新推书信息
        interface.load(fn=update_fn, outputs=outputs)
    
    return interface 