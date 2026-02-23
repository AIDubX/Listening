import os
import json
import regex as re
import shutil
from pathlib import Path
import gradio as gr
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from tqdm.std import tqdm
from .character_config import load_config_files
from loguru import logger
from app.services.ab import AudiobookManager, BOOKS_DIR
import asyncio

# 创建管理器实例
audiobook_manager = AudiobookManager()

def create_audiobook_tab():

    current_process_message = gr.State("")

        
    # 书籍管理区域
    with gr.Row():
        with gr.Column(scale=1):
            # 书籍列表
            gr.Markdown("#### 有声列表")
            book_list = gr.Dropdown(
                choices=audiobook_manager.get_book_list(),
                label="选择有声作品",
                interactive=True
            )
            
            with gr.Row():
                refresh_books_btn = gr.Button("刷新列表")
                delete_book_btn = gr.Button("删除作品")
            
            # 添加书籍区域
            gr.Markdown("#### 添加新作品")
            book_title = gr.Textbox(label="作品标题", placeholder="请输入作品标题")
            
            # 文件上传
            with gr.Tabs():
                with gr.TabItem("文件上传"):
                    file_upload = gr.File(label="上传TXT文件", file_types=[".txt"])
                with gr.TabItem("文件路径"):
                    file_path = gr.Textbox(label="输入文件路径", placeholder="请输入TXT文件的完整路径")
            
            chapter_rules = gr.Textbox(
                label="分章规则",
                value=r"(第[零一二三四五六七八九十百千万0-9]+(?:章|集) \s*[^\n]+)",
                lines=1
            )
            
            # 测试分章
            test_chapter_btn = gr.Button("测试分章")
            chapter_preview = gr.Textbox(label="章节预览", lines=5)
            
            # 角色配置
            gr.Markdown("#### 角色配置")
            role_configs = load_config_files()
            role_config = gr.Dropdown(
                choices=role_configs,
                label="选择角色配置",
                interactive=True
            )

            refresh_role_btn = gr.Button("刷新角色配置")

            
            # 添加书籍按钮
            add_book_btn = gr.Button("添加作品")
        
        with gr.Column(scale=2):
            # 章节列表和内容
            gr.Markdown("#### 章节列表")
            with gr.Row():
                chapter_list = gr.Dropdown(label="章节", interactive=True,scale=3)
                with gr.Column(scale=1):
                    refresh_chapters_btn = gr.Button("刷新章节",scale=1)
                with gr.Column(scale=1):
                    get_chapter_content = gr.Button("获取内容",scale=1)
                    get_chapter_preview = gr.Button("自动画本",scale=1)

            
            with gr.Tabs():
                with gr.TabItem("章节内容"):
                    chapter_content = gr.Textbox(label="内容", max_lines=15, lines=15)
                with gr.TabItem("画本预览"):
                    script_preview = gr.Textbox(label="预览", max_lines=15, lines=15)
                
                with gr.TabItem("章节音频"):
                    listen_preview = gr.Audio(label="试听", interactive=False)

                with gr.TabItem("成品下载"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            refresh_download_btn = gr.Button("刷新下载链接")
                            # 压缩下载全部
                            compress_download_btn = gr.Button("压缩下载全部")
                        download_status = gr.Textbox(label="下载状态", interactive=False, scale=2)
                    download_link = gr.File(label="下载链接", interactive=False)
            
            # 制作控制
            gr.Markdown("#### 制作控制")
            with gr.Row():
                start_process_btn = gr.Button("制作当前章节")
                all_chapters_btn = gr.Button("从当前章节制作")
                stop_process_btn = gr.Button("停止制作")
            
            # 进度显示
            process_progress = gr.Progress(track_tqdm=True)
            process_status = gr.Textbox(label="制作状态", interactive=False)
    
    # 事件处理
    def on_book_selected(book_id):
        """选择书籍时更新章节列表"""
        logger.debug(f'选择了作品 {book_id}')
        if not book_id:
            return gr.update(choices=[]), "", "未选择作品"
        
        book_info = audiobook_manager.get_book_info(book_id)
        if not book_info:
            return gr.update(choices=[]), "", "获取作品信息失败"
        
        chapters = [x['title'] for x in book_info['chapters']]
        logger.debug(f'获取到 {len(chapters)} 个章节')
        
        # 创建(label, value)元组列表
        chapter_choices = [(title, title) for title in chapters]
        
        # 返回更新后的章节列表和空的内容，并更新状态
        status_msg = f"已加载作品《{book_info['title']}》，共{len(chapters)}章"
        return gr.update(choices=chapter_choices, value=chapter_choices[0][1] if chapter_choices else None), "", status_msg
    
    def get_chapter_audio(book_id, chapter_title):
        """获取章节音频"""
        if not book_id or not chapter_title:
            return None
        
        book_info = audiobook_manager.get_book_info(book_id)
        if not book_info:
            return None
        
        # 检查是否有成品输出
        if 'output' not in book_info:
            return None
        
        output = book_info['output']
        if not output:
            return None
        
        # 返回当前章节的音频文件路径
        if chapter_title in output:
            audio_path = output[chapter_title]
            if audio_path and os.path.exists(audio_path):
                return audio_path
        
        return None
    
    def on_chapter_selected(book_id, chapter_title):
        """选择章节时显示内容"""
        if not book_id or not chapter_title:
            return "", None
        
        book_info = audiobook_manager.get_book_info(book_id)
        if not book_info:
            return "", None
        
        # 根据章节标题查找章节内容
        content = ""
        for chapter in book_info['chapters']:
            if chapter['title'] == chapter_title:
                try:
                    with open(chapter['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"读取章节内容错误: {e}")
                    content = f"读取章节内容错误: {str(e)}"
                break
        
        # 获取章节音频
        audio_path = get_chapter_audio(book_id, chapter_title)
        
        return content, audio_path
    
    def on_file_upload(file, path):
        """上传文件或输入路径时读取内容"""
        if file:
            try:
                return os.path.basename(file.name).split(".")[0]
            except Exception as e:
                print(f"读取文件错误: {e}")
                return ""
        elif path:
            try:
                return os.path.basename(path).split(".")[0]
            except Exception as e:
                print(f"处理路径错误: {e}")
                return ""
        return ""
    
    def test_chapter_splitting(file, path, rules):
        """测试章节切分"""
        if not rules:
            return "请设置分章规则"
        
        content = None
        if file:
            try:
                try:
                    with open(file.name, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file.name, "r", encoding="gbk") as f:
                        content = f.read()
            except Exception as e:
                return f"读取上传文件错误: {str(e)}"
        elif path:
            try:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(path, "r", encoding="gbk") as f:
                        content = f.read()
            except Exception as e:
                return f"读取路径文件错误: {str(e)}"
        else:
            return "请上传文件或输入文件路径"
        
        if content:
            try:
                chapters = audiobook_manager.split_chapters(content, rules)
                preview = "\n\n".join([f"[{i+1}] {title}" for i, (title, _) in enumerate(chapters[:10])])
                if len(chapters) > 10:
                    preview += f"\n\n... 共 {len(chapters)} 章"
                return preview
            except Exception as e:
                return f"分章测试失败: {str(e)}"
        
        return "无法获取文件内容"
    
    def add_new_book(title, file, path, rules, role_config_name):
        """添加新书籍"""
        if not title:
            return "请输入标题"
        
        if not file and not path:
            return "请上传文件或输入文件路径"
        
        content = None
        if file:
            try:
                try:
                    with open(file.name, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file.name, "r", encoding="gbk") as f:
                        content = f.read()
            except Exception as e:
                return f"读取上传文件错误: {str(e)}"
        elif path:
            try:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(path, "r", encoding="gbk") as f:
                        content = f.read()
            except Exception as e:
                return f"读取路径文件错误: {str(e)}"
        
        if not content:
            return "无法获取文件内容"
        
        try:
            # 加载角色配置
            book_id = audiobook_manager.add_book(title, content, rules, role_config_name)
            
            # 更新书籍列表
            return f"书籍添加成功！", gr.update(choices=audiobook_manager.get_book_list()), ""
        except Exception as e:
            return f"添加失败: {str(e)}", gr.update(choices=[]), ""
    
    def delete_selected_book(book_id):
        """删除选中的书籍"""
        if not book_id:
            return "请选择要删除的书籍", gr.update(choices=audiobook_manager.get_book_list())
        
        success = audiobook_manager.delete_book(book_id)
        if success:
            return "书籍删除成功", gr.update(choices=audiobook_manager.get_book_list())
        else:
            return "书籍删除失败", gr.update(choices=audiobook_manager.get_book_list())
    
    def get_book_script(book_id,chapter_index):
        """获取书籍脚本"""
        if not book_id:
            return gr.update(value="请选择作品")
        
        book_info = audiobook_manager.get_book_info(book_id)
        script = audiobook_manager.audiobook_script(book_id,chapter_index)
        if type(script) == str:
            return gr.update(value=script)
        s = ""
        for item in script:
            s += f'【{item["name"]}】{item["text"]}\n'
        return gr.update(value=s)
    
    def get_download_links(book_id,chapter_title):
        """获取成品下载链接"""
        if not book_id:
            return None
        
        book_info = audiobook_manager.get_book_info(book_id)
        if not book_info:
            return None
        
        # 检查是否有成品输出
        if 'output' not in book_info:
            return None
        
        output = book_info['output']
        if not output:
            return None
        
        # 返回第一个可用的音频文件路径
        if chapter_title in output:
            audio_path = output[chapter_title]
            if audio_path and os.path.exists(audio_path):
                return audio_path
        
        return None
    
    def refresh_download_links(book_id,chapter_title):
        """刷新下载链接"""
        if not book_id:
            return gr.update(value=None), "请选择作品"
        
        # 如果没有指定章节，尝试获取第一个章节
        if not chapter_title:
            book_info = audiobook_manager.get_book_info(book_id)
            if book_info and book_info.get('chapters'):
                chapter_title = book_info['chapters'][0].get('title')
        
        download_path = get_download_links(book_id,chapter_title)
        if download_path:
            return gr.update(value=download_path), f"已找到成品文件: {os.path.basename(download_path)}"
        else:
            return gr.update(value=None), "暂无可下载的成品文件"
    
    get_chapter_preview.click(
        fn=get_book_script,
        inputs=[book_list, chapter_list],
        outputs=[script_preview]
    )

    async def start_processing_all_chapters(book,title):
        book_info = audiobook_manager.get_book_info(book)
        if not book_info or 'chapters' not in book_info:
            return "书籍信息错误"
        progress = gr.Progress(track_tqdm=True)
        
        
        do_list = []
        flag = False
        ready = 0
        for index,chapter in enumerate(book_info['chapters']):
            if chapter.get('title') == title:
                flag = True
            else:
                ready += 1

            if flag:
                progress(index / len(book_info['chapters'])-1, desc=f"正在处理章节 {chapter.get('title')}")
                await start_processing(book, chapter.get('title'))
        
        return "所有章节处理完成"

    
    async def start_processing(book_id,chapter_title):
        logger.debug(f"开始处理书籍 {book_id} 章节 {chapter_title}")
        """开始制作有声书"""
        if not book_id:
            return "请选择作品"
       
        if audiobook_manager.is_currently_processing():
            return "正在处理中，请先停止当前任务"

        progress = gr.Progress()

        audiobook_manager.start_processing(
            book_id,
            chapter_title,
            update_status=current_process_message,
            update_progress=process_progress
        ),

        while audiobook_manager.processing_progress < 1.0:
            # logger.debug(f"当前处理进度: {audiobook_manager.processing_progress}")
            progress(audiobook_manager.processing_progress, desc=f"制作{chapter_title}")
            await asyncio.sleep(1)
        
        # 更新状态
        return "处理完成"
    
    # 绑定事件
    def on_book_change(book_id):
        """书籍变化时的处理函数"""
        chapter_update = on_book_selected(book_id)
        # 获取第一个章节的标题
        first_chapter_title = None
        if chapter_update[0].get('choices'):
            first_chapter_title = chapter_update[0].get('choices')[0][1]  # 获取元组的第二个元素
        
        download_update = refresh_download_links(book_id, first_chapter_title)
        
        # 获取第一个章节的音频
        audio_path = None
        if first_chapter_title:
            audio_path = get_chapter_audio(book_id, first_chapter_title)
        
        # 合并返回结果
        return chapter_update[0], chapter_update[1], chapter_update[2], download_update[0], download_update[1], audio_path
    
    async def compress_download(book_id):
        """压缩下载"""
        if not book_id:
            return "请选择作品"
        
        book_info = audiobook_manager.get_book_info(book_id)
        if not book_info or 'output' not in book_info:
            return None,"书籍信息错误"
        
        output = book_info['output']
        if not output:
            return None,"暂无可下载的成品文件"
        
        # 压缩所有章节的音频文件
        compress_file_list = []
        for chapter_title, audio_path in output.items():
            if audio_path and os.path.exists(audio_path):
                # 使用zip压缩
                compress_file_list.append(audio_path)
        
        if len(compress_file_list) == 0:
            return None,"暂无可下载的成品文件"

        zip_path = Path("data") / book_id / f"{book_id}.zip"
        if zip_path.exists():
            zip_path.unlink()


        # 使用异步压缩文件
        async def compress_file(filelist):
            """异步压缩文件，避免阻塞事件循环"""

            # 使用asyncio.to_thread在单独的线程中执行同步操作
            def _compress_sync():
                import zipfile
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in filelist:
                        zipf.write(file_path, os.path.basename(file_path))
                return zip_path
            
            # 在线程池中执行压缩操作
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _compress_sync)
        
        # 并发压缩所有文件
        await compress_file(compress_file_list)
        
        return gr.update(value=zip_path.as_posix()),"所有章节音频已压缩"

    book_list.change(
        fn=on_book_change,
        inputs=[book_list],
        outputs=[chapter_list, chapter_content, process_status, download_link, download_status, listen_preview]
    )
    refresh_chapters_btn.click(
        fn=on_book_change,
        inputs=[book_list],
        outputs=[chapter_list, chapter_content, process_status, download_link, download_status, listen_preview]
    )
    
    
    chapter_list.change(
        fn=on_chapter_selected,
        inputs=[book_list, chapter_list],
        outputs=[chapter_content, listen_preview]
    )

    get_chapter_content.click(
        fn=on_chapter_selected,
        inputs=[book_list, chapter_list],
        outputs=[chapter_content, listen_preview]
    )

    compress_download_btn.click(
        fn=compress_download,
        inputs=[book_list],
        outputs=[download_link,process_status]
    )
    
    # 初始化时自动加载第一个作品的章节
    def init_tab():
        books = audiobook_manager.get_book_list()
        if books:
            first_book_id = books[0][1]
            chapter_update = on_book_selected(first_book_id)
            # 获取第一个章节的标题
            first_chapter_title = None
            if chapter_update[0].get('choices'):
                first_chapter_title = chapter_update[0].get('choices')[0][1]  # 获取元组的第二个元素
            
            download_update = refresh_download_links(first_book_id, first_chapter_title)
            
            # 获取第一个章节的音频
            audio_path = None
            if first_chapter_title:
                audio_path = get_chapter_audio(first_book_id, first_chapter_title)
            
            # 合并返回结果
            return chapter_update[0], chapter_update[1], chapter_update[2], download_update[0], download_update[1], audio_path
        return gr.update(choices=[]), "", "", gr.update(value=None), "请选择作品", None
    
    # 应用初始化
    init_result = init_tab()
    if init_result:
        # logger.debug(init_result)
        chapter_list.choices = init_result[0].get('choices', [])
        chapter_list.value = init_result[0].get('value')
        chapter_content.value = init_result[1]
        download_link.value = init_result[3]
        download_status.value = init_result[4]
        listen_preview.value = init_result[5]
    
    file_upload.change(
        fn=on_file_upload,
        inputs=[file_upload, file_path],
        outputs=[book_title]
    )
    
    file_path.change(
        fn=on_file_upload,
        inputs=[file_upload, file_path],
        outputs=[book_title]
    )
    
    test_chapter_btn.click(
        fn=test_chapter_splitting,
        inputs=[file_upload, file_path, chapter_rules],
        outputs=[chapter_preview]
    )

    refresh_role_btn.click(
        fn=lambda: gr.update(choices=load_config_files()),
        inputs=[],
        outputs=[role_config]
    )
    
    add_book_btn.click(
        fn=add_new_book,
        inputs=[book_title, file_upload, file_path, chapter_rules, role_config],
        outputs=[process_status, book_list, book_title]
    )
    
    delete_book_btn.click(
        fn=delete_selected_book,
        inputs=[book_list],
        outputs=[process_status, book_list]
    )
    def value_change(msg):
        logger.info(msg)
        return msg
    
    start_process_btn.click(
        fn=start_processing,
        inputs=[book_list,chapter_list],
        outputs=[process_status]
    )

    all_chapters_btn.click(
        fn=start_processing_all_chapters,
        inputs=[book_list,chapter_list],
        outputs=[process_status]
    )
    
    current_process_message.change(
        fn=value_change,
        inputs=[current_process_message],
        outputs=[process_status]
    )

    stop_process_btn.click(
        fn=lambda: audiobook_manager.stop_processing(),
        inputs=[],
        outputs=[process_status]
    )
    
    refresh_books_btn.click(
        fn=lambda: gr.update(choices=audiobook_manager.get_book_list()),
        inputs=[],
        outputs=[book_list]
    )
    
    # 绑定刷新下载链接按钮事件
    refresh_download_btn.click(
        fn=refresh_download_links,
        inputs=[book_list, chapter_list],
        outputs=[download_link, download_status]
    )
    
 
    return [book_list, chapter_list, chapter_content, process_status, listen_preview]

# 导出函数供主界面调用
def get_tab():
    return create_audiobook_tab()