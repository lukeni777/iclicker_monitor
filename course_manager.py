import json
import os
import datetime
import csv
import glob

class CourseManager:
    def __init__(self, data_file="courses.json", csv_file="courses.csv"):
        """初始化课程管理器"""
        self.data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        self.csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_file)
        self.courses = []
        # 尝试从CSV加载数据，如果CSV不存在则从JSON加载
        if not self.load_courses_from_csv():
            self.load_courses_from_json()
            # 如果从JSON加载了数据，同步到CSV
            if self.courses:
                self.save_courses_to_csv()
    
    def load_courses_from_json(self):
        """从JSON文件加载课程数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.courses = json.load(f)
                print(f"成功从JSON加载 {len(self.courses)} 门课程")
            else:
                print("JSON课程文件不存在")
                self.courses = []
        except Exception as e:
            print(f"从JSON加载课程数据时出错: {e}")
            self.courses = []
            return False
        return True
    
    def load_courses_from_csv(self):
        """从CSV文件加载课程数据"""
        try:
            if os.path.exists(self.csv_file):
                self.courses = []
                with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 将数据转换为正确的格式
                        course = {
                            "id": int(row.get("id", 0)),
                            "day": row.get("day", ""),
                            "start_time": row.get("start_time", ""),
                            "end_time": row.get("end_time", ""),
                            "course_code": row.get("course_code", ""),
                            "course_name": row.get("course_name", ""),
                            "created_at": row.get("created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        }
                        if "updated_at" in row:
                            course["updated_at"] = row["updated_at"]
                        self.courses.append(course)
                print(f"成功从CSV加载 {len(self.courses)} 门课程")
                return True
            else:
                print("CSV课程文件不存在")
                return False
        except Exception as e:
            print(f"从CSV加载课程数据时出错: {e}")
            return False
    
    def save_courses_to_json(self):
        """保存课程数据到JSON文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.courses, f, ensure_ascii=False, indent=2)
            print(f"成功保存 {len(self.courses)} 门课程到JSON文件")
            return True
        except Exception as e:
            print(f"保存课程数据到JSON文件时出错: {e}")
            return False
    
    def save_courses_to_csv(self):
        """保存课程数据到CSV文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
            
            # 定义CSV列名
            fieldnames = ["id", "day", "start_time", "end_time", "course_code", "course_name", "created_at"]
            
            with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                # 写入表头
                writer.writeheader()
                # 写入课程数据
                for course in self.courses:
                    # 只写入fieldnames中定义的字段
                    row = {}
                    for field in fieldnames:
                        row[field] = course.get(field, "")
                    writer.writerow(row)
            print(f"成功保存 {len(self.courses)} 门课程到CSV文件")
            return True
        except Exception as e:
            print(f"保存课程数据到CSV文件时出错: {e}")
            return False
    
    def save_courses(self):
        """保存课程数据到文件（同时保存到JSON和CSV）"""
        json_result = self.save_courses_to_json()
        csv_result = self.save_courses_to_csv()
        return json_result and csv_result
    
    def add_course(self, day, start_time, end_time, course_code, course_name):
        """添加新课程"""
        # 生成唯一ID
        course_id = 1
        if self.courses:
            course_id = max(course['id'] for course in self.courses) + 1
            
        course = {
            "id": course_id,
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "course_code": course_code,
            "course_name": course_name,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.courses.append(course)
        return course_id
    
    def update_course(self, course_id, day=None, start_time=None, end_time=None, 
                     course_code=None, course_name=None):
        """更新课程信息"""
        for course in self.courses:
            if course["id"] == course_id:
                if day is not None:
                    course["day"] = day
                if start_time is not None:
                    course["start_time"] = start_time
                if end_time is not None:
                    course["end_time"] = end_time
                if course_code is not None:
                    course["course_code"] = course_code
                if course_name is not None:
                    course["course_name"] = course_name
                course["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True
        return False
    
    def delete_course(self, course_id):
        """删除课程"""
        original_length = len(self.courses)
        self.courses = [course for course in self.courses if course["id"] != course_id]
        return len(self.courses) < original_length
    
    def get_all_courses(self):
        """获取所有课程"""
        return self.courses
    
    def get_course_by_id(self, course_id):
        """通过ID获取课程"""
        for course in self.courses:
            if course["id"] == course_id:
                return course
        return None
    
    def get_courses_by_day(self, day):
        """获取指定星期几的所有课程"""
        return [course for course in self.courses if course["day"] == day]
    
    def get_current_course(self):
        """获取当前时间正在进行的课程"""
        now = datetime.datetime.now()
        current_day = "周" + "一二三四五六日"[now.weekday()]
        current_time = now.strftime("%H:%M")
        
        # 查找当前星期几且时间在上课时间范围内的课程
        for course in self.courses:
            if course["day"] == current_day:
                if course["start_time"] <= current_time <= course["end_time"]:
                    return course
        
        return None
    
    def search_courses(self, keyword):
        """根据关键字搜索课程"""
        keyword = keyword.lower()
        results = []
        
        for course in self.courses:
            if (keyword in course["course_code"].lower() or 
                keyword in course["course_name"].lower() or
                keyword in course["day"].lower()):
                results.append(course)
        
        return results
    
    def get_course_icon_path(self, course_name):
        """获取课程图标的路径
        
        Args:
            course_name: 课程名称
            
        Returns:
            str: 课程图标的完整路径，如果不存在则返回None
        """
        try:
            # 构建保存目录路径
            icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "course")
            
            if not os.path.exists(icon_dir):
                return None
            
            # 清理课程名称（与GUI中的处理方式保持一致）
            import re
            sanitized_name = re.sub(r'[^\w\u4e00-\u9fa5_-]', '', course_name)
            
            if not sanitized_name:
                return None
            
            # 查找匹配的图片文件
            # 尝试不同的图片扩展名
            extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            for ext in extensions:
                icon_path = os.path.join(icon_dir, f"{sanitized_name}{ext}")
                if os.path.exists(icon_path):
                    return icon_path
            
            # 如果没有找到，尝试使用glob匹配
            pattern = os.path.join(icon_dir, f"{sanitized_name}.*")
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
            
            return None
        except Exception as e:
            print(f"获取课程图标路径时发生错误: {str(e)}")
            return None

# 如果直接运行此文件，可以进行简单的测试
if __name__ == "__main__":
    # 示例使用
    manager = CourseManager()
    print("课程管理器初始化完成")