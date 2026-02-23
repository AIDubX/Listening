import gradio as gr
import requests
from datetime import datetime
from app.config import settings

def fetch_latest_books():
    """获取最新推书信息"""
    try:
        response = requests.get(f"https://modelscope.cn/models/AIListening/tweet/resolve/master/book.json")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching books: {e}")
        return None

def create_book_tab():
    """创建推书标签页"""
    with gr.Column():
        # 顶部标题和刷新按钮
        with gr.Row(elem_classes=["header-row"]):
            with gr.Column(scale=3):
                gr.Markdown("## 📚 今日推荐")
            # 在线网盘
            with gr.Column(scale=1):
                doc_btn = gr.Button(
                    "📚 在线文档",
                    variant="secondary",
                    elem_classes=["book-link-button"],
                    link="https://yxi3w0wmgv2.feishu.cn/wiki/Xu6ewRvXYiljTUknOVqcoGsan3d"  # Will be updated dynamically
                )
            with gr.Column(scale=1):
                doc_btn = gr.Button(
                    "💾 网盘更新",
                    variant="secondary",
                    elem_classes=["book-link-button"],
                    link="https://pan.quark.cn/s/c0d85687acb3"  # Will be updated dynamically
                )
            with gr.Column(scale=1):
                rss_btn = gr.Button(
                    "🔔 添加到阅读",
                    variant="primary",
                    elem_classes=["action-button"],
                    link="/import/legado/redirect/rss"
                )
        # 日期显示
        date_text = gr.Textbox(
            label="推荐日期",
            interactive=False,
            container=False,
            show_label=False,
            elem_classes=["date-text"]
        )
        
        # 书籍展示区
        book_boxes = []
        for i in range(2):
            with gr.Group(elem_classes=["book-card"]):
                with gr.Row():
                    with gr.Column(scale=1):
                        platform = gr.Textbox(
                            label="平台",
                            interactive=False,
                            container=True,
                            elem_classes=["platform-tag"]
                        )
                    with gr.Column(scale=3):
                        name = gr.Textbox(
                            label="书名",
                            interactive=False,
                            container=True,
                            elem_classes=["book-title"]
                        )
                description = gr.Textbox(
                    label="简介",
                    interactive=False,
                    container=True,
                    lines=3,
                    elem_classes=["book-description"]
                )
                link = gr.Button(
                    "🔗 查看详情",
                    variant="secondary",
                    elem_classes=["book-link-button"],
                    link=""  # Will be updated dynamically
                )
                book_boxes.append({"platform": platform, "name": name, "description": description, "link": link})

        def update_books():
            data = fetch_latest_books()
            if not data:
                return [gr.update(value="")] * 7 + [gr.update(link="")] * 2  # Updated for button links
            
            date_str = datetime.strptime(data["data"], "%Y-%m-%d").strftime("%Y年%m月%d日")
            results = [gr.update(value=f"📅 {date_str}")]
            
            for i, book in enumerate(data["book"]):
                if i < len(book_boxes):
                    results.extend([
                        gr.update(value=book["platform"]),
                        gr.update(value=book["name"]),
                        gr.update(value=book["description"]),
                        gr.update(link=book.get("link", ""))  # Update button link
                    ])
            
            return results

        
        return update_books, [date_text] + [component for box in book_boxes for component in [box["platform"], box["name"], box["description"], box["link"]]]

# 添加自定义CSS样式
CUSTOM_CSS = """
/* 响应式布局基础设置 */
@media (max-width: 768px) {
    .header-row {
        flex-direction: column;
        align-items: stretch !important;
        gap: 8px !important;
    }
    .action-button {
        margin-top: 0 !important;
    }
}

.header-row {
    margin-bottom: 0.5rem;
    gap: 8px;
}

.action-button {
    width: 100%;
    margin: 0 !important;
}

.date-text {
    color: #666;
    font-size: 0.9em;
    text-align: center;
    margin: 4px 0 8px 0;
    padding: 0;
}

.book-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

.book-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 3px 6px rgba(0,0,0,0.15);
}

.platform-tag {
    background-color: #e8f0fe;
    border-radius: 4px;
    padding: 4px 8px;
    color: #1a73e8;
    font-weight: 600;
    text-align: center;
    border: 1px solid #1a73e8;
    font-size: 0.9em;
}

.book-title {
    font-size: 1.1em;
    font-weight: bold;
    color: #2c3e50;
    margin: 4px 0;
    padding: 4px 0;
}

.book-description {
    color: #5f6368;
    line-height: 1.5;
    font-size: 0.9em;
    background-color: #fafafa;
    border-radius: 4px;
    padding: 8px !important;
    margin-top: 4px;
}

.book-link-button {
    margin-top: 8px !important;
    width: auto !important;
    min-width: 120px;
    font-size: 0.9em !important;
    padding: 2px 12px !important;
    height: 32px !important;
    border: 1px solid #1a73e8 !important;
    background-color: white !important;
    color: #1a73e8 !important;
}

.book-link-button:hover {
    background-color: #f8f9fa !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* 移除textbox的默认边框 */
.book-title, .book-description, .platform-tag {
    border: none !important;
    background: transparent;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
    width: 4px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 2px;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
""" 