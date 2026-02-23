import gradio as gr
from app.config import settings

def create_about_tab():
    """创建关于选项卡"""
    with gr.Column():
        gr.Markdown(f"""
        ## 关于 {settings.APP_TITLE}
        
        {settings.APP_SUMMARY}
        
        ### 特点
        - 只需要阅读+AI听书，就能实现多角色AI听书
        - 解压即用，省去繁琐的配置过程。
        
        
        ### 版本信息
        
        - 当前版本: {settings.APP_VERSION}
        - 开发者: {settings.CONTACT["name"]}
        - 全平台ID：  {settings.CONTACT["name"]}
        - 公众号 - AIDub
        
        ### 协议
        
        1. 本项目不开源，仅供个人使用，禁止商用。
        2. 不得用于任何违法违规用途
        3. 不得侵犯他人权益
        4. 不得违反中华人民共和国法律法规
        5. 若违反以上条款，由使用者自行承担全部责任，与开发者无关。
        """)
    
    return [] 