import os
import threading
import json
import regex as re
from concurrent.futures import ThreadPoolExecutor
from app.ui.tabs.character_config import load_config_files
from loguru import logger
import shutil
from pathlib import Path
from app.utils.character_recognition import CharacterRecognition
from app.model.audiobook import AudioScript as Params
import time
import gradio as gr
import asyncio
from queue import Queue
from .indextts_vllm import get_tts_wav2,QwenEmotion
from scipy.io import wavfile
from app.utils.pack_audio import speed_change
from app.services.speaker import SpeakerManager
from pydub import AudioSegment

# 书籍存储目录
BOOKS_DIR = Path("data").absolute().as_posix()

# 确保目录存在
os.makedirs(BOOKS_DIR, exist_ok=True)


class AudiobookManager:
    def __new__(cls,*args,**kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):

            self.books = {}
            self.current_book = None
            self.load_books()
            self.processing_lock = threading.Lock()
            self.is_processing = False
            self.processing_thread = None
            self.processing_progress = 0
            self.tts_queue = Queue()
            self.emotion_queue  = Queue()
            self.write_queue = Queue()
            self.adjust_speed_queue = Queue()
            self.concat_queue = Queue()
            
            # 线程停止标志
            self.stop_event = threading.Event()
            
            # 线程引用
            self.emotion_thread = None
            self.tts_thread = None
            self.write_thread = None
            self.adjust_speed_thread = None
            self.monitor_thread = None
            self.concat_thread = None
            
            self.initialized = True
            self.loop = asyncio.new_event_loop()
            self.init_tasks_thread()
            logger.info("AudiobookManager 初始化完成")
    
    def init_tasks_thread(self):
        self.emotion_thread = threading.Thread(target=self.emotion_task)
        self.emotion_thread.start()
        
        # 启动异步TTS任务线程
        self.tts_thread = threading.Thread(target=self.run_async_tts_task)
        self.tts_thread.start()
        
        # 启动写入队列处理线程
        self.write_thread = threading.Thread(target=self.write_task)
        self.write_thread.start()
        
        # 启动速度调整队列处理线程
        self.adjust_speed_thread = threading.Thread(target=self.adjust_speed_task)
        self.adjust_speed_thread.start()
        
        # 启动线程监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_tasks)
        self.monitor_thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
        self.monitor_thread.start()

        # 合并并生成字幕线程
        self.concat_thread = threading.Thread(target=self.concat_task)
        self.concat_thread.start()
        
        logger.info("所有后台任务线程已启动")

    
    def update_book_info(self,id,info):
        """更新书籍信息"""
        self.books[id] = info
        with open(Path(BOOKS_DIR) / id / "book_info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=4)
    
    def concat_task(self):
        """合并并生成字幕任务"""
        while not self.stop_event.is_set():
            try:
                # 使用wait_for实现超时获取
                id,title = self.concat_queue.get()
                # logger.info(f"从合并队列获取到任务: {id}, {title}")
                if title is None:
                    break
                # 合并并生成字幕
                script = self.get_chapter_script(id,title)
                count = 0
                audio = []
                for item in script:
                    if 'audio_path' in item['extra']:
                        count += 1
                        audio.append([item['extra']['audio_path'],item['extra']['audio_length']])
                if len(audio) == len(script):
                    # 代表全生成完了，可以进行合成。
                    # todo: 实现合成逻辑
                    combine_audio = AudioSegment.silent(duration=0)
                    for audio_path,length in audio:
                        audio_segment = AudioSegment.from_file(audio_path)
                        combine_audio += audio_segment
                    output_path = Path("data") / id / "output" / f"{title}.ogg"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    # 导出合并后的音频
                    combine_audio.export(output_path, format="ogg")
                    info = self.books[id]
                    if info.get('output') is None:
                        info['output'] = {}
                    info['output'][title] = output_path.as_posix()
                    self.update_book_info(id,info)
                    self.processing_progress = 1.0
                else:
                    self.processing_progress = count / len(script)
                # logger.info(f"章节 {title} 合并完成，共 {count} 个音频文件")
            except Exception as e:
                logger.error(f"合并并生成字幕任务出错: {e}")

    def run_async_tts_task(self):
        """在新线程中运行异步TTS任务"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.tts_async_task())
        self.loop.close()

    async def tts_async_task(self):
        logger.info('TTS异步任务线程启动')
        while not self.stop_event.is_set():
            try:
                # 使用wait_for实现超时获取
                id,title,item = self.tts_queue.get()
                # logger.info(f"从TTS队列获取到任务: {id}, {title}, {item}")
                if item is None:
                    break
                spk_info = SpeakerManager().get_speaker(item.spk)
                if item.emotion in spk_info['emotion']:
                    ref_wav_path = spk_info['emotion'][item.emotion]['ref_wav_path']
                else:
                    ref_wav_path = spk_info.get("ref_wav_path")
                logger.debug(f"text: {item.text}, ref_wav_path: {ref_wav_path}, vec: {item.extra.get('vec',None)}")
                async for (sr,wav) in get_tts_wav2(item.text, 
                                                ref_wav_path, 
                                                vec=item.extra.get('vec',None),
                                                stream=False,
                                                format=None):
                    logger.debug(f"tts_result: sr={sr}")
        
                    
                    if item.speed != 1.0:
                        self.adjust_speed_queue.put((id,title,item.id, item.speed, sr, wav))
                    else:
                        self.write_queue.put((id,title,item.id,sr,wav))
                self.tts_queue.task_done()
            except asyncio.TimeoutError:
                # 超时，继续循环检查停止标志
                continue
            except Exception as e:
                logger.error(f"TTS异步任务出错: {e}")
        logger.info('TTS异步任务线程已停止')
    
    def emotion_task(self):
        logger.info('情感分析线程启动')
        # 用于计算vec
        while not self.stop_event.is_set():
            try:
                # 使用超时获取，避免无限阻塞
                book_id,title,item = self.emotion_queue.get(timeout=1.0)
                if item is None:
                    break
                # 计算vec
                (vec_dict,_) = QwenEmotion('').inference(item.original_text)
                vec = [v for k,v in vec_dict.items()]
                item.extra['vec'] = vec
        
                self.tts_queue.put((book_id, title, item)),
                
                self.emotion_queue.task_done()
            except:
                # 超时或其他异常，继续循环检查停止标志
                continue
        logger.info('情感分析线程已停止')

    
    def get_chapter_script(self,id,title):
        """获取章节脚本"""
        with open(Path("data") / id / 'scripts' / f"{title}.json", 'r', encoding='utf-8') as f:
            script = json.load(f)
        return script
    
    def save_chapter_script(self,id,title,script):
        """保存章节脚本"""
        with open(Path("data") / id / 'scripts' / f"{title}.json", 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=4)

    def write_task(self):
        """处理写入队列的任务"""
        logger.info('写入队列处理线程启动')
        while not self.stop_event.is_set():
            try:
                book_id,title,item_id, sr, wav = self.write_queue.get()
                # logger.info(f"从写入队列获取到任务: {book_id}, {title}, {item_id}, 采样率: {sr}, 音频长度: {len(wav)}")
                audio_path = Path("data") / book_id / 'audio' / title / f"{item_id}.wav"
                audio_path.parent.mkdir(parents=True, exist_ok=True)
                # 这里应该实现实际的音频写入逻辑
                # 例如: save_audio(item_id, sr, wav)
                wavfile.write(audio_path.as_posix(), sr, wav)
                # logger.debug(f"写入音频文件: {audio_path.as_posix()}")
                script = self.get_chapter_script(book_id,title)
                script[item_id]['extra']['audio_path'] = audio_path.as_posix()
                script[item_id]['extra']['audio_length'] = len(wav)
                self.save_chapter_script(book_id,title,script)
                self.concat_queue.put((book_id,title))
                
                self.write_queue.task_done()
            except Exception as e:
                logger.error(f"写入队列处理任务失败: {e}")
                # 超时或其他异常，继续循环检查停止标志
                continue
        logger.info('写入队列处理线程已停止')

    def adjust_speed_task(self):
        """处理速度调整队列的任务"""
        logger.info('速度调整队列处理线程启动')
        while not self.stop_event.is_set():
            try:
                # 使用超时获取，避免无限阻塞
                item = self.adjust_speed_queue.get()
                if item is None:
                    break
                
                book_id,title,item_id, speed, sr, wav = item
                wav = speed_change(wav, speed, sr)
                
                self.write_queue.put((book_id,title,item_id,sr,wav))
                
                logger.debug(f"调整音频速度: {item_id}, 速度: {speed}")
                
                self.adjust_speed_queue.task_done()
            except:
                # 超时或其他异常，继续循环检查停止标志
                continue
        logger.info('速度调整队列处理线程已停止')
    
    def stop_all_tasks(self):
        """停止所有后台任务线程"""
        logger.info("正在停止所有后台任务线程...")
        
        # 设置停止标志
        self.stop_event.set()
        
        # 向所有队列发送停止信号
        self.emotion_queue.put(None)
        self.tts_queue.put_nowait(None)  # 异步队列使用put_nowait
        self.write_queue.put(None)
        self.adjust_speed_queue.put(None)
        
        # 等待所有线程结束
        threads_to_join = [
            (self.emotion_thread, "情感分析线程"),
            (self.tts_thread, "TTS异步任务线程"),
            (self.write_thread, "写入队列处理线程"),
            (self.adjust_speed_thread, "速度调整队列处理线程"),
            (self.monitor_thread, "线程监控线程")
        ]
        
        for thread, name in threads_to_join:
            if thread and thread.is_alive():
                thread.join(timeout=5.0)  # 设置超时，避免无限等待
                if thread.is_alive():
                    logger.warning(f"{name}未能正常停止")
                else:
                    logger.info(f"{name}已正常停止")
        
        logger.info("所有后台任务线程已停止")
    
    def get_threads_status(self):
        """获取所有线程的状态"""
        threads_status = {
            "emotion_thread": {
                "name": "情感分析线程",
                "alive": self.emotion_thread.is_alive() if self.emotion_thread else False,
                "queue_size": self.emotion_queue.qsize()
            },
            "tts_thread": {
                "name": "TTS异步任务线程",
                "alive": self.tts_thread.is_alive() if self.tts_thread else False,
                "queue_size": self.tts_queue.qsize()
            },
            "write_thread": {
                "name": "写入队列处理线程",
                "alive": self.write_thread.is_alive() if self.write_thread else False,
                "queue_size": self.write_queue.qsize()
            },
            "adjust_speed_thread": {
                "name": "速度调整队列处理线程",
                "alive": self.adjust_speed_thread.is_alive() if self.adjust_speed_thread else False,
                "queue_size": self.adjust_speed_queue.qsize()
            }
        }
        return threads_status
    
    def log_queue_status(self):
        """记录队列状态"""
        status = self.get_threads_status()
        logger.info("===== 线程状态监控 =====")
        for thread_id, thread_info in status.items():
            logger.info(f"{thread_info['name']}: {'运行中' if thread_info['alive'] else '已停止'}, 队列大小: {thread_info['queue_size']}")
        logger.info("========================")
    
    def monitor_tasks(self):
        """监控所有后台任务线程的状态"""
        logger.info("线程监控线程已启动")
        monitor_interval = 60  # 每60秒监控一次
        
        while not self.stop_event.is_set():
            try:
                # 记录当前状态
                self.log_queue_status()
                
                # 检查是否有线程意外停止
                threads_to_check = [
                    (self.emotion_thread, "情感分析线程"),
                    (self.tts_thread, "TTS异步任务线程"),
                    (self.write_thread, "写入队列处理线程"),
                    (self.adjust_speed_thread, "速度调整队列处理线程")
                ]
                
                for thread, name in threads_to_check:
                    if thread and not thread.is_alive():
                        logger.warning(f"{name}意外停止，可能需要重启")
                
                # 等待下一次监控
                # 使用wait实现可中断的等待
                self.stop_event.wait(monitor_interval)
            except Exception as e:
                logger.error(f"线程监控过程中发生错误: {e}")
                # 发生错误时也等待一段时间再继续
                self.stop_event.wait(monitor_interval)
        
        logger.info("线程监控线程已停止")

    def load_books(self):
        """加载所有书籍信息"""
        self.books = {}
        for book_id in os.listdir(BOOKS_DIR):
            book_path = os.path.join(BOOKS_DIR, book_id)
            if os.path.isdir(book_path):
                info_file = os.path.join(book_path, "book_info.json")
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            book_info = json.load(f)
                            self.books[book_id] = book_info
                    except Exception as e:
                        logger.error(f"加载书籍信息错误 {book_id}: {e}")
    
    def get_book_list(self):
        """获取书籍列表"""
        self.load_books()
        books = [(book_info['title'], book_id) for book_id, book_info in self.books.items()]
        logger.debug(f'获取到 {len(books)} 部作品')
        return books
    
    def add_book(self, title, content, chapter_rules, role_config):
        """添加新书"""
        # 生成唯一ID
        book_id = title.replace(" ", "")
        book_path = os.path.join(BOOKS_DIR, book_id)
        os.makedirs(book_path, exist_ok=True)
        
        # 保存原文
        with open(os.path.join(book_path, "original.txt"), 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 切分章节
        chapters = self.split_chapters(content, chapter_rules)
        
        # 保存章节
        chapters_dir = os.path.join(book_path, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)

        _chapters = []
        
        for i, (chapter_title, chapter_content) in enumerate(chapters, 1):
            chapter_file = os.path.join(chapters_dir, f"{chapter_title}.txt")
            _chapters.append({
                "path": chapter_file,
                "title": chapter_title
            })
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(chapter_title + "\n\n" + chapter_content)
        
        

        # 保存书籍信息
        book_info = {
            "title": title,
            "author": "未知",
            "added_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chapter_count": len(chapters),
            "chapters": _chapters,
            "role_config": role_config,
            "chapter_rules": chapter_rules,
            "processed_chapters": {}
        }
        
        with open(os.path.join(book_path, "book_info.json"), 'w', encoding='utf-8') as f:
            json.dump(book_info, f, ensure_ascii=False, indent=2)
        
        self.books[book_id] = book_info
        return book_id
    
    def split_chapters(self, content, rules=r"(第[零一二三四五六七八九十百千万0-9]+(?:章|集) \s*[^\n]+)"):
        """根据规则切分章节"""
        chapters = []

        splits = re.split(rules, content)
        if splits[0] == "":
            splits = splits[1:]
        for i in range(0, len(splits), 2):
            if i+1 < len(splits):
                chapter_title = re.sub("\W+", "", splits[i].strip())
                # logger.debug(f"chapter_title: {chapter_title}")z
                chapter_content = splits[i + 1].strip()
                # logger.debug(f"chapter_content: {chapter_content}")
                chapters.append((chapter_title, chapter_content))
        return chapters
    
    def get_book_info(self, book_id):
        """获取书籍详情"""
        book_info = self.books.get(book_id)
        # logger.debug(f'获取到书籍 {book_id} 详情 {book_info}')
        return book_info
    
    def delete_book(self, book_id):
        """删除书籍"""
        if book_id in self.books:
            book_path = os.path.join(BOOKS_DIR, book_id)
            if os.path.exists(book_path):
                shutil.rmtree(book_path)
            del self.books[book_id]
            return True
        return False
    
    def process_chapter(self, book_id, chapter_title, chapter_path):
        """处理单个章节（生成音频）"""
        # 这里是占位实现，实际应该调用TTS模型
        book_info = self.get_book_info(book_id)
        if not book_info:
            return False
        
        # todo: 调用TTS模型生成音频
        # 1. 判断是否有画本存在
        script_path = Path(chapter_path.replace("chapters", "scripts")).with_suffix(".json")
        if not script_path.exists():
            self.audiobook_script(book_id, chapter_title)
        
        # 2. 读取画本
        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        # 2.1 读取角色配置
        role_config = book_info['role_config']
        with open(Path("configs/listening").joinpath(role_config).with_suffix(".json"), 'r', encoding='utf-8') as f:
            role_data = json.load(f)
        
        

        # 3. 格式化成tts需要的参数
        role_item = {}
        for script_item in script_data:
            item = Params(**script_item)
            if role_item.get(item.name) is None:
                role_item[item.name] = []
            role_item[item.name].append(item)

        # 4. 放进asyncio.Queue
        for item in role_item:
            for task in role_item[item]:
                if task.name != "旁白":
                    # logger.debug(f"添加到情感队列: {task}")
                    self.emotion_queue.put((book_id,chapter_title,task))
                else:
                    # logger.debug(f"添加到TTS队列: {task}")
                    
                    self.tts_queue.put((book_id,chapter_title,task))
        # 标记为已处理
        # if 'processed_chapters' not in book_info:
        #     book_info['processed_chapters'] = {}
        # if chapter_title not in book_info['processed_chapters']:
        #     book_info['processed_chapters'][chapter_title] = False
        
        # 保存更新后的信息
        # book_path = os.path.join(BOOKS_DIR, book_id)
        # with open(os.path.join(book_path, "book_info.json"), 'w', encoding='utf-8') as f:
        #     json.dump(book_info, f, ensure_ascii=False, indent=2)
        
        return True
    
    def start_processing(self, book_id, chapter_title=None, update_status:gr.State=None, update_progress:gr.Progress=None):
        logger.info(f"开始处理书籍 {book_id} 章节 {chapter_title}")
        """开始处理书籍的所有章节"""
        with self.processing_lock:
            if self.is_processing:
                if update_status:
                    update_status.value = "正在处理中，请先停止当前任务"
                return False
            
            self.is_processing = True
            self.processing_progress = 0
        
        try:
            book_info = self.get_book_info(book_id)
            if not book_info:
                if update_status:
                    update_status.value = "书籍信息不存在"
                return False
            
            chapter_info = None
            if chapter_title:
                for i in book_info.get("chapters",[]):
                    if i.get("title") == chapter_title:
                        chapter_info = i
                        break
            if chapter_info is None:
                if update_status:
                    update_status.value = "章节信息不存在"
                return False
            
            chapter_title = chapter_info['title']
            chapter_path =  chapter_info['path']
            success = self.process_chapter(
                book_id, 
                chapter_title,
                chapter_path
            )
            
            # total_chapters = len(book_info['chapters'])
            # processed_count = len(book_info.get('processed_chapters', []))
            
            # if update_status:
            #     update_status.value = f"开始处理，共 {total_chapters} 章，已处理 {processed_count} 章"
            #     logger.info(f"开始处理，共 {total_chapters} 章，已处理 {processed_count} 章")
            
            # 获取未处理的章节
            # unprocessed_chapters = {}
            # for i in book_info.get("chapters",[]):
            #     if i.get("title") not in book_info.get('processed_chapters',{}).keys():
            #         unprocessed_chapters[i.get("title")] = i
            # # 判断字典是否为空
            # if not unprocessed_chapters:
            #     if update_status:
            #         logger.info("所有章节已处理完成")
            #         update_status.value = "所有章节已处理完成"
            #     return True
            
            # 处理每个章节
            if chapter_title is None:
                unprocessed_chapters = {}
                for i, chapter_title in update_progress.tqdm(enumerate(unprocessed_chapters.keys())):
                    if not self.is_processing:
                        if update_status:
                            update_status.value = "处理已停止"
                        return False
                    
                    chapter_title = unprocessed_chapters[chapter_title]['title']
                    chapter_path =  unprocessed_chapters[chapter_title]['path']
                    if update_status:
                        update_status.value = f"正在处理第 {i + 1} 章: {chapter_title}"
                        logger.info(f"正在处理第 {i + 1} 章: {chapter_title}")
                    
                    # 处理当前章节
                    success = self.process_chapter(
                        book_id, 
                        chapter_title,
                        chapter_path
                    )
                    
                    if not success:
                        break
                
                if self.is_processing:
                    self.processing_progress = 100
                    return True
                else:
                    return False
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"处理书籍 {book_id} 时出错: {e}")
            if update_status:
                update_status.value = f"处理书籍 {book_id} 时出错: {e}"
            return False
        finally:
            with self.processing_lock:
                self.is_processing = False
    
    def _update_chapter_progress(self, chapter_progress, chapter_index, total_unprocessed, update_progress):
        """更新章节进度"""
        # 计算全局进度
        base_progress = chapter_index / total_unprocessed * 100
        chapter_weight = 100 / total_unprocessed
        global_progress = base_progress + (chapter_progress / 100) * chapter_weight
        self.processing_progress = global_progress
        if update_progress:
            update_progress(global_progress)
    
    def stop_processing(self):
        """停止处理"""
        with self.processing_lock:
            self.is_processing = False
        return "处理已停止"
    
    def is_currently_processing(self):
        """检查是否正在处理"""
        with self.processing_lock:
            return self.is_processing

    
    def get_tags_data(self,config):
        tags_data = {"dialogue": {"defaultRole": [{"id": "默认对话", "value": "dialogue"}],
                                        "defaultFlag": [{"id": "默认对话", "value": True}],
                                        "role": []}, "narration": {}}
        for k, v in config.items():
            if k == "旁白" or k == "默认对话":
                continue
            tags_data["dialogue"]["defaultRole"].append(
                {"id": k, "value": v.get("tag", 'dialogue')})
            tags_data["dialogue"]["defaultFlag"].append({"id": k, "value": False})
            tags_data["dialogue"]["role"].append({"id": k, "value": v.get("regex", k)})

        return tags_data


    def audiobook_script(self, book_id, chapter_title):
        logger.info(f"获取章节画本：{book_id} {chapter_title}")
        """获取章节音频脚本"""
        book_info = self.get_book_info(book_id)
        if not book_info :
            return "书籍信息不存在"
        chapter_path = None
        for chapter in book_info['chapters']:
            if chapter.get("title") == chapter_title:
                chapter_path = chapter.get("path")
                break
        if chapter_path is None:
            return "章节不存在"
        # 读取画本需要的角色规则
        role_config = {}
        with open(Path("configs/listening").joinpath(book_info['role_config']), 'r', encoding='utf-8') as f:
            role_config = json.load(f)
            tags_data = self.get_tags_data(role_config)

        script = []
        # logger.info(f"角色规则：{tags_data}")
        c = CharacterRecognition(tags_data)
        # 读取章节内容
        id = 0 
        with open(chapter_path, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                if i.strip() == "":
                    continue
                for s in c.handle_text(i.strip()):
                    if s['tag'] == "narration":
                        role = "旁白"
                    elif s['tag'] == "dialogue" and not s.get("id"):
                        role = "默认对话"
                    else:
                        role = s["id"]
                    
                    params = Params(id=id,text=s['text'], name=role,original_text=i.strip(),**role_config.get(role, {}))
                    script.append(params.model_dump())
                    id += 1
        script_path = Path(chapter_path.replace("chapters", "scripts"))
        script_path.parent.mkdir(parents=True, exist_ok=True)

        with open(script_path.with_suffix('.json'), 'w+', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=4)
        return script


if __name__=="__main__":
    audiobook_manager = AudiobookManager()
    