import socket

def get_ip_address() -> str:
    """
    获取本机网卡IP地址
    
    Returns:
        str: IP地址，如果获取失败则返回'127.0.0.1'
    """
    try:
        # 创建一个UDP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接一个外部地址(不需要真实连接)
        s.connect(('www.baidu.com', 80))
        # 获取本机IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'
