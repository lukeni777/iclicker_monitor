import tkinter as tk
from tkinter import ttk
import datetime
import threading
import time
from PIL import Image, ImageTk
import os

# 导入现有模块
from course_manager import CourseManager
from floating_image_detector import FloatingImageDetector

class IntegratedFloatingPanel:
    def __init__(self):
        """初始化集成浮窗面板"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("集成控制面板")
        self.root.geometry("400x400")  # 足够大的尺寸以显示所有信息
        self.root.overrideredirect(True)  # 去除窗口边框
        self.root.attributes("-alpha", 0.95)  # 设置窗口透明度
        self.root.attributes("-topmost", True)  # 窗口置顶
        
        # 使窗口可拖动
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.root.bind("<Escape>", self.exit_program)
        
        # 设置窗口背景
        self.root.configure(bg="#2c3e50")
        
        # 初始化变量
        self.is_running = False
        self.is_paused = False
        self.manager = CourseManager()  # 课程管理器实例（独立实例，因为这是一个独立的程序）
        self.image_detector = None  # 屏幕检测工具实例
        self.detection_thread = None
        
        # 当前时间和日期
        self.current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.current_day = "周" + "一二三四五六日"[datetime.datetime.now().weekday()]
        
        # 创建界面组件
        self.create_widgets()
        
        # 启动时间更新线程
        self.time_update_thread = threading.Thread(target=self.update_time)
        self.time_update_thread.daemon = True
        self.time_update_thread.start()
        
        # 启动主循环
        self.root.mainloop()
    
    def start_drag(self, event):
        """开始拖动窗口"""
        self.x = event.x
        self.y = event.y
    
    def drag(self, event):
        """拖动窗口"""
        x = self.root.winfo_pointerx() - self.x
        y = self.root.winfo_pointery() - self.y
        self.root.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建标题栏
        title_frame = tk.Frame(self.root, bg="#34495e")
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 标题标签
        title_label = tk.Label(
            title_frame,
            text="IClicker 集成控制面板",
            font=("微软雅黑", 12, "bold"),
            fg="white",
            bg="#34495e"
        )
        title_label.pack(pady=5)
        
        # 当前时间和日期显示
        time_frame = tk.Frame(self.root, bg="#2c3e50")
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 日期标签
        self.date_var = tk.StringVar()
        self.date_var.set(f"{self.current_date} {self.current_day}")
        date_label = tk.Label(
            time_frame,
            textvariable=self.date_var,
            font=("微软雅黑", 10),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        date_label.pack(side=tk.LEFT, padx=5)
        
        # 时间标签
        self.time_var = tk.StringVar()
        self.time_var.set(self.current_time)
        time_label = tk.Label(
            time_frame,
            textvariable=self.time_var,
            font=("微软雅黑", 12, "bold"),
            fg="#3498db",
            bg="#2c3e50"
        )
        time_label.pack(side=tk.RIGHT, padx=5)
        
        # 课程信息区域
        course_frame = tk.LabelFrame(
            self.root,
            text="今日课程",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("微软雅黑", 10)
        )
        course_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 课程列表
        self.course_tree = ttk.Treeview(
            course_frame,
            columns=("course_name", "start_time", "end_time"),
            show="headings",
            height=5
        )
        
        # 设置列宽和标题
        self.course_tree.column("course_name", width=150, anchor=tk.W)
        self.course_tree.column("start_time", width=80, anchor=tk.CENTER)
        self.course_tree.column("end_time", width=80, anchor=tk.CENTER)
        
        self.course_tree.heading("course_name", text="课程名称")
        self.course_tree.heading("start_time", text="开始时间")
        self.course_tree.heading("end_time", text="结束时间")
        
        # 设置样式
        style = ttk.Style()
        style.configure("Treeview", 
                        background="#34495e", 
                        foreground="#ecf0f1",
                        fieldbackground="#34495e")
        style.configure("Treeview.Heading", 
                        background="#7f8c8d", 
                        foreground="white")
        
        self.course_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 加载今日课程
        self.load_today_courses()
        
        # 屏幕检测区域
        detector_frame = tk.LabelFrame(
            self.root,
            text="屏幕检测",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("微软雅黑", 10)
        )
        detector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 屏幕检测状态标签
        self.detector_status_var = tk.StringVar()
        self.detector_status_var.set("屏幕检测未启动")
        self.detector_status_label = tk.Label(
            detector_frame,
            textvariable=self.detector_status_var,
            font=("微软雅黑", 10),
            fg="#e74c3c",
            bg="#2c3e50"
        )
        self.detector_status_label.pack(pady=5)
        
        # 创建屏幕检测工具的嵌入框架
        self.detector_container = tk.Frame(detector_frame, bg="#2c3e50")
        self.detector_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化屏幕检测工具（嵌入模式）
        self.image_detector = FloatingImageDetector(parent=self.detector_container, embedded=True)
        
        # 控制按钮区域
        button_frame = tk.Frame(self.root, bg="#2c3e50")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 开始按钮
        self.start_button = tk.Button(
            button_frame,
            text="开始",
            command=self.start_program,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#27ae60",
            activebackground="#229954",
            bd=0,
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 暂停按钮
        self.pause_button = tk.Button(
            button_frame,
            text="暂停",
            command=self.pause_program,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#f39c12",
            activebackground="#e67e22",
            bd=0,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            state=tk.DISABLED
        )
        self.pause_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 关闭按钮
        self.exit_button = tk.Button(
            button_frame,
            text="关闭",
            command=self.exit_program,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#e74c3c",
            activebackground="#c0392b",
            bd=0,
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.exit_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 提示标签
        tip_label = tk.Label(
            self.root,
            text="拖动窗口任意位置移动 | ESC键快速退出",
            font=("微软雅黑", 8),
            fg="#bdc3c7",
            bg="#2c3e50"
        )
        tip_label.pack(pady=(0, 5))
    
    def load_today_courses(self):
        """加载今日课程信息"""
        # 获取当前星期几
        current_day = "周" + "一二三四五六日"[datetime.datetime.now().weekday()]
        
        # 获取今日课程
        today_courses = self.manager.get_courses_by_day(current_day)
        
        # 清空现有课程列表
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        
        # 添加今日课程
        if today_courses:
            for course in today_courses:
                self.course_tree.insert("", tk.END, values=(
                    course["course_name"],
                    course["start_time"],
                    course["end_time"]
                ))
        else:
            # 如果没有今日课程，显示提示信息
            self.course_tree.insert("", tk.END, values=("今日无课程", "", ""))
    
    def update_time(self):
        """实时更新时间"""
        while True:
            try:
                now = datetime.datetime.now()
                self.current_time = now.strftime("%H:%M:%S")
                self.current_date = now.strftime("%Y-%m-%d")
                self.current_day = "周" + "一二三四五六日"[now.weekday()]
                
                # 更新界面显示
                self.root.after(0, lambda: self.time_var.set(self.current_time))
                self.root.after(0, lambda: self.date_var.set(f"{self.current_date} {self.current_day}"))
                
                # 每分钟检查一次是否需要重新加载课程（比如日期变更）
                if now.second == 0 and now.minute % 1 == 0:
                    self.root.after(0, self.load_today_courses)
                
                # 每秒更新一次
                time.sleep(1)
            except Exception as e:
                print(f"时间更新出错: {e}")
                time.sleep(1)
    
    def start_program(self):
        """开始程序"""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            
            # 更新按钮状态
            self.start_button.config(text="运行中", state=tk.DISABLED, bg="#7f8c8d")
            self.pause_button.config(state=tk.NORMAL)
            
            # 启动屏幕检测
            self.start_image_detection()
    
    def pause_program(self):
        """暂停程序"""
        if self.is_running:
            if not self.is_paused:
                self.is_paused = True
                self.pause_button.config(text="继续")
                # 暂停屏幕检测
                self.pause_image_detection()
            else:
                self.is_paused = False
                self.pause_button.config(text="暂停")
                # 继续屏幕检测
                self.resume_image_detection()
    
    def start_image_detection(self):
        """启动屏幕检测"""
        if self.image_detector:
            # 调用屏幕检测工具的toggle_detection方法启动检测
            self.image_detector.toggle_detection()
            # 更新状态显示
            self.detector_status_var.set("屏幕检测已启动")
            self.detector_status_label.config(fg="#2ecc71")
            print("屏幕检测已启动")
    
    def pause_image_detection(self):
        """暂停屏幕检测"""
        if self.image_detector:
            # 调用屏幕检测工具的toggle_detection方法停止检测
            self.image_detector.toggle_detection()
            # 更新状态显示
            self.detector_status_var.set("屏幕检测已暂停")
            self.detector_status_label.config(fg="#f39c12")
            print("屏幕检测已暂停")
    
    def resume_image_detection(self):
        """继续屏幕检测"""
        self.start_image_detection()
    
    def exit_program(self, event=None):
        """退出程序"""
        # 停止所有线程和功能
        self.is_running = False
        self.is_paused = False
        
        # 销毁窗口
        self.root.destroy()

if __name__ == "__main__":
    try:
        # 启动集成浮窗面板
        app = IntegratedFloatingPanel()
    except Exception as e:
        print(f"程序启动出错: {e}")
