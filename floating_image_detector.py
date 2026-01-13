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
    def __init__(self, parent=None, embedded=False):
        # 如果提供了父窗口且设置为嵌入模式，则不创建新窗口
        self.embedded = embedded
        if embedded and parent:
            self.root = parent
            self.is_embedded = True
        else:
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title("界面检测工具")
            self.root.geometry("280x160")
            self.root.overrideredirect(True)  # 去除窗口边框
            self.root.attributes("-alpha", 0.9)  # 设置窗口透明度
            self.root.attributes("-topmost", True)  # 窗口置顶
            self.is_embedded = False
        
        # 只有在非嵌入模式下才绑定拖动和退出事件
        if not self.embedded:
            # 使窗口可拖动
            self.root.bind("<Button-1>", self.start_drag)
            self.root.bind("<B1-Motion>", self.drag)
            self.root.bind("<Escape>", self.exit_program)
        
        # 设置窗口背景
        self.root.configure(bg="#2c3e50")
        
        # 初始化变量
        self.is_detecting = False
        self.detection_thread = None
        self.reference_images = {}  # 改为字典，key为文件夹名称，value为该文件夹下的所有参考图像
        self.detection_result = "未检测"
        self.current_interface = "未检测"
        
        # 定义特殊处理的界面名称
        self.special_interfaces = {
            "course_not_started": False,
            "course_starts": False
        }
        
        # 加载参考图像
        self.load_reference_images()
        
        # 创建界面组件
        self.create_widgets()
        
        # 只有在非嵌入模式下才启动主循环
        if not self.embedded:
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
        """创建界面组件，优化显示效果"""
        # 创建标题标签
        title_label = tk.Label(
            self.root,
            text="界面检测工具",
            font=("微软雅黑", 10, "bold"),
            fg="white",
            bg="#34495e",
            height=1
        )
        title_label.pack(fill=tk.X)
        
        # 创建状态显示区域
        self.status_var = tk.StringVar()
        self.status_var.set("当前界面：未检测")
        status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("微软雅黑", 9, "bold"),
            fg="white",
            bg="#2c3e50",
            wraplength=200,
            height=1,
            justify="center"
        )
        status_label.pack(pady=2, padx=5, fill=tk.BOTH, expand=True)
        
        # 创建按钮框架
        button_frame = tk.Frame(self.root, bg="#2c3e50")
        button_frame.pack(pady=2, padx=5, fill=tk.X)
        
        # 创建开始/停止检测按钮
        self.detect_button = tk.Button(
            button_frame,
            text="开始检测",
            command=self.toggle_detection,
            font=("微软雅黑", 8, "bold"),
            fg="white",
            bg="#27ae60",
            activebackground="#229954",
            bd=0,
            relief=tk.FLAT,
            padx=3,
            pady=2
        )
        self.detect_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # 只有在非嵌入模式下才显示退出按钮
        if not self.embedded:
            # 创建退出按钮
            exit_button = tk.Button(
                button_frame,
                text="退出",
                command=self.exit_program,
                font=("微软雅黑", 8, "bold"),
                fg="white",
                bg="#e74c3c",
                activebackground="#c0392b",
                bd=0,
                relief=tk.FLAT,
                padx=3,
                pady=2
            )
            exit_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=1)
        
        # 只有在非嵌入模式下才显示提示标签
        if not self.embedded:
            # 创建提示标签
            tip_label = tk.Label(
                self.root,
                text="ESC键快速退出",
                font=("微软雅黑", 8),
                fg="#bdc3c7",
                bg="#2c3e50"
            )
            tip_label.pack(pady=(0, 2))
    
    def load_reference_images(self):
        """加载所有参考图像，从img/test下的所有子文件夹"""
        try:
            base_dir = "img/test"
            if os.path.exists(base_dir):
                # 获取base_dir下的所有子文件夹
                subfolders = [f for f in os.listdir(base_dir) 
                             if os.path.isdir(os.path.join(base_dir, f))]
                
                total_images = 0
                for folder in subfolders:
                    folder_path = os.path.join(base_dir, folder)
                    folder_images = []
                    
                    # 加载该文件夹下的所有图片
                    for filename in os.listdir(folder_path):
                        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                            img_path = os.path.join(folder_path, filename)
                            try:
                                # 读取图像并转换为灰度图
                                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                                if img is not None:
                                    folder_images.append(img)
                                    print(f"加载参考图像: {folder}/{filename}")
                            except Exception as e:
                                print(f"加载图像 {folder}/{filename} 时出错: {e}")
                    
                    if folder_images:
                        self.reference_images[folder] = folder_images
                        total_images += len(folder_images)
                        print(f"文件夹 '{folder}' 加载 {len(folder_images)} 张图像")
                
                print(f"\n总共加载 {total_images} 张参考图像，来自 {len(self.reference_images)} 个文件夹")
                print(f"可识别的界面类型: {list(self.reference_images.keys())}")
            else:
                print(f"参考图像基础目录不存在: {base_dir}")
        except Exception as e:
            print(f"加载参考图像时出错: {e}")
    
    def capture_screen(self):
        """捕获当前屏幕画面，优化性能和错误处理"""
        try:
            # 获取屏幕尺寸，仅捕获需要的区域
            screenshot = pyautogui.screenshot()
            
            # 转换为OpenCV格式
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 转换为灰度图以提高匹配速度
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # 应用轻微的高斯模糊以减少噪声影响
            gray_screenshot = cv2.GaussianBlur(gray_screenshot, (3, 3), 0)
            
            return gray_screenshot
        except Exception as e:
            print(f"屏幕捕获出错: {e}")
            return None
    
    def match_template(self, screen_gray, template, threshold=0.85):
        """使用模板匹配算法进行图像比对，优化了匹配精度和性能"""
        try:
            # 获取模板的高度和宽度
            h, w = template.shape
            
            # 如果屏幕图像比模板小，直接返回不匹配
            if screen_gray.shape[0] < h or screen_gray.shape[1] < w:
                return False
            
            # 使用TM_CCOEFF_NORMED方法进行模板匹配（性能和准确性的平衡）
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            
            # 找出匹配度大于阈值的位置
            max_val = cv2.minMaxLoc(result)[1]  # 获取最大匹配值
            
            # 如果最大匹配值大于阈值，认为匹配成功
            return max_val >= threshold
        except Exception as e:
            print(f"模板匹配出错: {e}")
            return False
    
    def detect_screen(self):
        """检测屏幕上的界面类型，支持多界面识别和特殊情况处理"""
        while self.is_detecting:
            try:
                # 捕获当前屏幕
                screen_gray = self.capture_screen()
                if screen_gray is None:
                    time.sleep(0.5)
                    continue
                
                # 重置特殊界面检测状态
                for interface in self.special_interfaces:
                    self.special_interfaces[interface] = False
                
                # 重置当前界面
                detected_interfaces = []
                
                # 遍历所有参考图像文件夹进行检测
                for interface_name, templates in self.reference_images.items():
                    # 检查该界面类型的所有模板是否都匹配
                    interface_matched = True
                    for template in templates:
                        if not self.match_template(screen_gray, template):
                            interface_matched = False
                            break
                    
                    if interface_matched:
                        detected_interfaces.append(interface_name)
                        # 更新特殊界面检测状态
                        if interface_name in self.special_interfaces:
                            self.special_interfaces[interface_name] = True
                
                # 处理特殊情况
                current_interface = self._handle_special_cases(detected_interfaces)
                
                # 更新检测结果
                self._update_detection_result(current_interface)
                
                # 控制检测频率，避免CPU占用过高
                time.sleep(0.3)
                
            except Exception as e:
                print(f"检测过程中出错: {e}")
                time.sleep(1)  # 出错时延长等待时间
    
    def _handle_special_cases(self, detected_interfaces):
        """处理特殊界面识别情况"""
        # 检查是否有特殊界面需要处理
        if self.special_interfaces["course_starts"]:
            # 如果检测到course_starts，无论是否同时检测到course_not_started，都优先判定为course_starts
            return "course_starts"
        elif self.special_interfaces["course_not_started"]:
            # 仅检测到course_not_started时，判定为course_not_started
            return "course_not_started"
        elif detected_interfaces:
            # 检查是否同时存在poll_answered和send_answer界面
            if "poll_answered" in detected_interfaces and "send_answer" in detected_interfaces:
                print(f"同时检测到poll_answered和send_answer界面，优先处理send_answer界面")
                return "send_answer"
            # 其他情况，返回第一个检测到的界面
            return detected_interfaces[0]
        else:
            # 未检测到任何界面
            return "未检测"
    
    def _update_detection_result(self, interface_name):
        """更新检测结果显示"""
        if interface_name != self.current_interface:
            self.current_interface = interface_name
            
            # 更新状态显示
            display_name = interface_name.replace("_", " ").title()
            self.status_var.set(f"当前界面：{display_name}")
            
            # 更新窗口背景色
            if interface_name == "未检测":
                self.root.configure(bg="#2c3e50")  # 默认颜色
            else:
                self.root.configure(bg="#27ae60")  # 检测到目标时变绿色
                print(f"检测到界面: {interface_name}")
    
    def toggle_detection(self):
        """切换检测状态"""
        if self.is_detecting:
            # 停止检测
            self.is_detecting = False
            self.detect_button.config(text="开始检测", bg="#27ae60")
            self.status_var.set(f"检测已停止 - 最后识别：{self.current_interface.replace('_', ' ').title()}")
            if self.detection_thread is not None:
                self.detection_thread.join()
            self.root.configure(bg="#2c3e50")  # 恢复默认颜色
        else:
            # 开始检测
            if not self.reference_images:
                self.status_var.set("错误：未找到参考图像")
                return
            
            self.is_detecting = True
            self.detect_button.config(text="停止检测", bg="#e74c3c")
            self.status_var.set("正在检测界面...")
            # 在新线程中执行检测
            self.detection_thread = threading.Thread(target=self.detect_screen)
            self.detection_thread.daemon = True
            self.detection_thread.start()
    
    def exit_program(self, event=None):
        """退出程序"""
        self.is_detecting = False
        if self.detection_thread is not None:
            self.detection_thread.join()
        # 只有在非嵌入模式下才销毁窗口
        if not self.embedded:
            self.root.destroy()

if __name__ == "__main__":
    try:
        # 检查是否安装了必要的库
        import pyautogui
        import cv2
        import numpy as np
        import PIL
        import os
    except ImportError as e:
        print(f"缺少必要的库: {e}")
        print("请运行以下命令安装所需库:")
        print("pip install pyautogui opencv-python numpy pillow")
        exit(1)
    
    # 打印程序信息
    print("=" * 60)
    print("        界面检测工具 - 启动信息        ")
    print("=" * 60)
    print("程序功能：")
    print("- 实时检测屏幕上的界面类型")
    print("- 支持多界面类型识别")
    print("- 处理特殊界面识别情况")
    print("- 可拖动的悬浮窗口界面")
    print("\n操作说明：")
    print("- 拖动窗口任意位置移动窗口")
    print("- 点击'开始检测'启动实时检测")
    print("- 点击'退出'或按ESC键关闭程序")
    print("=" * 60)
    
    # 启动程序
    app = FloatingImageDetector()