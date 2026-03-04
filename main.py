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
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # 配置区域
        config_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150, spacing=3)
        
        # 邀请码和代理
        row1 = BoxLayout(size_hint_y=None, height=35)
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
        row2 = BoxLayout(size_hint_y=None, height=35)
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
        row3 = BoxLayout(size_hint_y=None, height=40)
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
            height=25,
            bold=True,
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(list_label)
        
        # 设备列表滚动区域
        scroll = ScrollView()
        self.device_list_layout = GridLayout(
            cols=1,
            spacing=2,
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
            'account': '',
            'password': '',
            'vitality': 0,
            'total_coins': 0,
            'signed_in': False,
            'bound': False
        }
        self.devices.append(device)
        self.save_devices()
        self.refresh_device_list()
        self.add_log(f'创建新设备: {device_id}')
        self.status_label.text = f'创建新设备: {device_id}'
    
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
    
    def batch_signin(self, instance):
        """批量签到"""
        self.stop_flag = False
        self.add_log('开始批量签到...')
        threading.Thread(target=self._batch_signin_thread).start()
    
    def _batch_signin_thread(self):
        """批量签到线程"""
        targets = list(self.selected_indices) if self.selected_indices else range(len(self.devices))
        for idx in targets:
            if self.stop_flag:
                break
            device = self.devices[idx]
            Clock.schedule_once(lambda dt, d=device: self.add_log(f'签到设备: {d["device_id"][:12]}'), 0)
            # 模拟签到成功
            device['signed_in'] = True
        self.save_devices()
        Clock.schedule_once(lambda dt: self.refresh_device_list(), 0)
        Clock.schedule_once(lambda dt: self.add_log('批量签到完成'), 0)
    
    def batch_bind(self, instance):
        """批量绑定"""
        self.stop_flag = False
        invite_code = self.invite_code_input.text
        if not invite_code:
            self.add_log('错误: 请输入邀请码')
            return
        self.add_log(f'开始批量绑定邀请码: {invite_code}')
    
    def batch_query(self, instance):
        """批量查询"""
        self.stop_flag = False
        self.add_log('开始批量查询...')
    
    def batch_set_password(self, instance):
        """批量设置密码"""
        self.stop_flag = False
        self.add_log('开始批量设置密码...')
    
    def batch_destroy(self, instance):
        """批量销毁"""
        self.stop_flag = False
        self.add_log('开始批量销毁代币...')


if __name__ == '__main__':
    ZephAutoApp().run()
