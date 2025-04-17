import json
import os
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QSpinBox, QLabel, QHBoxLayout, QComboBox
import shutil
import pkgutil


class AreaConfig(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = self.get_config_path()
        self.config = self.load_config()

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(10,10, 10,10)
        self.grid_layout.setSpacing(10)

        self.ui_elements = {}
        self.create_ui()

        self.update_totals()
    
    def resource_path(self,relative_path):
        """
        在打包和开发环境中获取资源文件的正确路径
        """
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)
        else:
            return os.path.join(os.path.abspath("."), relative_path)

    def get_config_path(self):
        user_data_dir = os.path.join(os.path.expanduser('~'), 'SchedulingSystemConfig')
        os.makedirs(user_data_dir, exist_ok=True)
        config_path = os.path.join(user_data_dir, 'AreaConfig.json')

        if not os.path.exists(config_path):
            if getattr(sys, 'frozen', False):
                # 如果是打包后的环境，从 sys._MEIPASS 目录获取资源
                default_path = self.resource_path(os.path.join('json', 'AreaConfig.json'))
                if os.path.exists(default_path):
                    with open(default_path, 'rb') as src, open(config_path, 'wb') as dst:
                        dst.write(src.read())
                else:
                    raise FileNotFoundError(f"无法找到打包环境下的默认配置文件: {default_path}")
            else:
                # 开发环境，直接从项目目录获取
                default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'json', 'AreaConfig.json')
                if os.path.exists(default_path):
                    shutil.copy(default_path, config_path)
                else:
                    raise FileNotFoundError(f"默认配置文件不存在: {default_path}")

        return config_path  # 确保在所有情况下都返回 config_path
    
    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {self.config_file}未找到。使用默认配置。")
            return {"uiControls":[], "calculations":[]}

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

    def create_ui(self):
        for control in self.config['uiControls']:
            if control['type'] =='select':
                element = self.create_combobox(control['options'], control['default'])
                element.currentTextChanged.connect(lambda text, key=control['key']: self.update_config(key, text))
            elif control['type'] =='number':
                element = self.create_spinbox(
                    control['default'],
                    control.get('min', 0),
                    control.get('max', 100),
                    control.get('readonly', False)
                    )
                if not control.get('readonly', False):
                    element.valueChanged.connect(lambda value, key=control['key']: self.update_config(key, value))
            else:
                continue # 跳过未知类型的控件

            self.ui_elements[control['key']] = element
            self.grid_layout.addLayout(
                self.create_labeled_element(control['label'], element),
                control['row'], control['col']
            )

            if control['type'] == 'number' and not control.get('readonly', False):
                element.valueChanged.connect(self.update_totals)

    def create_spinbox(self, default, minimum, maximum, readonly=False):
        spinbox = QSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setValue(default)
        spinbox.setReadOnly(readonly)
        spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons if readonly else QSpinBox.ButtonSymbols.UpDownArrows)
        return spinbox
    
    def create_combobox(self, options, default):
        combobox = QComboBox()
        combobox.addItems(options)
        combobox.setCurrentText(default)
        return combobox

    def create_labeled_element(self, label_text, element):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(element)
        layout.addStretch()
        return layout
    
    def update_totals(self):
        for calc in self.config.get('calculations',[]):
            target = calc['target']
            formula = calc['formula']
            try:
                result = eval(formula, {}, {k: v.value() for k, v in self.ui_elements.items() if isinstance(v, QSpinBox)})
                self.ui_elements[target].setValue(int(result))
            except Exception as e:
                print(f"计算{target}时出错：{e}")
        self.save_config()
                      
    def update_config(self, key, value):
        for control in self.config['uiControls']:
            if control['key'] == key:
                control['default'] = value
                break
        self.save_config()

    def get_config(self):
        result ={}
        for control in self.config['uiControls']:
            if control['type'] == 'select':
                result[control['key']] = self.ui_elements[control['key']].currentText()
            elif control['type'] == 'number':
                result[control['key']] = self.ui_elements[control['key']].value()
        return result