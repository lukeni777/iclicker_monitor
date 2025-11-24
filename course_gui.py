import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from course_manager import CourseManager
import datetime
import os
import shutil
import re

def validate_time_format(time_str):
    """验证时间格式"""
    try:
        if len(time_str) != 5 or time_str[2] != ":":
            return False
        hour, minute = map(int, time_str.split(":"))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except:
        return False

class CourseGUI:
    def __init__(self, root):
        """初始化课程管理GUI"""
        self.root = root
        self.root.title("课程表管理系统")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # 初始化课程管理器
        self.manager = CourseManager()
        self.selected_course_id = None
        
        # 创建界面
        self.create_widgets()
        self.load_course_list()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧输入区域
        input_frame = ttk.LabelFrame(main_frame, text="课程信息", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 星期几
        ttk.Label(input_frame, text="星期几:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.day_var = tk.StringVar()
        day_values = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_combo = ttk.Combobox(input_frame, textvariable=self.day_var, values=day_values, width=15)
        day_combo.grid(row=0, column=1, pady=5)
        day_combo.current(0)
        
        # 开始时间
        ttk.Label(input_frame, text="开始时间:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_time_var = tk.StringVar()
        start_time_entry = ttk.Entry(input_frame, textvariable=self.start_time_var, width=15)
        start_time_entry.grid(row=1, column=1, pady=5)
        ttk.Label(input_frame, text="格式: HH:MM").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # 结束时间
        ttk.Label(input_frame, text="结束时间:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.end_time_var = tk.StringVar()
        end_time_entry = ttk.Entry(input_frame, textvariable=self.end_time_var, width=15)
        end_time_entry.grid(row=2, column=1, pady=5)
        ttk.Label(input_frame, text="格式: HH:MM").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # 课号
        ttk.Label(input_frame, text="课号:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.course_code_var = tk.StringVar()
        course_code_entry = ttk.Entry(input_frame, textvariable=self.course_code_var, width=15)
        course_code_entry.grid(row=3, column=1, pady=5)
        
        # 课程名称
        ttk.Label(input_frame, text="课程名称:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.course_name_var = tk.StringVar()
        course_name_entry = ttk.Entry(input_frame, textvariable=self.course_name_var, width=30)
        course_name_entry.grid(row=4, column=1, columnspan=2, pady=5)
        
        # 课程图标截图上传
        ttk.Label(input_frame, text="课程图标:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.icon_path_var = tk.StringVar()
        self.icon_path_var.set("未选择图片")
        self.icon_label = ttk.Label(input_frame, textvariable=self.icon_path_var, width=30, relief=tk.SUNKEN)
        self.icon_label.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        self.upload_icon_button = ttk.Button(input_frame, text="选择截图", command=self.upload_course_icon)
        self.upload_icon_button.grid(row=5, column=2, sticky=tk.W, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        self.add_button = ttk.Button(button_frame, text="添加课程", command=self.add_course)
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        self.update_button = ttk.Button(button_frame, text="更新课程", command=self.update_course)
        self.update_button.pack(side=tk.LEFT, padx=5)
        self.update_button.config(state=tk.DISABLED)
        
        self.delete_button = ttk.Button(button_frame, text="删除课程", command=self.delete_course)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.delete_button.config(state=tk.DISABLED)
        
        self.clear_button = ttk.Button(button_frame, text="清空输入", command=self.clear_inputs)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 创建右侧课程列表
        list_frame = ttk.LabelFrame(main_frame, text="课程列表", padding="10")
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview显示课程列表
        columns = ("id", "day", "start_time", "end_time", "course_code", "course_name")
        self.course_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.course_tree.heading("id", text="ID")
        self.course_tree.heading("day", text="星期几")
        self.course_tree.heading("start_time", text="开始时间")
        self.course_tree.heading("end_time", text="结束时间")
        self.course_tree.heading("course_code", text="课号")
        self.course_tree.heading("course_name", text="课程名称")
        
        # 设置列宽
        self.course_tree.column("id", width=50, anchor=tk.CENTER)
        self.course_tree.column("day", width=80, anchor=tk.CENTER)
        self.course_tree.column("start_time", width=100, anchor=tk.CENTER)
        self.course_tree.column("end_time", width=100, anchor=tk.CENTER)
        self.course_tree.column("course_code", width=120, anchor=tk.CENTER)
        self.course_tree.column("course_name", width=200, anchor=tk.W)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.course_tree.yview)
        self.course_tree.configure(yscroll=scrollbar.set)
        
        # 放置Treeview和滚动条
        self.course_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.course_tree.bind("<<TreeviewSelect>>", self.on_select_course)
        
        # 顶部保存按钮区域 - 添加更明显的保存按钮
        top_save_frame = ttk.Frame(input_frame)
        top_save_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        self.top_save_button = ttk.Button(top_save_frame, text="💾 保存课程表", 
                                         command=self.save_courses, 
                                         style="Accent.TButton")
        self.top_save_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 创建样式使保存按钮更加突出
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="black", background="#4CAF50", 
                       font=('Arial', 10, 'bold'))
        
        # 底部保存按钮 - 保留并改进
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # 添加保存状态标签
        self.save_status_var = tk.StringVar()
        self.save_status_var.set("")
        self.save_status_label = ttk.Label(save_frame, textvariable=self.save_status_var, 
                                         font=("SimHei", 10), foreground="green")
        self.save_status_label.pack(side=tk.LEFT, padx=10)
        
        self.save_button = ttk.Button(save_frame, text="💾 保存课程表", 
                                    command=self.save_courses, 
                                    style="Accent.TButton")
        self.save_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def load_course_list(self):
        """加载课程列表到Treeview"""
        # 清空现有数据
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        
        # 添加课程数据
        for course in self.manager.get_all_courses():
            self.course_tree.insert("", tk.END, values=(course["id"], course["day"], 
                                                     course["start_time"], course["end_time"], 
                                                     course["course_code"], course["course_name"]))
    
    def on_select_course(self, event):
        """选择课程时触发"""
        selected_items = self.course_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        course_id = int(self.course_tree.item(item, "values")[0])
        course = self.manager.get_course_by_id(course_id)
        
        if course:
            self.selected_course_id = course_id
            self.day_var.set(course["day"])
            self.start_time_var.set(course["start_time"])
            self.end_time_var.set(course["end_time"])
            self.course_code_var.set(course["course_code"])
            self.course_name_var.set(course["course_name"])
            
            # 检查课程图标是否存在
            icon_path = self.manager.get_course_icon_path(course["course_name"])
            if icon_path and os.path.exists(icon_path):
                self.icon_path_var.set(f"已上传: {os.path.basename(icon_path)}")
            else:
                self.icon_path_var.set("未选择图片")
            
            # 启用更新和删除按钮
            self.update_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
    
    def clear_inputs(self):
        """清空输入框"""
        self.day_var.set("周一")
        self.start_time_var.set("")
        self.end_time_var.set("")
        self.course_code_var.set("")
        self.course_name_var.set("")
        self.icon_path_var.set("未选择图片")
        self.selected_course_id = None
        
        # 禁用更新和删除按钮
        self.update_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        
        # 取消选择
        self.course_tree.selection_remove(self.course_tree.selection())
    
    def sanitize_filename(self, filename):
        """移除文件名中的特殊字符"""
        # 移除非字母数字、中文和下划线的字符
        return re.sub(r'[^\w\u4e00-\u9fa5_-]', '', filename)
    
    def upload_course_icon(self):
        """上传课程图标截图"""
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择课程图标截图",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        
        if file_path:
            self.icon_path_var.set(f"已选择: {os.path.basename(file_path)}")
    
    def save_course_icon(self, course_name, icon_path):
        """保存课程图标到指定目录"""
        if not icon_path or icon_path == "未选择图片" or icon_path.startswith("已上传:"):
            return True
        
        try:
            # 创建保存目录（如果不存在）
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "course")
            os.makedirs(save_dir, exist_ok=True)
            
            # 获取原文件扩展名
            _, ext = os.path.splitext(icon_path)
            if ext == "":
                # 如果没有扩展名，默认使用.png
                ext = ".png"
            
            # 清理课程名称作为文件名
            sanitized_name = self.sanitize_filename(course_name)
            if not sanitized_name:
                messagebox.showerror("错误", "课程名称无法转换为有效的文件名")
                return False
            
            # 构建保存路径
            save_path = os.path.join(save_dir, f"{sanitized_name}{ext}")
            
            # 如果文件存在，先删除
            if os.path.exists(save_path):
                os.remove(save_path)
            
            # 复制文件
            if icon_path.startswith("已选择:"):
                # 从已选择的路径中提取实际路径
                actual_path = icon_path.replace("已选择: ", "")
                # 重新打开文件选择对话框获取完整路径
                file_path = filedialog.askopenfilename(
                    title="重新选择课程图标截图",
                    filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
                )
                if file_path:
                    shutil.copy2(file_path, save_path)
            else:
                shutil.copy2(icon_path, save_path)
            
            print(f"课程图标已保存到: {save_path}")
            return True
        except Exception as e:
            messagebox.showerror("保存错误", f"保存课程图标时发生错误: {str(e)}")
            return False
    
    def add_course(self):
        """添加课程"""
        # 获取输入值
        day = self.day_var.get()
        start_time = self.start_time_var.get()
        end_time = self.end_time_var.get()
        course_code = self.course_code_var.get().strip()
        course_name = self.course_name_var.get().strip()
        icon_path = self.icon_path_var.get()
        
        # 验证输入
        if not validate_time_format(start_time):
            messagebox.showerror("输入错误", "开始时间格式不正确，请使用HH:MM格式")
            return
        
        if not validate_time_format(end_time):
            messagebox.showerror("输入错误", "结束时间格式不正确，请使用HH:MM格式")
            return
        
        if end_time <= start_time:
            messagebox.showerror("输入错误", "结束时间必须晚于开始时间")
            return
        
        if not course_code:
            messagebox.showerror("输入错误", "课号不能为空")
            return
        
        if not course_name:
            messagebox.showerror("输入错误", "课程名称不能为空")
            return
        
        # 添加课程
        course_id = self.manager.add_course(day, start_time, end_time, course_code, course_name)
        
        # 保存课程图标
        if not icon_path.startswith("未选择"):
            self.save_course_icon(course_name, icon_path)
        
        messagebox.showinfo("成功", f"课程添加成功！课程ID: {course_id}")
        
        # 刷新列表并清空输入
        self.load_course_list()
        self.clear_inputs()
    
    def update_course(self):
        """更新课程"""
        if self.selected_course_id is None:
            messagebox.showerror("错误", "请先选择要更新的课程")
            return
        
        # 获取输入值
        day = self.day_var.get()
        start_time = self.start_time_var.get()
        end_time = self.end_time_var.get()
        course_code = self.course_code_var.get().strip()
        course_name = self.course_name_var.get().strip()
        icon_path = self.icon_path_var.get()
        
        # 验证输入
        if not validate_time_format(start_time):
            messagebox.showerror("输入错误", "开始时间格式不正确，请使用HH:MM格式")
            return
        
        if not validate_time_format(end_time):
            messagebox.showerror("输入错误", "结束时间格式不正确，请使用HH:MM格式")
            return
        
        if end_time <= start_time:
            messagebox.showerror("输入错误", "结束时间必须晚于开始时间")
            return
        
        if not course_code:
            messagebox.showerror("输入错误", "课号不能为空")
            return
        
        if not course_name:
            messagebox.showerror("输入错误", "课程名称不能为空")
            return
        
        # 获取原课程信息
        old_course = self.manager.get_course_by_id(self.selected_course_id)
        old_name = old_course["course_name"]
        
        # 更新课程
        if self.manager.update_course(self.selected_course_id, day, start_time, end_time, course_code, course_name):
            # 如果课程名称改变，需要处理图标文件
            if old_name != course_name:
                # 检查旧图标是否存在
                old_icon_path = self.manager.get_course_icon_path(old_name)
                if old_icon_path and os.path.exists(old_icon_path):
                    # 如果上传了新图标，直接保存新图标
                    if not icon_path.startswith("未选择") and not icon_path.startswith("已上传:"):
                        self.save_course_icon(course_name, icon_path)
                    else:
                        # 否则，重命名旧图标
                        try:
                            _, ext = os.path.splitext(old_icon_path)
                            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "course")
                            new_icon_path = os.path.join(save_dir, f"{self.sanitize_filename(course_name)}{ext}")
                            if os.path.exists(new_icon_path):
                                os.remove(new_icon_path)
                            os.rename(old_icon_path, new_icon_path)
                        except Exception as e:
                            print(f"重命名课程图标时发生错误: {str(e)}")
            else:
                # 课程名称未改变，直接保存新图标（如果有）
                if not icon_path.startswith("未选择") and not icon_path.startswith("已上传:"):
                    self.save_course_icon(course_name, icon_path)
            
            messagebox.showinfo("成功", "课程更新成功！")
            # 刷新列表并清空输入
            self.load_course_list()
            self.clear_inputs()
        else:
            messagebox.showerror("错误", "课程更新失败")
    
    def delete_course(self):
        """删除课程"""
        if self.selected_course_id is None:
            messagebox.showerror("错误", "请先选择要删除的课程")
            return
        
        course = self.manager.get_course_by_id(self.selected_course_id)
        if not course:
            messagebox.showerror("错误", "课程不存在")
            return
        
        # 确认删除
        if messagebox.askyesno("确认删除", 
                              f"确定要删除课程 '{course['course_name']}' (课号: {course['course_code']}) 吗？"):
            if self.manager.delete_course(self.selected_course_id):
                # 删除课程图标
                icon_path = self.manager.get_course_icon_path(course["course_name"])
                if icon_path and os.path.exists(icon_path):
                    try:
                        os.remove(icon_path)
                        print(f"已删除课程图标: {icon_path}")
                    except Exception as e:
                        print(f"删除课程图标时发生错误: {str(e)}")
                
                messagebox.showinfo("成功", "课程删除成功！")
                # 刷新列表并清空输入
                self.load_course_list()
                self.clear_inputs()
            else:
                messagebox.showerror("错误", "课程删除失败")
    
    def save_courses(self):
        """保存课程表到JSON和CSV文件"""
        try:
            # 保存到文件
            if self.manager.save_courses():
                # 更新保存状态
                save_time = datetime.datetime.now().strftime("%H:%M:%S")
                self.save_status_var.set(f"最后保存: {save_time}")
                
                # 获取CSV文件路径用于显示
                csv_file_path = getattr(self.manager, 'csv_file', 'courses.csv')
                csv_file_name = os.path.basename(csv_file_path)
                
                messagebox.showinfo("保存成功", 
                                  f"课程表已成功保存！\n" 
                                  f"1. 数据已保存到程序目录中的 {csv_file_name} 文件\n" 
                                  f"2. 您可以使用Excel或其他表格软件查看和编辑该文件\n" 
                                  f"3. 下次打开软件时将自动加载这些课程")
                return True
            else:
                self.save_status_var.set("保存失败")
                messagebox.showerror("保存失败", 
                                    "无法保存课程表数据。请检查文件权限或磁盘空间。")
                return False
        except Exception as e:
            self.save_status_var.set(f"保存出错: {str(e)}")
            messagebox.showerror("保存错误", f"保存过程中发生错误: {str(e)}")
            return False

def main():
    """主函数"""
    root = tk.Tk()
    app = CourseGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()