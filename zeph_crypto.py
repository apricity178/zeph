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
import binascii
import os


class ZephCrypto:
    """Zeph App 加密解密类"""
    
    def __init__(self):
        self.algorithm = "AES-CBC"
        self.key_length = 32
        self.iv_length = 16
        self.fixed_key_string = "zeph-fixed-key-for-login-payload-encryption-2024"
        self.xor_key = "zeph-captcha-xor-2024"
        self.gcm_key_string = "asldhlfhdshkfashfluksdahfkjsadhfkjsdhfjshjkfhlakjshfjsdhfhsadflh"
        self.gcm_key = self.gcm_key_string[:32].encode('utf-8')
    
    def get_fixed_key(self):
        key_hash = hashlib.sha256(self.fixed_key_string.encode()).digest()
        return key_hash[:32]
    
    def encrypt_with_fixed_key(self, data):
        key = self.get_fixed_key()
        iv = bytes([random.randint(0, 255) for _ in range(self.iv_length)])
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = json.dumps(data, separators=(',', ':')) if isinstance(data, dict) else str(data)
        encrypted = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        
        result = iv + encrypted
        return base64.b64encode(result).decode()
    
    def decrypt_with_fixed_key(self, encrypted_data):
        key = self.get_fixed_key()
        data = base64.b64decode(encrypted_data)
        
        iv = data[:self.iv_length]
        encrypted = data[self.iv_length:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        
        return json.loads(decrypted.decode())
    
    def encrypt_with_session_key(self, data, session_key):
        key = base64.b64decode(session_key)
        iv = bytes([random.randint(0, 255) for _ in range(self.iv_length)])
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = json.dumps(data, separators=(',', ':')) if isinstance(data, dict) else str(data)
        encrypted = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        
        result = iv + encrypted
        return base64.b64encode(result).decode()
    
    def decrypt_with_session_key(self, encrypted_data, session_key):
        key = base64.b64decode(session_key)
        data = base64.b64decode(encrypted_data)
        
        iv = data[:self.iv_length]
        encrypted = data[self.iv_length:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        
        return json.loads(decrypted.decode())
    
    def xor_decrypt(self, encrypted_base64):
        try:
            data = base64.b64decode(encrypted_base64)
            decrypted = bytearray()
            for i, byte in enumerate(data):
                decrypted.append(byte ^ ord(self.xor_key[i % len(self.xor_key)]))
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            raise Exception(f"XOR解密失败: {str(e)}")
    
    def aes_gcm_encrypt(self, data):
        try:
            iv = os.urandom(12)
            cipher = AES.new(self.gcm_key, AES.MODE_GCM, nonce=iv)
            plaintext = json.dumps(data, separators=(',', ':'))
            encrypted, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            combined = encrypted + tag
            return {
                'encryptedData': binascii.hexlify(combined).decode('utf-8'),
                'iv': binascii.hexlify(iv).decode('utf-8')
            }
        except Exception as e:
            raise Exception(f"AES-GCM加密失败: {str(e)}")
    
    def aes_gcm_decrypt(self, encrypted_hex, iv_hex):
        try:
            encrypted_bytes = binascii.unhexlify(encrypted_hex)
            iv_bytes = binascii.unhexlify(iv_hex)
            
            ciphertext = encrypted_bytes[:-16]
            tag = encrypted_bytes[-16:]
            
            cipher = AES.new(self.gcm_key, AES.MODE_GCM, nonce=iv_bytes)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            
            result = decrypted.decode('utf-8', errors='ignore')
            
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                raise Exception("无法提取JSON数据")
        except Exception as e:
            raise Exception(f"AES-GCM解密失败: {str(e)}")
    
    def generate_captcha_request_params(self):
        decrypt_a_bytes = os.urandom(32)
        decrypt_a = binascii.hexlify(decrypt_a_bytes).decode('utf-8')
        
        i_bytes = os.urandom(12)
        i = binascii.hexlify(i_bytes).decode('utf-8')
        
        return {
            'decryptA': decrypt_a,
            'i': i
        }
    
    def decrypt_captcha_response(self, response):
        if response.get("encrypted") and response.get("data"):
            return self.xor_decrypt(response["data"])
        return response
    
    def generate_nonce(self):
        return str(uuid.uuid4())
    
    def generate_timestamp(self):
        return int(time.time() * 1000)
    
    def build_login_request(self, data):
        encrypted_data = self.encrypt_with_fixed_key(data)
        return {
            "encrypted": True,
            "data": encrypted_data
        }
    
    def build_encrypted_request(self, data, session_id, session_key):
        encrypted_data = self.encrypt_with_session_key(data, session_key)
        return {
            "sessionId": session_id,
            "encryptedData": encrypted_data,
            "nonce": self.generate_nonce(),
            "timestamp": self.generate_timestamp()
        }
    
    def decrypt_response(self, response, session_key=None):
        if response.get("encrypted") and response.get("data"):
            if session_key:
                return self.decrypt_with_session_key(response["data"], session_key)
            else:
                try:
                    return self.decrypt_with_fixed_key(response["data"])
                except:
                    return response
        return response
