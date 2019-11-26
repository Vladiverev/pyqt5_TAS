import pytest
import json
from pathlib import Path
from PyQt5 import QtCore, QtWidgets, QtGui
import sys

from base_managers import GenerateFiles


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass

    def isatty(self):
        pass


class BaseGrid(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        QtGui.QGuiApplication.processEvents()
        self.layout = QtWidgets.QHBoxLayout(self)
        scroll_area, scroll_area_widget_contents = self.scroll_area()

        self.gridLayout = QtWidgets.QGridLayout(scroll_area_widget_contents)
        self.layout.addWidget(scroll_area)

        self.settings_info = GenerateFiles.update_settings()
        self.combobox = {}
        self.group_box = {}

    # def debug_trace(self):
    #     '''Set a tracepoint in the Python debugger that works with Qt'''
    #
    #     # Or for Qt5
    #     # from PyQt5.QtCore import pyqtRemoveInputHook
    #
    #     from pdb import set_trace
    #     QtCore.pyqtRemoveInputHook()
    #     set_trace()

    def scroll_area(self):
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area_widget_contents = QtWidgets.QWidget()
        scroll_area.setWidget(scroll_area_widget_contents)
        return scroll_area, scroll_area_widget_contents

    def add_button(self, name, obj_name, func, positions):
        btn = QtWidgets.QPushButton(name, self)
        btn.clicked.connect(func)
        btn.setObjectName(f"{obj_name}")
        self.gridLayout.addWidget(btn, *positions)
        return btn

    def add_combobox(self, param_name, param_items):
        widgets = QtWidgets.QWidget(self)
        layout = QtWidgets.QFormLayout(widgets)

        self.combobox[param_name] = QtWidgets.QComboBox(widgets)
        self.combobox[param_name].setObjectName(param_name)
        self.combobox[param_name].addItems(param_items)

        layout.addRow(QtWidgets.QLabel(param_name + ' :'), self.combobox[param_name])
        return widgets

    def add_group_combobox(self, params):
        parent_group_box = QtWidgets.QWidget(self)
        parent_layout = QtWidgets.QVBoxLayout(parent_group_box)

        for param in params:
            group_box = QtWidgets.QGroupBox(param, parent_group_box)
            layout = QtWidgets.QFormLayout(group_box)
            self.combobox[param] = {}
            for param_name in params[param]:
                choice_param = ['Random'] + params[param][param_name] + ['Default'] if isinstance(
                    params[param][param_name],
                    list) else ['Random',
                                'Default']
                print(112333, param_name)

                self.combobox[param][param_name] = QtWidgets.QComboBox(group_box)
                self.combobox[param][param_name].setObjectName(param_name)
                self.combobox[param][param_name].addItems(choice_param)
                print(112333, self.combobox[param][param_name])
                layout.addRow(QtWidgets.QLabel(param_name + ' :'), self.combobox[param][param_name])
                group_box.setLayout(layout)
            parent_layout.addWidget(group_box)
        return parent_group_box


class WidgetGroupBox(QtWidgets.QWidget):

    def __init__(self, parent=None, params=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.param = params.copy()
        for param_name in self.param:
            print(param_name)
            print(self.param)
            self.GroupBox = QtWidgets.QGroupBox(param_name, self)
            self.GroupBox.setLayout(QtWidgets.QVBoxLayout())
            for i in self.param[param_name]:
                self.param[param_name][i] = QtWidgets.QCheckBox("{}".format(i), self.GroupBox)
                self.GroupBox.layout().addWidget(self.param[param_name][i])

            self.layout().addWidget(self.GroupBox)
            self.GroupBox.toggled.connect(self.onToggled)
            self.GroupBox.setCheckable(True)

    def onToggled(self, on):
        for box in self.sender().findChildren(QtWidgets.QCheckBox):
            box.setChecked(on)
            box.setEnabled(True)


class GenericWorker(QtCore.QObject):
    start = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)

    def __init__(self, function, repeat):
        super(GenericWorker, self).__init__()
        self.function = function
        self.repeat = repeat
        self.start.connect(self.run)
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.finished.emit()

    @QtCore.pyqtSlot()
    def run(self):
        for i in range(self.repeat):
            self.function()
            self.progress.emit(i)
            if not self._is_running:
                break
        self.finished.emit()


class Tab1(BaseGrid):

    def __init__(self, parent=None):
        super(Tab1, self).__init__(parent)

        # self.debug_trace()

        self.output = QtWidgets.QTextBrowser(self)
        self.group, self.group_1, self.group_2 = self.add_group()
        self.add_group()

        self.pbar = QtWidgets.QProgressBar(self)
        self.pbar.setFormat("%v/%m")
        self._gif = QtWidgets.QLabel()
        self.anim = QtGui.QMovie(str(Path('./icons/bears.gif')))
        self._gif.setMovie(self.anim)

        self.hosts_label = self.add_combobox(param_name='hosts', param_items=self.settings_info['hosts'])
        self.rand_label = self.add_combobox(param_name='random_filters',
                                            param_items=self.settings_info['params_testing']['random_filters'])
        self.ajax_label = self.add_combobox(param_name='tree_ajax',
                                            param_items=self.settings_info['params_testing']['tree_ajax'])
        self.run_btn = self.add_button(name='Run', obj_name='Run', positions=[3, 1], func=self.button_run)
        self.stop_btn = self.add_button(name='Stop', obj_name='Stop', positions=[4, 1], func=self.button_stop)
        self.stop_btn.setEnabled(False)

        self.repeat_label = self.add_combobox(param_name='Repeat',
                                              param_items=['1'] + [str(x * 7) for x in range(1, 7)])

        self.gridLayout.addWidget(self.hosts_label, 3, 0)
        self.gridLayout.addWidget(self.repeat_label, 4, 0)
        self.gridLayout.addWidget(self.rand_label, 3, 2)
        self.gridLayout.addWidget(self.ajax_label, 4, 2)
        self.gridLayout.addWidget(self.output, 10, 0, 10, 2)
        self.gridLayout.addWidget(self.pbar, 10, 2)
        self.gridLayout.addWidget(self._gif, 11, 2)

        self.my_worker = None
        self.my_thread = None
        self.threadPool = []

        # sys.stdout = EmittingStream(textWritten=self.data_append)

    def add_scroll_area(self, name, group, positions):
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(group)
        name_lable = QtWidgets.QLabel(name)
        lab_pos = positions.copy()
        lab_pos[0] = min(0, lab_pos[0] - 1)
        self.gridLayout.addWidget(name_lable, *lab_pos)
        self.gridLayout.addWidget(scroll_area, *positions)
        return group

    def add_group(self):
        group = self.add_scroll_area(name='Користувачі',
                                     group=WidgetGroupBox(parent=self, params={'users': self.settings_info['users']}),
                                     positions=[2, 0])
        group_1 = self.add_scroll_area(name='Найменування тестів',
                                       group=WidgetGroupBox(parent=self, params=self.settings_info['reports']),
                                       positions=[2, 1])
        group_2 = self.add_scroll_area(name='Фільтри',
                                       group=self.add_group_combobox(params=
                                                                     {'params_base': self.settings_info['params_base'],
                                                                      'params_choice': self.settings_info[
                                                                          'params_choice'],
                                                                      'params_bool': self.settings_info['params_bool'],
                                                                      }),
                                       positions=[2, 2])
        return group, group_1, group_2

    def run_func(self):
        select_users = [v for (k, v) in self.group.param.items() for v in v if
                        self.group.param[k][v].checkState() == 2]
        select_reports = [v for (k, v) in self.group_1.param.items() for v in v if
                          self.group_1.param[k][v].checkState() == 2]

        select_params_base = {k: v.currentText() for (k, v) in self.combobox['params_base'].items()}
        select_params_choice = {k: v.currentText() for (k, v) in self.combobox['params_choice'].items()}
        select_params_bool = {k: v.currentText() for (k, v) in self.combobox['params_bool'].items()}
        select_params_testing = {x: self.combobox[x].currentText() for x in ['random_filters', 'tree_ajax']}
        print(select_users)
        print(select_params_base)
        print(select_params_choice)
        print(select_params_bool)

        pytest.main(
            [
                '--verbose',
                '--tb=no',
                '-s',
                f'-k={" or ".join(str(x) for x in select_reports)}',
                '--users=' + json.dumps(select_users),
                f'--params_base=' + json.dumps(select_params_base),
                f'--params_choice=' + json.dumps(select_params_choice),
                f'--params_bool=' + json.dumps(select_params_bool),
                f'--params_testing=' + json.dumps(select_params_testing),
                f'--hosts={self.combobox["hosts"].currentText()}',
            ]
        )

    def button_run(self):
        # self.debug_trace()
        self.my_thread = QtCore.QThread()

        self.my_worker = GenericWorker(function=self.run_func, repeat=int(self.combobox['Repeat'].currentText()))
        self.pbar.setMaximum(int(self.combobox['Repeat'].currentText()))
        self.my_worker.start.connect(lambda: self.run_btn.setEnabled(False))
        self.my_worker.start.connect(lambda: self.anim.start())
        self.my_worker.start.connect(lambda: self.stop_btn.setEnabled(True))
        self.my_worker.moveToThread(self.my_thread)
        self.my_thread.start()
        self.my_worker.start.emit("")

        self.threadPool.append(self.my_thread)
        self.my_worker.progress.connect(self.onCountChanged)
        self.my_worker.finished.connect(lambda: self.run_btn.setEnabled(True))
        self.my_worker.finished.connect(lambda: self.stop_btn.setEnabled(False))
        self.my_worker.finished.connect(lambda: self.anim.stop())

    def onCountChanged(self, value):
        self.pbar.setValue(value + 1)

    def button_stop(self):
        self.my_worker.stop()
        self.run_btn.setEnabled(True)
        self.my_thread = None

    def data_append(self, text=None):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(str(text) if text else '')
        self.output.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__


class Tab2(BaseGrid):

    def __init__(self, parent=None):
        super(Tab2, self).__init__(parent)

        # self.debug_trace()
        self.host_line = self.line_edit('Host:', positions_name=[0, 0], positions_line=[0, 1])
        self.add_button(name='Add host', obj_name='post_hosts', positions=[1, 1], func=self.button_clicked)
        self.add_button(name='Delete hosts', obj_name='delete_hosts', positions=[1, 0], func=self.button_clicked)

        self.user_line = self.line_edit('User name:', positions_name=[4, 0], positions_line=[4, 1])
        self.user_pass_line = self.line_edit('User pass:', positions_name=[5, 0], positions_line=[5, 1])
        self.add_button(name='Add or update user', obj_name='post_users', positions=[6, 1], func=self.button_clicked)
        self.add_button(name='Delete user', obj_name='delete_users', positions=[6, 0], func=self.button_clicked)

        self.info_widgets()

        self.line = {
            'users': [self.user_line, self.user_pass_line],
            'hosts': [self.host_line]
        }

    def button_clicked(self):
        method, key = self.sender().objectName().split('_')

        if method == 'delete':
            if self.line[key][0].text() in self.settings_info[key] and isinstance(self.settings_info[key], dict):
                self.settings_info[key].pop(self.line[key][0].text())
                print(self.settings_info[key])
            elif self.line[key][0].text() in self.settings_info[key] and isinstance(self.settings_info[key], list):
                self.settings_info[key].remove(self.line[key][0].text())
                print(self.settings_info[key])
        else:
            if key == 'users' and self.user_line.text():
                self.settings_info['users'].update({self.user_line.text(): self.user_pass_line.text()})
            elif key == 'hosts' and self.host_line.text():
                self.settings_info['hosts'].append(self.host_line.text())
        GenerateFiles.update_settings(data=self.settings_info)
        self.info_widgets()

    def line_edit(self, name, positions_name, positions_line):
        name_line = QtWidgets.QLabel(name)
        edit_line = QtWidgets.QLineEdit()

        self.gridLayout.addWidget(name_line, *positions_name)
        self.gridLayout.addWidget(edit_line, *positions_line)
        return edit_line

    def curr_info(self, text, positions):
        editor = QtWidgets.QTextBrowser()
        editor.setPlainText(str(text))
        self.gridLayout.addWidget(editor, *positions)
        return editor

    def info_widgets(self):
        nl = '\n'
        self.curr_info(text=f'{nl.join(str(x) for x in self.settings_info["hosts"])}',
                       positions=[2, 0, 1, 2])
        self.curr_info(text=f'{nl.join(str(x) for x in self.settings_info["users"])}',
                       positions=[7, 0, 3, 2])


class Page1(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(Page1, self).__init__(parent)
        self.tab1 = Tab1(parent=self)
        self.tab2 = Tab2(parent=self)
        self.addTab(self.tab1, "API Tests")
        self.addTab(self.tab2, "Settings")


class App(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.resize(1200, 1200)
        self.initui()
        self.startPage1()
        exitAction = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtWidgets.qApp.quit)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.show()

    def startPage1(self):
        x = Page1(self)
        self.setWindowTitle("TAS client")
        self.setCentralWidget(x)

    def initui(self):
        QtWidgets.QShortcut(QtGui.QKeySequence('F5'), self, self.startPage1)

    def closeEvent(self, event):

        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                               "Are you sure to quit?", QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
