import tkinter as tk
from tkinter import ttk
import datetime
import threading
import time
import os
import sys
import pyautogui
import cv2
import numpy as np
import keyboard
from PIL import Image, ImageTk

# 导入现有模块
from course_manager import CourseManager
from floating_image_detector import FloatingImageDetector

# 确保日志文件夹存在
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class IntegratedFloatingPanel:
    def __init__(self):
        """初始化集成浮窗面板"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("集成控制面板")
        self.root.geometry("400x650")  # 增加高度以容纳鼠标控制区域
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
        self.mouse_control_running = False  # 鼠标控制功能状态
        self.mouse_control_thread = None  # 鼠标控制线程
        self.manager = CourseManager()  # 课程管理器实例（独立实例，因为这是一个独立的程序）
        self.image_detector = None  # 屏幕检测工具实例
        self.detection_thread = None
        
        # 鼠标控制状态变量
        self.current_main_behavior = "未启动"  # 当前大型行为状态
        self.current_sub_behavior = "等待中"  # 当前小行为状态
        
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
    
    def log_message(self, message_type, content):
        """记录日志信息"""
        try:
            # 获取当前时间
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 日志文件路径
            log_file = os.path.join(LOG_DIR, f"mouse_control_log_{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
            
            # 构建日志消息
            log_message = f"[{current_time}] [{message_type}] {content}"
            
            # 打印到控制台
            print(log_message)
            
            # 写入日志文件
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"日志记录失败: {e}")
    
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
        title_label.pack(side=tk.LEFT, pady=5, padx=5)
        
        # 右上角关闭按钮
        self.close_button = tk.Button(
            title_frame,
            text="×",
            command=self.exit_program,
            font=("微软雅黑", 14, "bold"),
            fg="white",
            bg="#e74c3c",
            activebackground="#c0392b",
            bd=0,
            relief=tk.FLAT,
            width=3,
            height=1
        )
        self.close_button.pack(side=tk.RIGHT, pady=2, padx=2)
        
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
        
        # 鼠标控制区域
        mouse_frame = tk.LabelFrame(
            self.root,
            text="鼠标控制",
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("微软雅黑", 10)
        )
        mouse_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 鼠标控制状态标签
        self.mouse_status_var = tk.StringVar()
        self.mouse_status_var.set("鼠标控制未启动")
        self.mouse_status_label = tk.Label(
            mouse_frame,
            textvariable=self.mouse_status_var,
            font=("微软雅黑", 10),
            fg="#e74c3c",
            bg="#2c3e50"
        )
        self.mouse_status_label.pack(pady=5)
        
        # 大型行为状态显示
        self.main_behavior_var = tk.StringVar()
        self.main_behavior_var.set("大型行为状态: 未启动")
        self.main_behavior_label = tk.Label(
            mouse_frame,
            textvariable=self.main_behavior_var,
            font=("微软雅黑", 10, "bold"),
            fg="#f39c12",
            bg="#2c3e50"
        )
        self.main_behavior_label.pack(pady=2)
        
        # 小行为状态显示
        self.sub_behavior_var = tk.StringVar()
        self.sub_behavior_var.set("小行为状态: 等待中")
        self.sub_behavior_label = tk.Label(
            mouse_frame,
            textvariable=self.sub_behavior_var,
            font=("微软雅黑", 10),
            fg="#3498db",
            bg="#2c3e50"
        )
        self.sub_behavior_label.pack(pady=2)
        
        # 鼠标控制按钮区域
        mouse_button_frame = tk.Frame(mouse_frame, bg="#2c3e50")
        mouse_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 开始按钮
        self.start_mouse_button = tk.Button(
            mouse_button_frame,
            text="鼠标控制开始",
            command=self.start_mouse_control,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#27ae60",
            activebackground="#229954",
            bd=0,
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.start_mouse_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 停止按钮
        self.stop_mouse_button = tk.Button(
            mouse_button_frame,
            text="停止",
            command=self.stop_mouse_control,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#e74c3c",
            activebackground="#c0392b",
            bd=0,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            state=tk.DISABLED
        )
        self.stop_mouse_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 提示标签
        tip_label = tk.Label(
            self.root,
            text="拖动窗口任意位置移动 | ESC键快速退出 | 空格键中断鼠标控制",
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
                self.log_message("错误", f"时间更新出错: {e}")
                time.sleep(1)
    
    def update_behavior_status(self, main_behavior, sub_behavior=None):
        """更新行为状态显示"""
        if main_behavior != self.current_main_behavior:
            self.current_main_behavior = main_behavior
            self.root.after(0, lambda: self.main_behavior_var.set(f"大型行为状态: {main_behavior}"))
            self.log_message("状态", f"大型行为状态更新为: {main_behavior}")
        
        if sub_behavior is not None and sub_behavior != self.current_sub_behavior:
            self.current_sub_behavior = sub_behavior
            self.root.after(0, lambda: self.sub_behavior_var.set(f"小行为状态: {sub_behavior}"))
            self.log_message("状态", f"小行为状态更新为: {sub_behavior}")
    
    def match_image(self, image_path, threshold=0.85):
        """在屏幕上查找指定图片的位置"""
        try:
            # 加载目标图片
            target_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if target_image is None:
                self.log_message("错误", f"无法加载图片: {image_path}")
                return None
            
            # 捕获当前屏幕
            screenshot = pyautogui.screenshot()
            screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            
            # 使用模板匹配
            result = cv2.matchTemplate(screen_gray, target_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 获取图片中心点
                h, w = target_image.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.log_message("操作", f"在屏幕上找到图片: {os.path.basename(image_path)}，匹配度: {max_val:.2f}，位置: ({center_x}, {center_y})")
                return (center_x, center_y, max_val)
            else:
                self.log_message("判断", f"未找到匹配的图片: {os.path.basename(image_path)}，最高匹配度: {max_val:.2f}")
                return None
        except Exception as e:
            self.log_message("错误", f"图片匹配出错: {e}")
            return None
    
    def find_all_matches(self, image_path, threshold=0.85):
        """在屏幕上查找所有匹配的图片位置"""
        try:
            # 加载目标图片
            target_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if target_image is None:
                self.log_message("错误", f"无法加载图片: {image_path}")
                return []
            
            # 捕获当前屏幕
            screenshot = pyautogui.screenshot()
            screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            
            # 使用模板匹配
            result = cv2.matchTemplate(screen_gray, target_image, cv2.TM_CCOEFF_NORMED)
            
            # 查找所有匹配度大于阈值的位置
            h, w = target_image.shape
            matches = []
            while True:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                if max_val >= threshold:
                    # 计算中心点
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    matches.append((center_x, center_y, max_val))
                    
                    # 在结果中标记已找到的位置，避免重复匹配
                    cv2.rectangle(result, max_loc, (max_loc[0] + w, max_loc[1] + h), (-1), -1)
                else:
                    break
            
            if matches:
                self.log_message("操作", f"在屏幕上找到 {len(matches)} 个匹配的图片: {os.path.basename(image_path)}")
            else:
                self.log_message("判断", f"未找到匹配的图片: {os.path.basename(image_path)}")
            
            return matches
        except Exception as e:
            self.log_message("错误", f"查找所有匹配图片出错: {e}")
            return []
    
    def perform_mouse_click(self, x, y, description="点击操作"):
        """执行鼠标点击操作"""
        try:
            # 获取当前鼠标位置
            current_x, current_y = pyautogui.position()
            self.log_message("操作", f"移动鼠标: 从({current_x}, {current_y})到({x}, {y})")
            
            # 移动鼠标到目标位置
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.1)  # 等待鼠标移动完成
            
            # 执行点击
            pyautogui.click()
            self.log_message("操作", f"执行{description}，位置: ({x}, {y})")
            return True
        except Exception as e:
            self.log_message("错误", f"鼠标点击操作出错: {e}")
            return False
    
    def get_next_course(self):
        """获取下一节课的信息"""
        try:
            now = datetime.datetime.now()
            current_day = "周" + "一二三四五六日"[now.weekday()]
            current_time = now.strftime("%H:%M")
            
            # 获取今日课程
            today_courses = self.manager.get_courses_by_day(current_day)
            
            # 按照开始时间排序
            today_courses.sort(key=lambda x: x["start_time"])
            
            # 查找下一节课
            for course in today_courses:
                if course["start_time"] > current_time:
                    self.log_message("判断", f"找到下一节课: {course['course_name']}，开始时间: {course['start_time']}")
                    return course
            
            self.log_message("判断", "今日没有更多课程")
            return None
        except Exception as e:
            self.log_message("错误", f"获取下一节课信息出错: {e}")
            return None
    
    def get_current_course_status(self):
        """获取当前课程状态"""
        try:
            now = datetime.datetime.now()
            current_day = "周" + "一二三四五六日"[now.weekday()]
            current_time = now.strftime("%H:%M")
            
            # 获取今日课程
            today_courses = self.manager.get_courses_by_day(current_day)
            
            # 检查当前是否有课程进行中
            current_course = None
            for course in today_courses:
                if course["start_time"] <= current_time <= course["end_time"]:
                    current_course = course
                    break
            
            if current_course:
                self.log_message("判断", f"当前课程: {current_course['course_name']}，进行中")
                return "course_in_progress", current_course
            
            # 检查是否处于课程切换时段（严格按照用户要求判断）
            # 1. 查找刚刚结束的课程
            last_course = None
            for course in today_courses:
                if course["end_time"] < current_time:
                    if not last_course or course["end_time"] > last_course["end_time"]:
                        last_course = course
            
            # 2. 查找即将开始的课程
            next_course = None
            for course in today_courses:
                if course["start_time"] > current_time:
                    if not next_course or course["start_time"] < next_course["start_time"]:
                        next_course = course
            
            # 3. 判断是否满足课程切换条件
            # 严格条件：当前时间处于过渡时间区间内，且在当前时间之前有一节课刚刚结束，之后有一节课即将开始
            if last_course and next_course:
                last_end_time = last_course["end_time"]
                next_start_time = next_course["start_time"]
                
                if last_end_time < current_time < next_start_time:
                    # 检查当前时间是否确实是在刚刚结束的课程之后（确保有一节课刚刚结束）
                    # 转换为分钟数进行比较，更精确地判断时间差
                    def time_to_minutes(time_str):
                        hours, minutes = map(int, time_str.split(':'))
                        return hours * 60 + minutes
                    
                    current_minutes = time_to_minutes(current_time)
                    last_end_minutes = time_to_minutes(last_end_time)
                    
                    # 确认当前时间确实在最后一节课结束之后
                    if current_minutes > last_end_minutes:
                        self.log_message("判断", f"当前处于课程切换时段: 刚刚结束的课程{last_course['course_name']}结束于{last_end_time}，下一节课{next_course['course_name']}开始于{next_start_time}")
                        return "course_switching", (next_course, last_end_time)
            
            # 检查是否有即将开始的课程（课程开始前）
            if next_course:
                self.log_message("判断", f"当前处于课程开始前: 下一节课{next_course['course_name']}开始于{next_course['start_time']}")
                return "course_before", next_course
            
            self.log_message("判断", "当前没有相关课程状态")
            return "no_course", None
        except Exception as e:
            self.log_message("错误", f"获取当前课程状态出错: {e}")
            return "error", None
    
    def course_before_behavior(self, course):
        """课程开始前行为"""
        try:
            self.update_behavior_status("课程开始前", "进入课程界面")
            
            # 检查当前界面是否为Course Menu
            current_interface = self.image_detector.current_interface if self.image_detector else "未检测"
            self.log_message("判断", f"当前界面: {current_interface}")
            
            if current_interface != "course_menu":
                self.log_message("判断", "当前不是课程菜单界面，等待中...")
                self.update_behavior_status("课程开始前", "等待中")
                return False
            
            # 获取课程图标路径
            course_icon_path = self.manager.get_course_icon_path(course["course_name"])
            if not course_icon_path:
                self.log_message("错误", f"未找到课程图标: {course['course_name']}")
                return False
            
            # 在屏幕上查找课程图标
            match_result = self.match_image(course_icon_path)
            if match_result:
                center_x, center_y, match_score = match_result
                # 执行点击操作
                return self.perform_mouse_click(center_x, center_y, f"点击{course['course_name']}课程图标")
            else:
                self.log_message("错误", f"未在屏幕上找到{course['course_name']}课程图标")
                return False
        except Exception as e:
            self.log_message("错误", f"课程开始前行为出错: {e}")
            return False
    
    def enter_poll_behavior(self):
        """进入答题行为"""
        try:
            self.update_behavior_status("课程进行中", "进入答题行为")
            
            # 检查当前界面是否为Course Starts
            current_interface = self.image_detector.current_interface if self.image_detector else "未检测"
            self.log_message("判断", f"当前界面: {current_interface}")
            
            if current_interface != "course_starts":
                self.log_message("判断", "当前不是课程开始界面，不执行进入答题行为")
                return False
            
            # 获取join按钮图片路径
            join_button_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "test", "course_starts", "join.PNG")
            if not os.path.exists(join_button_path):
                self.log_message("错误", "未找到join按钮图片")
                return False
            
            # 在屏幕上查找join按钮
            match_result = self.match_image(join_button_path)
            if match_result:
                center_x, center_y, match_score = match_result
                # 执行点击操作
                return self.perform_mouse_click(center_x, center_y, "点击join按钮进入答题")
            else:
                self.log_message("错误", "未在屏幕上找到join按钮")
                return False
        except Exception as e:
            self.log_message("错误", f"进入答题行为出错: {e}")
            return False
    
    def answer_poll_behavior(self):
        """答题行为"""
        try:
            self.update_behavior_status("课程进行中", "答题行为")
            
            # 检查当前界面是否为Poll Starts
            current_interface = self.image_detector.current_interface if self.image_detector else "未检测"
            self.log_message("判断", f"当前界面: {current_interface}")
            
            if current_interface != "poll_starts":
                self.log_message("判断", "当前不是投票开始界面，不执行答题行为")
                return False
            
            # 获取A选项图片路径
            a_option_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "click", "a.PNG")
            if not os.path.exists(a_option_path):
                self.log_message("错误", "未找到A选项图片")
                return False
            
            # 在屏幕上查找A选项
            match_result = self.match_image(a_option_path)
            if match_result:
                center_x, center_y, match_score = match_result
                # 执行点击操作
                return self.perform_mouse_click(center_x, center_y, "点击A选项答题")
            else:
                self.log_message("错误", "未在屏幕上找到A选项")
                return False
        except Exception as e:
            self.log_message("错误", f"答题行为出错: {e}")
            return False
    
    def exit_session_behavior(self):
        """退出行为"""
        try:
            self.update_behavior_status("课程切换时", "退出行为")
            
            # 检查当前界面是否为Leave Session
            current_interface = self.image_detector.current_interface if self.image_detector else "未检测"
            self.log_message("判断", f"当前界面: {current_interface}")
            
            if current_interface != "leave_session":
                self.log_message("判断", "当前不是离开会话界面，不执行退出行为")
                return False
            
            # 获取leave按钮图片路径
            leave_button_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "click", "leave.PNG")
            if not os.path.exists(leave_button_path):
                self.log_message("错误", "未找到leave按钮图片")
                return False
            
            # 在屏幕上查找leave按钮
            match_result = self.match_image(leave_button_path)
            if match_result:
                center_x, center_y, match_score = match_result
                # 执行点击操作
                return self.perform_mouse_click(center_x, center_y, "点击leave按钮退出会话")
            else:
                self.log_message("错误", "未在屏幕上找到leave按钮")
                return False
        except Exception as e:
            self.log_message("错误", f"退出行为出错: {e}")
            return False
    
    def return_behavior(self):
        """返回行为"""
        try:
            self.update_behavior_status("课程切换时", "返回行为")
            
            # 获取return按钮图片路径
            return_button_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "click", "return.PNG")
            if not os.path.exists(return_button_path):
                self.log_message("错误", "未找到return按钮图片")
                return False
            
            # 在屏幕上查找所有匹配的return按钮
            matches = self.find_all_matches(return_button_path)
            if matches:
                # 选择最左侧的匹配
                leftmost_match = min(matches, key=lambda x: x[0])
                center_x, center_y, match_score = leftmost_match
                # 执行点击操作
                return self.perform_mouse_click(center_x, center_y, "点击最左侧的return按钮返回")
            else:
                self.log_message("错误", "未在屏幕上找到return按钮")
                return False
        except Exception as e:
            self.log_message("错误", f"返回行为出错: {e}")
            return False
    
    def mouse_control_logic(self):
        """鼠标控制主逻辑"""
        try:
            self.log_message("重要", "鼠标控制功能启动")
            
            # 启动屏幕检测
            if self.image_detector and not self.image_detector.is_detecting:
                self.image_detector.toggle_detection()
                self.log_message("操作", "启动屏幕检测")
            
            # 监听空格键中断
            keyboard.on_press_key('space', lambda _: self.stop_mouse_control())
            
            while self.mouse_control_running:
                try:
                    # 获取当前课程状态
                    status, course_info = self.get_current_course_status()
                    
                    if status == "course_before":
                        # 课程开始前行为
                        course = course_info
                        self.course_before_behavior(course)
                    
                    elif status == "course_in_progress":
                        # 课程进行中行为
                        current_course = course_info
                        
                        # 检查当前界面，执行相应的小行为
                        current_interface = self.image_detector.current_interface if self.image_detector else "未检测"
                        
                        if current_interface == "course_menu":
                            # 当检测到Course Menu界面时，点击当前正在进行的课程图标
                            self.log_message("判断", f"当前界面为Course Menu，且当前有课程进行中: {current_course['course_name']}")
                            self.update_behavior_status("课程进行中", "进入当前课程界面")
                            
                            # 获取当前课程图标路径
                            course_icon_path = self.manager.get_course_icon_path(current_course["course_name"])
                            if not course_icon_path:
                                self.log_message("错误", f"未找到当前课程图标: {current_course['course_name']}")
                            else:
                                # 在屏幕上查找课程图标
                                match_result = self.match_image(course_icon_path)
                                if match_result:
                                    center_x, center_y, match_score = match_result
                                    # 执行点击操作
                                    self.perform_mouse_click(center_x, center_y, f"点击{current_course['course_name']}课程图标")
                                else:
                                    self.log_message("错误", f"未在屏幕上找到{current_course['course_name']}课程图标")
                        elif current_interface == "course_starts":
                            self.enter_poll_behavior()
                        elif current_interface == "poll_starts":
                            self.answer_poll_behavior()
                        else:
                            self.update_behavior_status("课程进行中", "等待中")
                    
                    elif status == "course_switching":
                        # 课程切换行为
                        next_course, last_end_time = course_info
                        
                        # 检查当前界面，执行退出或返回行为
                        current_interface = self.image_detector.current_interface if self.image_detector else "未检测"
                        
                        if current_interface == "leave_session":
                            # 优先执行退出行为
                            self.exit_session_behavior()
                        elif current_interface == "course_menu":
                            # 已回到课程菜单，完成切换
                            self.log_message("判断", "已成功切换到课程菜单界面")
                            # 检查是否有下一节课
                            if next_course:
                                self.log_message("操作", "准备进入下一节课")
                                # 立即执行课程开始前行为
                                self.course_before_behavior(next_course)
                        else:
                            # 执行返回行为
                            self.return_behavior()
                    
                    elif status == "no_course":
                        # 没有课程，等待中
                        self.update_behavior_status("等待中", "今日无课程")
                    
                    else:
                        # 错误状态，等待中
                        self.update_behavior_status("错误", "状态异常")
                    
                    # 控制循环频率
                    time.sleep(1)
                    
                except Exception as e:
                    self.log_message("错误", f"鼠标控制逻辑循环出错: {e}")
                    time.sleep(1)
        except Exception as e:
            self.log_message("错误", f"鼠标控制主逻辑出错: {e}")
        finally:
            # 移除键盘监听
            keyboard.unhook_all()
            self.log_message("重要", "鼠标控制功能停止")
    
    # 不再需要程序控制功能，因为按钮已被删除
    
    def start_mouse_control(self):
        """启动鼠标控制功能"""
        try:
            # 启动屏幕检测（如果未启动）
            if self.image_detector and not self.image_detector.is_detecting:
                self.image_detector.toggle_detection()
                self.log_message("操作", "启动屏幕检测")
            
            # 更新界面状态
            self.mouse_control_running = True
            self.start_mouse_button.config(state=tk.DISABLED)
            self.stop_mouse_button.config(state=tk.NORMAL)
            self.mouse_status_var.set("鼠标控制已启动")
            self.mouse_status_label.config(fg="#2ecc71")
            
            # 重置行为状态显示
            self.update_behavior_status("准备中", "初始化")
            
            # 启动鼠标控制线程
            self.mouse_control_thread = threading.Thread(target=self.mouse_control_logic)
            self.mouse_control_thread.daemon = True
            self.mouse_control_thread.start()
            
            self.log_message("重要", "鼠标控制功能启动")
        except Exception as e:
            self.log_message("错误", f"启动鼠标控制功能出错: {e}")
            self.stop_mouse_control()
    
    def stop_mouse_control(self):
        """停止鼠标控制功能"""
        try:
            # 停止鼠标控制线程
            self.mouse_control_running = False
            
            if self.mouse_control_thread:
                self.mouse_control_thread.join(timeout=2.0)
            
            # 移除键盘监听
            keyboard.unhook_all()
            
            # 更新界面状态
            self.start_mouse_button.config(state=tk.NORMAL)
            self.stop_mouse_button.config(state=tk.DISABLED)
            self.mouse_status_var.set("鼠标控制已停止")
            self.mouse_status_label.config(fg="#e74c3c")
            
            # 重置行为状态显示
            self.update_behavior_status("未启动", "等待中")
            
            self.log_message("重要", "鼠标控制功能停止")
        except Exception as e:
            self.log_message("错误", f"停止鼠标控制功能出错: {e}")
    
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
        try:
            # 停止所有线程和功能
            self.is_running = False
            self.is_paused = False
            self.mouse_control_running = False
            
            # 移除键盘监听
            keyboard.unhook_all()
            
            # 如果屏幕检测工具正在运行，确保停止它
            if self.image_detector and hasattr(self.image_detector, 'toggle_detection'):
                try:
                    # 确保检测已停止
                    self.image_detector.detection_running = False
                    if hasattr(self.image_detector, 'stop_detection'):
                        self.image_detector.stop_detection()
                except Exception as e:
                    self.log_message("错误", f"停止屏幕检测时出错: {e}")
            
            # 确保所有线程都已停止
            self.time_update_thread = None
            self.detection_thread = None
            if self.mouse_control_thread:
                self.mouse_control_thread.join(timeout=1.0)
            
            self.log_message("重要", "程序退出")
            
            # 销毁窗口
            self.root.destroy()
        except Exception as e:
            print(f"退出程序时出错: {e}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        # 启动集成浮窗面板
        app = IntegratedFloatingPanel()
    except Exception as e:
        print(f"程序启动出错: {e}")
