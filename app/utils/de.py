from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import json


def decrypt_multi_phoneme(encrypted_data: str, salt: str, iv: str, machine_id: str) -> dict:
    """
    解密多音字数据
    
    Args:
        encrypted_data: 十六进制格式的加密数据
        salt: 十六进制格式的盐值
        iv: 十六进制格式的初始化向量
        machine_id: 机器ID（用于密钥生成）
    
    Returns:
        解密后的多音字数据字典
    """
    try:
        # 将十六进制字符串转换为字节
        encrypted_bytes = bytes.fromhex(encrypted_data)
        salt_bytes = bytes.fromhex(salt)
        iv_bytes = bytes.fromhex(iv)
        
        # 使用PBKDF2HMAC生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(machine_id.encode())
        
        # 创建解密器
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv_bytes), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # 解密数据
        decrypted_padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # 去除PKCS7填充
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        
        # 解析JSON数据
        return json.loads(decrypted_data.decode('utf-8'))
        
    except Exception as e:
        logger.error(f"解密失败: {str(e)}")
        raise