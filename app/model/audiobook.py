from pydantic import BaseModel
from fastapi import Query


class AudioScript(BaseModel):
    id: int = Query(0, description="id", title="id")
    text: str = Query("", description="text内容")
    spk: str = Query("", description="发音人", title="发音人")
    emotion: str = Query("", description="情感", title="情感")
    speed: float = Query(1.0, description="语速", title="语速")
    text_lang: str = Query("", description="文本语言", title="文本语言")
    name: str = Query("", description="角色", title="角色")
    original_text: str = Query("", description="原始文本", title="原始文本")
    extra: dict  = Query({}, description="额外信息", title="额外信息")
