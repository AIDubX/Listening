import pyfiglet
from app.config import settings
print(pyfiglet.figlet_format("CyberWon",font="big"))
print(pyfiglet.figlet_format(f"V {settings.APP_VERSION}",font="contessa"))
from loguru import logger
import os,sys
from app.services.indextts_vllm import TTS



def wait_for_gpu():
    from vllm.utils import GiB_bytes, MemorySnapshot, memory_profiling
    import time
    while True:
        snapshot = MemorySnapshot()
        GiB = lambda b: round(b / GiB_bytes, 2)
        requested_memory = (snapshot.total_memory * 0.25)
        if snapshot.free_memory >= requested_memory:
            TTS()
            break
        logger.info(f"当前可用显存{GiB(snapshot.free_memory)}小于请求显存{GiB(requested_memory)}，等待...")
        time.sleep(3)

wait_for_gpu()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import os
from pathlib import Path
import secrets


from app.api.routes import router as api_router
from app.ui.gradio_interface import create_gradio_interface
from app.utils.network import get_ip_address

from app.utils.frp import FRP
from threading import Thread
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import warnings
warnings.filterwarnings("ignore", message=".*torch.*")
warnings.filterwarnings("ignore", message=".*numpy.*")
# todo: 增加调试模式，允许自定义加载


# 创建安全依赖
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """验证HTTP Basic认证"""
    if settings.ENABLE_AUTH:
        is_username_correct = secrets.compare_digest(credentials.username, settings.AUTH_USERNAME)
        is_password_correct = secrets.compare_digest(credentials.password, settings.AUTH_PASSWORD)
        
        if not (is_username_correct and is_password_correct):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
    return credentials.username


@asynccontextmanager
async def lifespan(app: FastAPI):
    # todo: 增加调试模式，允许自定义加载
    if not settings.DEBUG:
        TTS()
    # 启动时执行的代码
    temp_dir = Path("TEMP")
    temp_dir.mkdir(exist_ok=True)
    os.environ["GRADIO_TEMP_DIR"] = str(temp_dir.absolute())
    logger.info(f"请复制地址到浏览器中打开: http://{get_ip_address()}:{settings.SERVER_PORT}")
    yield

    frp.stop()

    # 关闭时执行的代码

def create_app() -> FastAPI:
    """
    应用工厂函数，创建并配置FastAPI应用
    """
    app = FastAPI(
        lifespan=lifespan,
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        summary=settings.APP_SUMMARY,
        terms_of_service=settings.TERMS_OF_SERVICE,
        contact=settings.CONTACT,
    )
     
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # 注册API路由
    app.include_router(api_router)

    # 创建并挂载Gradio界面
    demo = create_gradio_interface()
    
    # 如果启用了认证，添加认证依赖
    if settings.ENABLE_AUTH:
        app = gr.mount_gradio_app(app, demo, path=settings.GRADIO_PATH, auth=lambda username, password: (
            username == settings.AUTH_USERNAME and password == settings.AUTH_PASSWORD
        ))
    else:
        app = gr.mount_gradio_app(app, demo, path=settings.GRADIO_PATH)

    return app 
