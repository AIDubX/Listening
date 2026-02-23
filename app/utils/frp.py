import os
import signal
import json
import platform
import uuid
import requests
import socket
import subprocess
import re
import time
import threading
import sys
from loguru import logger
from app.config import settings

class ReverseSSH:
    def __init__(self, ssh_host, ssh_port, ssh_user, ssh_password, remote_port, local_port):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.remote_port = remote_port
        self.local_port = local_port

        self.client = None
        self.transport = None
        self.running = False

    def open_reverse_tunnel(self):
        """建立反向 SSH 隧道"""
        try:
            import paramiko
        except ImportError:
            logger.error("请先安装 paramiko: pip install paramiko")
            return

        try:
            self.running = True
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            logger.info(f"正在连接到 SSH 服务器： {self.ssh_host}:{self.ssh_port} {self.ssh_user} {self.ssh_password} ...")
            self.client.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=str(self.ssh_password)
            )

            self.transport = self.client.get_transport()
            logger.info(f"开启转发服务 {self.remote_port} -> {self.local_port}...")
            self.transport.request_port_forward('', self.remote_port)

            while self.running:
                channel = self.transport.accept(1)
                if channel is None:
                    continue
                self.handle_connection(channel)
        except Exception as e:
            logger.error(f"Error: {e}")
            self.retry_count += 1
            if self.retry_count < 4:
                logger.info(f"连接失败，重试第{self.retry_count}次")
                self.open_reverse_tunnel()
            else:
                logger.error("连接失败，请检查SSH服务器信息")
        finally:
            self.stop()

    def handle_connection(self, channel):
        """处理单个远程连接"""
        local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            local_socket.connect(('127.0.0.1', self.local_port))
        except Exception as e:
            logger.error(f"Local connection failed: {e}")
            return

        threading.Thread(target=self.forward_data, args=(channel, local_socket), daemon=True).start()
        threading.Thread(target=self.forward_data, args=(local_socket, channel), daemon=True).start()

    def forward_data(self, src, dest):
        """数据转发"""
        while True:
            try:
                data = src.recv(1024)
                if not data:
                    break
                dest.sendall(data)
            except:
                break
        src.close()
        dest.close()

    def stop(self):
        """停止隧道"""
        self.running = False
        if self.transport:
            try:
                self.transport.close()
            except Exception as e:
                logger.error(f"Error closing transport: {e}")
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.error(f"Error closing SSH client: {e}")
        logger.info("SSH隧道已关闭。")

class FRP:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'pid'):
            self.pid = None
            self.is_stopped = False
            self.server = None
            self.wan_url = None
            self.is_started = False

    def start(self):
        """启动FRP服务"""
        settings.load_config()
        if not settings.ENABLE_NAT:
            logger.info("内网穿透未启用")
            return
        self.is_started = True

        if settings.NAT_TYPE == "gradio":
            # return
            self.public_gradio()
        elif settings.NAT_TYPE == "ssh":
            self.public_ssh()
        else:
            logger.error(f"不支持的穿透类型: {settings.NAT_TYPE}")

    def public_gradio(self):
        """使用gradio进行公网映射"""
        response = requests.get("https://api.gradio.app/v2/tunnel-request")

        if response and response.status_code == 200:
            # logger.debug(f"using gradio tunnel, gradio response code: {response.status_code}")
            try:
                payload = response.json()[0]
                remote_host, remote_port = payload["host"], int(payload["port"])
                if platform.system().lower() == "windows":
                    cmd = "frpc_windows_amd64_v0.2.exe"
                elif platform.system() == "Linux":
                    cmd = "./frpc_linux_amd64_v0.2"
                settings.load_config()
                # logger.debug(f"nat token: {settings.NAT_TOKEN}")

                command = [
                    cmd, 'http',
                    '-l', str(settings.SERVER_PORT),
                    '-i', 'localhost',
                    '--uc', '--sd', 'random', '--ue',
                    '--server_addr', f'{remote_host}:{remote_port}',
                    '--disable_log_color',
                    "-n", os.getenv("ACC_USER_NICKNAME").split("@")[0]
                ]
                # logger.debug(f"gradio command: {command}")

                p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.pid = p.pid

                while not self.is_stopped:
                    if p.stdout is None:
                        continue
                    line = p.stdout.readline()
                    if line == "":
                        continue
                    if "start proxy success" in line:
                        result = re.search(f"start proxy success: (.+)\n", line)
                        if result is None:
                            logger.error("创建外网失败")
                            break
                        else:
                            self.wan_url = result.group(1)
                            logger.debug(f"外网地址: {self.wan_url}")

            except FileNotFoundError as e:
                logger.error(f"frpc执行文件未找到: {e}请下载frpc_windows_amd64_v0.2.exe到整合包根目录。")
            except Exception as e:
                logger.error(f"外网地址创建失败: {e}")
        else:
            logger.error(f"请求gradio api失败: {response.status_code}")
            
    def public_ssh(self):
        """使用SSH隧道进行公网映射"""
        try:
            import paramiko
        except ImportError:
            import os,sys
            logger.error("正在安装paramiko...,等待安装完成后，请重新启动外网")
            os.system(sys.executable + " -m pip install paramiko")
            return

        if not settings.NAT_SERVER:
            logger.error("请先配置SSH服务器信息")
            return

        self.server = ReverseSSH(
            settings.NAT_SERVER,
            ssh_port=settings.NAT_SSH_PORT,
            ssh_user=settings.NAT_USERNAME,
            ssh_password=settings.NAT_PASSWORD,
            remote_port=settings.NAT_REMOTE_PORT,
            local_port=settings.SERVER_PORT
        )

        self.wan_url = f"http://{settings.NAT_SERVER}:{settings.NAT_REMOTE_PORT}"
        logger.debug(f"外网地址: {self.wan_url}")
        self.server.open_reverse_tunnel()

    def stop(self):
        """停止FRP服务"""
        try:
            if self.pid:
                self.wan_url = None
                os.kill(self.pid, signal.SIGTERM)
            if self.server:
                self.wan_url = None
                self.server.stop()
        except:
            logger.warning("服务已停止")
        finally:
            self.is_started = False
            self.is_stopped = True



if __name__ == "__main__":
    frp = FRP()
    frp.start()
    input("按回车键退出")
    frp.stop()

