[app]
# 应用标题
title = Zeph Auto Tool

# 包名
package.name = zephauto

# 包域名
package.domain = com.zephauto

# 主程序文件
source.dir = .

# 源代码包含的文件
source.include_patterns = main.py,zeph_crypto.py,README.md

# 包含的文件
source.include_exts = py,png,jpg,kv,atlas,json,txt

# 版本号
version = 1.0.0

# 依赖项
requirements = python3,kivy,requests,pycryptodome,urllib3,charset-normalizer,idna,certifi

# 添加Android权限
android.permissions = INTERNET, ACCESS_NETWORK_STATE, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Android API版本
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b

# 架构
android.archs = arm64-v8a, armeabi-v7a

# 应用图标
# icon.filename = %(source.dir)s/icon.png

# 屏幕方向
orientation = portrait

# 全屏模式
fullscreen = 0

# 是否使用Android日志
android.logcat_filters = *:S python:D

# 构建模式 (debug/release)
android.build_mode = debug

# 是否启用AndroidX
android.enable_androidx = True

[buildozer]
# 构建目录
build_dir = ./.buildozer

# 应用目录
bin_dir = ./bin

# 日志级别
log_level = 2

# 警告模式
warn_on_root = 1
