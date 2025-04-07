import json
import os 
import random 
import logging


logging.basicConfig(level=logging.INFO)


class Scheduler:
    def __init__(self, staff_list,area_config):
        logging.info(f"Initialized Scheduler with area_config: {area_config}")
        logging.info(f"Staff list: {staff_list}")
    
        self.area_config = self.parse_area_config(area_config)
        self.staff_list = self.parse_staff_list(staff_list)
        
        #从JSON 文件加载文本配置
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, '..', 'json', "staff_table_config.json")
                                 
        with open(json_path, 'r',encoding='utf-8') as f:
            config = json.load(f)
            self.text = config['scheduler_key']

        self.inbound_front = []
        self.inbound_back = []
        self.outbound_front = []
        self.outbound_back = []
        self.mobile_team = []
        self.inbound_count = 0
        self.outbound_count = 0

        logging.info(f"Text configuration: {self.text}")

    def parse_area_config(self, area_config):
        required_heys = ['Inbound_Front', 'Inbound_back', 'Outbound_Front', 'Outbound_back', 'Inbound_total','Outbound_total']
        for key in required_heys:
            if key not in area_config:
                raise ValueError(f"Nissing key in area_config: {key}")
            
        return area_config
    
    def parse_staff_list(self, staff_list):
        parsed_list =[]
        for staff in staff_list:
            if not isinstance(staff, dict):
                raise ValueError(f"意外的员工格式：{staff}")
            
            #只添加 Attendance为‘Y'的员工
            if staff.get('Attendance') == "Y":
                parsed_list.append(staff)

        return parsed_list

    def generate_result_dict(self):
        result = {
            self.text['inbound']:{
                self.text['front']: self.inbound_front,
                self.text['back']: self.inbound_back
            },
            self.text['outbound']: {
            self.text['front']: self.outbound_front,
            self.text['back']: self.outbound_back
            },
        }
        return result

    def assign_to_leader_position(self, staff, leader_position):
        if leader_position == 'inbound_front':
            if len(self.inbound_front) < self.area_config['Inbound_Front']:
                self.inbound_front.append(staff['name'])
                return True
        elif leader_position == 'inbound_back':
            if len(self.inbound_back)< self.area_config['Inbound_back']:
                self.inbound_back.append(staff['name'])
                return True
        elif leader_position =='outbound_front':
            if len(self.outbound_front) < self.area_config['Outbound_Front']:
                self.outbound_front.append(staff['name'])
                return True
        elif leader_position == 'outbound_back':
            if len(self.outbound_back) < self.area_config['Outbound_back']:
                self.outbound_back.append(staff['name'])
                return True
        return False

    def get_staff_position(self, staff):
        if staff['name'] in self.inbound_front:
            return 'inbound_front'
        elif staff['name'] in self.inbound_back:
            return "inbound_back"
        elif staff['name'] in self.outbound_front:
            return 'outbound_front' 
        elif staff['name'] in self.outbound_back:
            return 'outbound_back'
        else:
            return None
        
    def assign_group(self):
        #步骤1：获取所有唯一的组
        all_groups = set()
        for staff in self.staff_list:
            if 'group_leader' in staff:
                all_groups.add(staff['group_leader'])
            elif 'group_member' in staff:
                all_groups.add(staff['group_member'])

        # 步骤2：为每个组建立成员列表，并确保组名唯一
        group_mapping = {}
        for staff in self.staff_list:
            if 'group_leader' in staff:
                group_name = self.normalize_group_name(staff['group_leader'])
            elif 'group_member' in staff:
                group_name = self.normalize_group_name(staff['group_member'])
            else:
                continue

            if group_name not in group_mapping:
                group_mapping[group_name] =[]

            group_mapping[group_name].append(staff)
        
        #步骤3：分配每个组的成员
        for group, members in group_mapping.items():
            leader = next((member for member in members if 'group_leader' in member), None)
            if leader and self.assign_staff(leader):
                leader_position = self.get_staff_position(leader)
                # 步骤4：根据Leader的位置，将其他成员分配到同一区域
                for member in members:
                    if member != leader:
                        self.assign_to_leader_position(member, leader_position)

    def normalize_group_name(self, group_name):
        # 这个方法用于标准化组名，确保相似的组名被视为相同
        #可以根据实际需求进行调整
        return group_name.lower().strip()
    
    def schedule(self):
        assigned_staff = set()

        #1.处理固定区域的员工
        for staff in self.staff_list:
            if staff['fixed_area']:
                if staff['fixed_area'] == self.text['inbound']:
                    if self.assign_inbound(staff):
                        assigned_staff.add(staff['name'])
                    else:
                        self.Log_assignment_error("无法为固定入境区域员工分配工作。",staff,{
                            "入境总人数":len(self.inbound_front) + len(self.inbound_back),
                            "入境总限制":self.area_config['Inbound_Total']
                            })
                        return False, None
            elif staff['fixed_area'] == self.text['outbound']:
                if self.assign_outbound(staff):
                    assigned_staff.add(staff['name'])
                else:
                    self.Log_assignment_error("无法为固定出境区域员工分配工作。",staff,{
                    "出境总人数":len(self.outbound_front)+ len(self.outbound_back),
                    "出境总限制":self.area_config['Outbound_Total']
                    })
                    return False, None
            
        #2.处理组
        self.assign_group()
        for staff in self.staff_list:
            if self.get_staff_position(staff):
                assigned_staff.add(staff['name'])

        # 3.处理剩余员工
        for staff in self.staff_list:
            if staff['name'] not in assigned_staff:
                if self.assign_staff(staff):
                    assigned_staff.add(staff['name'])
                else:
                    self.Log_assignment_error("无法为普通员工分配工作。",staff,{})
                    return False, None

        # 生成并返回排班结果字典
        result_dict = self.generate_result_dict()
        return True, result_dict

    def assign_front(self, staff, area):
        if area == self.text['outbound']:
            front_limit = self.area_config['Outbound_Front']
            current_front = self.outbound_front
        elif area == self.text['inbound']:
            front_limit = self.area_config['Inbound_Front']
            current_front = self.inbound_front
        else:
            logging.error(f"无效的区域：{area}")
            return False
        
        if len(current_front) < front_limit:
            current_front.append(staff['name'])
            logging.info(f"成功将{staff['name']}分配到{area}前台")
            return True
        else:
            logging.info(f"{area}前台已满，无法分配 {staff['name']}")
            return False

    def assign_back(self, staff,area):
        if area == self.text['outbound']:
            back_limit = self.area_config['Outbound_back']
            current_back = self.outbound_back
        elif area == self.text['inbound']:
            back_limit = self.area_config['Inbound_back']
            current_back = self.inbound_back
        else:
            logging.error(f"无效的区域：{area}")
            return False

        if len(current_back) < back_limit:
            current_back.append(staff['name'])
            logging.info(f"成功将 {staff['name']} 分配到 {area} 后台")
            return True
        else:
            logging.info(f"{area}后台已满，无法分配{staff['name']}")
            return False

    def assign_inbound(self, staff):
        #检查入境总人数是否已满
        if len(self.inbound_front) + len(self.inbound_back) >= self.area_config['Inbound_total']:
            logging.info(f"入境区域已满员，无法分配{staff['name']}")
            return False

        area = self.text['inbound']
        preferred_section = staff.get('preferred_section','')
                                      
        #检查前台和后台的空缺情况
        front_vacancy = self.area_config['Inbound_Front'] - len(self.inbound_front)
        back_vacancy = self.area_config['Inbound_back'] - len(self.inbound_back)

        if preferred_section == self.text['front'] and front_vacancy > 0:
            return self.assign_front(staff, area)
        elif preferred_section == self.text['back'] and back_vacancy > 0:
            return self.assign_back(staff, area)
        

        #如果偏好设置未成功或没有偏好，尝试其他分配方式
        if front_vacancy > 0 and back_vacancy > 0:
        #两者都有空缺，分配到空缺数较大的区域
            if front_vacancy > back_vacancy:
                return self.assign_front(staff, area)
            else:
                return self.assign_back(staff, area)
        elif front_vacancy > 0:
            #只有前台有空缺
            return self.assign_front(staff, area)
        elif back_vacancy > 0:
            #只有后台有空缺
            return self.assign_back(staff,area)
        else:
            # 两者都没有空缺
            logging.info(f"入境前台和后台都已满员，无法分配{staff['name']}")
            return False

    def assign_outbound(self, staff):
        #检查出境总人数是否已满
        if len(self.outbound_front) + len(self.outbound_back) >= self.area_config['Outbound_total']:
            logging.info(f"出境区域已满员，无法分配 {staff['name']}")
            return False
        
        area = self.text['outbound']
        preferred_section = staff.get('preferred_section','')

        #检查前台和后台的空缺情况
        front_vacancy = self.area_config['Outbound_Front'] - len(self.outbound_front)
        back_vacancy = self.area_config['Outbound_back'] - len(self.outbound_back)

        if preferred_section == self.text['front'] and front_vacancy > 0:
            return self.assign_front(staff, area)
        elif preferred_section == self.text['back'] and back_vacancy > 0:
            return self.assign_back(staff,area)
        

        #如果偏好设置未成功或没有偏好，尝试其他分配方式
        if front_vacancy > 0 and back_vacancy > 0:
        #两者都有空缺，分配到空缺数较大的区域
            if front_vacancy > back_vacancy:
                return self.assign_front(staff, area)
            else:
                return self.assign_back(staff,area)
        elif front_vacancy > 0:
            #只有前台有空缺
            return self.assign_front(staff, area)
        elif back_vacancy > 0:
            # 只有后台有空缺
            return self.assign_back(staff, area)
        else:
            # 两者都没有空缺
            logging.info(f"出境前台和后台都已满员，无法分配 {staff['name']}")
            return False


    def assign_mobile(self,staff):
        preferred_area = staff.get('preferred_area','')

        # 1、检查偏好是否为入境
        if preferred_area == self.text['inbound']:
            if self.assign_inbound(staff):
                return True
 
        #2.检查偏好是否为出境
        elif preferred_area == self.text['outbound']:
            if self.assign_outbound(staff):
                return True

        #3.如果没有明确的偏好或上述分配失败
        inbound_vacancy = self.area_config['Inbound_total']-(len(self.inbound_front) + len(self.inbound_back))
        outbound_vacancy = self.area_config['Outbound_total'] - (len(self.outbound_front) + len(self.outbound_back))

        if inbound_vacancy > 0 and outbound_vacancy > 0:
            # 两者都有空缺，分配到空缺数较大的区域
            if inbound_vacancy > outbound_vacancy:
                return self.assign_inbound(staff)
            else:
                return self.assign_outbound(staff)
        elif inbound_vacancy > 0:
            #只有入境有空缺
            return self.assign_inbound(staff)
        elif outbound_vacancy >0:
            #只有出境有空缺
            return self.assign_outbound(staff)
        else:
            # 两者都没有空缺
            logging.info(f"出境和入境都已满员，无法分配 {staff['name']}")
            return False
        
    def Log_assignment_error(self, message, staff, area_info):

        logging.error(f"{message}相关参数如下：")
        logging.error(f"员工信息：{staff}")
        for key, value in area_info.items():
            logging.error(f"{key}: {value}")

    def assign_staff(self,staff):

        team_name = staff['team_name']

        #1、入境团队分配
        if team_name == self.area_config['Inbound_team']:
            if not self.assign_inbound(staff):
                self.Log_assignment_error("无法为入境团队成员分配工作.",staff,{
                "入境前台人数":len(self.inbound_front),
                "入境后台人数":len(self.inbound_back),
                "入境总人数":len(self.inbound_front) + len(self.inbound_back),
                "入境总限制":self.area_config['Inbound_total']
                })
                return False 
            return True
        
        #2.出境团队分配
        elif team_name == self.area_config['Outbound_team']:
            if not self.assign_outbound(staff):
                self.Log_assignment_error("无法为出境团队成员分配工作.",staff,{
                "出境前台人数":len(self.outbound_front),
                "出境后台人数":len(self.outbound_back),
                "出境总人数":len(self.outbound_front) + len(self.outbound_back),
                "出境总限制":self.area_config['Outbound_total']
                })
                return False 
            return True

        #3.机动团队分配
        elif team_name == self.area_config['Mobile_team']:
            if not self.assign_mobile(staff):
                self.Log_assignment_error("无法为机动团队成员分配工作1.",staff,{
                "出境前台人数":len(self.outbound_front),
                "出境后台人数":len(self.outbound_back),
                "出境总人数":len(self.outbound_front) + len(self.outbound_back),
                "出境总限制":self.area_config['Outbound_total']
                })
                self.Log_assignment_error("无法为机动团队成员分配工作2.",staff,{
                "入境前台人数":len(self.inbound_front),
                "入境后台人数":len(self.inbound_back),
                "入境总人数":len(self.inbound_front) + len(self.inbound_back),
                "入境总限制":self.area_config['Inbound_total']
                })
                return False 
            return True
        else:
            logging.error(f"未知的团队名称：{team_name}")
            return False