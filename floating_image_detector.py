import tkinter as tk
from tkinter import ttk
import pyautogui
import cv2
import numpy as np
import os
import threading
import time
from PIL import Image, ImageTk

class FloatingImageDetector:
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("图像检测工具")
        self.root.geometry("250x150")
        self.root.overrideredirect(True)  # 去除窗口边框
        self.root.attributes("-alpha", 0.9)  # 设置窗口透明度
        self.root.attributes("-topmost", True)  # 窗口置顶
        
        # 使窗口可拖动
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.root.bind("<Escape>", self.exit_program)
        
        # 设置窗口背景
        self.root.configure(bg="#2c3e50")
        
        # 初始化变量
        self.is_detecting = False
        self.detection_thread = None
        self.reference_images = []
        self.detection_result = "未检测"
        
        # 加载参考图像
        self.load_reference_images()
        
        # 创建界面组件
        self.create_widgets()
        
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
        # 创建标题标签
        title_label = tk.Label(
            self.root,
            text="图像检测工具",
            font=("微软雅黑", 12, "bold"),
            fg="white",
            bg="#34495e"
        )
        title_label.pack(fill=tk.X)
        
        # 创建状态显示区域
        self.status_var = tk.StringVar()
        self.status_var.set("当前界面：未检测")
        status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("微软雅黑", 10),
            fg="white",
            bg="#2c3e50",
            wraplength=230
        )
        status_label.pack(pady=10)
        
        # 创建按钮框架
        button_frame = tk.Frame(self.root, bg="#2c3e50")
        button_frame.pack(pady=5, padx=10, fill=tk.X)
        
        # 创建开始/停止检测按钮
        self.detect_button = tk.Button(
            button_frame,
            text="开始检测",
            command=self.toggle_detection,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#27ae60",
            activebackground="#229954",
            bd=0,
            relief=tk.FLAT,
            padx=5,
            pady=3
        )
        self.detect_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 创建退出按钮
        exit_button = tk.Button(
            button_frame,
            text="退出",
            command=self.exit_program,
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#e74c3c",
            activebackground="#c0392b",
            bd=0,
            relief=tk.FLAT,
            padx=5,
            pady=3
        )
        exit_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
    
    def load_reference_images(self):
        """加载参考图像"""
        try:
            reference_dir = "img/test/course_menu"
            if os.path.exists(reference_dir):
                for filename in os.listdir(reference_dir):
                    if filename.endswith((".PNG", ".png", ".JPG", ".jpg", ".JPEG", ".jpeg")):
                        img_path = os.path.join(reference_dir, filename)
                        # 读取图像并转换为灰度图
                        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                        if img is not None:
                            self.reference_images.append(img)
                            print(f"加载参考图像: {filename}")
                print(f"共加载 {len(self.reference_images)} 张参考图像")
            else:
                print(f"参考图像目录不存在: {reference_dir}")
        except Exception as e:
            print(f"加载参考图像时出错: {e}")
    
    def capture_screen(self):
        """捕获当前屏幕画面"""
        try:
            screenshot = pyautogui.screenshot()
            # 转换为OpenCV格式
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            # 转换为灰度图以提高匹配速度
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            return gray_screenshot
        except Exception as e:
            print(f"屏幕捕获出错: {e}")
            return None
    
    def match_template(self, screen_gray, template, threshold=0.85):
        """使用模板匹配算法进行图像比对"""
        try:
            # 获取模板的高度和宽度
            h, w = template.shape
            
            # 使用TM_CCOEFF_NORMED方法进行模板匹配
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            
            # 找出匹配度大于阈值的位置
            locations = np.where(result >= threshold)
            
            # 如果有匹配项，返回True
            return len(locations[0]) > 0
        except Exception as e:
            print(f"模板匹配出错: {e}")
            return False
    
    def detect_screen(self):
        """检测屏幕上是否包含所有参考图像"""
        while self.is_detecting:
            # 捕获当前屏幕
            screen_gray = self.capture_screen()
            if screen_gray is None:
                time.sleep(0.5)
                continue
            
            # 检查是否所有参考图像都匹配
            all_matched = True
            for template in self.reference_images:
                if not self.match_template(screen_gray, template):
                    all_matched = False
                    break
            
            # 更新检测结果
            if all_matched:
                self.detection_result = "course_menu"
                self.status_var.set("当前界面：course menu")
                self.root.configure(bg="#27ae60")  # 检测到目标时变绿色
            else:
                self.detection_result = "未检测"
                self.status_var.set("当前界面：未检测")
                self.root.configure(bg="#2c3e50")  # 未检测到目标时保持默认颜色
            
            # 控制检测频率，避免CPU占用过高
            time.sleep(0.3)
    
    def toggle_detection(self):
        """切换检测状态"""
        if self.is_detecting:
            # 停止检测
            self.is_detecting = False
            self.detect_button.config(text="开始检测", bg="#27ae60")
            if self.detection_thread is not None:
                self.detection_thread.join()
        else:
            # 开始检测
            if len(self.reference_images) == 0:
                self.status_var.set("错误：未找到参考图像")
                return
            
            self.is_detecting = True
            self.detect_button.config(text="停止检测", bg="#e74c3c")
            # 在新线程中执行检测
            self.detection_thread = threading.Thread(target=self.detect_screen)
            self.detection_thread.daemon = True
            self.detection_thread.start()
    
    def exit_program(self, event=None):
        """退出程序"""
        self.is_detecting = False
        if self.detection_thread is not None:
            self.detection_thread.join()
        self.root.destroy()

if __name__ == "__main__":
    try:
        # 检查是否安装了必要的库
        import pyautogui
        import cv2
        import numpy as np
        import PIL
    except ImportError as e:
        print(f"缺少必要的库: {e}")
        print("请运行以下命令安装所需库:")
        print("pip install pyautogui opencv-python numpy pillow")
        exit(1)
    
    # 启动程序
    app = FloatingImageDetector()