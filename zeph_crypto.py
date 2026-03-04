"""
Zeph App 加密模块
从 app.bc60777b.js 中提取的加密规则
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import base64
import json
import uuid
import time
import random


class ZephCrypto:
    """Zeph App 加密解密类"""
    
    def __init__(self):
        self.algorithm = "AES-CBC"
        self.key_length = 32  # 256 bits
        self.iv_length = 16   # 128 bits
        self.fixed_key_string = "zeph-fixed-key-for-login-payload-encryption-2024"
    
    def get_fixed_key(self):
        """
        获取固定密钥（用于登录）
        固定密钥字符串经过 SHA-256 哈希后取前32字节
        """
        key_hash = hashlib.sha256(self.fixed_key_string.encode()).digest()
        return key_hash[:32]
    
    def encrypt_with_fixed_key(self, data):
        """
        使用固定密钥加密（登录请求）
        
        Args:
            data: 要加密的数据（字典或字符串）
            
        Returns:
            base64编码的加密字符串
        """
        key = self.get_fixed_key()
        iv = bytes([random.randint(0, 255) for _ in range(self.iv_length)])
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = json.dumps(data) if isinstance(data, dict) else str(data)
        encrypted = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        
        # IV + 密文
        result = iv + encrypted
        return base64.b64encode(result).decode()
    
    def decrypt_with_fixed_key(self, encrypted_data):
        """
        使用固定密钥解密
        
        Args:
            encrypted_data: base64编码的加密字符串
            
        Returns:
            解密后的数据（字典）
        """
        key = self.get_fixed_key()
        data = base64.b64decode(encrypted_data)
        
        iv = data[:self.iv_length]
        encrypted = data[self.iv_length:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        
        return json.loads(decrypted.decode())
    
    def encrypt_with_session_key(self, data, session_key):
        """
        使用会话密钥加密
        
        Args:
            data: 要加密的数据（字典或字符串）
            session_key: base64编码的会话密钥
            
        Returns:
            base64编码的加密字符串
        """
        key = base64.b64decode(session_key)
        iv = bytes([random.randint(0, 255) for _ in range(self.iv_length)])
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = json.dumps(data) if isinstance(data, dict) else str(data)
        encrypted = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        
        # IV + 密文
        result = iv + encrypted
        return base64.b64encode(result).decode()
    
    def decrypt_with_session_key(self, encrypted_data, session_key):
        """
        使用会话密钥解密
        
        Args:
            encrypted_data: base64编码的加密字符串
            session_key: base64编码的会话密钥
            
        Returns:
            解密后的数据（字典）
        """
        key = base64.b64decode(session_key)
        data = base64.b64decode(encrypted_data)
        
        iv = data[:self.iv_length]
        encrypted = data[self.iv_length:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        
        return json.loads(decrypted.decode())
    
    def generate_nonce(self):
        """
        生成随机 nonce (UUID v4 格式)
        """
        return str(uuid.uuid4())
    
    def generate_timestamp(self):
        """
        生成时间戳（毫秒）
        """
        return int(time.time() * 1000)
    
    def build_login_request(self, data):
        """
        构建登录请求体
        
        Args:
            data: 登录数据（包含 deviceId 等）
            
        Returns:
            加密后的请求体字典
        """
        encrypted_data = self.encrypt_with_fixed_key(data)
        return {
            "encrypted": True,
            "data": encrypted_data
        }
    
    def build_encrypted_request(self, data, session_id, session_key):
        """
        构建加密请求体（用于已登录后的请求）
        
        Args:
            data: 请求数据
            session_id: 会话ID
            session_key: 会话密钥（base64编码）
            
        Returns:
            加密后的请求体字典
        """
        encrypted_data = self.encrypt_with_session_key(data, session_key)
        return {
            "sessionId": session_id,
            "encryptedData": encrypted_data,
            "nonce": self.generate_nonce(),
            "timestamp": self.generate_timestamp()
        }
    
    def decrypt_response(self, response, session_key=None):
        """
        解密响应数据
        
        Args:
            response: 响应字典（包含 encrypted 和 data 字段）
            session_key: 会话密钥（如果是加密响应）
            
        Returns:
            解密后的数据
        """
        if response.get("encrypted") and response.get("data"):
            if session_key:
                return self.decrypt_with_session_key(response["data"], session_key)
            else:
                # 尝试使用固定密钥解密（登录响应）
                try:
                    return self.decrypt_with_fixed_key(response["data"])
                except:
                    return response
        return response
