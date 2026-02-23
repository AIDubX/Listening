import gradio as gr
from loguru import logger
from app.config import settings
from app.services.tts_service import (
    get_available_voices,
    get_voice_emotions,
    get_default_emotion_for_voice,
    get_reference_text,
    get_reference_audio_path,
    refresh_speakers,
    speaker_manager
)


def create_voice_config_tab():
    """创建音色配置选项卡"""
    with gr.Column():
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 音色管理")

                with gr.Row():
                    voice_delete_btn = gr.Button("删除发音人", variant="stop",scale=1)
                    delete_emotion_btn = gr.Button("删除情感", variant="stop",scale=1)
                # 使用动态获取的音色列表
                with gr.Row():
                    voice_name = gr.Textbox(label="音色名称",scale=2)
                    emotion_value = gr.Textbox(label="情感名称",value="正常",scale=2)
                    
                # 上传音频的控件
                upload_audio = gr.Audio(label="上传情感音频", type="filepath")
                ref_text = gr.Textbox(label="音频文本")
                ref_text_lang = gr.Textbox(label="音频文本语言(zh/ja/en)",placeholder="",value="zh")
                
                voice_create_btn = gr.Button("新增", variant="primary")
                status_text = gr.Textbox(label="状态")

            with gr.Column(scale=2):
                gr.Markdown("### 音色详情")
                with gr.Row():
                    available_voices = get_available_voices()
                    default_voice = available_voices[0] if available_voices else settings.DEFAULT_VOICE
                    voice_list = gr.Dropdown(
                        available_voices,
                        label="选择要配置的音色",
                        value=default_voice
                    )
                    refresh_btn = gr.Button("刷新音色列表", variant="secondary")
                
                    # 音色情感列表
                emotion_list = gr.Radio(
                    choices=get_voice_emotions(default_voice),
                    label="情感列表",
                    value=get_default_emotion_for_voice(default_voice),
                    interactive=True
                )
                
                # 参考文本
                reference_text = gr.Textbox(
                    label="参考文本",
                    value=get_reference_text(default_voice),
                    lines=2,
                    interactive=False
                )
                
                # 参考音频
                reference_audio = gr.Audio(
                    label="参考音频",
                    value=get_reference_audio_path(default_voice),
                    type="filepath",
                    interactive=False
                )
        
        # 刷新音色列表
        def refresh_voice_list():
            voices = refresh_speakers()
            default_voice = voices[0] if len(voices) > 0 else settings.DEFAULT_VOICE
            emotions = get_voice_emotions(default_voice)
            default_emotion = get_default_emotion_for_voice(default_voice)
            ref_text = get_reference_text(default_voice)
            ref_audio = get_reference_audio_path(default_voice)
            
            return {
                voice_list: gr.update(choices=voices, value=default_voice),
                emotion_list: gr.update(choices=emotions, value=default_emotion),
                reference_text: ref_text,
                reference_audio: ref_audio,
                voice_name: default_voice
            }
        
        refresh_btn.click(
            fn=refresh_voice_list,
            inputs=[],
            outputs=[voice_list, emotion_list, reference_text, reference_audio, voice_name]
        )
        
        # 当选择音色变化时，更新音色详情和参考音频
        def update_voice_details(voice):
            if isinstance(voice,list):
                logger.error(f"voice_list: {voice}")
                voice = voice[0]
            emotions = get_voice_emotions(voice)
            default_emotion = get_default_emotion_for_voice(voice)
            ref_text = get_reference_text(voice)
            ref_audio = get_reference_audio_path(voice)
            
            return {
                emotion_list: gr.update(choices=emotions, value=default_emotion),
                emotion_value: default_emotion,
                reference_text: ref_text,
                reference_audio: ref_audio,
                voice_name: voice
            }
        
        voice_list.change(
            fn=update_voice_details,
            inputs=[voice_list],
            outputs=[emotion_list, emotion_value,reference_text, reference_audio, voice_name]
        )

    
        # 当选择情感变化时，更新参考音频和文本
        def update_emotion_details(voice, emotion):
            ref_text = get_reference_text(voice, emotion)
            ref_audio = get_reference_audio_path(voice, emotion)
            
            return {
                emotion_value: emotion,
                reference_text: ref_text,
                reference_audio: ref_audio
            }
        
        emotion_list.change(
            fn=update_emotion_details,
            inputs=[voice_list, emotion_list],
            outputs=[emotion_value,reference_text, reference_audio]
        )
         # 事件
        def create_speaker_and_notify(name, emotion, ref_wav_path, text, text_lang):
            gr.update(interactive=False)
            result = speaker_manager.create_speaker(name, emotion, ref_wav_path, text, text_lang)
            # 显示通知
            gr.Info(f"成功新增音色: {name}，请刷新音色列表")
            gr.update(interactive=True)
            return result
            
        voice_create_btn.click(
            fn=create_speaker_and_notify,
            inputs=[voice_name,emotion_value,upload_audio,ref_text,ref_text_lang],
            outputs=status_text
        )

        voice_delete_btn.click(
            fn=lambda name: speaker_manager.delete_speaker(name),
            inputs=voice_name,
            outputs=status_text
        )

        delete_emotion_btn.click(
            fn=lambda name,emotion: speaker_manager.delete_emotion(name,emotion),
            inputs=[voice_name,emotion_value],
            outputs=status_text
        )

    return [voice_list, voice_name]