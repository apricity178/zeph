"""
Zeph Auto Tool - Android Version
使用Kivy框架开发
"""

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
import json
import uuid
import time
import threading
import random
from datetime import datetime

# 导入加密模块
from zeph_crypto import ZephCrypto

# 设置窗口背景色
Window.clearcolor = (0.95, 0.95, 0.95, 1)


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
        tab_panel.add_widget(TabbedPanelHeader(text='设备管理', content=device_tab))
        
        # 批量操作标签页
        batch_tab = self.create_batch_tab()
        tab_panel.add_widget(TabbedPanelHeader(text='批量操作', content=batch_tab))
        
        # 日志标签页
        log_tab = self.create_log_tab()
        tab_panel.add_widget(TabbedPanelHeader(text='日志', content=log_tab))
        
        root.add_widget(tab_panel)
        
        # 状态栏
        self.status_label = Label(
            text='就绪',
            size_hint_y=None,
            height=30,
            color=(0.2, 0.2, 0.2, 1),
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
        row1.add_widget(Label(text='邀请码:', size_hint_x=0.2, bold=True))
        self.invite_code_input = TextInput(
            text=self.config.get('invite_code', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='输入邀请码'
        )
        row1.add_widget(self.invite_code_input)
        row1.add_widget(Label(text='代理:', size_hint_x=0.2, bold=True))
        self.proxy_url_input = TextInput(
            text=self.config.get('proxy_url', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='代理链接'
        )
        row1.add_widget(self.proxy_url_input)
        config_box.add_widget(row1)
        
        # 打码平台配置
        row2 = BoxLayout(size_hint_y=None, height=35)
        row2.add_widget(Label(text='打码用户:', size_hint_x=0.2, bold=True))
        self.captcha_user_input = TextInput(
            text=self.config.get('captcha_username', ''),
            multiline=False,
            size_hint_x=0.3,
            hint_text='用户名'
        )
        row2.add_widget(self.captcha_user_input)
        row2.add_widget(Label(text='打码密码:', size_hint_x=0.2, bold=True))
        self.captcha_pass_input = TextInput(
            text=self.config.get('captcha_password', ''),
            multiline=False,
            password=True,
            size_hint_x=0.3,
            hint_text='密码'
        )
        row2.add_widget(self.captcha_pass_input)
        config_box.add_widget(row2)
        
        # 保存配置按钮
        row3 = BoxLayout(size_hint_y=None, height=40)
        save_btn = Button(
            text='保存配置',
            size_hint_x=0.3,
            background_color=(0.3, 0.7, 0.3, 1)
        )
        save_btn.bind(on_press=self.save_config)
        row3.add_widget(save_btn)
        
        reset_btn = Button(
            text='重置签到',
            size_hint_x=0.3,
            background_color=(0.7, 0.7, 0.3, 1)
        )
        reset_btn.bind(on_press=self.reset_checkin_status)
        row3.add_widget(reset_btn)
        
        query_all_btn = Button(
            text='查询全部',
            size_hint_x=0.3,
            background_color=(0.3, 0.3, 0.7, 1)
        )
        query_all_btn.bind(on_press=self.query_all_accounts)
        row3.add_widget(query_all_btn)
        
        config_box.add_widget(row3)
        layout.add_widget(config_box)
        
        # 设备列表标题
        layout.add_widget(Label(
            text='设备列表（勾选要操作的设备）',
            size_hint_y=None,
            height=25,
            bold=True,
            color=(0.2, 0.2, 0.8, 1)
        ))
        
        # 表头
        header = BoxLayout(size_hint_y=None, height=35, spacing=2)
        header.add_widget(Label(text='选', size_hint_x=0.08, bold=True))
        header.add_widget(Label(text='设备ID', size_hint_x=0.3, bold=True))
        header.add_widget(Label(text='绑定', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='签到', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='活力', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='币值', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='天数', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='查', size_hint_x=0.12, bold=True))
        layout.add_widget(header)
        
        # 设备列表（可滚动）
        scroll = ScrollView(size_hint_y=0.5)
        self.device_list_layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
        self.device_list_layout.bind(minimum_height=self.device_list_layout.setter('height'))
        scroll.add_widget(self.device_list_layout)
        layout.add_widget(scroll)
        
        # 操作按钮
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
        
        create_btn = Button(text='创建设备', background_color=(0.2, 0.6, 0.2, 1))
        create_btn.bind(on_press=self.create_device)
        btn_box.add_widget(create_btn)
        
        bind_btn = Button(text='绑定邀请码', background_color=(0.2, 0.2, 0.6, 1))
        bind_btn.bind(on_press=self.bind_invite)
        btn_box.add_widget(bind_btn)
        
        checkin_btn = Button(text='签到', background_color=(0.6, 0.2, 0.6, 1))
        checkin_btn.bind(on_press=self.checkin)
        btn_box.add_widget(checkin_btn)
        
        destroy_btn = Button(text='销毁代币', background_color=(0.8, 0.4, 0.2, 1))
        destroy_btn.bind(on_press=self.destroy_coins)
        btn_box.add_widget(destroy_btn)
        
        delete_btn = Button(text='删除', background_color=(0.8, 0.2, 0.2, 1))
        delete_btn.bind(on_press=self.delete_device)
        btn_box.add_widget(delete_btn)
        
        stop_btn = Button(text='停止', background_color=(0.9, 0.1, 0.1, 1))
        stop_btn.bind(on_press=self.stop_all)
        btn_box.add_widget(stop_btn)
        
        layout.add_widget(btn_box)
        
        # 更新设备列表
        self.update_device_list()
        
        return layout
    
    def create_batch_tab(self):
        """创建批量操作标签页"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 批量创建设备
        create_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150, spacing=5)
        create_box.add_widget(Label(
            text='批量创建设备',
            size_hint_y=None,
            height=30,
            bold=True,
            font_size=16
        ))
        
        row1 = BoxLayout(size_hint_y=None, height=40)
        row1.add_widget(Label(text='数量:', size_hint_x=0.3, bold=True))
        self.batch_create_count = TextInput(
            text='5',
            multiline=False,
            size_hint_x=0.7,
            input_filter='int'
        )
        row1.add_widget(self.batch_create_count)
        create_box.add_widget(row1)
        
        create_btn = Button(
            text='开始批量创建',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.2, 1)
        )
        create_btn.bind(on_press=self.batch_create)
        create_box.add_widget(create_btn)
        
        layout.add_widget(create_box)
        
        # 批量操作
        batch_box = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=5)
        batch_box.add_widget(Label(
            text='批量操作（仅对选中设备）',
            size_hint_y=None,
            height=30,
            bold=True,
            font_size=16
        ))
        
        row2 = BoxLayout(size_hint_y=None, height=50, spacing=5)
        batch_checkin_btn = Button(text='批量签到', background_color=(0.6, 0.2, 0.6, 1))
        batch_checkin_btn.bind(on_press=self.batch_checkin)
        row2.add_widget(batch_checkin_btn)
        
        batch_bind_btn = Button(text='批量绑定', background_color=(0.2, 0.2, 0.6, 1))
        batch_bind_btn.bind(on_press=self.batch_bind)
        row2.add_widget(batch_bind_btn)
        
        batch_destroy_btn = Button(text='批量销毁', background_color=(0.8, 0.4, 0.2, 1))
        batch_destroy_btn.bind(on_press=self.batch_destroy)
        row2.add_widget(batch_destroy_btn)
        batch_box.add_widget(row2)
        
        row3 = BoxLayout(size_hint_y=None, height=50, spacing=5)
        batch_password_btn = Button(text='批量设密码', background_color=(0.2, 0.6, 0.6, 1))
        batch_password_btn.bind(on_press=self.batch_set_password)
        row3.add_widget(batch_password_btn)
        
        batch_query_btn = Button(text='批量查询', background_color=(0.3, 0.3, 0.7, 1))
        batch_query_btn.bind(on_press=self.batch_query)
        row3.add_widget(batch_query_btn)
        batch_box.add_widget(row3)
        
        layout.add_widget(batch_box)
        layout.add_widget(BoxLayout())  # 填充
        
        return layout
    
    def create_log_tab(self):
        """创建日志标签页"""
        layout = BoxLayout(orientation='vertical', padding=10)
        layout.add_widget(Label(
            text='运行日志',
            size_hint_y=None,
            height=30,
            bold=True,
            font_size=16
        ))
        
        self.log_text = TextInput(
            multiline=True,
            readonly=True,
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(0, 1, 0, 1),
            font_size=12
        )
        layout.add_widget(self.log_text)
        
        clear_btn = Button(
            text='清空日志',
            size_hint_y=None,
            height=40,
            background_color=(0.7, 0.2, 0.2, 1)
        )
        clear_btn.bind(on_press=self.clear_logs)
        layout.add_widget(clear_btn)
        
        return layout
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f'[{timestamp}] {message}\n'
        Clock.schedule_once(lambda dt: self._update_log(log_entry), 0)
    
    def _update_log(self, entry):
        """更新日志"""
        self.log_text.text += entry
        self.log_text.cursor = (len(self.log_text.text), 0)
    
    def clear_logs(self, instance):
        """清空日志"""
        self.log_text.text = ''
    
    def set_status(self, message):
        """设置状态"""
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', message), 0)
    
    def load_config(self):
        """加载配置"""
        self.config = {
            'invite_code': '',
            'proxy_url': '',
            'captcha_username': '',
            'captcha_password': ''
        }
        if self.config_store.exists('config'):
            stored = self.config_store.get('config')
            self.config.update(stored)
    
    def save_config(self, instance=None):
        """保存配置"""
        self.config = {
            'invite_code': self.invite_code_input.text,
            'proxy_url': self.proxy_url_input.text,
            'captcha_username': self.captcha_user_input.text,
            'captcha_password': self.captcha_pass_input.text
        }
        self.config_store.put('config', **self.config)
        self.log('配置已保存')
    
    def load_devices(self):
        """加载设备"""
        self.devices = []
        if self.device_store.exists('devices'):
            stored = self.device_store.get('devices')
            self.devices = stored.get('devices', [])
    
    def save_devices(self):
        """保存设备"""
        self.device_store.put('devices', devices=self.devices)
    
    def update_device_list(self):
        """更新设备列表"""
        self.device_list_layout.clear_widgets()
        
        for i, device in enumerate(self.devices):
            row = BoxLayout(size_hint_y=None, height=40, spacing=2)
            
            checkbox = CheckBox(size_hint_x=0.08)
            checkbox.active = i in self.selected_indices
            checkbox.bind(active=lambda cb, val, idx=i: self.on_checkbox_change(idx, val))
            row.add_widget(checkbox)
            
            device_id = device.get('device_id', '')[:12] + '...'
            row.add_widget(Label(text=device_id, size_hint_x=0.3, font_size=11))
            row.add_widget(Label(
                text='✓' if device.get('invite_bound') else '✗',
                size_hint_x=0.1,
                color=(0, 0.8, 0, 1) if device.get('invite_bound') else (0.8, 0, 0, 1)
            ))
            row.add_widget(Label(
                text='✓' if device.get('checked_in') else '✗',
                size_hint_x=0.1,
                color=(0, 0.8, 0, 1) if device.get('checked_in') else (0.8, 0, 0, 1)
            ))
            row.add_widget(Label(text=str(device.get('vitality', 0)), size_hint_x=0.1))
            row.add_widget(Label(text=str(device.get('coins', 0)), size_hint_x=0.1))
            row.add_widget(Label(text=str(device.get('continuous_days', 0)), size_hint_x=0.1))
            
            query_btn = Button(text='查', size_hint_x=0.12, font_size=10)
            query_btn.bind(on_press=lambda btn, idx=i: self.query_single_account(idx))
            row.add_widget(query_btn)
            
            self.device_list_layout.add_widget(row)
    
    def on_checkbox_change(self, index, value):
        """复选框改变"""
        if value:
            self.selected_indices.add(index)
        else:
            self.selected_indices.discard(index)
    
    def create_device(self, instance):
        """创建设备"""
        self.stop_flag = False
        self.log('开始创建设备...')
        threading.Thread(target=self._create_device_thread).start()
    
    def _create_device_thread(self):
        """创建设备线程"""
        try:
            device_id = ''.join(random.choices('0123456789abcdef', k=16))
            device_fingerprint = device_id
            session_id = str(uuid.uuid4())
            
            self.log(f'生成设备ID: {device_id}')
            
            device = {
                'device_id': device_id,
                'device_fingerprint': device_fingerprint,
                'session_id': session_id,
                'created_at': time.time(),
                'invite_bound': False,
                'checked_in': False,
                'vitality': 0,
                'coins': 0,
                'continuous_days': 0
            }
            
            self.devices.append(device)
            self.save_devices()
            
            Clock.schedule_once(lambda dt: self.update_device_list(), 0)
            Clock.schedule_once(lambda dt: self.log(f'设备 {device_id} 创建成功'), 0)
            Clock.schedule_once(lambda dt: self.set_status(f'已创建设备: {device_id}'), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.log(f'创建设备失败: {str(e)}'), 0)
    
    def bind_invite(self, instance):
        """绑定邀请码"""
        invite_code = self.invite_code_input.text
        if not invite_code:
            self.log('请先输入邀请码')
            return
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log(f'开始绑定邀请码: {invite_code}')
    
    def checkin(self, instance):
        """签到"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log('开始签到...')
    
    def destroy_coins(self, instance):
        """销毁代币"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log('开始销毁代币...')
    
    def delete_device(self, instance):
        """删除设备"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        for idx in sorted(self.selected_indices, reverse=True):
            device_id = self.devices[idx]['device_id']
            del self.devices[idx]
            self.log(f'删除设备: {device_id}')
        self.selected_indices.clear()
        self.save_devices()
        self.update_device_list()
    
    def stop_all(self, instance):
        """停止所有操作"""
        self.stop_flag = True
        self.log('已发送停止信号')
    
    def reset_checkin_status(self, instance):
        """重置签到状态"""
        for device in self.devices:
            device['checked_in'] = False
        self.save_devices()
        self.update_device_list()
        self.log('已重置签到状态')
    
    def query_single_account(self, index):
        """查询单个账户"""
        device = self.devices[index]
        self.log(f'查询设备: {device["device_id"]}')
    
    def query_all_accounts(self, instance):
        """查询所有账户"""
        self.log('开始查询所有账户...')
    
    def batch_create(self, instance):
        """批量创建"""
        try:
            count = int(self.batch_create_count.text)
            if count <= 0 or count > 100:
                self.log('请输入1-100之间的数量')
                return
            self.log(f'开始批量创建 {count} 个设备...')
            for i in range(count):
                if self.stop_flag:
                    break
                self._create_device_thread()
                time.sleep(0.3)
        except ValueError:
            self.log('请输入有效的数量')
    
    def batch_checkin(self, instance):
        """批量签到"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log(f'批量签到 {len(self.selected_indices)} 个设备...')
    
    def batch_bind(self, instance):
        """批量绑定"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log(f'批量绑定 {len(self.selected_indices)} 个设备...')
    
    def batch_destroy(self, instance):
        """批量销毁"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log(f'批量销毁 {len(self.selected_indices)} 个设备...')
    
    def batch_set_password(self, instance):
        """批量设置密码"""
        if not self.selected_indices:
            self.log('请先选择设备')
            return
        self.log(f'批量设置密码 {len(self.selected_indices)} 个设备...')
    
    def batch_query(self, instance):
        """批量查询"""
        self.query_all_accounts(instance)


if __name__ == '__main__':
    ZephAutoApp().run()
