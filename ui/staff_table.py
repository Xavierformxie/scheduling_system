import json 
import os 
import sys
import pandas as pd
import re
from PyQt6.QtWidgets import (
QTableWidget, QTableWidgetItem,QComboBox, QHeaderView,
QLineEdit, QWidget, QVBoxLayout, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal
import pkgutil
import shutil


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None

class EditableOnDoubleClickDelegate(QStyledItemDelegate):
    def createEditor(self, parent,option, index):
        editor = super().createEditor(parent, option,index)
        if isinstance(editor, QLineEdit):
            editor.editingFinished.connect(lambda: self.commitAndCloseEditor(editor))
        return editor

    def commitAndCloseEditor(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

class DoubleClickComboBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        return editor

    def setEditorData(self, editor, index):
        # 从模型中取出下拉选项数据（保存在UserRole中），确保数据非None
        options = index.model().data(index, Qt.ItemDataRole.UserRole)
        if isinstance(editor, QComboBox) and options is not None:
            editor.clear()
            editor.addItems(options)
        # 设置当前显示的文本
        value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if value is not None:
            editor.setCurrentText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class StaffTable(QTableWidget):
    staff_data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.staff_data = self.load_staff_data()
        self.setup_table()
        self.populate_table()

    def get_config_path(self):
        user_data_dir = os.path.join(os.path.expanduser('~'), 'SchedulingSystemConfig')
        os.makedirs(user_data_dir, exist_ok=True)
        config_path = os.path.join(user_data_dir, 'staff_table_config.json')

        if not os.path.exists(config_path):
            if getattr(sys, 'frozen', False):
                # 如果是打包后的环境
                default_config = pkgutil.get_data(__name__, "json/staff_table_config.json")
                if default_config is None:
                    raise FileNotFoundError("无法找到默认配置文件 'json/staff_table_config.json'")
                with open(config_path, 'wb') as f:
                    f.write(default_config)
            else:
                # 开发环境
                default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'json', 'staff_table_config.json')
                if os.path.exists(default_path):
                    shutil.copy(default_path, config_path)
                else:
                    raise FileNotFoundError(f"默认配置文件不存在: {default_path}")

        return config_path  # 确保在所有情况下都返回 config_path

    def get_default_config(self):
        return {
            "columns":[
                {
                    "key":"name",
                    "display":"姓名",
                    "type":"text",
                    "readonly": False,
                    "sortable": True,
                    "default":"",
                    "width_percent":10
                },
                {
                    "key":"Attendance",
                    "display":"出勤",
                    "type":"select",
                    "options":[
                        "N",
                        "Y"
                    ],
                    "readonly": False,
                    "sortable": True,
                    "default":"N",
                    "width_percent":5
                },
                {
                    "key":"fixed_area",
                    "display":"固定区域",
                    "type":"select",
                    "options":[
                        "",
                        "入境",
                        "出境"
                    ],
                    "readonly": False,
                    "sortable": True,
                    "default":"",
                    "width_percent":10
                },
                {
                    "key":"preferred_area",
                    "display":"擅长区域",
                    "type":"select",
                    "options":[
                        "",
                        "入境",
                        "出境"
                    ],
                    "readonly": False,
                    "sortable": True,
                    "default":"",
                    "width_percent":10
                },
                {
                    "key":"preferred_section",
                    "display":"擅长环节",
                    "type":"select",
                    "options":[
                        "",
                        "前台",
                        "后台"
                    ],
                    "readonly": False,
                    "sortable": False,
                    "default":"",
                    "width_percent":10
                },
                {
                    "key":"team_name",
                    "display":"队名",
                    "type":"select",
                    "options":[
                        "",
                        "一队",
                        "二队",
                        "三队"
                    ],
                    "readonly": False,
                    "sortable": False,
                    "default":"",
                    "width_percent":10
                },
                {
                    "key":"Group_leader",
                    "display":"组长",
                    "type":"text",
                    "readonly": False,
                    "sortable": False,
                    "default":"",
                    "width_percent":15
                },
                {
                    "key":"Group_members",
                    "display":"组员",
                    "type":"list",
                    "readonly": False,
                    "sortable": False,
                    "default":"",
                    "width_percent":30,
                    "separators":[
                        ",",
                        "、"
                    ]
                }
            ],
            "scheduler_key":{
                "front":"前台",
                "back":"后台",
                "inbound":"入境",
                "outbound":"出境"
            },
            "default_data_path":""
        }


    def save_config(self, config):
        config_path = self.get_config_path()
        with open(config_path, 'w' ,  encoding = 'utf-8' ) as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    
    def save_default_import(self,path):
        self.config['default_data_path'] = path
        self.save_config(self.config)
    
    def load_config(self):
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8')as f:
                config = json.load(f)
        else:
            #如果配置文件不存在，使用默认配置
            config = self.get_default_config()
            self.save_config(config) 
        return config
    
    def load_staff_data(self):
        excel_path = self.config.get('default_data_path','')
        if excel_path.endswith('.xlsx'):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, '..', excel_path)
            return self._load_excel(full_path)
        return []
    
    def _load_excel(self, excel_path):
        try:
            df = pd.read_excel(excel_path)
            display_to_key = {col['display']: col['key'] for col in self.config['columns']}
            df.rename(columns=display_to_key, inplace=True)
            df =df.fillna('')# 将NaN替换为空字符串
            return df.to_dict('records')
        except FileNotFoundError:
            print(f"Excel文件未找到:{excel_path}")
            return []
        except Exception as e:
            print(f"读取Excel文件时发生错误:{e}")
            return []

    def setup_table(self):
        self.setColumnCount(len(self.config['columns']))
        self.setHorizontalHeaderLabels([col['display'] for col in self.config['columns']])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setRowCount(len(self.staff_data))
        self.cellChanged.connect(self.on_cell_changed)

        for col, column_config in enumerate(self.config['columns']):
            if column_config.get('type')in ['text','list']:
                self.setItemDelegateForColumn(col, EditableOnDoubleClickDelegate(self))
            elif column_config.get('type') == 'select':
                delegate = DoubleClickComboBoxDelegate(self)
                self.setItemDelegateForColumn(col, delegate)
            elif column_config.get('readonly',False):
                self.setItemDelegateForColumn(col, ReadOnlyDelegate(self))

    def populate_table(self):
        for row, staff in enumerate(self.staff_data):
            for col, column_config in enumerate(self.config['columns']):
                key = column_config['key']
                default_value = column_config.get('default')
                value = staff.get(key, default_value)


                # 如果值为None且存在默认值，使用默认值
                if value is None and default_value is not None:
                    value = default_value

                item = self.create_cell_item(column_config, value)
                self.setItem(row, col, item)

    def create_cell_item(self, column_config, value):
        item = QTableWidgetItem(str(value))
        if column_config.get('type') == 'select':
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setData(Qt.ItemDataRole.UserRole, column_config.get('options', []))
        elif column_config.get('readonly', False):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def split_list_items(self, value, column_config):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            separators = column_config.get('separators', [','])
            pattern ='|'.join(re.escape(sep) for sep in separators)
            return [item.strip() for item in re.split(pattern, value) if item.strip()]
        return []

    def on_cell_changed(self, row, column):
        item = self.item(row, column)
        if item:
            key = self.config['columns'][column]['key']
            self.staff_data[row][key] = item.text()
            self.staff_data_changed.emit()

    def get_staff_data(self):
        return self.staff_data

    def save_staff_data(self):
        excel_path = self.config.get('default_data_path','')
        if excel_path.endswith('.xlsx'):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir,'..', excel_path)
            self._save_excel(full_path)

    def _save_excel(self, excel_path):
        df = pd.DataFrame(self.staff_data)
        key_to_display = {col['key']: col['display'] for col in self.config['columns']}
        # 将列名从键转换为显示名称
        df.rename(columns=key_to_display, inplace=True)
        df.to_excel(excel_path, index=False)
        print(f"数据已保存到：{excel_path}")

    def remove_selected_rows(self):
        selected_rows = sorted(set(index.row() for index in self.selectedIndexes()), reverse=True)
        for row in selected_rows:
            self.removeRow(row)
            del self.staff_data[row]
        self.staff_data_changed.emit()

    def add_empty_row(self):
        new_row = {col['key']: '' for col in self.config['columns']}
        self.staff_data.append(new_row)
        self.setRowCount(self.rowCount()+ 1)
        row = self.rowCount()- 1
        for col, column_config in enumerate(self.config['columns']):
            item = self.create_cell_item(column_config,'')
            self.setItem(row, col, item)
        self.staff_data_changed.emit()