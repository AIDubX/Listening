import gradio as gr
from app.config import settings

def create_auth_config_tab():
    """创建安全认证配置选项卡"""
    with gr.Column():
        gr.Markdown("## 安全设置")
        
        with gr.Row():
            with gr.Column(scale=1):
                enable_auth = gr.Checkbox(
                    label="启用HTTP Basic认证",
                    value=settings.ENABLE_AUTH,
                    info="启用后需要输入用户名和密码才能访问网页"
                )
                
                auth_username = gr.Textbox(
                    label="用户名",
                    value=settings.AUTH_USERNAME,
                    placeholder="请输入用户名"
                )
                
                auth_password = gr.Textbox(
                    label="密码",
                    value=settings.AUTH_PASSWORD,
                    type="password",
                    placeholder="请输入密码"
                )

                with gr.Row():
                    save_btn = gr.Button("保存配置", variant="primary")
                    show_tts = gr.Button("获取加密配置", variant="secondary")
            
                
                status_text = gr.Text(label="状态")

        # 保存配置
        def save_auth_config(enable, username, password):
            try:
                settings.ENABLE_AUTH = enable
                settings.AUTH_USERNAME = username
                settings.AUTH_PASSWORD = password
                
                settings.save_config()
                return f"安全配置已保存 - 认证状态: {'已启用' if enable else '未启用'}"
            except Exception as e:
                return f"保存配置失败: {str(e)}"
        
        save_btn.click(
            fn=save_auth_config,
            inputs=[enable_auth, auth_username, auth_password],
            outputs=[status_text]
        ) 
        
        def show_tts_config(request: gr.Request):
            import json
            import base64
            import time
            
            scheme = request.url.scheme
            host = request.headers.get("host")
            return json.dumps({
                "contentType": "audio/ogg",
                "header": json.dumps({"Authorization": f"Basic {base64.b64encode(f'{settings.AUTH_USERNAME}:{settings.AUTH_PASSWORD}'.encode()).decode()}"}),
                "id": time.time(),
                "lastUpdateTime": time.time(),
                "name": f"AI听书(auth)",
                "url": f"{scheme}://{host}/listening,"
                r'{"method":"POST","body":{"text":"{{speakText}}","id":"default"}}',
                "concurrentRate": "1"
            })
            
                
        
        show_tts.click(
            fn=show_tts_config,
            inputs=[],
            outputs=[status_text]
        )

