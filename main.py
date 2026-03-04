"""
Zeph Auto Tool - Android Version
使用Kivy框架开发
"""

import os
import sys

# 设置Kivy配置
os.environ['KIVY_TEXT'] = 'pil'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.properties import StringProperty
import json
import uuid
import time
import threading
import random
import hashlib
import requests
from datetime import datetime

# 导入加密模块
from zeph_crypto import ZephCrypto

# 尝试注册中文字体
def setup_chinese_font():
    """设置中文字体"""
    try:
        # Android系统常见中文字体路径
        font_paths = [
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/NotoSansSC-Regular.otf',
            '/system/fonts/DroidSansFallback.ttf',
            '/system/fonts/NotoSansCJK-Regular.ttc.0',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                # 注册为默认字体
                LabelBase.register('Roboto', font_path, font_path, font_path, font_path)
                return font_path
    except Exception as e:
        print(f"Font setup error: {e}")
    return None

# 设置中文字体
CHINESE_FONT = setup_chinese_font()

# 设置窗口背景色
Window.clearcolor = (0.15, 0.15, 0.15, 1)


class ChineseLabel(Label):
    """支持中文的Label"""
    def __init__(self, **kwargs):
        if CHINESE_FONT:
            kwargs['font_name'] = 'Roboto'
        super().__init__(**kwargs)


class ChineseButton(Button):
    """支持中文的Button"""
    def __init__(self, **kwargs):
        if CHINESE_FONT:
            kwargs['font_name'] = 'Roboto'
        super().__init__(**kwargs)


class ChineseTextInput(TextInput):
    """支持中文的TextInput"""
    def __init__(self, **kwargs):
        if CHINESE_FONT:
            kwargs['font_name'] = 'Roboto'
        super().__init__(**kwargs)


class ZephAutoApp(App):
    """主应用类"""
    
    def __init__(self, **kwargs):
        super(ZephAutoApp, self).__init__(**kwargs)
        self.crypto = ZephCrypto()
        self.devices = []
        self.stop_flag = False
        
        # 网站基础URL
        self.base_url = "https://myt.sale"
        
        # API端点
        self.login_url = f"{self.base_url}/api/device/login"
        self.signin_url = f"{self.base_url}/api/app/signin"
        self.bind_inviter_url = f"{self.base_url}/api/app/user/bind-inviter"
        self.set_password_url = f"{self.base_url}/api/app/user/set-account-password"
        self.coin_destroy_url = f"{self.base_url}/api/app/coin/destroy"
        self.captcha_generate_url = f"{self.base_url}/api/captcha/generate"
        self.captcha_verify_url = f"{self.base_url}/api/captcha/verify"
        self.register_url = f"{self.base_url}/api/app/device/register-with-captcha"
        
        # 存储
        self.device_store = JsonStore('devices.json')
        self.config_store = JsonStore('config.json')
        
        # 加载数据
        self.load_devices()
        self.load_config()
        
        # 选中设备索引
        self.selected_indices = set()
    
    def build(self):
        """构建UI"""
        self.title = 'Zeph Auto Tool'
        
        # 主布局
        root = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # 创建标签页
        tab_panel = TabbedPanel(do_default_tab=False)
        
        # 设备管理标签页
        device_tab = self.create_device_tab()
        device_header = TabbedPanelHeader(text='设备管理')
        device_header.content = device_tab
        tab_panel.add_widget(device_header)
        
        # 批量操作标签页
        batch_tab = self.create_batch_tab()
        batch_header = TabbedPanelHeader(text='批量操作')
        batch_header.content = batch_tab
        tab_panel.add_widget(batch_header)
        
        # 日志标签页
        log_tab = self.create_log_tab()
        log_header = TabbedPanelHeader(text='日志')
        log_header.content = log_tab
        tab_panel.add_widget(log_header)
        
        root.add_widget(tab_panel)
        
        # 状态栏
        self.status_label = ChineseLabel(
            text='就绪',
            size_hint_y=None,
            height=30,
            color=(0.9, 0.9, 0.9, 1),
            bold=True
        )
        root.add_widget(self.status_label)
        
        return root
    
    def create_device_tab(self):
        """创建设备管理标签页"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # 配置区域
        config_box = BoxLayout(orientation='vertical', size_hint_y=None, height=220, spacing=8)
        
        # 邀请码和代理
        row1 = BoxLayout(size_hint_y=None, height=45)
        row1.add_widget(ChineseLabel(text='邀请码:', size_hint_x=0.2, bold=True))
        self.invite_code_input = ChineseTextInput(
            text=self.config.get('invite_code', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='输入邀请码'
        )
        row1.add_widget(self.invite_code_input)
        row1.add_widget(ChineseLabel(text='代理:', size_hint_x=0.2, bold=True))
        self.proxy_url_input = ChineseTextInput(
            text=self.config.get('proxy_url', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='代理链接'
        )
        row1.add_widget(self.proxy_url_input)
        config_box.add_widget(row1)
        
        # 打码平台配置
        row2 = BoxLayout(size_hint_y=None, height=45)
        row2.add_widget(ChineseLabel(text='打码用户:', size_hint_x=0.2, bold=True))
        self.captcha_user_input = ChineseTextInput(
            text=self.config.get('captcha_username', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='用户名'
        )
        row2.add_widget(self.captcha_user_input)
        row2.add_widget(ChineseLabel(text='打码密码:', size_hint_x=0.2, bold=True))
        self.captcha_pass_input = ChineseTextInput(
            text=self.config.get('captcha_password', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='密码',
            password=True
        )
        row2.add_widget(self.captcha_pass_input)
        config_box.add_widget(row2)
        
        # 保存配置按钮
        row3 = BoxLayout(size_hint_y=None, height=50, spacing=10)
        save_btn = ChineseButton(
            text='保存配置',
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        save_btn.bind(on_press=self.save_config)
        row3.add_widget(save_btn)
        
        create_btn = ChineseButton(
            text='创建新设备',
            size_hint_x=0.5,
            background_color=(0.2, 0.4, 0.8, 1)
        )
        create_btn.bind(on_press=self.create_device)
        row3.add_widget(create_btn)
        config_box.add_widget(row3)
        
        layout.add_widget(config_box)
        
        # 设备列表
        list_label = ChineseLabel(
            text='设备列表:',
            size_hint_y=None,
            height=30,
            bold=True,
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(list_label)
        
        # 设备列表滚动区域
        scroll = ScrollView()
        self.device_list_layout = GridLayout(
            cols=1,
            spacing=3,
            size_hint_y=None
        )
        self.device_list_layout.bind(minimum_height=self.device_list_layout.setter('height'))
        scroll.add_widget(self.device_list_layout)
        layout.add_widget(scroll)
        
        # 刷新设备列表
        self.refresh_device_list()
        
        return layout
    
    def create_batch_tab(self):
        """创建批量操作标签页"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = ChineseLabel(
            text='批量操作',
            size_hint_y=None,
            height=40,
            font_size='20sp',
            bold=True,
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(title)
        
        # 操作按钮
        btn_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=200)
        
        btn_data = [
            ('批量签到', self.batch_signin, (0.2, 0.6, 0.2, 1)),
            ('批量绑定', self.batch_bind, (0.2, 0.4, 0.8, 1)),
            ('批量查币', self.batch_query, (0.8, 0.6, 0.2, 1)),
            ('批量设密', self.batch_set_password, (0.6, 0.2, 0.6, 1)),
            ('批量销毁', self.batch_destroy, (0.8, 0.2, 0.2, 1)),
            ('停止操作', self.stop_operations, (0.5, 0.5, 0.5, 1)),
        ]
        
        for text, callback, color in btn_data:
            btn = ChineseButton(
                text=text,
                background_color=color,
                font_size='16sp'
            )
            btn.bind(on_press=callback)
            btn_layout.add_widget(btn)
        
        layout.add_widget(btn_layout)
        
        # 说明文字
        info = ChineseLabel(
            text='提示: 在设备列表中勾选设备后，点击上方按钮进行批量操作',
            size_hint_y=None,
            height=60,
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(info)
        
        layout.add_widget(BoxLayout())  # 填充空间
        
        return layout
    
    def create_log_tab(self):
        """创建日志标签页"""
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # 日志显示区域
        scroll = ScrollView()
        self.log_label = ChineseLabel(
            text='日志:\n',
            size_hint_y=None,
            markup=True,
            color=(0.9, 0.9, 0.9, 1)
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll.add_widget(self.log_label)
        layout.add_widget(scroll)
        
        # 清除日志按钮
        clear_btn = ChineseButton(
            text='清除日志',
            size_hint_y=None,
            height=40,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        clear_btn.bind(on_press=self.clear_log)
        layout.add_widget(clear_btn)
        
        return layout
    
    def refresh_device_list(self):
        """刷新设备列表"""
        self.device_list_layout.clear_widgets()
        
        if not self.devices:
            no_device = ChineseLabel(
                text='暂无设备，请点击"创建新设备"',
                size_hint_y=None,
                height=40,
                color=(0.7, 0.7, 0.7, 1)
            )
            self.device_list_layout.add_widget(no_device)
            return
        
        # 表头
        header = BoxLayout(size_hint_y=None, height=30)
        header.add_widget(ChineseLabel(text='选择', size_hint_x=0.1, bold=True, color=(0.9, 0.9, 0.9, 1)))
        header.add_widget(ChineseLabel(text='设备ID', size_hint_x=0.25, bold=True, color=(0.9, 0.9, 0.9, 1)))
        header.add_widget(ChineseLabel(text='账户', size_hint_x=0.2, bold=True, color=(0.9, 0.9, 0.9, 1)))
        header.add_widget(ChineseLabel(text='活力', size_hint_x=0.1, bold=True, color=(0.9, 0.9, 0.9, 1)))
        header.add_widget(ChineseLabel(text='币值', size_hint_x=0.1, bold=True, color=(0.9, 0.9, 0.9, 1)))
        header.add_widget(ChineseLabel(text='签到', size_hint_x=0.1, bold=True, color=(0.9, 0.9, 0.9, 1)))
        header.add_widget(ChineseLabel(text='操作', size_hint_x=0.15, bold=True, color=(0.9, 0.9, 0.9, 1)))
        self.device_list_layout.add_widget(header)
        
        # 设备行
        for i, device in enumerate(self.devices):
            row = BoxLayout(size_hint_y=None, height=40)
            
            # 复选框
            checkbox = CheckBox(size_hint_x=0.1)
            checkbox.bind(active=lambda cb, val, idx=i: self.on_checkbox_active(idx, val))
            if i in self.selected_indices:
                checkbox.active = True
            row.add_widget(checkbox)
            
            # 设备信息
            device_id = device.get('device_id', 'N/A')[:12]
            row.add_widget(ChineseLabel(text=device_id, size_hint_x=0.25, color=(0.9, 0.9, 0.9, 1)))
            
            account = device.get('account', 'N/A')
            row.add_widget(ChineseLabel(text=account, size_hint_x=0.2, color=(0.9, 0.9, 0.9, 1)))
            
            vitality = str(device.get('vitality', 0))
            row.add_widget(ChineseLabel(text=vitality, size_hint_x=0.1, color=(0.9, 0.9, 0.9, 1)))
            
            coins = f"{device.get('total_coins', 0):.2f}"
            row.add_widget(ChineseLabel(text=coins, size_hint_x=0.1, color=(0.9, 0.9, 0.9, 1)))
            
            signed = '是' if device.get('signed_in', False) else '否'
            row.add_widget(ChineseLabel(text=signed, size_hint_x=0.1, color=(0.9, 0.9, 0.9, 1)))
            
            # 删除按钮
            del_btn = ChineseButton(
                text='删除',
                size_hint_x=0.15,
                background_color=(0.8, 0.2, 0.2, 1),
                font_size='12sp'
            )
            del_btn.bind(on_press=lambda btn, idx=i: self.delete_device(idx))
            row.add_widget(del_btn)
            
            self.device_list_layout.add_widget(row)
    
    def on_checkbox_active(self, index, value):
        """复选框状态变化"""
        if value:
            self.selected_indices.add(index)
        else:
            self.selected_indices.discard(index)
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_label.text += f'[{timestamp}] {message}\n'
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        pass  # 简化处理
    
    def clear_log(self, instance=None):
        """清除日志"""
        self.log_label.text = '日志:\n'
    
    def load_devices(self):
        """加载设备"""
        try:
            if self.device_store.exists('devices'):
                self.devices = self.device_store.get('devices')['data']
            else:
                self.devices = []
        except:
            self.devices = []
    
    def save_devices(self):
        """保存设备"""
        self.device_store.put('devices', data=self.devices)
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_store.exists('config'):
                self.config = self.config_store.get('config')['data']
            else:
                self.config = {}
        except:
            self.config = {}
    
    def save_config(self, instance=None):
        """保存配置"""
        self.config['invite_code'] = self.invite_code_input.text
        self.config['proxy_url'] = self.proxy_url_input.text
        self.config['captcha_username'] = self.captcha_user_input.text
        self.config['captcha_password'] = self.captcha_pass_input.text
        self.config_store.put('config', data=self.config)
        self.add_log('配置已保存')
        self.status_label.text = '配置已保存'
    
    def create_device(self, instance=None):
        """创建新设备"""
        device_id = uuid.uuid4().hex[:16]
        device = {
            'device_id': device_id,
            'android_id': uuid.uuid4().hex[:16],
            'device_fingerprint': self.generate_fingerprint(),
            'account': '',
            'password': '',
            'vitality': 0,
            'total_coins': 0,
            'continuous_days': 0,
            'signed_in': False,
            'invite_bound': False
        }
        self.devices.append(device)
        self.save_devices()
        self.refresh_device_list()
        self.add_log(f'创建新设备: {device_id}')
        self.status_label.text = f'创建新设备: {device_id}'
    
    def generate_fingerprint(self):
        """生成设备指纹"""
        return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()
    
    def delete_device(self, index):
        """删除设备"""
        if 0 <= index < len(self.devices):
            device_id = self.devices[index].get('device_id', 'N/A')
            del self.devices[index]
            self.save_devices()
            self.refresh_device_list()
            self.add_log(f'删除设备: {device_id}')
    
    def stop_operations(self, instance=None):
        """停止操作"""
        self.stop_flag = True
        self.add_log('正在停止操作...')
        self.status_label.text = '已停止'
    
    def get_session(self, device):
        """获取会话"""
        session = requests.Session()
        
        headers = {
            "Host": "myt.sale",
            "User-Agent": "Mozilla/5.0 (Linux; Android 9; ASUS_AI2401_A Build/PQ3B.190801.01221007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://myt.sale",
            "X-Requested-With": "com.zeph.vitality",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://myt.sale/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        session.headers.update(headers)
        
        # 获取并设置代理
        proxies = self.get_proxy()
        if proxies:
            session.proxies.update(proxies)
            self.add_log(f"已设置代理: {proxies['http']}")
        
        # 加载设备的cookies
        if device.get("cookies"):
            session.cookies.update(device["cookies"])
        
        return session
    
    def get_proxy(self):
        """获取代理"""
        proxy_url = self.config.get('proxy_url', '')
        if not proxy_url:
            return None
        
        try:
            response = requests.get(proxy_url, timeout=10)
            if response.status_code == 200:
                proxy = response.text.strip()
                if ':' in proxy:
                    return {
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    }
        except Exception as e:
            self.add_log(f"获取代理失败: {str(e)}")
        
        return None
    
    def login(self, device):
        """执行真实的登录操作"""
        max_retries = 3
        for attempt in range(max_retries):
            session = self.get_session(device)
            
            try:
                # 生成登录请求数据（使用真实加密）
                login_payload = {
                    "device_fingerprint": device['device_fingerprint']
                }
                encrypted_payload = self.crypto.encrypt_with_fixed_key(login_payload)
                login_data = {
                    "encryptedPayload": encrypted_payload
                }
                
                # 发送登录请求
                self.add_log(f"正在登录设备: {device['device_id']}")
                response = session.post(self.login_url, json=login_data, timeout=10)
                
                # 检查响应
                if response.status_code == 200:
                    # 保存cookies
                    device["cookies"] = dict(session.cookies)
                    
                    # 解析响应
                    response_data = response.json()
                    
                    # 如果响应是加密的，尝试解密
                    if response_data.get("encrypted") and response_data.get("data"):
                        try:
                            decrypted_data = self.crypto.decrypt_with_fixed_key(response_data["data"])
                            
                            # 从解密的数据中提取会话信息
                            if "data" in decrypted_data and "session" in decrypted_data["data"]:
                                session_info = decrypted_data["data"]["session"]
                                device["session_id"] = session_info.get("sessionId", str(uuid.uuid4()))
                                device["session_key"] = session_info.get("sessionKey", "")
                                device["token"] = decrypted_data["data"].get("token", "")
                                device["openid"] = decrypted_data["data"].get("openid", "")
                                self.add_log(f"会话ID: {device['session_id']}")
                            
                            # 保存会话数据，包括活力值和币值
                            device["session_data"] = decrypted_data.get("data", {})
                            
                            # 提取活力值和币值
                            user_data = device["session_data"].get("user", {})
                            vitality = user_data.get("vitality", 0)
                            total_coins = user_data.get("totalCoins", 0)
                            continuous_days = user_data.get("continuousDays", 0)
                            if vitality or total_coins or continuous_days:
                                device["vitality"] = vitality
                                device["total_coins"] = total_coins
                                device["continuous_days"] = continuous_days
                                self.add_log(f"活力值: {vitality}, 币值: {total_coins}, 签到天数: {continuous_days}")
                            
                            response_data = decrypted_data
                        except Exception as e:
                            self.add_log(f"解密响应失败: {str(e)}")
                    
                    # 保存会话信息（如果没有从加密响应中获取）
                    if "session_id" not in device:
                        device["session_id"] = str(uuid.uuid4())
                    if "session_key" not in device:
                        device["session_key"] = ""
                    if "token" not in device:
                        device["token"] = hashlib.md5((device["device_id"] + str(time.time())).encode()).hexdigest()
                    if "openid" not in device:
                        device["openid"] = ""
                    
                    self.save_devices()
                    self.add_log(f"设备登录成功: {device['device_id']}")
                    return True
                
                self.add_log(f"设备登录失败: {device['device_id']}, 状态码: {response.status_code}")
                if attempt < max_retries - 1:
                    self.add_log(f"重试登录 ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return False
            except requests.exceptions.ProxyError as e:
                error_message = f"代理连接失败: {str(e)}"
                self.add_log(error_message)
                if attempt < max_retries - 1:
                    self.add_log(f"重新获取代理并重试登录 ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return False
            except Exception as e:
                error_message = f"登录失败: {str(e)}"
                self.add_log(error_message)
                if attempt < max_retries - 1:
                    self.add_log(f"重试登录 ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return False
    
    def recognize_captcha(self, svg_data):
        """识别验证码"""
        captcha_username = self.config.get('captcha_username', '')
        captcha_password = self.config.get('captcha_password', '')
        
        if not captcha_username or not captcha_password:
            self.add_log("请先配置打码平台账户")
            return None
        
        try:
            # 先尝试使用resvg-py转换SVG
            try:
                import resvg
                from io import BytesIO
                from PIL import Image
                import base64
                
                # 使用resvg转换
                svg_bytes = svg_data.encode('utf-8')
                tree = resvg.parse(svg_bytes)
                png_data = tree.render()
                
                # 转换为PIL Image
                img = Image.open(BytesIO(png_data))
                
                # 转换为base64
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                self.add_log("SVG已成功转换为PNG并编码为base64 (resvg-py)")
                
            except:
                # 如果resvg失败，尝试使用svglib
                try:
                    from svglib.svglib import svg2rlg
                    from reportlab.graphics import renderPM
                    from io import BytesIO
                    import base64
                    
                    drawing = svg2rlg(BytesIO(svg_data.encode('utf-8')))
                    buffer = BytesIO()
                    renderPM.drawToFile(drawing, buffer, fmt='PNG', dpi=300)
                    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    self.add_log("SVG已成功转换为PNG并编码为base64 (svglib)")
                    
                except:
                    # 直接使用SVG的base64编码
                    import base64
                    img_base64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
                    self.add_log("直接使用SVG编码为base64")
            
            # 调用打码平台
            tts_url = "https://api.ttshitu.com/predict"
            tts_data = {
                "username": captcha_username,
                "password": captcha_password,
                "typeid": "3",
                "image": img_base64
            }
            
            response = requests.post(tts_url, json=tts_data, timeout=30)
            result = response.json()
            
            if result.get('success', False):
                captcha_value = result.get('data', {}).get('result', '')
                if captcha_value:
                    return captcha_value
            
            self.add_log(f"打码平台调用失败: {result.get('message', '未知错误')}")
            
        except Exception as e:
            self.add_log(f"验证码识别失败: {str(e)}")
        
        return None
    
    def batch_signin(self, instance):
        """批量签到"""
        self.stop_flag = False
        self.add_log('开始批量签到...')
        threading.Thread(target=self._batch_signin_thread).start()
    
    def _batch_signin_thread(self):
        """批量签到线程"""
        targets = list(self.selected_indices) if self.selected_indices else range(len(self.devices))
        success_count = 0
        
        for idx in targets:
            if self.stop_flag:
                break
            
            device = self.devices[idx]
            
            # 检查是否已经签到
            if device.get("signed_in", False):
                self.add_log(f"设备 {device['device_id']} 今日已签到，跳过")
                continue
            
            Clock.schedule_once(lambda dt, d=device: self.add_log(f'签到设备: {d["device_id"][:12]}'), 0)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 先登录
                    if not self.login(device):
                        break
                    
                    # 创建会话
                    session = self.get_session(device)
                    
                    # 第一步：获取图形验证码
                    self.add_log(f"设备 {device['device_id']} 正在获取验证码")
                    captcha_payload = {}
                    session_key = device.get("session_key")
                    
                    if session_key:
                        # 使用会话密钥加密
                        captcha_data = self.crypto.build_encrypted_request(
                            captcha_payload,
                            device.get("session_id", str(uuid.uuid4())),
                            session_key
                        )
                    else:
                        # 使用固定密钥加密
                        encrypted_data = self.crypto.encrypt_with_fixed_key(captcha_payload)
                        captcha_data = {
                            "sessionId": device.get("session_id", str(uuid.uuid4())),
                            "encryptedData": encrypted_data,
                            "nonce": self.crypto.generate_nonce(),
                            "timestamp": self.crypto.generate_timestamp()
                        }
                    
                    # 发送获取验证码请求
                    captcha_response = session.post(self.captcha_generate_url, json=captcha_data, timeout=10)
                    
                    if captcha_response.status_code != 200:
                        self.add_log(f"获取验证码失败: {captcha_response.status_code}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试获取验证码 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                    captcha_data = captcha_response.json()
                    
                    # 如果响应是加密的，尝试解密
                    if captcha_data.get("encrypted") and captcha_data.get("data"):
                        try:
                            decrypted_captcha = self.crypto.decrypt_with_session_key(captcha_data["data"], session_key)
                            self.add_log(f"解密后的验证码响应: {{'c': 1, 'msg': '生成验证码成功', 'data': {{...}}}}")
                            captcha_data = decrypted_captcha
                        except Exception as e:
                            self.add_log(f"解密验证码响应失败: {str(e)}")
                    
                    # 第二步：验证验证码
                    self.add_log(f"设备 {device['device_id']} 正在验证验证码")
                    verify_payload = {}
                    
                    # 从解密后的验证码响应中提取验证码信息
                    if isinstance(captcha_data, dict) and "data" in captcha_data:
                        captcha_data = captcha_data["data"]
                        # 提取验证码ID
                        if "captchaId" in captcha_data:
                            verify_payload["captchaId"] = captcha_data["captchaId"]
                            self.add_log(f"提取到验证码ID: {captcha_data['captchaId']}")
                        # 提取SVG并使用OCR识别
                        captcha_value = None
                        if "svg" in captcha_data:
                            svg_data = captcha_data["svg"]
                            # 使用OCR识别验证码
                            captcha_value = self.recognize_captcha(svg_data)
                            if not captcha_value:
                                self.add_log("验证码识别失败，跳过该设备")
                                break
                        else:
                            self.add_log("没有找到SVG验证码数据，跳过该设备")
                            break
                        verify_payload["captchaCode"] = captcha_value
                        self.add_log(f"验证码识别成功: {captcha_value}")
                    
                    if session_key:
                        # 使用会话密钥加密
                        verify_data = self.crypto.build_encrypted_request(
                            verify_payload,
                            device.get("session_id", str(uuid.uuid4())),
                            session_key
                        )
                    else:
                        # 使用固定密钥加密
                        encrypted_data = self.crypto.encrypt_with_fixed_key(verify_payload)
                        verify_data = {
                            "sessionId": device.get("session_id", str(uuid.uuid4())),
                            "encryptedData": encrypted_data,
                            "nonce": self.crypto.generate_nonce(),
                            "timestamp": self.crypto.generate_timestamp()
                        }
                    
                    # 发送验证验证码请求
                    verify_response = session.post(self.captcha_verify_url, json=verify_data, timeout=10)
                    
                    if verify_response.status_code != 200:
                        self.add_log(f"验证验证码失败: {verify_response.status_code}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试验证验证码 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                    verify_data = verify_response.json()
                    
                    if verify_data.get("encrypted") and verify_data.get("data"):
                        try:
                            decrypted_verify = self.crypto.decrypt_with_session_key(verify_data["data"], session_key)
                            self.add_log(f"解密后的验证响应: {decrypted_verify}")
                            verify_data = decrypted_verify
                        except Exception as e:
                            self.add_log(f"解密验证响应失败: {str(e)}")
                    
                    # 检查验证码是否错误，如果错误则重新获取验证码
                    if verify_data.get("c") == 0 and "验证码错误" in verify_data.get("msg", ""):
                        self.add_log(f"验证码错误，重新获取验证码 ({attempt+1}/{max_retries})...")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        else:
                            self.add_log(f"设备 {device['device_id']} 验证码错误次数过多，跳过")
                            break
                    
                    # 第三步：执行签到
                    # 生成签到请求数据（使用真实加密）
                    checkin_payload = {
                        "token": device.get("token", ""),
                        "deviceId": device.get("device_id", ""),
                        "captchaId": verify_payload.get("captchaId", ""),
                        "captchaCode": verify_payload.get("captchaCode", "")
                    }
                    
                    if session_key:
                        # 使用会话密钥加密
                        checkin_data = self.crypto.build_encrypted_request(
                            checkin_payload,
                            device.get("session_id", str(uuid.uuid4())),
                            session_key
                        )
                    else:
                        # 使用固定密钥加密
                        encrypted_data = self.crypto.encrypt_with_fixed_key(checkin_payload)
                        checkin_data = {
                            "sessionId": device.get("session_id", str(uuid.uuid4())),
                            "encryptedData": encrypted_data,
                            "nonce": self.crypto.generate_nonce(),
                            "timestamp": self.crypto.generate_timestamp()
                        }
                    
                    # 发送签到请求
                    self.add_log(f"设备 {device['device_id']} 正在签到")
                    checkin_response = session.post(self.signin_url, json=checkin_data, timeout=10)
                    
                    if checkin_response.status_code != 200:
                        self.add_log(f"签到失败: {checkin_response.status_code}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试签到 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                    checkin_data = checkin_response.json()
                    
                    if checkin_data.get("encrypted") and checkin_data.get("data"):
                        try:
                            decrypted_checkin = self.crypto.decrypt_with_session_key(checkin_data["data"], session_key)
                            self.add_log(f"解密后的签到响应: {decrypted_checkin}")
                            checkin_data = decrypted_checkin
                        except Exception as e:
                            self.add_log(f"解密签到响应失败: {str(e)}")
                    
                    if checkin_data.get("c") == 1:
                        device["signed_in"] = True
                        success_count += 1
                        self.add_log(f"设备签到成功: {device['device_id']}")
                        self.save_devices()
                        Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
                        break
                    else:
                        msg = checkin_data.get("msg", "未知错误")
                        if "今日已签到" in msg:
                            device["signed_in"] = True
                            self.save_devices()
                            Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
                            self.add_log(f"设备 {device['device_id']} 今日已签到")
                            break
                        self.add_log(f"签到失败: {msg}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试签到 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                except Exception as e:
                    self.add_log(f"签到出错: {str(e)}")
                    if attempt < max_retries - 1:
                        self.add_log(f"重试签到 ({attempt+1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    break
        
        self.save_devices()
        Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
        Clock.schedule_once(lambda dt: self.add_log(f'批量签到完成，成功 {success_count} 个'), 0)
    
    def batch_bind(self, instance):
        """批量绑定"""
        self.stop_flag = False
        invite_code = self.invite_code_input.text
        if not invite_code:
            self.add_log('错误: 请输入邀请码')
            return
        self.add_log(f'开始批量绑定邀请码: {invite_code}')
        threading.Thread(target=self._batch_bind_thread, args=(invite_code,)).start()
    
    def _batch_bind_thread(self, invite_code):
        """批量绑定线程"""
        targets = list(self.selected_indices) if self.selected_indices else range(len(self.devices))
        success_count = 0
        
        for idx in targets:
            if self.stop_flag:
                break
            
            device = self.devices[idx]
            
            # 检查是否已经绑定过
            if device.get("invite_bound", False):
                self.add_log(f"设备 {device['device_id']} 已经绑定过邀请人，跳过")
                continue
            
            Clock.schedule_once(lambda dt, d=device: self.add_log(f'绑定邀请码到设备: {d["device_id"][:12]}'), 0)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 先登录
                    if not self.login(device):
                        break
                    
                    # 创建会话
                    session = self.get_session(device)
                    
                    # 生成绑定邀请码请求
                    bind_payload = {
                        "inviteCode": invite_code,
                        "token": {}
                    }
                    
                    session_key = device.get("session_key")
                    if session_key:
                        bind_data = self.crypto.build_encrypted_request(
                            bind_payload,
                            device.get("session_id", str(uuid.uuid4())),
                            session_key
                        )
                    else:
                        encrypted_data = self.crypto.encrypt_with_fixed_key(bind_payload)
                        bind_data = {
                            "sessionId": device.get("session_id", str(uuid.uuid4())),
                            "encryptedData": encrypted_data,
                            "nonce": self.crypto.generate_nonce(),
                            "timestamp": self.crypto.generate_timestamp()
                        }
                    
                    # 发送绑定请求
                    bind_response = session.post(self.bind_inviter_url, json=bind_data, timeout=10)
                    
                    if bind_response.status_code != 200:
                        self.add_log(f"绑定失败: {bind_response.status_code}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试绑定 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                    bind_data = bind_response.json()
                    
                    if bind_data.get("encrypted") and bind_data.get("data"):
                        try:
                            decrypted_bind = self.crypto.decrypt_with_session_key(bind_data["data"], session_key)
                            self.add_log(f"解密后的绑定响应: {decrypted_bind}")
                            bind_data = decrypted_bind
                        except Exception as e:
                            self.add_log(f"解密绑定响应失败: {str(e)}")
                    
                    if bind_data.get("c") == 1:
                        device["invite_bound"] = True
                        success_count += 1
                        self.add_log(f"邀请码 {invite_code} 绑定成功到设备: {device['device_id']}")
                        self.save_devices()
                        break
                    else:
                        msg = bind_data.get("msg", "未知错误")
                        if "已经绑定过邀请人" in msg:
                            device["invite_bound"] = True
                            self.save_devices()
                            self.add_log(f"设备 {device['device_id']} 已经绑定过邀请人")
                            break
                        self.add_log(f"绑定失败: {msg}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试绑定 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                except Exception as e:
                    self.add_log(f"绑定出错: {str(e)}")
                    if attempt < max_retries - 1:
                        self.add_log(f"重试绑定 ({attempt+1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    break
        
        Clock.schedule_once(lambda dt: self.add_log(f'批量绑定完成，成功 {success_count} 个'), 0)
    
    def batch_query(self, instance):
        """批量查询"""
        self.stop_flag = False
        self.add_log('开始批量查询...')
        threading.Thread(target=self._batch_query_thread).start()
    
    def _batch_query_thread(self):
        """批量查询线程"""
        targets = list(self.selected_indices) if self.selected_indices else range(len(self.devices))
        
        for idx in targets:
            if self.stop_flag:
                break
            
            device = self.devices[idx]
            Clock.schedule_once(lambda dt, d=device: self.add_log(f'查询设备: {d["device_id"][:12]}'), 0)
            
            # 登录会自动查询账户信息
            if self.login(device):
                Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
        
        Clock.schedule_once(lambda dt: self.add_log('批量查询完成'), 0)
    
    def batch_set_password(self, instance):
        """批量设置密码"""
        self.stop_flag = False
        self.add_log('开始批量设置密码...')
        threading.Thread(target=self._batch_set_password_thread).start()
    
    def _batch_set_password_thread(self):
        """批量设置密码线程"""
        targets = list(self.selected_indices) if self.selected_indices else range(len(self.devices))
        success_count = 0
        
        for idx in targets:
            if self.stop_flag:
                break
            
            device = self.devices[idx]
            Clock.schedule_once(lambda dt, d=device: self.add_log(f'设置密码设备: {d["device_id"][:12]}'), 0)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 先登录
                    if not self.login(device):
                        break
                    
                    # 生成随机用户名和密码
                    username = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(random.randint(8, 16)))
                    password = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(random.randint(8, 16)))
                    
                    # 创建会话
                    session = self.get_session(device)
                    
                    # 生成设置密码请求
                    set_pass_payload = {
                        "username": username,
                        "password": password
                    }
                    
                    session_key = device.get("session_key")
                    if session_key:
                        set_pass_data = self.crypto.build_encrypted_request(
                            set_pass_payload,
                            device.get("session_id", str(uuid.uuid4())),
                            session_key
                        )
                    else:
                        encrypted_data = self.crypto.encrypt_with_fixed_key(set_pass_payload)
                        set_pass_data = {
                            "sessionId": device.get("session_id", str(uuid.uuid4())),
                            "encryptedData": encrypted_data,
                            "nonce": self.crypto.generate_nonce(),
                            "timestamp": self.crypto.generate_timestamp()
                        }
                    
                    # 发送设置密码请求
                    set_pass_response = session.post(self.set_password_url, json=set_pass_data, timeout=10)
                    
                    if set_pass_response.status_code != 200:
                        self.add_log(f"设置密码失败: {set_pass_response.status_code}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试设置密码 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                    set_pass_data = set_pass_response.json()
                    
                    if set_pass_data.get("encrypted") and set_pass_data.get("data"):
                        try:
                            decrypted_set_pass = self.crypto.decrypt_with_session_key(set_pass_data["data"], session_key)
                            self.add_log(f"解密后的设置密码响应: {decrypted_set_pass}")
                            set_pass_data = decrypted_set_pass
                        except Exception as e:
                            self.add_log(f"解密设置密码响应失败: {str(e)}")
                    
                    if set_pass_data.get("c") == 1:
                        device["account"] = username
                        device["password"] = password
                        success_count += 1
                        self.add_log(f"设备 {device['device_id']} 设置密码成功: 用户名={username}, 密码={password}")
                        self.save_devices()
                        Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
                        break
                    else:
                        self.add_log(f"设置密码失败: {set_pass_data.get('msg', '未知错误')}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试设置密码 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                except Exception as e:
                    self.add_log(f"设置密码出错: {str(e)}")
                    if attempt < max_retries - 1:
                        self.add_log(f"重试设置密码 ({attempt+1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    break
        
        Clock.schedule_once(lambda dt: self.add_log(f'批量设置密码完成，成功 {success_count} 个'), 0)
    
    def batch_destroy(self, instance):
        """批量销毁"""
        self.stop_flag = False
        self.add_log('开始批量销毁代币...')
        threading.Thread(target=self._batch_destroy_thread).start()
    
    def _batch_destroy_thread(self):
        """批量销毁线程"""
        targets = list(self.selected_indices) if self.selected_indices else range(len(self.devices))
        success_count = 0
        
        for idx in targets:
            if self.stop_flag:
                break
            
            device = self.devices[idx]
            Clock.schedule_once(lambda dt, d=device: self.add_log(f'销毁设备: {d["device_id"][:12]}'), 0)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 先登录
                    if not self.login(device):
                        break
                    
                    # 创建会话
                    session = self.get_session(device)
                    
                    # 生成销毁代币请求
                    amount = device.get("total_coins", 0)
                    if amount <= 0:
                        self.add_log(f"设备 {device['device_id']} 没有代币可销毁")
                        break
                    
                    destroy_payload = {
                        "amount": amount
                    }
                    
                    session_key = device.get("session_key")
                    if session_key:
                        destroy_data = self.crypto.build_encrypted_request(
                            destroy_payload,
                            device.get("session_id", str(uuid.uuid4())),
                            session_key
                        )
                    else:
                        encrypted_data = self.crypto.encrypt_with_fixed_key(destroy_payload)
                        destroy_data = {
                            "sessionId": device.get("session_id", str(uuid.uuid4())),
                            "encryptedData": encrypted_data,
                            "nonce": self.crypto.generate_nonce(),
                            "timestamp": self.crypto.generate_timestamp()
                        }
                    
                    # 发送销毁请求
                    destroy_response = session.post(self.coin_destroy_url, json=destroy_data, timeout=10)
                    
                    if destroy_response.status_code != 200:
                        self.add_log(f"销毁失败: {destroy_response.status_code}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试销毁 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                    destroy_data = destroy_response.json()
                    
                    if destroy_data.get("encrypted") and destroy_data.get("data"):
                        try:
                            decrypted_destroy = self.crypto.decrypt_with_session_key(destroy_data["data"], session_key)
                            self.add_log(f"解密后的销毁响应: {decrypted_destroy}")
                            destroy_data = decrypted_destroy
                        except Exception as e:
                            self.add_log(f"解密销毁响应失败: {str(e)}")
                    
                    if destroy_data.get("c") == 1:
                        device["total_coins"] = 0
                        success_count += 1
                        self.add_log(f"设备销毁代币成功: {device['device_id']}, 销毁 {amount} 个")
                        self.save_devices()
                        Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
                        break
                    else:
                        self.add_log(f"销毁失败: {destroy_data.get('msg', '未知错误')}")
                        if attempt < max_retries - 1:
                            self.add_log(f"重试销毁 ({attempt+1}/{max_retries})...")
                            time.sleep(1)
                            continue
                        break
                    
                except Exception as e:
                    self.add_log(f"销毁出错: {str(e)}")
                    if attempt < max_retries - 1:
                        self.add_log(f"重试销毁 ({attempt+1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    break
        
        Clock.schedule_once(lambda dt: self.add_log(f'批量销毁完成，成功 {success_count} 个'), 0)


if __name__ == '__main__':
    ZephAutoApp().run()
