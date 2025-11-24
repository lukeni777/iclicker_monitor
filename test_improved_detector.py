import tkinter as tk
import threading
import time
import sys
from floating_image_detector import FloatingImageDetector

class TestDetector:
    def __init__(self):
        # 创建一个线程来运行GUI
        self.gui_thread = threading.Thread(target=self.run_gui)
        self.gui_thread.daemon = True
        self.gui_thread.start()
        
        # 等待GUI初始化
        time.sleep(2)
        
        # 测试功能
        self.test_detection()
    
    def run_gui(self):
        # 创建并运行FloatingImageDetector实例
        self.app = FloatingImageDetector()
    
    def test_detection(self):
        print("\n===== 开始测试界面检测功能 =====")
        
        try:
            # 等待一段时间确保GUI完全加载
            time.sleep(3)
            
            print("\n1. 检查参考图像加载情况：")
            if hasattr(self.app, 'reference_images') and self.app.reference_images:
                print(f"   ✅ 成功加载 {len(self.app.reference_images)} 个界面类型的参考图像")
                for interface_name, templates in self.app.reference_images.items():
                    print(f"   - {interface_name}: {len(templates)} 张图像")
            else:
                print("   ❌ 参考图像加载失败")
            
            print("\n2. 检查特殊界面处理逻辑：")
            if hasattr(self.app, 'special_interfaces'):
                print(f"   ✅ 特殊界面配置: {self.app.special_interfaces}")
            else:
                print("   ❌ 特殊界面配置缺失")
            
            print("\n3. 模拟界面检测测试：")
            # 模拟检测到course_not_started界面
            self.app.special_interfaces["course_not_started"] = True
            detected = self.app._handle_special_cases(["course_not_started"])
            print(f"   - 仅检测到course_not_started: 结果 = {detected}")
            
            # 模拟同时检测到course_not_started和course_starts界面
            self.app.special_interfaces["course_starts"] = True
            detected = self.app._handle_special_cases(["course_not_started", "course_starts"])
            print(f"   - 同时检测到course_not_started和course_starts: 结果 = {detected}")
            
            # 模拟检测到其他界面
            detected = self.app._handle_special_cases(["poll_starts"])
            print(f"   - 检测到其他界面(poll_starts): 结果 = {detected}")
            
            print("\n4. 测试界面名称格式化：")
            interface_name = "poll_starts"
            display_name = interface_name.replace("_", " ").title()
            print(f"   - 原始名称: {interface_name} -> 显示名称: {display_name}")
            
            print("\n===== 测试完成 =====")
            print("\n请手动在GUI中点击'开始检测'按钮测试实际的屏幕检测功能。")
            print("程序将在10秒后自动退出测试模式。")
            
            # 等待10秒后退出
            time.sleep(10)
            
        except Exception as e:
            print(f"\n测试过程中出错: {e}")
        finally:
            # 退出程序
            sys.exit(0)

if __name__ == "__main__":
    print("启动改进后的界面检测工具测试...")
    test = TestDetector()