import tkinter as tk
from tkinter import ttk
import pyautogui
import math
import time
import threading

class MousePaintTool:
    def __init__(self, root):
        self.root = root
        self.root.title("鼠标绘画工具")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        
        # 确保窗口居中
        self.center_window()
        
        # 创建覆盖层窗口用于显示标记点
        self.overlay = None
        self.markers = []
        
        # 创建按钮
        self.create_widgets()
        
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建按钮
        draw_button = tk.Button(
            self.root,
            text="绘制圆圈",
            command=self.start_drawing,
            width=100,
            height=40,
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 14)
        )
        draw_button.pack(expand=True)
    
    def create_overlay(self):
        """创建透明覆盖层窗口"""
        if self.overlay is not None:
            self.overlay.destroy()
        
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-transparentcolor", "black")
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="black")
        
        # 创建画布用于绘制标记点
        self.canvas = tk.Canvas(
            self.overlay,
            width=self.root.winfo_screenwidth(),
            height=self.root.winfo_screenheight(),
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack()
    
    def draw_marker(self, x, y):
        """在指定位置绘制标记点"""
        if self.overlay is None:
            self.create_overlay()
        
        # 创建半透明红色圆形标记点
        r = 7.5  # 半径为7.5像素（直径15像素）
        # 在Windows上，我们直接使用红色，不使用stipple参数
        # 如果需要更精确的透明度控制，可以考虑使用其他库如PIL
        marker = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill="#FF0000",
            outline=""
        )
        self.markers.append(marker)
    
    def clear_markers(self):
        """清除所有标记点"""
        if self.overlay is not None:
            for marker in self.markers:
                self.canvas.delete(marker)
            self.markers.clear()
            self.overlay.destroy()
            self.overlay = None
    
    def draw_circle(self):
        """绘制圆形轨迹"""
        try:
            # 获取屏幕分辨率
            screen_width, screen_height = pyautogui.size()
            
            # 计算屏幕中心点
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            # 圆的参数
            radius = 100
            steps = 100  # 绘制圆的步数
            duration = 2.0  # 总持续时间2秒
            step_duration = duration / steps  # 每步的持续时间
            
            # 创建覆盖层
            self.create_overlay()
            
            # 绘制圆形轨迹
            for i in range(steps + 1):
                angle = (2 * math.pi * i) / steps
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # 移动鼠标
                pyautogui.moveTo(x, y, duration=step_duration)
                
                # 点击鼠标（在每个点都点击）
                pyautogui.click(x, y)
                
                # 每隔10像素绘制一个标记点
                if i % 2 == 0:  # 由于steps=100，每步大约移动2π*100/100≈6.28像素，所以每两步绘制一个标记点
                    self.draw_marker(x, y)
            
            # 保持标记点显示5秒
            time.sleep(5)
            
            # 清除标记点
            self.clear_markers()
            
        except Exception as e:
            print(f"发生错误: {e}")
            self.clear_markers()
    
    def start_drawing(self):
        """开始绘制过程"""
        # 在新线程中执行绘制操作，避免UI卡顿
        drawing_thread = threading.Thread(target=self.draw_circle)
        drawing_thread.daemon = True
        drawing_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MousePaintTool(root)
    root.mainloop()