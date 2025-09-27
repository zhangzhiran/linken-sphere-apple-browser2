#!/usr/bin/env python3
"""
Linken Sphere Apple Browser - 简化GUI界面
紧凑、简洁、功能完整的用户界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import asyncio
import json
import os
import sys
import platform
from datetime import datetime

# 尝试导入主程序
try:
    from linken_sphere_playwright_browser import LinkenSphereAppleBrowser
except ImportError:
    LinkenSphereAppleBrowser = None

class SimpleLinkenGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # 配置
        self.config = {
            'browse_duration': 60,
            'major_cycles': 3,
            'minor_cycles_per_major': 8,
            'max_retries': 3,
            'linken_api_port': 40080,  # 修正：使用正确的 Linken Sphere API 端口
            'debug_port': 12345,
            'max_threads': 2,
            # 'use_existing_session': True  # 已删除：不再使用现有会话功能
        }
        
        # 状态
        self.browser_threads = {}
        self.thread_counter = 0
        self.is_running = False
        self.selected_session = None  # 用户选择的特定会话
        self.available_profiles = []  # 可用的配置文件列表
        self.used_profiles = set()    # 已使用的配置文件UUID

        # 多线程资源管理
        self.used_debug_ports = set()  # 已使用的调试端口
        self.resource_lock = threading.Lock()  # 资源分配锁
        
        self.create_widgets()
        self.load_config()
        self.refresh_profiles()  # 获取可用的配置文件
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title("🔗 Linken Sphere Apple Browser")
        self.root.geometry("700x550")
        self.root.configure(bg='#2c2c2c')
        self.root.resizable(True, True)
        self.root.minsize(600, 400)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 设置应用图标
        self.set_application_icon()

    def set_application_icon(self):
        """设置应用程序图标 - 跨平台支持"""
        try:
            # 获取当前脚本目录
            if getattr(sys, 'frozen', False):
                # 如果是打包的可执行文件
                app_dir = os.path.dirname(sys.executable)
            else:
                # 如果是Python脚本
                app_dir = os.path.dirname(os.path.abspath(__file__))

            # 根据平台选择图标文件
            if platform.system() == "Windows":
                icon_path = os.path.join(app_dir, "app_icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    print(f"✅ 设置Windows图标: {icon_path}")
                else:
                    print(f"⚠️ Windows图标文件不存在: {icon_path}")

            elif platform.system() == "Darwin":  # macOS
                # macOS使用PNG图标
                icon_path = os.path.join(app_dir, "app_icon.png")
                if os.path.exists(icon_path):
                    # 在macOS上，tkinter可以使用PNG作为图标
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(icon_path)
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.root.iconphoto(True, photo)
                        print(f"✅ 设置macOS图标: {icon_path}")
                    except ImportError:
                        # 如果没有PIL，使用默认方法
                        self.root.iconbitmap(icon_path)
                        print(f"✅ 设置macOS图标(默认): {icon_path}")
                else:
                    print(f"⚠️ macOS图标文件不存在: {icon_path}")

            else:  # Linux和其他系统
                icon_path = os.path.join(app_dir, "app_icon.png")
                if os.path.exists(icon_path):
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(icon_path)
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.root.iconphoto(True, photo)
                        print(f"✅ 设置Linux图标: {icon_path}")
                    except ImportError:
                        print(f"⚠️ PIL不可用，无法设置Linux图标")
                else:
                    print(f"⚠️ Linux图标文件不存在: {icon_path}")

        except Exception as e:
            print(f"⚠️ 设置图标失败: {e}")

    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='#2c2c2c')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = tk.Label(main_frame, text="🔗 Linken Sphere Apple Browser", 
                              bg='#2c2c2c', fg='white', font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # 配置区域
        self.create_config_section(main_frame)
        
        # 控制区域
        self.create_control_section(main_frame)
        
        # 状态区域
        self.create_status_section(main_frame)
        
        # 日志区域
        self.create_log_section(main_frame)
    
    def create_config_section(self, parent):
        """创建配置区域"""
        config_frame = tk.LabelFrame(parent, text="⚙️ 配置", bg='#2c2c2c', fg='white', font=('Arial', 10, 'bold'))
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 配置变量
        self.browse_duration_var = tk.StringVar(value=str(self.config['browse_duration']))
        self.major_cycles_var = tk.StringVar(value=str(self.config['major_cycles']))
        self.minor_cycles_var = tk.StringVar(value=str(self.config['minor_cycles_per_major']))
        self.max_threads_var = tk.StringVar(value=str(self.config['max_threads']))
        # self.use_existing_session_var = tk.BooleanVar(value=self.config.get('use_existing_session', False))  # 已删除
        self.debug_port_var = tk.StringVar(value=str(self.config['debug_port']))
        
        # 第一行：基本配置
        row1 = tk.Frame(config_frame, bg='#2c2c2c')
        row1.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(row1, text="浏览时长(秒):", bg='#2c2c2c', fg='white').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.browse_duration_var, width=8, bg='#404040', fg='white').pack(side=tk.LEFT, padx=(5, 15))
        
        tk.Label(row1, text="大循环:", bg='#2c2c2c', fg='white').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.major_cycles_var, width=5, bg='#404040', fg='white').pack(side=tk.LEFT, padx=(5, 15))
        
        tk.Label(row1, text="小循环:", bg='#2c2c2c', fg='white').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.minor_cycles_var, width=5, bg='#404040', fg='white').pack(side=tk.LEFT, padx=(5, 15))
        
        tk.Label(row1, text="线程数:", bg='#2c2c2c', fg='white').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.max_threads_var, width=5, bg='#404040', fg='white').pack(side=tk.LEFT, padx=5)

        # 第二行：高级选项
        row2 = tk.Frame(config_frame, bg='#2c2c2c')
        row2.pack(fill=tk.X, padx=10, pady=5)

        # 使用现有会话选项 - 已删除
        # self.existing_session_checkbox = tk.Checkbutton(...) # 已删除

        # 刷新会话状态按钮
        self.refresh_sessions_btn = tk.Button(
            row2,
            text="🔄 刷新会话状态",
            command=self.refresh_session_status,
            bg="#1e3a8a",
            fg="white",
            font=("Arial", 9),
            relief=tk.RAISED,
            bd=1,
            cursor="hand2"
        )
        self.refresh_sessions_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 会话选择按钮
        self.select_session_btn = tk.Button(
            row2,
            text="🎯 选择会话",
            command=self.show_session_selector,
            bg="#6f42c1",
            fg="white",
            font=("Arial", 9),
            relief=tk.RAISED,
            bd=1,
            cursor="hand2"
        )
        self.select_session_btn.pack(side=tk.RIGHT, padx=(5, 0))



        # 第三行：调试端口配置
        row3 = tk.Frame(config_frame, bg='#2c2c2c')
        row3.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(row3, text="调试端口:", bg='#2c2c2c', fg='white').pack(side=tk.LEFT)
        tk.Entry(row3, textvariable=self.debug_port_var, width=8, bg='#404040', fg='white').pack(side=tk.LEFT, padx=(5, 15))

        # 调试端口说明
        tk.Label(row3, text="(启动会话时使用的调试端口)", bg='#2c2c2c', fg='#888888', font=('Arial', 8)).pack(side=tk.LEFT, padx=(10, 0))

        # 配置按钮
        button_row = tk.Frame(config_frame, bg='#2c2c2c')
        button_row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_row, text="💾 保存", command=self.save_config, 
                 bg='#0d7377', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_row, text="📁 导入", command=self.import_config, 
                 bg='#0d7377', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_row, text="📤 导出", command=self.export_config, 
                 bg='#0d7377', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
    
    def create_control_section(self, parent):
        """创建控制区域"""
        control_frame = tk.LabelFrame(parent, text="🎮 控制", bg='#2c2c2c', fg='white', font=('Arial', 10, 'bold'))
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        button_frame = tk.Frame(control_frame, bg='#2c2c2c')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 主要控制按钮
        self.start_button = tk.Button(button_frame, text="🚀 开始", command=self.start_automation,
                                     bg='#28a745', fg='white', font=('Arial', 10, 'bold'), width=8)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="⏹️ 停止", command=self.stop_all_automation,
                                    bg='#dc3545', fg='white', font=('Arial', 10, 'bold'), width=8)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.new_thread_button = tk.Button(button_frame, text="➕ 新线程", command=self.create_new_thread,
                                          bg='#17a2b8', fg='white', font=('Arial', 10, 'bold'), width=8)
        self.new_thread_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🗑️ 清理", command=self.cleanup_finished_threads,
                 bg='#6c757d', fg='white', font=('Arial', 10, 'bold'), width=8).pack(side=tk.LEFT, padx=5)
    
    def create_status_section(self, parent):
        """创建状态区域"""
        status_frame = tk.LabelFrame(parent, text="📊 状态", bg='#2c2c2c', fg='white', font=('Arial', 10, 'bold'))
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_content = tk.Frame(status_frame, bg='#2c2c2c')
        status_content.pack(fill=tk.X, padx=10, pady=5)
        
        # 状态标签
        self.status_label = tk.Label(status_content, text="状态: 就绪", bg='#2c2c2c', fg='#28a745', font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT)
        
        self.threads_label = tk.Label(status_content, text="线程: 0/2", bg='#2c2c2c', fg='#17a2b8', font=('Arial', 10))
        self.threads_label.pack(side=tk.RIGHT)
        
        # 线程列表框架
        thread_list_frame = tk.Frame(status_frame, bg='#2c2c2c')
        thread_list_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # 线程列表
        self.thread_listbox = tk.Listbox(thread_list_frame, height=3, bg='#404040', fg='white',
                                        selectbackground='#0d7377', font=('Consolas', 9))
        self.thread_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 线程控制按钮
        thread_control_frame = tk.Frame(thread_list_frame, bg='#2c2c2c')
        thread_control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        tk.Button(thread_control_frame, text="⏸️", command=self.pause_selected_thread,
                 bg='#ffc107', fg='black', font=('Arial', 8), width=3).pack(pady=1)
        tk.Button(thread_control_frame, text="▶️", command=self.resume_selected_thread,
                 bg='#28a745', fg='white', font=('Arial', 8), width=3).pack(pady=1)
        tk.Button(thread_control_frame, text="⏹️", command=self.stop_selected_thread,
                 bg='#dc3545', fg='white', font=('Arial', 8), width=3).pack(pady=1)
    
    def create_log_section(self, parent):
        """创建日志区域"""
        log_frame = tk.LabelFrame(parent, text="📝 日志", bg='#2c2c2c', fg='white', font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志控制
        log_control = tk.Frame(log_frame, bg='#2c2c2c')
        log_control.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Button(log_control, text="🗑️ 清空", command=self.clear_logs, 
                 bg='#6c757d', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(log_control, text="💾 保存", command=self.save_logs, 
                 bg='#6c757d', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        # 日志文本
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg='#1e1e1e', fg='#00ff00',
                                                 font=('Consolas', 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists("linken_sphere_config.json"):
                with open("linken_sphere_config.json", 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)

                # 更新GUI
                self.browse_duration_var.set(str(self.config['browse_duration']))
                self.major_cycles_var.set(str(self.config['major_cycles']))
                self.minor_cycles_var.set(str(self.config['minor_cycles_per_major']))
                self.max_threads_var.set(str(self.config['max_threads']))
                # self.use_existing_session_var.set(self.config.get('use_existing_session', True))  # 已删除
                self.debug_port_var.set(str(self.config.get('debug_port', 12345)))

                self.log_message("✅ 配置已加载")
        except Exception as e:
            self.log_message(f"⚠️ 加载配置失败: {e}")

    def is_session_running(self, session):
        """判断会话是否正在运行"""
        status = session.get('status', '').lower()
        # 包含 'running' 或 'automation' 的状态都视为运行中
        return 'running' in status or 'automation' in status

    def refresh_session_status(self):
        """刷新会话状态"""
        try:
            import requests

            # 获取会话状态
            response = requests.get("http://127.0.0.1:40080/sessions", timeout=5)
            response.raise_for_status()
            sessions = response.json()

            # 统计会话状态 - 使用新的判断逻辑
            running_sessions = [s for s in sessions if self.is_session_running(s)]
            stopped_sessions = [s for s in sessions if not self.is_session_running(s)]
            running_count = len(running_sessions)
            stopped_count = len(stopped_sessions)
            total_count = len(sessions)

            # 显示状态信息
            status_msg = f"会话状态: 运行中 {running_count} | 已停止 {stopped_count} | 总计 {total_count}"
            self.log_message(f"🔄 {status_msg}")

            # 如果有运行中的会话，显示详细信息
            if running_count > 0:
                self.log_message("📋 运行中的会话:")
                for i, session in enumerate(running_sessions, 1):
                    name = session.get('name', 'Unknown')
                    uuid = session.get('uuid', 'Unknown')
                    status = session.get('status', 'Unknown')
                    proxy = session.get('proxy', {})
                    protocol = proxy.get('protocol', 'Unknown')
                    self.log_message(f"   {i}. {name} ({uuid[:8]}...) - {protocol} - {status}")
            else:
                self.log_message("⚠️ 没有运行中的会话，请先启动 Linken Sphere 会话")

        except Exception as e:
            error_msg = f"❌ 获取会话状态失败: {e}"
            self.log_message(error_msg)

    def show_session_selector(self):
        """显示会话选择器"""
        try:
            import requests

            # 获取运行中的会话
            response = requests.get("http://127.0.0.1:40080/sessions", timeout=5)
            response.raise_for_status()
            sessions = response.json()

            # 显示所有会话（运行中和已停止的）
            if not sessions:
                messagebox.showinfo("信息", "没有找到任何会话\n请先在 Linken Sphere 中创建配置文件")
                return

            # 创建会话选择窗口（包含所有会话）
            self.create_session_selector_window(sessions)

        except Exception as e:
            messagebox.showerror("错误", f"获取会话列表失败: {e}")

    def create_session_selector_window(self, sessions):
        """创建会话选择窗口"""
        # 创建新窗口
        selector_window = tk.Toplevel(self.root)
        selector_window.title("🎯 选择会话")
        selector_window.geometry("700x600")  # 增大窗口以容纳搜索和排序功能
        selector_window.configure(bg='#2c2c2c')
        selector_window.resizable(True, True)  # 允许调整大小

        # 设置窗口居中
        selector_window.transient(self.root)
        selector_window.grab_set()

        # 标题
        title_label = tk.Label(
            selector_window,
            text="🎯 选择要使用的会话",
            bg='#2c2c2c',
            fg='white',
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(10, 10))

        # 搜索和排序控制区域
        control_frame = tk.Frame(selector_window, bg='#2c2c2c')
        control_frame.pack(fill=tk.X, padx=20, pady=10)

        # 搜索框
        search_frame = tk.Frame(control_frame, bg='#2c2c2c')
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(search_frame, text="🔍 搜索:", bg='#2c2c2c', fg='#ffffff', font=('Arial', 10)).pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            bg='#404040',
            fg='#ffffff',
            insertbackground='#ffffff',
            font=('Arial', 10),
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=(5, 10))

        # 排序选项
        sort_frame = tk.Frame(control_frame, bg='#2c2c2c')
        sort_frame.pack(fill=tk.X)

        tk.Label(sort_frame, text="📊:", bg='#2c2c2c', fg='#ffffff', font=('Arial', 10)).pack(side=tk.LEFT)
        sort_var = tk.StringVar(value="name")
        sort_options = [("名称", "name"), ("状态", "status"), ("代理", "proxy")]
        for text, value in sort_options:
            tk.Radiobutton(
                sort_frame,
                text=text,
                variable=sort_var,
                value=value,
                bg='#2c2c2c',
                fg='#ffffff',
                selectcolor='#404040',
                activebackground='#2c2c2c',
                activeforeground='#ffffff',
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=(5, 10))

        # 统计信息 - 使用新的判断逻辑
        running_count = len([s for s in sessions if self.is_session_running(s)])
        stopped_count = len([s for s in sessions if not self.is_session_running(s)])

        # 说明文字
        info_label = tk.Label(
            selector_window,
            text=f"总共 {len(sessions)} 个会话 (🟢 {running_count} 个运行中, 🔴 {stopped_count} 个已停止)",
            bg='#2c2c2c',
            fg='#cccccc',
            font=('Arial', 10)
        )
        info_label.pack(pady=(0, 5))

        # 提示信息
        tip_label = tk.Label(
            selector_window,
            text="💡 选择已停止的会话将自动启动它",
            bg='#2c2c2c',
            fg='#ffa500',
            font=('Arial', 9)
        )
        tip_label.pack(pady=(0, 10))

        # 会话列表框架
        list_frame = tk.Frame(selector_window, bg='#2c2c2c')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建列表框和滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        session_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Consolas', 10),
            selectbackground='#404040',
            selectforeground='#ffffff',
            height=10
        )
        session_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=session_listbox.yview)

        # 存储原始会话列表和过滤后的列表
        original_sessions = sessions.copy()
        filtered_sessions = sessions.copy()

        def update_session_list():
            """更新会话列表显示"""
            nonlocal filtered_sessions

            # 获取搜索关键词
            search_text = search_var.get().lower().strip()

            # 过滤会话
            if search_text:
                filtered_sessions = [
                    session for session in original_sessions
                    if search_text in session.get('name', '').lower() or
                       search_text in session.get('uuid', '').lower() or
                       search_text in session.get('proxy', {}).get('protocol', '').lower()
                ]
            else:
                filtered_sessions = original_sessions.copy()

            # 排序会话
            sort_by = sort_var.get()
            if sort_by == "name":
                filtered_sessions.sort(key=lambda x: x.get('name', '').lower())
            elif sort_by == "status":
                filtered_sessions.sort(key=lambda x: (not self.is_session_running(x), x.get('name', '').lower()))
            elif sort_by == "proxy":
                filtered_sessions.sort(key=lambda x: (x.get('proxy', {}).get('protocol', ''), x.get('name', '').lower()))

            # 清空并重新填充列表
            session_listbox.delete(0, tk.END)
            for session in filtered_sessions:
                name = session.get('name', 'Unknown')
                uuid = session.get('uuid', 'Unknown')
                proxy = session.get('proxy', {})
                protocol = proxy.get('protocol', 'Unknown')

                # 状态图标 - 使用新的判断逻辑
                is_running = self.is_session_running(session)
                status_icon = "🟢" if is_running else "🔴"
                status_text = "运行中" if is_running else "已停止"

                display_text = f"{status_icon} {name} ({uuid[:8]}...) - {protocol} - {status_text}"
                session_listbox.insert(tk.END, display_text)

        # 绑定搜索和排序事件
        search_var.trace('w', lambda *args: update_session_list())
        sort_var.trace('w', lambda *args: update_session_list())

        # 初始填充列表
        update_session_list()

        # 按钮框架
        button_frame = tk.Frame(selector_window, bg='#2c2c2c')
        button_frame.pack(pady=20)

        # 选择按钮
        def select_session():
            selection = session_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个会话")
                return

            selected_index = selection[0]
            selected_session = filtered_sessions[selected_index]  # 使用过滤后的列表

            # 检查会话状态
            name = selected_session.get('name', 'Unknown')
            uuid = selected_session.get('uuid', 'Unknown')

            if not self.is_session_running(selected_session):
                # 询问是否启动已停止的会话
                result = messagebox.askyesno(
                    "启动会话",
                    f"会话 '{name}' 当前已停止。\n\n是否要启动此会话？"
                )

                if result:
                    # 启动会话
                    if self.start_linken_sphere_session(uuid):
                        # 启动成功，保存选择的会话
                        self.selected_session = selected_session
                        self.log_message(f"🎯 已启动并选择会话: {name} ({uuid[:8]}...)")
                        selector_window.destroy()
                        messagebox.showinfo("成功", f"已启动并选择会话:\n{name}\n\n现在点击开始将使用此会话")
                    else:
                        messagebox.showerror("错误", f"启动会话 '{name}' 失败")
                else:
                    return
            else:
                # 会话已在运行，直接选择
                self.selected_session = selected_session
                self.log_message(f"🎯 已选择会话: {name} ({uuid[:8]}...)")
                selector_window.destroy()
                messagebox.showinfo("成功", f"已选择会话:\n{name}\n\n现在点击开始将使用此会话")

        select_btn = tk.Button(
            button_frame,
            text="✅ 选择此会话",
            command=select_session,
            bg='#28a745',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12
        )
        select_btn.pack(side=tk.LEFT, padx=5)

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="❌ 取消",
            command=selector_window.destroy,
            bg='#dc3545',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=8
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # 自动刷新按钮
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 刷新",
            command=lambda: self.refresh_session_list(selector_window, session_listbox, sessions),
            bg='#17a2b8',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=8
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

    def refresh_session_list(self, window, listbox, current_sessions):
        """刷新会话选择窗口中的会话列表"""
        try:
            import requests

            response = requests.get("http://127.0.0.1:40080/sessions", timeout=5)
            response.raise_for_status()
            sessions = response.json()

            # 清空列表
            listbox.delete(0, tk.END)

            # 重新填充所有会话
            for i, session in enumerate(sessions):
                name = session.get('name', 'Unknown')
                uuid = session.get('uuid', 'Unknown')
                status = session.get('status', 'Unknown')
                proxy = session.get('proxy', {})
                protocol = proxy.get('protocol', 'Unknown')

                # 状态图标 - 使用新的判断逻辑
                is_running = self.is_session_running(session)
                status_icon = "🟢" if is_running else "🔴"
                status_text = "运行中" if is_running else "已停止"

                display_text = f"{i+1}. {status_icon} {name} ({uuid[:8]}...) - {protocol} - {status_text} ({status})"
                listbox.insert(tk.END, display_text)

            # 更新当前会话列表
            current_sessions.clear()
            current_sessions.extend(sessions)

            running_count = len([s for s in sessions if self.is_session_running(s)])
            stopped_count = len([s for s in sessions if not self.is_session_running(s)])

            self.log_message(f"🔄 会话列表已刷新，发现 {len(sessions)} 个会话 (🟢 {running_count} 运行中, 🔴 {stopped_count} 已停止)")

        except Exception as e:
            messagebox.showerror("错误", f"刷新会话列表失败: {e}")

    def check_session_proxy_config(self, session_uuid):
        """检查会话的代理配置"""
        try:
            import requests
            response = requests.get("http://127.0.0.1:40080/sessions", timeout=5)
            if response.status_code == 200:
                sessions = response.json()
                for session in sessions:
                    if session.get('uuid') == session_uuid:
                        proxy = session.get('proxy', {})
                        if proxy:
                            self.log_message(f"✅ 会话有代理配置: {proxy.get('protocol', 'Unknown')}")
                            return True
                        else:
                            self.log_message(f"⚠️ 会话没有代理配置")
                            return False
            return False
        except Exception as e:
            self.log_message(f"⚠️ 检查代理配置失败: {e}")
            return False

    def start_linken_sphere_session(self, session_uuid, debug_port=None):
        """启动 Linken Sphere 会话"""
        try:
            import requests
            import time

            self.log_message(f"🚀 正在启动会话 {session_uuid[:8]}...")

            # 直接启动会话，不需要预先检查代理配置
            self.log_message(f"🔗 设置会话连接...")
            try:
                connection_url = "http://127.0.0.1:40080/sessions/connection"
                # 添加必需的 type 参数，通常为 "http" 或 "socks5"
                connection_payload = f'{{\n    "uuid": "{session_uuid}",\n    "type": "http"\n}}'
                headers = {'Content-Type': 'application/json'}

                connection_response = requests.post(connection_url, data=connection_payload, headers=headers, timeout=10)
                self.log_message(f"� 连接设置响应: {connection_response.status_code}")

                if connection_response.status_code == 200:
                    self.log_message(f"✅ 会话连接设置成功")
                else:
                    self.log_message(f"⚠️ 连接设置响应: {connection_response.status_code} - {connection_response.text}")
                    # 即使连接设置失败，也尝试启动会话

            except Exception as e:
                self.log_message(f"⚠️ 会话连接设置失败: {e}")
                # 继续尝试启动会话

            # 启动会话 - 按照官方示例格式
            start_url = "http://127.0.0.1:40080/sessions/start"

            # 使用字符串格式的 JSON 载荷，使用传入的调试端口或配置中的端口
            if debug_port is None:
                debug_port = self.config['debug_port']
            start_payload = f'{{\n    "uuid": "{session_uuid}",\n    "headless": false,\n    "debug_port": {debug_port}\n}}'

            # 按照官方示例，使用空的 headers
            headers = {}

            self.log_message(f"📤 发送启动请求到: {start_url}")
            self.log_message(f"📋 请求载荷: {start_payload}")
            start_response = requests.request("POST", start_url, headers=headers, data=start_payload)

            self.log_message(f"📥 收到响应，状态码: {start_response.status_code}")

            if start_response.status_code == 200:
                session_data = start_response.json()
                debug_port = session_data.get('debug_port')
                self.log_message(f"✅ 会话启动成功，调试端口: {debug_port}")
            elif start_response.status_code == 400:
                self.log_message(f"❌ 启动失败 (400): {start_response.text}")
                try:
                    error_data = start_response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    self.log_message(f"   错误详情: {error_msg}")
                except:
                    pass
                return False
            elif start_response.status_code == 409:
                self.log_message(f"⚠️ 会话已在运行 (409)")
                # 会话已在运行，尝试使用配置的端口
                self.log_message(f"💡 尝试连接到调试端口 {debug_port}")
            else:
                self.log_message(f"❌ 启动失败，状态码: {start_response.status_code}")
                self.log_message(f"   响应内容: {start_response.text}")
                return False

            # 如果不是 200 状态码，不要调用 raise_for_status()
            if start_response.status_code != 200 and start_response.status_code != 409:
                return False

            # 3. 轮询等待会话启动（最多30秒）
            self.log_message(f"⏳ 等待会话启动...")

            for attempt in range(15):  # 15次，每次2秒
                time.sleep(2)

                try:
                    sessions_response = requests.get("http://127.0.0.1:40080/sessions", timeout=5)
                    sessions_response.raise_for_status()
                    sessions = sessions_response.json()

                    for session in sessions:
                        if session.get('uuid') == session_uuid:
                            status = session.get('status', 'Unknown')
                            self.log_message(f"   状态检查 ({attempt+1}/15): {status}")

                            if self.is_session_running(session):
                                self.log_message(f"✅ 会话启动成功！")
                                return True
                            break

                except Exception as e:
                    self.log_message(f"   状态检查失败: {e}")

            self.log_message(f"⏰ 会话启动超时（30秒）")
            return False

        except requests.exceptions.Timeout:
            self.log_message(f"⏰ 启动请求超时，请稍后重试")
            return False
        except Exception as e:
            self.log_message(f"❌ 启动会话失败: {e}")
            return False





    def refresh_profiles(self):
        """刷新可用的配置文件列表"""
        try:
            import requests
            response = requests.get("http://127.0.0.1:40080/sessions", timeout=5)
            if response.status_code == 200:
                self.available_profiles = response.json()
                self.log_message(f"🔍 发现 {len(self.available_profiles)} 个配置文件")

                # 显示配置文件信息
                for profile in self.available_profiles:
                    name = profile.get('name', 'Unknown')
                    uuid = profile.get('uuid', 'Unknown')
                    self.log_message(f"  📋 {name} ({uuid[:8]}...)")

            else:
                self.log_message("⚠️ 无法获取配置文件列表")
                self.available_profiles = []
        except Exception as e:
            self.log_message(f"⚠️ 获取配置文件失败: {e}")
            self.available_profiles = []

    def get_next_available_profile(self):
        """获取下一个可用的配置文件"""
        if not self.available_profiles:
            self.refresh_profiles()

        # 查找未使用的配置文件
        for profile in self.available_profiles:
            uuid = profile.get('uuid')
            if uuid and uuid not in self.used_profiles:
                self.used_profiles.add(uuid)
                return profile

        # 如果所有配置文件都在使用，返回None
        return None

    def allocate_debug_port(self):
        """分配一个唯一的调试端口"""
        with self.resource_lock:
            base_port = self.config['debug_port']

            # 尝试从基础端口开始分配
            for offset in range(20):  # 最多尝试20个端口
                port = base_port + offset
                if port not in self.used_debug_ports:
                    self.used_debug_ports.add(port)
                    self.log_message(f"🔌 分配调试端口: {port}")
                    return port

            # 如果所有端口都被占用，返回基础端口（可能会冲突）
            self.log_message(f"⚠️ 所有端口都被占用，使用基础端口: {base_port}")
            return base_port

    def release_debug_port(self, port):
        """释放调试端口"""
        with self.resource_lock:
            if port in self.used_debug_ports:
                self.used_debug_ports.remove(port)
                self.log_message(f"🔓 释放调试端口: {port}")

    def save_config(self):
        """保存配置"""
        try:
            # 从GUI更新配置
            self.config['browse_duration'] = int(self.browse_duration_var.get())
            self.config['major_cycles'] = int(self.major_cycles_var.get())
            self.config['minor_cycles_per_major'] = int(self.minor_cycles_var.get())
            self.config['max_threads'] = int(self.max_threads_var.get())
            # self.config['use_existing_session'] = self.use_existing_session_var.get()  # 已删除
            self.config['debug_port'] = int(self.debug_port_var.get())
            
            with open("linken_sphere_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.log_message("✅ 配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def import_config(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                self.config.update(imported_config)
                
                # 更新GUI
                self.browse_duration_var.set(str(self.config['browse_duration']))
                self.major_cycles_var.set(str(self.config['major_cycles']))
                self.minor_cycles_var.set(str(self.config['minor_cycles_per_major']))
                self.max_threads_var.set(str(self.config['max_threads']))
                # self.use_existing_session_var.set(self.config.get('use_existing_session', True))  # 已删除
                
                self.log_message(f"📁 配置已导入: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"导入配置失败: {e}")
    
    def export_config(self):
        """导出配置"""
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # 更新配置
                self.config['browse_duration'] = int(self.browse_duration_var.get())
                self.config['major_cycles'] = int(self.major_cycles_var.get())
                self.config['minor_cycles_per_major'] = int(self.minor_cycles_var.get())
                self.config['max_threads'] = int(self.max_threads_var.get())
                # self.config['use_existing_session'] = self.use_existing_session_var.get()  # 已删除
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                
                self.log_message(f"📤 配置已导出: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"导出配置失败: {e}")
    
    def start_automation(self):
        """开始自动化"""
        if LinkenSphereAppleBrowser is None:
            messagebox.showerror("错误", "无法导入 LinkenSphereAppleBrowser 模块")
            return
        
        try:
            self.save_config()  # 保存当前配置
            self.create_new_thread()
            self.log_message("🚀 自动化已开始")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def stop_all_automation(self):
        """停止所有自动化"""
        stopped_count = 0
        for thread_info in self.browser_threads.values():
            if thread_info['status'] in ['running', 'paused', 'starting']:
                thread_info['status'] = 'stopping'
                thread_info['stop_event'].set()
                thread_info['pause_event'].set()  # 确保线程不会卡在暂停状态
                stopped_count += 1

        self.is_running = False
        self.log_message(f"⏹️ 已发送停止信号给 {stopped_count} 个线程")
        self.update_display()

        # 等待一段时间后检查线程状态
        self.root.after(2000, self.check_thread_status)
    
    def create_new_thread(self):
        """创建新线程"""
        if len([t for t in self.browser_threads.values() if t['status'] in ['running', 'starting']]) >= self.config['max_threads']:
            messagebox.showwarning("警告", f"已达到最大线程数 ({self.config['max_threads']})")
            return

        self.thread_counter += 1
        thread_id = f"Thread-{self.thread_counter}"

        # 检查是否有用户选择的会话
        selected_session = getattr(self, 'selected_session', None)
        if selected_session:
            # 使用用户选择的会话
            profile_name = selected_session.get('name', 'Unknown')
            profile_uuid = None  # 使用现有会话时不需要配置文件UUID
            self.log_message(f"🎯 使用用户选择的会话: {profile_name}")
        else:
            # 新会话模式：需要获取可用的配置文件
            profile = self.get_next_available_profile()
            if not profile:
                messagebox.showwarning("警告", "没有可用的配置文件。请确保有足够的 Linken Sphere 配置文件。")
                return
            profile_name = profile.get('name', 'Unknown')
            profile_uuid = profile.get('uuid')

        # 分配唯一的调试端口
        allocated_debug_port = self.allocate_debug_port()

        thread_info = {
            'id': thread_id,
            'status': 'starting',
            'stop_event': threading.Event(),
            'pause_event': threading.Event(),
            'thread': None,
            'profile_uuid': profile_uuid,
            'profile_name': profile_name,
            'debug_port': allocated_debug_port
        }

        # 初始状态为运行（不暂停）
        thread_info['pause_event'].set()

        thread = threading.Thread(target=self.run_browser_thread, args=(thread_info,))
        thread_info['thread'] = thread

        self.browser_threads[thread_id] = thread_info
        thread.start()

        self.is_running = True
        self.update_display()
        self.log_message(f"➕ 创建线程: {thread_id} (配置: {profile_name})")
    
    def run_browser_thread(self, thread_info):
        """运行浏览器线程"""
        thread_id = thread_info['id']
        profile_uuid = thread_info['profile_uuid']
        profile_name = thread_info['profile_name']
        stop_event = thread_info['stop_event']
        pause_event = thread_info['pause_event']
        allocated_debug_port = thread_info['debug_port']

        try:
            # 检查是否在启动前就被停止
            if stop_event.is_set():
                thread_info['status'] = 'stopped'
                return

            # 获取用户选择的会话（如果有）
            selected_session = getattr(self, 'selected_session', None)

            # 判断是否使用现有会话：如果用户选择了会话，则使用现有会话模式
            use_existing = selected_session is not None

            browser = LinkenSphereAppleBrowser(
                browse_duration=self.config['browse_duration'],
                major_cycles=self.config['major_cycles'],
                max_retries=self.config['max_retries'],
                profile_uuid=profile_uuid,  # 传递指定的配置文件UUID
                use_existing_session=use_existing,  # 根据是否选择会话来决定模式
                selected_session=selected_session  # 传递用户选择的特定会话
            )

            # 设置调试端口配置
            browser.debug_port_start = allocated_debug_port
            browser.allocated_debug_port = allocated_debug_port

            thread_info['status'] = 'running'
            self.log_message(f"🚀 {thread_id} 开始运行 (配置: {profile_name})")
            self.update_display()

            # 运行自动化，带有停止和暂停控制
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 创建一个可控制的运行任务
                task = loop.create_task(self.run_browser_with_control(browser, thread_info))
                loop.run_until_complete(task)
            finally:
                loop.close()

        except Exception as e:
            self.log_message(f"❌ {thread_id} 运行失败: {e}")
            thread_info['status'] = 'error'
        finally:
            # 释放调试端口
            self.release_debug_port(allocated_debug_port)

            # 释放配置文件（仅在使用新会话模式时）
            if profile_uuid and profile_uuid in self.used_profiles:
                self.used_profiles.remove(profile_uuid)
                self.log_message(f"✅ {thread_id} 已完成 (已释放配置: {profile_name})")
            else:
                self.log_message(f"✅ {thread_id} 已完成")

            if thread_info['status'] != 'error':
                thread_info['status'] = 'finished'

            self.update_display()

    async def run_browser_with_control(self, browser, thread_info):
        """带控制的真实浏览器运行"""
        stop_event = thread_info['stop_event']
        pause_event = thread_info['pause_event']

        try:
            # 修改浏览器实例以支持控制信号
            browser.stop_event = stop_event
            browser.pause_event = pause_event
            browser.thread_info = thread_info
            browser.gui_log_callback = self.log_message
            browser.gui_update_callback = self.update_display

            # 运行真实的浏览器自动化
            await browser.run()

        except Exception as e:
            self.log_message(f"❌ {thread_info['id']} 浏览器运行异常: {e}")
            raise
    
    def cleanup_finished_threads(self):
        """清理已完成的线程"""
        finished = [tid for tid, info in self.browser_threads.items() 
                   if info['status'] in ['finished', 'error']]
        
        for thread_id in finished:
            del self.browser_threads[thread_id]
        
        self.update_display()
        self.log_message(f"🗑️ 已清理 {len(finished)} 个线程")

    def pause_selected_thread(self):
        """暂停选中的线程"""
        selection = self.thread_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个线程")
            return

        # 从显示文本中提取线程ID
        selected_text = self.thread_listbox.get(selection[0])
        thread_id = selected_text.split(' - ')[0].split(' ')[1]  # 提取Thread-X

        if thread_id in self.browser_threads:
            thread_info = self.browser_threads[thread_id]
            if thread_info['status'] == 'running':
                thread_info['status'] = 'paused'
                thread_info['pause_event'].clear()  # 暂停线程
                self.log_message(f"⏸️ 线程 {thread_id} 已暂停")
                self.update_display()
            else:
                messagebox.showinfo("信息", f"线程 {thread_id} 当前状态: {thread_info['status']}")

    def resume_selected_thread(self):
        """恢复选中的线程"""
        selection = self.thread_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个线程")
            return

        # 从显示文本中提取线程ID
        selected_text = self.thread_listbox.get(selection[0])
        thread_id = selected_text.split(' - ')[0].split(' ')[1]  # 提取Thread-X

        if thread_id in self.browser_threads:
            thread_info = self.browser_threads[thread_id]
            if thread_info['status'] == 'paused':
                thread_info['status'] = 'running'
                thread_info['pause_event'].set()  # 恢复线程
                self.log_message(f"▶️ 线程 {thread_id} 已恢复")
                self.update_display()
            else:
                messagebox.showinfo("信息", f"线程 {thread_id} 当前状态: {thread_info['status']}")

    def stop_selected_thread(self):
        """停止选中的线程"""
        selection = self.thread_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个线程")
            return

        # 从显示文本中提取线程ID
        selected_text = self.thread_listbox.get(selection[0])
        thread_id = selected_text.split(' - ')[0].split(' ')[1]  # 提取Thread-X

        if thread_id in self.browser_threads:
            thread_info = self.browser_threads[thread_id]
            if thread_info['status'] in ['running', 'paused', 'starting']:
                thread_info['status'] = 'stopping'
                thread_info['stop_event'].set()
                thread_info['pause_event'].set()  # 确保不会卡在暂停状态
                self.log_message(f"⏹️ 线程 {thread_id} 正在停止")
                self.update_display()
            else:
                messagebox.showinfo("信息", f"线程 {thread_id} 当前状态: {thread_info['status']}")

    def check_thread_status(self):
        """检查线程状态"""
        active_threads = [tid for tid, info in self.browser_threads.items()
                         if info['status'] in ['running', 'paused', 'starting']]

        if active_threads:
            self.log_message(f"⚠️ 仍有 {len(active_threads)} 个线程在运行")
        else:
            self.log_message("✅ 所有线程已停止")
    
    def update_display(self):
        """更新显示 - 线程安全"""
        def _update():
            try:
                # 更新状态
                running = len([t for t in self.browser_threads.values() if t['status'] == 'running'])
                paused = len([t for t in self.browser_threads.values() if t['status'] == 'paused'])
                active = len([t for t in self.browser_threads.values() if t['status'] in ['running', 'starting', 'paused']])

                if running > 0:
                    self.status_label.config(text="状态: 运行中", fg='#28a745')
                elif paused > 0:
                    self.status_label.config(text="状态: 已暂停", fg='#ffc107')
                else:
                    self.status_label.config(text="状态: 就绪", fg='#6c757d')

                # 显示详细的线程状态
                if paused > 0:
                    self.threads_label.config(text=f"线程: {running}运行 {paused}暂停/{self.config['max_threads']}")
                else:
                    self.threads_label.config(text=f"线程: {active}/{self.config['max_threads']}")

                # 更新线程列表
                self.thread_listbox.delete(0, tk.END)
                for thread_id, info in self.browser_threads.items():
                    status_emoji = {
                        'starting': '🔄',
                        'running': '▶️',
                        'paused': '⏸️',
                        'stopping': '⏹️',
                        'stopped': '🛑',
                        'finished': '✅',
                        'error': '❌'
                    }.get(info['status'], '❓')

                    # 显示配置文件信息
                    profile_name = info.get('profile_name', 'Unknown')
                    profile_short = profile_name[:12] + "..." if len(profile_name) > 12 else profile_name

                    self.thread_listbox.insert(tk.END, f"{status_emoji} {thread_id} - {info['status']} ({profile_short})")
            except tk.TclError:
                # GUI已关闭，忽略错误
                pass

        # 确保在主线程中执行GUI更新
        try:
            self.root.after(0, _update)
        except (tk.TclError, RuntimeError):
            # GUI已关闭，忽略错误
            pass
    
    def log_message(self, message):
        """记录日志 - 线程安全"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"

            try:
                self.log_text.insert(tk.END, formatted_message)
                self.log_text.see(tk.END)

                # 限制日志行数
                lines = int(self.log_text.index('end-1c').split('.')[0])
                if lines > 1000:
                    self.log_text.delete('1.0', '500.0')
            except tk.TclError:
                # GUI已关闭，忽略错误
                pass

            print(formatted_message.strip())

        # 确保在主线程中执行GUI更新
        try:
            self.root.after(0, _log)
        except (tk.TclError, RuntimeError):
            # GUI已关闭，只打印到控制台
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🗑️ 日志已清空")
    
    def save_logs(self):
        """保存日志"""
        file_path = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"💾 日志已保存: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {e}")
    
    def on_closing(self):
        """窗口关闭"""
        if self.is_running:
            if messagebox.askokcancel("确认退出", "程序正在运行，确定退出吗？"):
                self.stop_all_automation()
                self.save_config()
                self.root.destroy()
        else:
            self.save_config()
            self.root.destroy()

def main():
    """主函数"""
    app = SimpleLinkenGUI()
    app.root.mainloop()

if __name__ == "__main__":
    main()
