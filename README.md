# Zeph Auto Tool - Android版本

## 项目说明

这是Zeph Auto Tool的Android版本，使用Kivy框架开发，可以打包为APK安装在Android设备上运行。

## 功能特性

- 设备管理（创建、删除、导出）
- 批量创建设备
- 邀请码绑定
- 自动签到（支持滑块验证码）
- 代币销毁
- 账户信息查询（活力值、代币、连续签到天数）
- 签到状态重置
- 代理支持
- 日志记录
- 数据本地存储

## 技术栈

- **框架**: Kivy (Python UI框架)
- **加密**: pycryptodome (AES加密)
- **网络**: requests (HTTP请求)
- **存储**: JsonStore (Kivy内置JSON存储)

## 项目结构

```
android_app/
├── main.py              # 主程序入口
├── zeph_crypto.py       # 加密模块
├── buildozer.spec       # Buildozer打包配置
├── .github/workflows/   # GitHub Actions配置
│   └── build_apk.yml    # 自动打包工作流
└── README.md           # 说明文档
```

## 打包步骤

### 方式一：GitHub Actions 在线打包（推荐）

这是最简单的方式，无需安装任何依赖，GitHub会自动为你打包APK。

#### 步骤：

1. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 创建一个新的公开仓库
   - 将 `android_app` 文件夹下的所有文件上传到仓库

2. **上传代码**
   ```bash
   # 初始化git仓库
   cd android_app
   git init
   git add .
   git commit -m "Initial commit"
   
   # 添加远程仓库（替换为你的仓库地址）
   git remote add origin https://github.com/你的用户名/仓库名.git
   git branch -M main
   git push -u origin main
   ```

3. **自动构建**
   - 代码推送到GitHub后，GitHub Actions会自动开始构建
   - 访问仓库的 "Actions" 标签页查看构建进度
   - 构建时间约10-20分钟

4. **下载APK**
   - 构建完成后，在Actions页面点击构建任务
   - 在 "Artifacts" 部分下载 `zeph-auto-tool-apk` 压缩包
   - 解压后即可获得APK文件

5. **创建版本发布（可选）**
   ```bash
   # 创建标签触发release构建
   git tag v1.0.0
   git push origin v1.0.0
   ```
   - APK会自动附加到GitHub Release中

#### 手动触发构建：
- 访问仓库的 "Actions" 标签页
- 选择 "Build Android APK" 工作流
- 点击 "Run workflow" 按钮

### 方式二：本地打包（需要Linux/WSL环境）

#### 1. 安装依赖

在Linux或WSL环境下安装buildozer：

```bash
# 安装buildozer
pip install buildozer

# 安装依赖
pip install kivy requests pycryptodome
```

#### 2. 配置buildozer

编辑 `buildozer.spec` 文件，确保以下配置正确：

```ini
# 应用标题
title = Zeph Auto Tool

# 包名
package.name = zephauto

# 包域名
package.domain = com.zephauto

# 依赖项
requirements = python3,kivy,requests,pycryptodome,Pillow

# Android权限
android.permissions = INTERNET, ACCESS_NETWORK_STATE, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
```

#### 3. 打包APK

在项目目录下运行：

```bash
# 首次打包（会自动下载Android SDK和NDK）
buildozer android debug

# 或者使用spec文件
buildozer -v android debug

# 打包release版本
buildozer android release
```

打包完成后，APK文件会生成在 `bin/` 目录下。

#### 4. 安装到手机

```bash
# 直接部署到连接的手机
buildozer android debug deploy run

# 或者手动安装APK
adb install bin/zephauto-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

## 使用说明

### 界面布局

应用包含4个标签页：

1. **设备标签页**
   - 配置邀请码和代理URL
   - 创建设备

2. **列表标签页**
   - 查看所有设备
   - 显示设备ID、活力值、代币、签到状态、绑定状态、连续签到天数
   - 全选/取消全选
   - 导出设备数据（JSON格式）

3. **操作标签页**
   - 批量签到
   - 批量绑定邀请码
   - 查询账户信息
   - 重置签到状态
   - 销毁代币
   - 停止操作

4. **日志标签页**
   - 查看操作日志
   - 清除日志

### 基本操作流程

1. 在**设备**标签页配置邀请码和代理（可选）
2. 点击"创建设备"生成新设备
3. 切换到**列表**标签页查看设备
4. 勾选需要操作的设备
5. 切换到**操作**标签页执行批量操作

## 注意事项

- 应用需要网络权限才能正常工作
- 设备数据保存在本地，卸载应用会丢失数据
- 建议定期导出设备数据备份

## 许可证

MIT License
