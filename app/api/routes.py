from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.speaker import SpeakerManager
from app.model.api import *
from app.services.tts import TTS
from app.api.book import router as book_router
import io
import wave
from fastapi.responses import StreamingResponse,RedirectResponse
import time
from loguru import logger
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.config import settings
from fastapi import status
import json
import base64
from app.utils.pinyin.multitone import MultiToneManager
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    # 在这里添加你的认证逻辑
    correct_username = settings.AUTH_USERNAME
    correct_password = settings.AUTH_PASSWORD

    if (
            credentials.username != correct_username
            or credentials.password != correct_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
dependencies = None

if settings.ENABLE_AUTH:
    dependencies = [Depends(authenticate)]

router = APIRouter(prefix="", tags=["api"], dependencies=dependencies)

# Include book router
router.include_router(book_router, prefix="/api", tags=["books"])


@router.get("/config")
async def get_config():
    """获取应用配置信息"""
    speaker_manager = SpeakerManager()
    speakers = speaker_manager.get_speakers()
    return {"message": "Hello World", "speaker": speakers}


@router.post("/")
async def tts(params: Params):
    """TTS合成"""
    _tts = TTS()
    return StreamingResponse(
        _tts.infer(params),
        media_type=f"audio/{params.format.value}",
        headers={"Cache-Control": "no-cache"}
    )

@router.get("/")
async def tts2(params: Params = Depends(Params)):
    if params.text == "" or params.text == None:
        return RedirectResponse(url="/ui")
    """TTS合成"""
    _tts = TTS()
    return StreamingResponse(
        _tts.infer(params),
        media_type=f"audio/ogg",
        headers={"Cache-Control": "no-cache"}
    )
    

def listening_handle(params: ReaderRequest):
    _tts = TTS()
    try:
        return StreamingResponse(
            _tts.listening(params),
            media_type="audio/ogg",
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"发生错误: {e} , {params}")
        return StreamingResponse(
            b'\x00\x00\x00\x00',
            media_type="audio/ogg",
            headers={"Cache-Control": "no-cache"}
        )

@router.get("/listening")
async def listening(params: ReaderRequest = Depends(ReaderRequest)):
    """获取听书信息"""
    return listening_handle(params)


@router.post("/listening")
async def listening_post(params: ReaderRequest):
    """获取听书信息"""
    return listening_handle(params)


@router.get("/import/legado/tts")
async def import_legado_tts(request: Request, params: ImportLegadoTTSRequest = Depends(ImportLegadoTTSRequest)):
    """导入Legado TTS"""
    scheme = request.url.scheme
    return {
            "contentType": "audio/ogg",
            "header": json.dumps({"Authorization": f"Basic {base64.b64encode(f'{settings.AUTH_USERNAME}:{settings.AUTH_PASSWORD}'.encode()).decode()}"}),
            "id": time.time(),
            "lastUpdateTime": time.time(),
            "name": f"AI听书({params.id})",
            "url": f"{scheme}://{request.headers.get('host')}/listening,"
            r'{"method":"POST","body":{"text":"{{speakText}}","id":"'+params.id+'"}}',
            "concurrentRate": "1"
        }
    
@router.get("/import/legado/rss")
async def import_legado_rss(request: Request):
    scheme = request.url.scheme
    """导入Legado RSS"""
    return [{
        "articleStyle": 0,
        "customOrder": 0,
        "enableJs": True,
        "enabled": True,
        "enabledCookieJar": False,
        "lastUpdateTime": 0,
        "loadWithBaseUrl": True,
        "singleUrl": True,
        "sourceIcon": "",
        "sourceName": "AI听书",
        "sourceUrl": f"{scheme}://{request.headers.get('host')}/ui"
    }]

@router.get("/import/legado/redirect/rss")
async def import_redirect_rss(request: Request):
    scheme = request.url.scheme
    """导入重定向"""
    return RedirectResponse(url=f'yuedu://rsssource/importonline?src={scheme}://{request.headers.get("host")}/import/legado/rss')

@router.get("/import/legado/redirect/tts")
async def import_redirect_tts(request: Request,params: ImportLegadoTTSRequest = Depends(ImportLegadoTTSRequest)):
    scheme = request.url.scheme
    """导入重定向"""
    if settings.ENABLE_AUTH:
        return RedirectResponse(url=f'legado://import/httpTTS?src={scheme}://{settings.AUTH_USERNAME}:{settings.AUTH_PASSWORD}@{request.headers.get("host")}/import/legado/tts?id={params.id}')
    else:
        return RedirectResponse(url=f'legado://import/httpTTS?src={scheme}://{request.headers.get("host")}/import/legado/tts?id={params.id}')

class MultiphonemeRequest(BaseModel):
    data: dict
    machine_id: str
    product_id: str
    phoneme: dict

@router.post("/multiphoneme")
async def multiphoneme(params: MultiphonemeRequest):
    """多音字更新"""
    # logger.info(f"多音字更新: {params}")
    MultiToneManager().load(params.data,params.phoneme)
    return {"message": "多音字更新成功"}

