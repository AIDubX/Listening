import gradio as gr
from app.config import settings
from app.utils.frp import FRP
import threading
import time

def create_nat_config_tab():
    """创建内网穿透配置选项卡"""
    with gr.Column():
        gr.Markdown("## 外网配置")
        with gr.Row():
            gr.Button(
                value="阿里云",
                link="https://www.aliyun.com/minisite/goods?userCode=uosbwb3u"
            )
            gr.Button(
                value="腾讯云",
                link="https://curl.qcloud.com/Dvw9rbg3"
            )
        
        with gr.Row():
            with gr.Column(scale=1):
                enable_nat = gr.Checkbox(
                    label="自动启动外网",
                    value=settings.ENABLE_NAT
                )
                
                nat_type = gr.Dropdown(
                    choices=["gradio","ssh"],
                    label="穿透类型",
                    value=settings.NAT_TYPE
                )
                
                nat_server = gr.Textbox(
                    label="服务器地址",
                    value=settings.NAT_SERVER,
                    placeholder="例如: ssh.example.com"
                )
                
                nat_username = gr.Textbox(
                    label="SSH用户名",
                    value=settings.NAT_USERNAME,
                    placeholder="SSH登录用户名"
                )
                
                nat_password = gr.Textbox(
                    label="SSH密码",
                    value=settings.NAT_PASSWORD,
                    type="password",
                    placeholder="SSH登录密码"
                )
                
                nat_ssh_port = gr.Number(
                    label="SSH端口",
                    value=settings.NAT_SSH_PORT,
                    precision=0,
                    minimum=1,
                    maximum=65535
                )
                
                nat_token = gr.Textbox(
                    label="认证Token",
                    value=settings.NAT_TOKEN,
                    type="password",
                    visible=False
                )
            
            with gr.Column(scale=1):
                nat_port = gr.Number(
                    label="本地端口",
                    value=settings.SERVER_PORT,
                    precision=0
                )
                
                nat_remote_port = gr.Number(
                    label="远程端口 (0表示随机)",
                    value=settings.NAT_REMOTE_PORT,
                    precision=0
                )
                
                nat_custom_domain = gr.Textbox(
                    label="自定义域名 (可选)",
                    value=settings.NAT_CUSTOM_DOMAIN,
                    placeholder="例如: myapp.example.com"
                )
                frp = FRP()
                with gr.Row():
                    save_btn = gr.Button("保存配置", variant="primary")
                    test_btn = gr.Button("外网启停")
                
                status_text = gr.Text(label="状态")
        
        # 根据穿透类型切换显示的认证方式
        def update_auth_fields(nat_type):
            if nat_type == "ssh":
                return {
                    nat_username: gr.update(visible=True),
                    nat_password: gr.update(visible=True),
                    nat_ssh_port: gr.update(visible=True),
                    nat_token: gr.update(visible=False)
                }
            else:
                return {
                    nat_username: gr.update(visible=False),
                    nat_password: gr.update(visible=False),
                    nat_ssh_port: gr.update(visible=False),
                    nat_token: gr.update(visible=True)
                }
        
        nat_type.change(
            fn=update_auth_fields,
            inputs=[nat_type],
            outputs=[nat_username, nat_password, nat_ssh_port, nat_token]
        )
        
        # 保存配置
        def save_nat_config(enable, type_, server, username, password, ssh_port, token, port, remote_port, custom_domain):
            try:
                settings.ENABLE_NAT = enable
                settings.NAT_TYPE = type_
                settings.NAT_SERVER = server
                settings.NAT_USERNAME = username
                settings.NAT_PASSWORD = password
                settings.NAT_SSH_PORT = int(ssh_port)
                settings.NAT_TOKEN = token
                settings.NAT_PORT = int(port)
                settings.NAT_REMOTE_PORT = int(remote_port)
                settings.NAT_CUSTOM_DOMAIN = custom_domain
                
                settings.save_config()
                
                auth_info = f"用户名: {username}" if type_ == "ssh" else f"Token: {'*' * len(token)}"
                return f"配置已保存 - 服务器: {server}, {auth_info}"
            except Exception as e:
                return f"保存配置失败: {str(e)}"
        
        save_btn.click(
            fn=save_nat_config,
            inputs=[enable_nat, nat_type, nat_server, nat_username, nat_password, nat_ssh_port, nat_token, nat_port, nat_remote_port, nat_custom_domain],
            outputs=[status_text]
        )
        
        # 测试连接
        def test_nat_connection(enable, type_, server, username, password, ssh_port, token, port, remote_port, custom_domain):
            frp = FRP()
            
            # 如果已经启动，则停止服务
            if not frp.is_stopped and frp.wan_url:
                frp.stop()
                return "外网已停止", "启动外网"
            
            # 启动服务
            thread = threading.Thread(target=frp.start, daemon=True)
            thread.start()
            
            # 等待服务启动（最多等待5秒）
            for _ in range(50):
                if frp.wan_url:
                    return f"外网已启动，地址：{frp.wan_url}", "停止外网"
                time.sleep(0.1)
            
            return "外网启动失败", "启动外网"
        
        test_btn.click(
            fn=test_nat_connection,
            inputs=[enable_nat, nat_type, nat_server, nat_username, nat_password, nat_ssh_port, nat_token, nat_port, nat_remote_port, nat_custom_domain],
            outputs=[status_text, test_btn]
        ) 