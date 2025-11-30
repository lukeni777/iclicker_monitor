import tkinter as tk
from tkinter import ttk, messagebox
from course_gui import CourseGUI
import os
import datetime

def main():
    """主程序入口"""
    print("===== IClicker Monitor 系统 =====")
    print("启动图形界面模式...")
    
    # 创建主窗口
    root = tk.Tk()
    
    # 设置窗口标题和图标（可选）
    root.title("IClicker Monitor")
    root.geometry("1000x650")
    
    # 创建标签页控件
    tab_control = ttk.Notebook(root)
    
    # 创建课程管理标签页
    course_tab = ttk.Frame(tab_control)
    tab_control.add(course_tab, text="课程管理")
    
    # 创建监测设置标签页（预留）
    monitor_tab = ttk.Frame(tab_control)
    tab_control.add(monitor_tab, text="监测设置")
    
    # 创建操作日志标签页（预留）
    log_tab = ttk.Frame(tab_control)
    tab_control.add(log_tab, text="操作日志")
    
    # 放置标签页控件
    tab_control.pack(expand=1, fill="both")
    
    # 在课程管理标签页中初始化课程管理界面
    course_gui_frame = ttk.Frame(course_tab)
    course_gui_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 这里我们直接创建课程管理界面的所有组件
    # 为了简化，我们复用CourseGUI类的大部分逻辑
    
    # 导入并初始化课程管理器
    from course_manager import CourseManager
    manager = CourseManager()
    
    # 显示欢迎信息
    welcome_label = ttk.Label(course_gui_frame, text="欢迎使用课程表管理系统", font=("SimHei", 14))
    welcome_label.pack(pady=10)
    
    # 创建一个按钮来打开独立的课程管理窗口
    def open_course_management():
        course_window = tk.Toplevel(root)
        course_window.title("课程表管理")
        course_window.geometry("900x600")
        course_window.transient(root)  # 设置为主窗口的子窗口
        course_window.grab_set()  # 模态窗口
        
        # 在新窗口中创建CourseGUI实例，传递现有的manager实例
        from course_gui import CourseGUI
        CourseGUI(course_window, manager)
    
    # 创建管理课程按钮
    manage_button = ttk.Button(course_gui_frame, text="管理课程", command=open_course_management, width=20)
    manage_button.pack(pady=20)
    
    # 显示当前已加载的课程数量和保存状态
    status_frame = ttk.Frame(course_gui_frame)
    status_frame.pack(pady=10, fill=tk.X, padx=20)
    
    courses_count = len(manager.get_all_courses())
    status_var = tk.StringVar()
    status_var.set(f"当前已加载 {courses_count} 门课程")
    status_label = ttk.Label(status_frame, textvariable=status_var, 
                           font=("SimHei", 10), foreground="blue")
    status_label.pack(side=tk.LEFT, padx=5)
    
    # 添加主界面保存按钮
    def save_courses_from_main():
        """从主界面保存课程表"""
        try:
            if manager.save_courses():
                save_time = datetime.datetime.now().strftime("%H:%M:%S")
                status_var.set(f"当前已加载 {len(manager.get_all_courses())} 门课程 | 最后保存: {save_time}")
                
                # 获取CSV文件路径用于显示
                csv_file_path = getattr(manager, 'csv_file', 'courses.csv')
                csv_file_name = os.path.basename(csv_file_path)
                csv_full_path = os.path.abspath(csv_file_path)
                
                messagebox.showinfo("保存成功", 
                                  f"课程表已成功保存！\n" 
                                  f"1. 数据已保存到: {csv_full_path}\n" 
                                  f"2. 您可以使用Excel或其他表格软件查看和编辑该文件\n" 
                                  f"3. 下次打开软件时将自动加载这些课程")
            else:
                status_var.set(f"保存失败 | 当前已加载 {len(manager.get_all_courses())} 门课程")
                messagebox.showerror("保存失败", "无法保存课程表数据")
        except Exception as e:
            status_var.set(f"保存出错 | 当前已加载 {len(manager.get_all_courses())} 门课程")
            messagebox.showerror("保存错误", f"保存过程中发生错误: {str(e)}")
    
    # 创建样式使保存按钮更加突出
    style = ttk.Style()
    style.configure("Accent.TButton", foreground="black", background="#4CAF50", 
                   font=('Arial', 10, 'bold'))
    
    save_button = ttk.Button(status_frame, text="💾 保存课程表", 
                           command=save_courses_from_main, 
                           style="Accent.TButton")
    save_button.pack(side=tk.RIGHT, padx=5)
    
    # 添加查看CSV文件按钮
    def open_csv_file():
        """打开CSV文件"""
        try:
            csv_file_path = getattr(manager, 'csv_file', 'courses.csv')
            if os.path.exists(csv_file_path):
                os.startfile(csv_file_path)  # 在Windows中打开文件
            else:
                messagebox.showinfo("提示", "CSV文件尚未创建，请先添加课程并保存")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开CSV文件: {str(e)}")
    
    view_button = ttk.Button(status_frame, text="📊 查看CSV文件", 
                           command=open_csv_file)
    view_button.pack(side=tk.RIGHT, padx=5)
    
    # 添加窗口关闭事件处理 - 自动保存
    def on_closing():
        """窗口关闭前提示保存"""
        if len(manager.get_all_courses()) > 0:
            answer = messagebox.askyesnocancel("确认退出", 
                                             "您是否要在退出前保存课程表？")
            if answer is None:  # 取消
                return
            if answer:  # 是
                manager.save_courses()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()