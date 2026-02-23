import gradio as gr
from app.config import settings
from app.services.tts_service import (
    text_to_speech, 
    get_available_voices, 
    get_voice_emotions,
    get_default_emotion_for_voice,
    dict_language
)


def create_speech_synthesis_tab():
    """创建语音合成选项卡"""
    with gr.Column():
        text_input = gr.Textbox(
            label="输入文本",
            placeholder="请输入要转换为语音的文本...",
            value="喜欢听书的朋友千万不能错过，老牌听书开发者出品，值得收藏使用。",
            lines=5
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                # 使用动态获取的音色列表
                available_voices = get_available_voices()
                default_voice = available_voices[0] if available_voices else settings.DEFAULT_VOICE
                
                voice_dropdown = gr.Dropdown(
                    available_voices,
                    label="选择音色",
                    value=default_voice
                )
            
            with gr.Column(scale=1):
                # 初始情感列表基于默认音色
                default_emotions = get_voice_emotions(default_voice)
                default_emotion = get_default_emotion_for_voice(default_voice)
                
                emotion_dropdown = gr.Dropdown(
                    default_emotions,
                    label="选择情感",
                    value=default_emotion
                )
        
        with gr.Row():
            with gr.Column(scale=1):
                speed_slider = gr.Slider(
                    minimum=0.5,
                    maximum=2.0,
                    value=1.0,
                    step=0.1,
                    label="语速"
                )
            
            with gr.Column(scale=1):
                language = gr.Dropdown(
                    label="语言",
                    choices=list(dict_language.keys()),
                    # value=dict_language.keys()[0],
                )
        
        
        with gr.Row():
            synthesize_btn = gr.Button("合成语音", variant="primary")
            refresh_btn = gr.Button("刷新音色")
            clear_btn = gr.Button("清除")
        
        output = gr.Audio(
            label="合成结果",
            type="filepath"
        )
        text_output = gr.Text(label="状态")
        
        # 当音色改变时，更新情感下拉菜单
        def update_emotions(voice):
            emotions = get_voice_emotions(voice)
            default_emotion = get_default_emotion_for_voice(voice)
            return {emotion_dropdown: gr.update(choices=emotions, value=default_emotion)}
        
        voice_dropdown.change(
            fn=update_emotions,
            inputs=[voice_dropdown],
            outputs=[emotion_dropdown]
        )
        
        # 刷新音色列表
        def refresh_voices():
            new_voices = get_available_voices()
            current_voice = voice_dropdown.value
            if current_voice not in new_voices:
                current_voice = new_voices[0] if new_voices else settings.DEFAULT_VOICE
            return {voice_dropdown: gr.update(choices=new_voices, value=current_voice)}
        
        refresh_btn.click(
            fn=refresh_voices,
            inputs=None,
            outputs=[voice_dropdown]
        ).then(
            fn=lambda: "音色列表已更新",
            inputs=None,
            outputs=[text_output]
        )
        
        synthesize_btn.click(
            fn=text_to_speech,
            inputs=[text_input, voice_dropdown, speed_slider, language, emotion_dropdown],
            outputs=[output]
        ).then(
            fn=lambda: "语音合成完成",
            inputs=None,
            outputs=[text_output]
        )
        
        # 更新清除函数，使用动态获取的默认值
        def clear_inputs():
            default_voice = available_voices[0] if available_voices else settings.DEFAULT_VOICE
            default_emotion = get_default_emotion_for_voice(default_voice)
            return ("", default_voice, 1.0, 1.0, default_emotion, None, "")
        
        clear_btn.click(
            fn=clear_inputs,
            inputs=None,
            outputs=[text_input, voice_dropdown, speed_slider, language, emotion_dropdown, output, text_output]
        )
    
    return [text_input, voice_dropdown, emotion_dropdown, speed_slider, language, synthesize_btn, output, text_output] 