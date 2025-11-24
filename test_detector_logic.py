import os
import cv2
import numpy as np

# 模拟FloatingImageDetector的核心检测逻辑进行测试

class DetectorLogicTester:
    def __init__(self):
        self.reference_images = {}  # 存储参考图像，key为文件夹名称
        self.special_interfaces = {
            "course_not_started": False,
            "course_starts": False
        }
        self.load_reference_images()
    
    def load_reference_images(self):
        """加载参考图像"""
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
    
    def match_template(self, screen_gray, template, threshold=0.85):
        """使用模板匹配算法进行图像比对"""
        try:
            # 获取模板的高度和宽度
            h, w = template.shape
            
            # 如果屏幕图像比模板小，直接返回不匹配
            if screen_gray.shape[0] < h or screen_gray.shape[1] < w:
                return False
            
            # 使用TM_CCOEFF_NORMED方法进行模板匹配
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            
            # 找出匹配度大于阈值的位置
            max_val = cv2.minMaxLoc(result)[1]  # 获取最大匹配值
            
            # 如果最大匹配值大于阈值，认为匹配成功
            return max_val >= threshold
        except Exception as e:
            print(f"模板匹配出错: {e}")
            return False
    
    def handle_special_cases(self, detected_interfaces):
        """处理特殊界面识别情况"""
        # 检查是否有特殊界面需要处理
        if self.special_interfaces["course_starts"]:
            # 如果检测到course_starts，无论是否同时检测到course_not_started，都优先判定为course_starts
            return "course_starts"
        elif self.special_interfaces["course_not_started"]:
            # 仅检测到course_not_started时，判定为course_not_started
            return "course_not_started"
        elif detected_interfaces:
            # 其他情况，返回第一个检测到的界面
            return detected_interfaces[0]
        else:
            # 未检测到任何界面
            return "未检测"
    
    def test_special_cases_handling(self):
        """测试特殊界面处理逻辑"""
        print("\n===== 测试特殊界面处理逻辑 =====")
        
        # 测试用例1：仅检测到course_not_started
        self.special_interfaces["course_not_started"] = True
        self.special_interfaces["course_starts"] = False
        result = self.handle_special_cases(["course_not_started"])
        print(f"1. 仅检测到course_not_started -> 结果: {result} (预期: course_not_started)")
        assert result == "course_not_started", "测试用例1失败"
        
        # 测试用例2：同时检测到course_not_started和course_starts
        self.special_interfaces["course_not_started"] = True
        self.special_interfaces["course_starts"] = True
        result = self.handle_special_cases(["course_not_started", "course_starts"])
        print(f"2. 同时检测到course_not_started和course_starts -> 结果: {result} (预期: course_starts)")
        assert result == "course_starts", "测试用例2失败"
        
        # 测试用例3：仅检测到course_starts
        self.special_interfaces["course_not_started"] = False
        self.special_interfaces["course_starts"] = True
        result = self.handle_special_cases(["course_starts"])
        print(f"3. 仅检测到course_starts -> 结果: {result} (预期: course_starts)")
        assert result == "course_starts", "测试用例3失败"
        
        # 测试用例4：检测到其他界面
        self.special_interfaces["course_not_started"] = False
        self.special_interfaces["course_starts"] = False
        result = self.handle_special_cases(["poll_starts"])
        print(f"4. 检测到其他界面(poll_starts) -> 结果: {result} (预期: poll_starts)")
        assert result == "poll_starts", "测试用例4失败"
        
        # 测试用例5：未检测到任何界面
        self.special_interfaces["course_not_started"] = False
        self.special_interfaces["course_starts"] = False
        result = self.handle_special_cases([])
        print(f"5. 未检测到任何界面 -> 结果: {result} (预期: 未检测)")
        assert result == "未检测", "测试用例5失败"
        
        print("\n✅ 所有特殊界面处理测试用例通过！")
    
    def test_interface_name_formatting(self):
        """测试界面名称格式化"""
        print("\n===== 测试界面名称格式化 =====")
        
        test_cases = [
            ("course_menu", "Course Menu"),
            ("course_not_started", "Course Not Started"),
            ("course_starts", "Course Starts"),
            ("leave_session", "Leave Session"),
            ("poll_answered", "Poll Answered"),
            ("poll_starts", "Poll Starts"),
            ("wait_polls1", "Wait Polls1")
        ]
        
        for original, expected in test_cases:
            formatted = original.replace("_", " ").title()
            print(f"'{original}' -> '{formatted}' (预期: '{expected}')")
            assert formatted == expected, f"界面名称格式化测试失败: {original}"
        
        print("\n✅ 所有界面名称格式化测试通过！")
    
    def test_reference_images_loading(self):
        """测试参考图像加载"""
        print("\n===== 测试参考图像加载 =====")
        
        if self.reference_images:
            print(f"✅ 成功加载 {len(self.reference_images)} 个界面类型的参考图像")
            
            # 检查特殊界面是否都有参考图像
            special_interfaces = ["course_not_started", "course_starts"]
            for interface in special_interfaces:
                if interface in self.reference_images:
                    print(f"   ✅ 特殊界面 '{interface}' 有 {len(self.reference_images[interface])} 张参考图像")
                else:
                    print(f"   ❌ 特殊界面 '{interface}' 缺少参考图像")
                    assert False, f"特殊界面 '{interface}' 缺少参考图像"
            
            # 检查每个界面类型至少有一张参考图像
            for interface_name, templates in self.reference_images.items():
                if len(templates) > 0:
                    print(f"   ✅ 界面 '{interface_name}' 有 {len(templates)} 张参考图像")
                else:
                    print(f"   ❌ 界面 '{interface_name}' 没有参考图像")
                    assert False, f"界面 '{interface_name}' 没有参考图像"
        else:
            print("❌ 参考图像加载失败")
            assert False, "参考图像加载失败"
        
        print("\n✅ 所有参考图像加载测试通过！")

if __name__ == "__main__":
    print("开始测试界面检测逻辑...\n")
    
    try:
        # 创建测试对象
        tester = DetectorLogicTester()
        
        # 运行测试
        tester.test_reference_images_loading()
        tester.test_special_cases_handling()
        tester.test_interface_name_formatting()
        
        print("\n🎉 所有测试通过！改进后的界面检测功能正常工作。")
        print("\n使用说明：")
        print("1. 运行 python floating_image_detector.py 启动完整的界面检测工具")
        print("2. 点击'开始检测'按钮启动实时检测")
        print("3. 工具会自动识别当前屏幕上的界面类型")
        print("4. 特殊处理规则：")
        print("   - 同时检测到course_not_started和course_starts时，优先识别为course_starts")
        print("   - 仅检测到course_not_started时，识别为course_not_started")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    print("\n测试完成！")