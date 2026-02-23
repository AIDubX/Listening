import os,sys
sys.path.insert(0,".")
os.environ["GRADIO_TEMP_DIR"] = "TEMP"
import uvicorn
import logging
from loguru import logger

import patch_vllm


# 启动服务器
if __name__ == "__main__":
    # 仅在主进程中导入和初始化可能触发多进程的模块

    # wait_for_gpu()
    from app import create_app
    from app.config import settings
    
    # 创建应用实例
    app = create_app()
    
    # 配置日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    
    # 启动服务器
    uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT, access_log=False)
    
# 如果需要热重载，请使用以下命令启动:
# python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --access-log false