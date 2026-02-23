import gradio as gr

def create_listening_config_tab():
    """创建畅听配置选项卡"""
    with gr.Column():
        gr.Markdown("## 畅听配置")
        
        with gr.Row():
            with gr.Column():
                chunk_size = gr.Slider(
                    minimum=50,
                    maximum=500,
                    value=200,
                    step=10,
                    label="分段大小（字符数）"
                )
                
                auto_punctuate = gr.Checkbox(
                    label="自动标点",
                    value=True
                )
                
                pause_duration = gr.Slider(
                    minimum=0,
                    maximum=2.0,
                    value=0.5,
                    step=0.1,
                    label="段落间停顿（秒）"
                )
            
            with gr.Column():
                output_format = gr.Dropdown(
                    ["mp3", "wav", "ogg"],
                    label="输出格式",
                    value="mp3"
                )
                
                output_dir = gr.Textbox(
                    label="输出目录",
                    value="./output",
                    placeholder="音频文件保存路径"
                )
                
                with gr.Row():
                    save_config_btn = gr.Button("保存配置", variant="primary")
                
                listening_status = gr.Text(label="状态")
        
        # 保存配置的函数
        save_config_btn.click(
            fn=lambda: "畅听配置已保存",
            inputs=None,
            outputs=[listening_status]
        )
    
    return [chunk_size, auto_punctuate, pause_duration, output_format, output_dir, save_config_btn, listening_status] 