def validate_configuration(staff_list, area_config):

    # 统计出勤的员工数量（假设出勤标识为 "Y" 存储在键 "Attendance" 中）
    attending_count = sum(1 for staff in staff_list if staff.get("Attendance") == "Y")
    
    # 这里假设配置中总出勤人数存储在 "total_attendance" 键中
    total_required = area_config.get("total_attendance")
    
    if total_required is None:
        # 如果配置中没有要求就认为校验通过
        return True, "配置中不存在总出勤人数要求"
    
    if attending_count != total_required:
        return False, f"出勤人数不匹配：当前出勤人数为 {attending_count}，要求出勤人数为 {total_required}"
    
    return True, "配置有效"