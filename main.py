"""
Zeph Auto Tool - Android Version
简洁、大方、易操作的界面设计
"""

import os
import sys

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
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp
import json
import uuid
import time
import threading
import random
import hashlib
import requests
from datetime import datetime

from zeph_crypto import ZephCrypto

def setup_chinese_font():
    try:
        font_paths = [
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/NotoSansSC-Regular.otf',
            '/system/fonts/DroidSansFallback.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/msyhbd.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/STZHONGS.TTF',
            'C:/Windows/Fonts/STFANGSO.TTF',
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                LabelBase.register('Roboto', font_path, font_path, font_path, font_path)
                print(f"Font loaded: {font_path}")
                return font_path
    except Exception as e:
        print(f"Font setup error: {e}")
    return None

CHINESE_FONT = setup_chinese_font()
Window.clearcolor = (0.12, 0.12, 0.14, 1)


class Theme:
    PRIMARY = (0.26, 0.59, 0.98, 1)
    SUCCESS = (0.30, 0.69, 0.31, 1)
    WARNING = (0.98, 0.73, 0.18, 1)
    DANGER = (0.86, 0.28, 0.26, 1)
    DARK = (0.18, 0.18, 0.20, 1)
    CARD = (0.22, 0.22, 0.24, 1)
    TEXT = (0.95, 0.95, 0.95, 1)
    TEXT_SECONDARY = (0.70, 0.70, 0.70, 1)


class CLabel(Label):
    def __init__(self, **kwargs):
        if CHINESE_FONT:
            kwargs['font_name'] = 'Roboto'
        super().__init__(**kwargs)


class CButton(Button):
    def __init__(self, **kwargs):
        if CHINESE_FONT:
            kwargs['font_name'] = 'Roboto'
        super().__init__(**kwargs)


class CTextInput(TextInput):
    def __init__(self, **kwargs):
        if CHINESE_FONT:
            kwargs['font_name'] = 'Roboto'
        super().__init__(**kwargs)


class Card(BoxLayout):
    def __init__(self, title="", **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.padding = dp(12)
        self.spacing = dp(8)
        
        if title:
            title_label = CLabel(
                text=title,
                size_hint_y=None,
                height=dp(28),
                color=Theme.TEXT,
                bold=True,
                font_size='16sp'
            )
            self.add_widget(title_label)


class ZephAutoApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crypto = ZephCrypto()
        self.devices = []
        self.stop_flag = False
        
        self.base_url = "https://myt.sale"
        self.login_url = f"{self.base_url}/api/device/login"
        self.signin_url = f"{self.base_url}/api/app/signin"
        self.bind_inviter_url = f"{self.base_url}/api/app/user/bind-inviter"
        self.captcha_generate_url = f"{self.base_url}/api/puzzle-captcha/generate"
        self.captcha_verify_url = f"{self.base_url}/api/puzzle-captcha/verify"
        self.register_url = f"{self.base_url}/api/app/device/register-with-puzzle"
        
        self.device_store = JsonStore('devices.json')
        self.config_store = JsonStore('config.json')
        
        self.load_devices()
        self.load_config()
        self.selected_indices = set()
    
    def build(self):
        self.title = 'Zeph Auto'
        
        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        
        header = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(8))
        header.add_widget(CLabel(
            text=' Zeph Auto Tool',
            font_size='22sp',
            bold=True,
            color=Theme.PRIMARY
        ))
        root.add_widget(header)
        
        tab_panel = TabbedPanel(do_default_tab=False, tab_pos='top_left')
        
        device_tab = self.create_device_tab()
        device_header = TabbedPanelHeader(text=' 设备')
        device_header.content = device_tab
        tab_panel.add_widget(device_header)
        
        list_tab = self.create_list_tab()
        list_header = TabbedPanelHeader(text=' 列表')
        list_header.content = list_tab
        tab_panel.add_widget(list_header)
        
        action_tab = self.create_action_tab()
        action_header = TabbedPanelHeader(text=' 操作')
        action_header.content = action_tab
        tab_panel.add_widget(action_header)
        
        log_tab = self.create_log_tab()
        log_header = TabbedPanelHeader(text=' 日志')
        log_header.content = log_tab
        tab_panel.add_widget(log_header)
        
        root.add_widget(tab_panel)
        
        self.status_label = CLabel(
            text='[OK] 就绪',
            size_hint_y=None,
            height=dp(32),
            color=Theme.TEXT_SECONDARY,
            font_size='13sp'
        )
        root.add_widget(self.status_label)
        
        return root
    
    def create_device_tab(self):
        # 使用ScrollView包装内容，确保不会超出标签页
        root = ScrollView()
        
        layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # 配置区域
        config_card = Card(title='基础配置')
        config_card.height = dp(200)
        config_card.size_hint_y = None
        
        # 邀请码输入行
        invite_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        invite_row.add_widget(CLabel(text='邀请码:', size_hint_x=0.18, color=Theme.TEXT, bold=True))
        self.invite_code_input = CTextInput(
            text=self.config.get('invite_code', ''),
            multiline=False,
            size_hint_x=0.82,
            hint_text='请输入邀请码',
            background_color=Theme.CARD,
            foreground_color=Theme.TEXT
        )
        invite_row.add_widget(self.invite_code_input)
        config_card.add_widget(invite_row)
        
        # 代理输入行
        proxy_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        proxy_row.add_widget(CLabel(text='代理URL:', size_hint_x=0.18, color=Theme.TEXT, bold=True))
        self.proxy_url_input = CTextInput(
            text=self.config.get('proxy_url', ''),
            multiline=False,
            size_hint_x=0.82,
            hint_text='http://api.proxy.com/get (可选)',
            background_color=Theme.CARD,
            foreground_color=Theme.TEXT
        )
        proxy_row.add_widget(self.proxy_url_input)
        config_card.add_widget(proxy_row)
        
        # 保存按钮
        save_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8), padding=(0, dp(5), 0, 0))
        save_btn = CButton(
            text='保存配置',
            size_hint_x=1,
            background_color=Theme.SUCCESS,
            color=Theme.TEXT
        )
        save_btn.bind(on_press=self.save_config)
        save_row.add_widget(save_btn)
        config_card.add_widget(save_row)
        
        layout.add_widget(config_card)
        
        # 创建设备区域
        create_card = Card(title='设备管理')
        create_card.height = dp(130)
        create_card.size_hint_y = None
        
        create_info = CLabel(
            text='点击按钮创建新设备',
            size_hint_y=None,
            height=dp(30),
            color=Theme.TEXT_SECONDARY,
            font_size='13sp'
        )
        create_card.add_widget(create_info)
        
        create_btn = CButton(
            text='创建设备',
            size_hint_y=None,
            height=dp(45),
            background_color=Theme.PRIMARY,
            color=Theme.TEXT
        )
        create_btn.bind(on_press=self.create_device)
        create_card.add_widget(create_btn)
        
        layout.add_widget(create_card)
        
        # 提示区域
        hint_card = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            padding=dp(8)
        )
        hint_label = CLabel(
            text='[TIP] 请在"列表"标签页查看和管理设备，在"操作"标签页执行批量操作',
            color=Theme.TEXT_SECONDARY,
            font_size='12sp'
        )
        hint_card.add_widget(hint_label)
        layout.add_widget(hint_card)
        
        root.add_widget(layout)
        return root
    
    def create_action_tab(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        title = CLabel(
            text=' 批量操作',
            size_hint_y=None,
            height=dp(40),
            font_size='18sp',
            bold=True,
            color=Theme.TEXT
        )
        layout.add_widget(title)
        
        btn_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(220))
        
        actions = [
            ('[OK] 批量签到', self.batch_signin, Theme.SUCCESS),
            (' 批量绑定', self.batch_bind, Theme.PRIMARY),
            ('� 查询账户', self.batch_query, Theme.WARNING),
            (' 重置签到', self.reset_signin_status, (0.6, 0.4, 0.8, 1)),
            (' 销毁代币', self.batch_destroy_coins, Theme.DANGER),
            ('[STOP] 停止操作', self.stop_operations, Theme.DARK),
        ]
        
        for text, callback, color in actions:
            btn = CButton(
                text=text,
                background_color=color,
                color=Theme.TEXT,
                font_size='15sp'
            )
            btn.bind(on_press=callback)
            btn_grid.add_widget(btn)
        
        layout.add_widget(btn_grid)
        
        info = CLabel(
            text='[TIP] 提示: 在列表中勾选设备后执行操作',
            size_hint_y=None,
            height=dp(50),
            color=Theme.TEXT_SECONDARY,
            font_size='13sp'
        )
        layout.add_widget(info)
        
        layout.add_widget(BoxLayout())
        return layout
    
    def create_list_tab(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        title = CLabel(
            text=' 设备列表',
            size_hint_y=None,
            height=dp(36),
            font_size='16sp',
            bold=True,
            color=Theme.TEXT
        )
        layout.add_widget(title)
        
        scroll = ScrollView()
        self.main_device_list = GridLayout(cols=1, spacing=dp(3), size_hint_y=None)
        self.main_device_list.bind(minimum_height=self.main_device_list.setter('height'))
        scroll.add_widget(self.main_device_list)
        layout.add_widget(scroll)
        
        btn_row1 = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        select_all_btn = CButton(
            text='[OK] 全选',
            size_hint_x=0.5,
            background_color=Theme.PRIMARY,
            color=Theme.TEXT
        )
        select_all_btn.bind(on_press=self.select_all_devices)
        btn_row1.add_widget(select_all_btn)
        
        deselect_btn = CButton(
            text='[X] 取消全选',
            size_hint_x=0.5,
            background_color=Theme.DARK,
            color=Theme.TEXT
        )
        deselect_btn.bind(on_press=self.deselect_all_devices)
        btn_row1.add_widget(deselect_btn)
        layout.add_widget(btn_row1)
        
        btn_row2 = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        export_all_btn = CButton(
            text=' 导出全部(JSON)',
            size_hint_x=0.5,
            background_color=Theme.SUCCESS,
            color=Theme.TEXT
        )
        export_all_btn.bind(on_press=lambda x: self.export_devices('json', selected_only=False))
        btn_row2.add_widget(export_all_btn)
        
        export_selected_btn = CButton(
            text=' 导出选中(JSON)',
            size_hint_x=0.5,
            background_color=Theme.WARNING,
            color=Theme.TEXT
        )
        export_selected_btn.bind(on_press=lambda x: self.export_devices('json', selected_only=True))
        btn_row2.add_widget(export_selected_btn)
        layout.add_widget(btn_row2)
        
        self.refresh_main_device_list()
        return layout
    
    def refresh_main_device_list(self):
        if not hasattr(self, 'main_device_list'):
            return
        self.main_device_list.clear_widgets()
        
        if not self.devices:
            no_device = CLabel(
                text='📭 暂无设备',
                size_hint_y=None,
                height=dp(40),
                color=Theme.TEXT_SECONDARY
            )
            self.main_device_list.add_widget(no_device)
            return
        
        header = BoxLayout(size_hint_y=None, height=dp(32))
        header.add_widget(CLabel(text='☑️', size_hint_x=0.08, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='设备ID', size_hint_x=0.22, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='活力', size_hint_x=0.08, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='金币', size_hint_x=0.08, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='签到', size_hint_x=0.08, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='绑定', size_hint_x=0.08, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='连续', size_hint_x=0.08, color=Theme.TEXT_SECONDARY, bold=True))
        header.add_widget(CLabel(text='操作', size_hint_x=0.3, color=Theme.TEXT_SECONDARY, bold=True))
        self.main_device_list.add_widget(header)
        
        for i, device in enumerate(self.devices):
            is_selected = i in self.selected_indices
            row_bg = Theme.CARD if is_selected else Theme.DARK
            
            row = BoxLayout(size_hint_y=None, height=dp(36))
            row.background_color = row_bg
            
            checkbox = CheckBox(size_hint_x=0.08, color=Theme.PRIMARY, active=is_selected)
            checkbox.bind(active=lambda cb, val, idx=i: self.on_checkbox_active(idx, val))
            row.add_widget(checkbox)
            
            device_id = device.get('device_id', 'N/A')[:10]
            id_label = CLabel(text=device_id, size_hint_x=0.22, color=Theme.TEXT)
            row.add_widget(id_label)
            
            vitality = str(device.get('vitality', 0))
            row.add_widget(CLabel(text=vitality, size_hint_x=0.08, color=Theme.TEXT))
            
            coins = f"{device.get('total_coins', 0):.1f}"
            row.add_widget(CLabel(text=coins, size_hint_x=0.08, color=Theme.TEXT))
            
            signed = '[OK]' if device.get('signed_in', False) else '[X]'
            row.add_widget(CLabel(text=signed, size_hint_x=0.08, color=Theme.TEXT))
            
            bound = '[OK]' if device.get('invite_bound', False) else '[X]'
            row.add_widget(CLabel(text=bound, size_hint_x=0.08, color=Theme.TEXT))
            
            continuous = str(device.get('continuous_days', 0))
            row.add_widget(CLabel(text=continuous, size_hint_x=0.08, color=Theme.TEXT))
            
            del_btn = CButton(
                text='[DEL]',
                size_hint_x=0.3,
                background_color=Theme.DANGER,
                color=Theme.TEXT,
                font_size='12sp'
            )
            del_btn.bind(on_press=lambda btn, idx=i: self.delete_device(idx))
            row.add_widget(del_btn)
            
            self.main_device_list.add_widget(row)
    
    def select_all_devices(self, instance=None):
        self.selected_indices = set(range(len(self.devices)))
        self.refresh_main_device_list()
        self.refresh_device_list()
        self.add_log('[OK] 已全选所有设备')
    
    def deselect_all_devices(self, instance=None):
        self.selected_indices = set()
        self.refresh_main_device_list()
        self.refresh_device_list()
        self.add_log('[X] 已取消全选')
    
    def export_devices(self, format_type='json', selected_only=False):
        if selected_only:
            if not self.selected_indices:
                self.add_log('[!] 请先选择要导出的设备')
                return
            devices_to_export = [self.devices[i] for i in self.selected_indices]
            export_name = '选中设备'
        else:
            devices_to_export = self.devices
            export_name = '全部设备'
        
        if not devices_to_export:
            self.add_log('[!] 没有可导出的设备')
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'zeph_devices_{timestamp}.json'
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_devices': len(devices_to_export),
                'devices': devices_to_export
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.add_log(f' 已导出 {len(devices_to_export)} 个设备到 {filename}')
            self.status_label.text = f'[OK] 已导出到 {filename}'
            
        except Exception as e:
            self.add_log(f'[X] 导出失败: {str(e)}')
    
    def create_log_tab(self):
        layout = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))
        
        scroll = ScrollView()
        self.log_label = CLabel(
            text=' 日志:\n',
            size_hint_y=None,
            markup=True,
            color=Theme.TEXT,
            font_size='12sp'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll.add_widget(self.log_label)
        layout.add_widget(scroll)
        
        clear_btn = CButton(
            text='[DEL] 清除日志',
            size_hint_y=None,
            height=dp(40),
            background_color=Theme.DARK,
            color=Theme.TEXT
        )
        clear_btn.bind(on_press=self.clear_log)
        layout.add_widget(clear_btn)
        
        return layout
    
    def on_checkbox_active(self, index, value):
        if value:
            self.selected_indices.add(index)
        else:
            self.selected_indices.discard(index)
    
    def add_log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_label.text += f'[{timestamp}] {message}\n'
    
    def clear_log(self, instance=None):
        self.log_label.text = ' 日志:\n'
    
    def load_devices(self):
        try:
            if self.device_store.exists('devices'):
                self.devices = self.device_store.get('devices')['data']
            else:
                self.devices = []
        except:
            self.devices = []
    
    def save_devices(self):
        self.device_store.put('devices', data=self.devices)
    
    def load_config(self):
        try:
            if self.config_store.exists('config'):
                self.config = self.config_store.get('config')['data']
            else:
                self.config = {}
        except:
            self.config = {}
    
    def save_config(self, instance=None):
        self.config['invite_code'] = self.invite_code_input.text
        self.config['proxy_url'] = self.proxy_url_input.text
        self.config_store.put('config', data=self.config)
        self.add_log('[OK] 配置已保存')
        self.status_label.text = '[OK] 配置已保存'
    
    def create_device(self, instance=None):
        def create_task():
            device_id = ''.join(random.choices('0123456789abcdef', k=16))
            device_fingerprint = device_id
            
            session = self.get_session({'cookies': {}})
            
            try:
                self.add_log(f' 设备 {device_id} 正在登录')
                
                login_payload = {
                    "deviceId": device_id,
                    "device_fingerprint": device_fingerprint
                }
                encrypted_login = self.crypto.encrypt_with_fixed_key(login_payload)
                login_data = {"encryptedPayload": encrypted_login}
                
                response = session.post(self.login_url, json=login_data, timeout=15)
                
                if response.status_code != 200:
                    self.add_log(f'[X] 登录失败: {response.status_code}')
                    return
                
                result = response.json()
                if result.get("encrypted") and result.get("data"):
                    result = self.crypto.decrypt_with_fixed_key(result["data"])
                
                if result.get("c") != 1:
                    self.add_log(f'[X] 登录失败: {result.get("msg", "未知错误")}')
                    return
                
                self.add_log(f'[OK] 设备 {device_id} 登录成功')
                
                self.add_log(f' 正在获取验证码')
                captcha_params = self.crypto.generate_captcha_request_params()
                captcha_response = session.post(self.captcha_generate_url, json=captcha_params, timeout=15)
                
                if captcha_response.status_code != 200:
                    self.add_log(f'[X] 获取验证码失败')
                    return
                
                captcha_result = self.crypto.decrypt_captcha_response(captcha_response.json())
                
                if captcha_result.get("c") != 1:
                    self.add_log(f'[X] 获取验证码失败: {captcha_result.get("msg")}')
                    return
                
                captcha_data = captcha_result.get("data", {})
                captcha_id = captcha_data.get("captchaId")
                puzzle_x = captcha_data.get("puzzleX")
                puzzle_y = captcha_data.get("puzzleY")
                
                self.add_log(f'[OK] 验证码获取成功')
                
                x_position = puzzle_x + random.uniform(-0.5, 0.5)
                y_position = puzzle_y + random.uniform(0, 5)
                
                trajectory = self.generate_drag_trajectory(0, puzzle_y, x_position, y_position)
                drag_time = trajectory[-1]["time"] if trajectory else 1500
                
                register_payload = {
                    "captchaId": captcha_id,
                    "xPosition": x_position,
                    "yPosition": y_position,
                    "dragTime": drag_time,
                    "dragTrajectory": trajectory
                }
                
                register_data = self.crypto.aes_gcm_encrypt(register_payload)
                register_data["deviceId"] = device_id
                
                self.add_log(f' 正在注册')
                register_response = session.post(self.register_url, json=register_data, timeout=15)
                
                if register_response.status_code != 200:
                    self.add_log(f'[X] 注册失败: {register_response.status_code}')
                    return
                
                register_result = register_response.json()
                
                if register_result.get("c") == 1:
                    result_data = register_result.get("data", {})
                    
                    new_device = {
                        "device_id": device_id,
                        "device_fingerprint": device_fingerprint,
                        "created_at": time.time(),
                        "token": result_data.get("token"),
                        "openid": result_data.get("openid"),
                        "vitality": result_data.get("user", {}).get("vitality", 0),
                        "total_coins": result_data.get("user", {}).get("totalCoins", 0),
                        "signed_in": False,
                        "cookies": dict(session.cookies)
                    }
                    
                    self.devices.append(new_device)
                    self.save_devices()
                    Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
                    self.add_log(f'[OK] 设备 {device_id} 注册成功')
                    self.status_label.text = f'[OK] 注册成功: {device_id}'
                else:
                    self.add_log(f'[X] 注册失败: {register_result.get("msg", "未知错误")}')
                    
            except Exception as e:
                self.add_log(f'[X] 注册出错: {str(e)}')
        
        threading.Thread(target=create_task, daemon=True).start()
    
    def generate_drag_trajectory(self, start_x, start_y, end_x, end_y):
        trajectory = []
        distance = abs(end_x - start_x)
        duration = int(distance * random.uniform(18, 25))
        duration = max(1000, min(3000, duration))
        
        num_points = random.randint(35, 50)
        
        for i in range(num_points):
            progress = i / (num_points - 1)
            
            if progress < 0.3:
                x = start_x + (end_x - start_x) * progress * progress * 3.3
            elif progress < 0.7:
                x = start_x + (end_x - start_x) * (0.3 + (progress - 0.3) * 1.75)
            else:
                remaining = 1 - progress
                x = end_x - (end_x - start_x) * remaining * remaining * 2.5
            
            jitter = random.uniform(-0.3, 0.3)
            y = start_y + (end_y - start_y) * progress + jitter
            
            time_val = int(duration * progress)
            
            trajectory.append({
                "x": round(x, 2),
                "y": round(y, 2),
                "time": time_val
            })
        
        return trajectory
    
    def delete_device(self, index):
        if 0 <= index < len(self.devices):
            device_id = self.devices[index].get('device_id', 'N/A')
            del self.devices[index]
            self.save_devices()
            self.refresh_device_list()
            self.add_log(f'[DEL] 删除设备: {device_id}')
    
    def get_session(self, device):
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
        
        proxies = self.get_proxy()
        if proxies:
            session.proxies.update(proxies)
            self.add_log(f"🌐 已设置代理")
        
        if device.get("cookies"):
            session.cookies.update(device["cookies"])
        
        return session
    
    def get_proxy(self):
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
            self.add_log(f"[X] 获取代理失败: {str(e)}")
        
        return None
    
    def stop_operations(self, instance=None):
        self.stop_flag = True
        self.add_log('[STOP] 正在停止操作...')
        self.status_label.text = '[STOP] 已停止'
    
    def batch_signin(self, instance=None):
        if not self.selected_indices:
            self.add_log('[!] 请先选择设备')
            return
        
        self.stop_flag = False
        selected_devices = [self.devices[i] for i in self.selected_indices]
        self.add_log(f'[OK] 开始批量签到，共 {len(selected_devices)} 个设备')
        
        def signin_task():
            for device in selected_devices:
                if self.stop_flag:
                    break
                self.do_signin(device)
        
        threading.Thread(target=signin_task, daemon=True).start()
    
    def do_signin(self, device):
        try:
            session = self.get_session(device)
            
            self.add_log(f" 设备 {device['device_id'][:10]} 正在登录")
            
            login_payload = {
                "deviceId": device['device_id'],
                "device_fingerprint": device['device_fingerprint']
            }
            encrypted_login = self.crypto.encrypt_with_fixed_key(login_payload)
            login_data = {"encryptedPayload": encrypted_login}
            
            response = session.post(self.login_url, json=login_data, timeout=15)
            
            if response.status_code != 200:
                self.add_log(f"[X] 登录失败: {response.status_code}")
                return
            
            result = response.json()
            if result.get("encrypted") and result.get("data"):
                result = self.crypto.decrypt_with_fixed_key(result["data"])
            
            if result.get("c") != 1:
                self.add_log(f"[X] 登录失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            session_info = data.get("session", {})
            device["session_id"] = session_info.get("sessionId", str(uuid.uuid4()))
            device["session_key"] = session_info.get("sessionKey", "")
            device["token"] = data.get("token", device.get("token", ""))
            
            user_data = data.get("user", {})
            if user_data:
                device["vitality"] = user_data.get("vitality", 0)
                device["total_coins"] = user_data.get("totalCoins", 0)
            
            device["cookies"] = dict(session.cookies)
            self.save_devices()
            
            self.add_log(f"[OK] 设备 {device['device_id'][:10]} 登录成功")
            
            self.add_log(f" 正在获取验证码")
            captcha_params = self.crypto.generate_captcha_request_params()
            captcha_response = session.post(self.captcha_generate_url, json=captcha_params, timeout=15)
            
            if captcha_response.status_code != 200:
                self.add_log(f"[X] 获取验证码失败")
                return
            
            captcha_result = self.crypto.decrypt_captcha_response(captcha_response.json())
            
            if captcha_result.get("c") != 1:
                self.add_log(f"[X] 获取验证码失败")
                return
            
            captcha_data = captcha_result.get("data", {})
            captcha_id = captcha_data.get("captchaId")
            puzzle_x = captcha_data.get("puzzleX")
            puzzle_y = captcha_data.get("puzzleY")
            
            self.add_log(f"[OK] 验证码获取成功")
            
            x_position = puzzle_x + random.uniform(-0.5, 0.5)
            y_position = puzzle_y + random.uniform(0, 5)
            
            trajectory = self.generate_drag_trajectory(0, puzzle_y, x_position, y_position)
            drag_time = trajectory[-1]["time"] if trajectory else 1500
            
            verify_payload = {
                "captchaId": captcha_id,
                "xPosition": x_position,
                "yPosition": y_position,
                "dragTime": drag_time,
                "dragTrajectory": trajectory
            }
            
            verify_data = self.crypto.aes_gcm_encrypt(verify_payload)
            
            self.add_log(f" 正在验证验证码")
            verify_response = session.post(self.captcha_verify_url, json=verify_data, timeout=15)
            
            if verify_response.status_code != 200:
                self.add_log(f"[X] 验证验证码失败")
                return
            
            verify_result = self.crypto.decrypt_captcha_response(verify_response.json())
            
            if verify_result.get("c") != 1:
                self.add_log(f"[X] 验证码验证失败: {verify_result.get('msg')}")
                return
            
            self.add_log(f"[OK] 验证码验证成功")
            
            self.add_log(f" 正在签到")
            
            checkin_payload = {
                "token": device.get("token", ""),
                "deviceId": device.get("device_id", "")
            }
            
            session_key = device.get("session_key")
            if session_key:
                checkin_data = self.crypto.build_encrypted_request(
                    checkin_payload,
                    device.get("session_id", str(uuid.uuid4())),
                    session_key
                )
            else:
                encrypted_data = self.crypto.encrypt_with_fixed_key(checkin_payload)
                checkin_data = {
                    "sessionId": device.get("session_id", str(uuid.uuid4())),
                    "encryptedData": encrypted_data,
                    "nonce": self.crypto.generate_nonce(),
                    "timestamp": self.crypto.generate_timestamp()
                }
            
            signin_response = session.post(self.signin_url, json=checkin_data, timeout=15)
            
            if signin_response.status_code != 200:
                self.add_log(f"[X] 签到失败: {signin_response.status_code}")
                return
            
            signin_result = signin_response.json()
            
            if signin_result.get("encrypted") and signin_result.get("data"):
                try:
                    signin_result = self.crypto.decrypt_with_session_key(signin_result["data"], session_key)
                except Exception as e:
                    self.add_log(f"[!] 解密签到响应失败: {str(e)}")
            
            if signin_result.get("c") == 1:
                self.add_log(f"[OK] 设备 {device['device_id'][:10]} 签到成功")
                device['signed_in'] = True
                self.save_devices()
                Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
            else:
                msg = signin_result.get('msg', '未知错误')
                if "今日已签到" in msg:
                    device['signed_in'] = True
                    self.save_devices()
                    self.add_log(f"[OK] 设备 {device['device_id'][:10]} 今日已签到")
                else:
                    self.add_log(f"[X] 签到失败: {msg}")
                
        except Exception as e:
            self.add_log(f"[X] 签到出错: {str(e)}")
    
    def batch_bind(self, instance=None):
        invite_code = self.config.get('invite_code', '')
        if not invite_code:
            self.add_log('[!] 请先设置邀请码')
            return
        
        if not self.selected_indices:
            self.add_log('[!] 请先选择设备')
            return
        
        self.stop_flag = False
        selected_devices = [self.devices[i] for i in self.selected_indices]
        self.add_log(f' 开始批量绑定，共 {len(selected_devices)} 个设备')
        
        def bind_task():
            for device in selected_devices:
                if self.stop_flag:
                    break
                self.do_bind_invite(device, invite_code)
        
        threading.Thread(target=bind_task, daemon=True).start()
    
    def do_bind_invite(self, device, invite_code):
        try:
            session = self.get_session(device)
            
            self.add_log(f" 设备 {device['device_id'][:10]} 正在登录")
            
            login_payload = {
                "deviceId": device['device_id'],
                "device_fingerprint": device['device_fingerprint']
            }
            encrypted_login = self.crypto.encrypt_with_fixed_key(login_payload)
            login_data = {"encryptedPayload": encrypted_login}
            
            response = session.post(self.login_url, json=login_data, timeout=15)
            
            if response.status_code != 200:
                self.add_log(f"[X] 登录失败: {response.status_code}")
                return
            
            result = response.json()
            if result.get("encrypted") and result.get("data"):
                result = self.crypto.decrypt_with_fixed_key(result["data"])
            
            if result.get("c") != 1:
                self.add_log(f"[X] 登录失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            session_info = data.get("session", {})
            device["session_id"] = session_info.get("sessionId", str(uuid.uuid4()))
            device["session_key"] = session_info.get("sessionKey", "")
            device["token"] = data.get("token", device.get("token", ""))
            device["cookies"] = dict(session.cookies)
            self.save_devices()
            
            self.add_log(f"[OK] 设备 {device['device_id'][:10]} 登录成功")
            
            if device.get('invite_bound', False):
                self.add_log(f"[!] 设备 {device['device_id'][:10]} 已绑定邀请码")
                return
            
            self.add_log(f" 正在绑定邀请码")
            
            bind_payload = {"token": {}, "inviteCode": invite_code}
            
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
            
            bind_response = session.post(self.bind_inviter_url, json=bind_data, timeout=15)
            
            if bind_response.status_code != 200:
                self.add_log(f"[X] 绑定失败: {bind_response.status_code}")
                return
            
            bind_result = bind_response.json()
            
            if bind_result.get("encrypted") and bind_result.get("data"):
                try:
                    bind_result = self.crypto.decrypt_with_session_key(bind_result["data"], session_key)
                except Exception as e:
                    self.add_log(f"[!] 解密绑定响应失败: {str(e)}")
            
            if bind_result.get("c") == 1:
                self.add_log(f"[OK] 设备 {device['device_id'][:10]} 绑定成功")
                device['invite_bound'] = True
                device['invite_code'] = invite_code
                self.save_devices()
                Clock.schedule_once(lambda dt: self.refresh_main_device_list(), 0)
            else:
                self.add_log(f"[X] 绑定失败: {bind_result.get('msg', '未知错误')}")
                
        except Exception as e:
            self.add_log(f"[X] 绑定出错: {str(e)}")
    
    def batch_query(self, instance=None):
        if not self.selected_indices:
            self.add_log('[!] 请先选择设备')
            return
        
        self.stop_flag = False
        selected_devices = [self.devices[i] for i in self.selected_indices]
        self.add_log(f'� 开始查询账户信息，共 {len(selected_devices)} 个设备')
        
        def query_task():
            for device in selected_devices:
                if self.stop_flag:
                    break
                self.do_query_account(device)
        
        threading.Thread(target=query_task, daemon=True).start()
    
    def do_query_account(self, device):
        try:
            session = self.get_session(device)
            
            self.add_log(f" 设备 {device['device_id'][:10]} 正在登录")
            
            login_payload = {
                "deviceId": device['device_id'],
                "device_fingerprint": device['device_fingerprint']
            }
            encrypted_login = self.crypto.encrypt_with_fixed_key(login_payload)
            login_data = {"encryptedPayload": encrypted_login}
            
            response = session.post(self.login_url, json=login_data, timeout=15)
            
            if response.status_code != 200:
                self.add_log(f"[X] 登录失败: {response.status_code}")
                return
            
            result = response.json()
            if result.get("encrypted") and result.get("data"):
                result = self.crypto.decrypt_with_fixed_key(result["data"])
            
            if result.get("c") != 1:
                self.add_log(f"[X] 登录失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            session_info = data.get("session", {})
            device["session_id"] = session_info.get("sessionId", str(uuid.uuid4()))
            device["session_key"] = session_info.get("sessionKey", "")
            device["token"] = data.get("token", device.get("token", ""))
            device["cookies"] = dict(session.cookies)
            
            user_data = data.get("user", {})
            vitality = user_data.get("vitality", 0)
            total_coins = user_data.get("totalCoins", 0)
            continuous_days = user_data.get("continuousDays", 0)
            
            device["vitality"] = vitality
            device["total_coins"] = total_coins
            device["continuous_days"] = continuous_days
            
            self.save_devices()
            
            self.add_log(f"[OK] 设备 {device['device_id'][:10]} 查询成功")
            self.add_log(f"   活力值: {vitality}, 代币: {total_coins:.2f}, 连续签到: {continuous_days}天")
            
            Clock.schedule_once(lambda dt: self.refresh_main_device_list(), 0)
            
        except Exception as e:
            self.add_log(f"[X] 查询出错: {str(e)}")
    
    def reset_signin_status(self, instance=None):
        if not self.selected_indices:
            self.add_log('[!] 请先选择设备')
            return
        
        count = 0
        for idx in self.selected_indices:
            if 0 <= idx < len(self.devices):
                self.devices[idx]['signed_in'] = False
                count += 1
        
        self.save_devices()
        self.refresh_main_device_list()
        self.refresh_device_list()
        self.add_log(f' 已重置 {count} 个设备的签到状态')
        self.status_label.text = f'[OK] 已重置 {count} 个设备签到状态'
    
    def batch_destroy_coins(self, instance=None):
        if not self.selected_indices:
            self.add_log('[!] 请先选择设备')
            return
        
        self.stop_flag = False
        selected_devices = [self.devices[i] for i in self.selected_indices]
        self.add_log(f' 开始批量销毁代币，共 {len(selected_devices)} 个设备')
        
        def destroy_task():
            for device in selected_devices:
                if self.stop_flag:
                    break
                self.do_destroy_coins(device)
        
        threading.Thread(target=destroy_task, daemon=True).start()
    
    def do_destroy_coins(self, device):
        try:
            session = self.get_session(device)
            
            self.add_log(f" 设备 {device['device_id'][:10]} 正在登录")
            
            login_payload = {
                "deviceId": device['device_id'],
                "device_fingerprint": device['device_fingerprint']
            }
            encrypted_login = self.crypto.encrypt_with_fixed_key(login_payload)
            login_data = {"encryptedPayload": encrypted_login}
            
            response = session.post(self.login_url, json=login_data, timeout=15)
            
            if response.status_code != 200:
                self.add_log(f"[X] 登录失败: {response.status_code}")
                return
            
            result = response.json()
            if result.get("encrypted") and result.get("data"):
                result = self.crypto.decrypt_with_fixed_key(result["data"])
            
            if result.get("c") != 1:
                self.add_log(f"[X] 登录失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            session_info = data.get("session", {})
            device["session_id"] = session_info.get("sessionId", str(uuid.uuid4()))
            device["session_key"] = session_info.get("sessionKey", "")
            device["token"] = data.get("token", device.get("token", ""))
            device["cookies"] = dict(session.cookies)
            self.save_devices()
            
            self.add_log(f"[OK] 设备 {device['device_id'][:10]} 登录成功")
            
            coins = device.get('total_coins', 0)
            if coins <= 0:
                self.add_log(f"[!] 设备 {device['device_id'][:10]} 无代币可销毁")
                return
            
            self.add_log(f" 正在销毁 {coins:.2f} 代币")
            
            destroy_payload = {"amount": coins}
            
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
            
            destroy_url = f"{self.base_url}/api/app/coin/destroy"
            destroy_response = session.post(destroy_url, json=destroy_data, timeout=15)
            
            if destroy_response.status_code != 200:
                self.add_log(f"[X] 销毁失败: {destroy_response.status_code}")
                return
            
            destroy_result = destroy_response.json()
            
            if destroy_result.get("encrypted") and destroy_result.get("data"):
                try:
                    destroy_result = self.crypto.decrypt_with_session_key(destroy_result["data"], session_key)
                except Exception as e:
                    self.add_log(f"[!] 解密销毁响应失败: {str(e)}")
            
            if destroy_result.get("c") == 1:
                self.add_log(f"[OK] 设备 {device['device_id'][:10]} 代币销毁成功")
                device['total_coins'] = 0
                self.save_devices()
                Clock.schedule_once(lambda dt: self.refresh_main_device_list(), 0)
            else:
                self.add_log(f"[X] 销毁失败: {destroy_result.get('msg', '未知错误')}")
                
        except Exception as e:
            self.add_log(f"[X] 销毁出错: {str(e)}")


if __name__ == '__main__':
    ZephAutoApp().run()
