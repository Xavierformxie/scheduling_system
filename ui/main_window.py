from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QPushButton, QWidget, QMessageBox, QToolBar,
                            QTableWidget, QTableWidgetItem, QHBoxLayout, QStackedWidget, QLineEdit,
                            QScrollArea, QApplication, QHeaderView,QFileDialog)

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from ui.staff_table import StaffTable
from ui.area_config import AreaConfig
from models.scheduler import Scheduler
from utils.excel_handler import ExcelHandler
from utils.vaildators import validate_configuration

class StaffTableWithSearch(QWidget):
    StaffTableWithSearch_data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)

        #创建顶部布局
        top_layout = QHBoxLayout()

        # 添加搜索栏
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索员工...")
        self.search_bar. textChanged.connect(self.search_staff)

        # 添加导入导出按钮
        self.default_import_button = QPushButton("默认导入路径")
        self.import_button =QPushButton("导入人员信息")
        self.export_button = QPushButton("导出人员信息")

        # 将组件添加到顶部布局
        top_layout.addWidget(self.search_bar)
        top_layout.addStretch()
        top_layout.addWidget(self.default_import_button)
        top_layout.addWidget(self.import_button)
        top_layout.addWidget(self.export_button)

        #创建员工表格
        self.staff_table = StaffTable()
        self.staff_table.staff_data_changed.connect(self.on_staff_data_changed)
        
        #将顶部布局和表格添加到主布局
        self.main_layout.addLayout(top_layout)
        self.main_layout.addWidget(self.staff_table)
        
    def search_staff(self, text):
        for row in range(self.staff_table.rowCount()):
            match = False
            for col in range(self.staff_table.columnCount()):
                item = self.staff_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.staff_table.setRowHidden(row, not match)

    def on_staff_data_changed(self):
        self.StaffTableWithSearch_data_changed.emit()

    def add_empty_row(self):
        self.staff_table.add_empty_row()
    
    def remove_selected_rows(self):
        self.staff_table.remove_selected_rows()

    def get_staff(self):
        return self.staff_table.get_staff_data()
    
    def default_import_staff(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _= QFileDialog.getOpenFileName(
            self,
            "选择默认导入文件",
            "",
            "Excel 文件(*.xlsx *.xls);;所有文件 (*)",
            options=options
        )
        if file_path:
            self.staff_table.save_default_import(file_path)

class ScheduleResultwidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        self.top_layout = QHBoxLayout()
        self.top_layout.addStretch(1)

        self.export_button = QPushButton("导出排班结果")
        self.top_layout.addWidget(self.export_button)

        self.content_layout.addLayout(self.top_layout)

        self.result_table = QTableWidget()
        self.content_layout.addWidget(self.result_table)

        self.scroll_area.setWidget(self.content_widget)

        self.main_layout.addWidget(self.scroll_area)

    def display_result(self, result):
        if not isinstance(result, dict):
            QMessageBox.warning(self,"错误","排班结果格式不正确")
            return
        
        areas = list(result.keys())

        locations = set()
        for area_data in result.values():
            locations.update(area_data.keys())
        locations = sorted(list(locations))

        self.result_table.setRowCount(len(areas))
        self.result_table.setColumnCount(len(locations))
        self.result_table.setVerticalHeaderLabels(areas)

        self.result_table.setVerticalHeaderLabels(areas)
        self.result_table.setHorizontalHeaderLabels(locations)

        for row, area in enumerate(areas):
            for col, location in enumerate(locations):
                staff_list = result[area].get(location, [])
                cell_text ="、".join(staff_list)
                item = QTableWidgetItem(cell_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                self.result_table.setItem(row, col, item)

        header = self.result_table.horizontalHeader()
        for col in range(len(locations)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        
        for row in range(self.result_table.rowCount()):
            self.result_table.setRowHeight(row, self.result_table.rowHeight(row)* 2)

        self.result_table.setWordWrap(True)
        self.result_table.viewport().update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动排班系统")
        screen = QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()

        max_width = int(available_geometry.width()* 0.9)
        height = int(available_geometry.height()* 0.9)

        self.resize(max_width, height)

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)

        self.create_toolbar()
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        self.staff_table_with_search = StaffTableWithSearch()
        self.area_config = AreaConfig()
        self.add_row_button = QPushButton("添加新员工")
        self.remove_row_button = QPushButton("删除选中员工")
        self.schedule_button =QPushButton("开始排班")

        scroll_layout.addWidget(self.staff_table_with_search)
        scroll_layout.addWidget(self.add_row_button)
        scroll_layout.addWidget(self.remove_row_button)
        scroll_layout.addWidget(self.area_config)
        scroll_layout.addWidget(self.schedule_button)
        
        scroll_area.setWidget(scroll_content)
        self.left_layout.addWidget(scroll_area)
        self.main_layout.addWidget(self.left_widget)

        self.schedule_result_widget = ScheduleResultwidget(self)
        self.schedule_result_widget.export_button.clicked.connect(self.export_result)

        self.central_widget.addWidget(self.main_widget)
        self.central_widget.addWidget(self.schedule_result_widget)

        self.add_row_button.clicked.connect(self.staff_table_with_search.add_empty_row)
        self.remove_row_button.clicked.connect(self.staff_table_with_search. remove_selected_rows)
        self.schedule_button.clicked.connect(self.start_scheduling)
        self.staff_table_with_search.StaffTableWithSearch_data_changed.connect(self.on_staff_data_changed)

        self.staff_table_with_search.default_import_button.clicked.connect(self.staff_table_with_search.default_import_staff)
        self.staff_table_with_search.import_button.clicked.connect(self.import_staff)
        self.staff_table_with_search.export_button.clicked.connect(self.export_staff)
        
    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        home_action = QAction(QIcon("path/to/home_icon.png"),"主页",self)
        view_result_action = QAction(QIcon("path/to/viev_result_icon.pne"),"查看排班结果",self)

        home_action.triggered.connect(self.go_home)
        view_result_action.triggered.connect(self.view_result)

        toolbar.addAction(home_action)
        toolbar.addAction(view_result_action)
    
    def start_scheduling(self):
        # 调用校验方法，假设它返回一个元组 (is_valid, message)
        is_valid, validate_msg = validate_configuration(self.staff_table_with_search.get_staff(), self.area_config.get_config())
        if not is_valid:
            QMessageBox.warning(self, "配置校验失败", validate_msg)
            return
        
        scheduler = Scheduler(self.staff_table_with_search.get_staff(), self.area_config.get_config())
        success, result_or_message = scheduler.schedule()
        if success:
            QMessageBox.information(self, "排班成功", "排班已完成,结果已显示")
            self.schedule_result_widget.display_result(result_or_message)
            self.central_widget.setCurrentWidget(self.schedule_result_widget)
        else:
            QMessageBox.warning(self, "排班失败", f"无法满足所有条件：{result_or_message}")

    def go_home(self):
        self.central_widget.setCurrentWidget(self.main_widget)

    def import_staff(self):
        ExcelHandler .import_staff(self.staff_table_with_search.staff_table)

    def export_staff(self):
        ExcelHandler.export_staff(self.staff_table_with_search.staff_table)
    
    def export_result(self):
        ExcelHandler.export_result(self.schedule_result_widget.result_table)

    def view_result(self):
        self.central_widget.setCurrentWidget(self.schedule_result_widget)
    
    def on_staff_data_changed(self):
        print("员工数据已更新")