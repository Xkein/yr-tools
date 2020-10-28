import os
import sys
from typing import Dict, List
import parse

from PyQt5.QtCore import QModelIndex, QItemSelectionModel, Qt
from PyQt5.QtGui import QColor, QColorConstants, QStandardItem, QStandardItemModel, QClipboard
from PyQt5.QtWidgets import QAction, QApplication, QFileDialog, QMainWindow, QMessageBox

sys.path.append(sys.path[0] + os.path.sep + "UI")
from Ui_HookManager import Ui_MainWindow
mainWindowHelper = Ui_MainWindow()

import utilitiy
from utilitiy import log
# work direction
work_dir = utilitiy.get_work_dir('HookManager')
utilitiy.init_dir([work_dir])
utilitiy.set_log_file(
    open(work_dir + 'hookmanager.log', 'w', encoding='utf-8'))

log("author: Xkein")
log("work dir: " + work_dir)
log()

def GetSourceDir():
    return mainWindowHelper.txtSource.toPlainText()


def GetInjPath():
    return mainWindowHelper.txtInj.toPlainText()

def IsShowSame():
    return mainWindowHelper.chkShowSame.isChecked()

def IsShowAnnotated():
    return mainWindowHelper.chkShowAnnotated.isChecked()

def is_hex(str : str):
    try:
        int(str, 16)
    except ValueError:
        return False
    return True

class Hook(object):
    hook_pattern = parse.compile(
        "{define}({address},{name},{size}){tail}", case_sensitive=True)
    
    def __init__(self, address: str, name: str, size: str):
        self.address = address.strip()
        self.name = name.strip()
        self.size = size.strip()
        self.annotated = False

        if is_hex(self.address) == False or is_hex(self.size) == False:
            log("hook parse error: " + self.GetInjString() + '\n')

    @staticmethod
    def IsHook(line: str):
        if line.find("DEFINE_HOOK") >= 0:
            if line.startswith("DEFINE_HOOK") == False:
                log("source parse error: " + line)
                return False
            hook_profile = Hook.hook_pattern.parse(line)
            if hook_profile == None:
                log("source parse error: " + line)
            return hook_profile != None
        return False

    def __eq__(self, o) -> bool:
        if o == None:
            return False
        return self.address == o.address and self.name == o.name and self.size == o.size

    def __ne__(self, o) -> bool:
        return not self == o

    def GetInjString(self):
        return self.address + " = " + self.name + ", " + self.size


file_list: List[str] = list()
file_hooks: Dict[str, Dict[str, Hook]] = dict()


def GetFiles(dir: str):
    for root, dirs, files in os.walk(dir, topdown=False):
        for file in files:
            if file.lower().endswith(".cpp"):
                path = os.path.join(os.path.relpath(root, dir), file)
                file_list.append(path)


def LoadFile(path: str):
    file = open(os.path.join(GetSourceDir(), path), errors='ignore')
    annotation = 0
    hook_list: Dict[str, Hook] = dict()
    for line in file.readlines():
        annotation += line.count("/*") - line.count("*/")
        if annotation < 0:
            annotation = 0

        if  Hook.IsHook(line):
            if annotation != 0:
                log("annotated hook: " + line)

            hook_profile = Hook.hook_pattern.parse(line)
            hook = Hook(hook_profile["address"],
                        hook_profile["name"], hook_profile["size"])
            hook.annotated = annotation != 0

            hook_list[hook.name] = hook

    file_hooks[path] = hook_list


def FindHook(name: str) -> Hook:
    for file in file_list:
        hook = file_hooks[file].get(name)
        if hook != None:
            return hook
    return None


inj_hooks: Dict[str, Hook] = dict()


def LoadINJ(path: str):
    file = open(path, errors='ignore')
    pattern = parse.compile("{address}={name},{size}")
    lines = file.readlines()
    for line in lines:
        if '=' in line and not line.startswith(';'):
            hook_profile = pattern.parse(line)
            if hook_profile == None:
                log("inj parse error: " + line)
                continue
            hook = Hook(hook_profile["address"],
                        hook_profile["name"], hook_profile["size"])
            inj_hooks[hook.name] = hook


def ClearAll():
    file_list.clear()
    file_hooks.clear()
    inj_hooks.clear()


def RefreshFileHookView():
    if mainWindowHelper.clvHooks.model() is QStandardItemModel:
        mainWindowHelper.clvHooks.model().destroyed()

    model_hooks = QStandardItemModel()

    for file in file_list:
        file_item = QStandardItem(file)

        for hook_name in file_hooks[file]:
            source_hook = file_hooks[file].get(hook_name)
            if source_hook != None:
                if IsShowSame() == False:
                    inj_hook = inj_hooks.get(hook_name)
                    if inj_hook == source_hook:
                        continue
                if IsShowAnnotated() == False and source_hook.annotated:
                    continue

            hook_item = QStandardItem(hook_name)
            file_item.appendRow(hook_item)
        
        if file_item.rowCount() > 0:
            model_hooks.appendRow(file_item)

    mainWindowHelper.clvHooks.setModel(model_hooks)


def RefreshAllHookList():
    if mainWindowHelper.tbvAllHooks.model() is QStandardItemModel:
        mainWindowHelper.tbvAllHooks.model().destroyed()

    model_allHooks = QStandardItemModel()

    columns = ["name", "inj addr", "source addr", "inj size", "source size"]
    model_allHooks.setColumnCount(len(columns))
    for idx in range(len(columns)):
        model_allHooks.setHeaderData(idx, Qt.Horizontal, columns[idx])

    all_hooks: set[str] = set()

    for inj_hook_name in inj_hooks:
        all_hooks.add(inj_hooks[inj_hook_name].name)

    for file in file_list:
        for hook_name in file_hooks[file]:
            all_hooks.add(file_hooks[file][hook_name].name)

    idx = 0
    for hook_name in all_hooks:
        inj_hook = inj_hooks.get(hook_name)
        source_hook = FindHook(hook_name)

        if source_hook != None:
            if IsShowSame() == False:
                if inj_hook == source_hook:
                    continue
            if IsShowAnnotated() == False and source_hook.annotated:
                    continue

        model_allHooks.setItem(idx, 0, QStandardItem(hook_name))
        if source_hook != None:
            if source_hook.annotated:
                model_allHooks.item(idx, 0).setBackground(QColorConstants.Green)
                
            if inj_hook == source_hook:
                model_allHooks.item(idx, 0).setBackground(QColorConstants.Gray)

        if inj_hook != None:
            model_allHooks.setItem(idx, 1, QStandardItem(inj_hook.address))
            model_allHooks.setItem(idx, 3, QStandardItem(inj_hook.size))

        if source_hook != None:
            model_allHooks.setItem(idx, 2, QStandardItem(source_hook.address))
            model_allHooks.setItem(idx, 4, QStandardItem(source_hook.size))

        idx = idx + 1

    mainWindowHelper.tbvAllHooks.setModel(model_allHooks)
    mainWindowHelper.tbvAllHooks.verticalHeader().setVisible(False)
    mainWindowHelper.tbvAllHooks.setColumnWidth(0, 400)
    mainWindowHelper.tbvAllHooks.setColumnWidth(1, 80)
    mainWindowHelper.tbvAllHooks.setColumnWidth(2, 80)
    mainWindowHelper.tbvAllHooks.setColumnWidth(3, 60)
    mainWindowHelper.tbvAllHooks.setColumnWidth(4, 80)


def RefreshList():
    RefreshFileHookView()
    RefreshAllHookList()

def TryAnalyse():
    source_dir = GetSourceDir()
    inj_path = GetInjPath()

    if os.path.isfile(inj_path) and os.path.isdir(source_dir):
        ClearAll()

        GetFiles(source_dir)

        LoadINJ(inj_path)
        for file in file_list:
            LoadFile(file)

        RefreshList()


class MainWindow(QMainWindow):
    def btnGetSource(self):
        _dir = QFileDialog.getExistingDirectory(
            self, "select source direction", os.getcwd())
        mainWindowHelper.txtSource.setText(_dir)
        self.btnAnalyse()

    def btnGetInj(self):
        _dir, _filter = QFileDialog.getOpenFileName(
            self, "select inj", os.getcwd(), "All Files (*);;Inj Files (*.inj)")
        mainWindowHelper.txtInj.setText(_dir)
        self.btnAnalyse()

    def btnAnalyse(self):
        TryAnalyse()

    def chkShowSame(self, state: int):
        RefreshList()
        
    def chkShowAnnotated(self, state: int):
        RefreshList()

    def clvHooksClicked(self, index: QModelIndex):
        if index.parent().column() != 0:
            return

        data = index.data()
        model = mainWindowHelper.tbvAllHooks.model()
        match = model.match(model.index(0, 0), Qt.DisplayRole,
                            data, 1, Qt.MatchContains)
        if len(match) > 0:
            mainWindowHelper.tbvAllHooks.selectRow(match[0].row())

    def btnGenerateInj(self):
        (_path, inj_name) = os.path.split(GetInjPath())
        inj = open(work_dir + inj_name, 'w', encoding='utf-8')
        inj.write("; ---------------generated by Xkein's Hook Manager---------------\n\n")

        for file in file_list:
            inj.write('; ' + file + '\n')

            for hook_name in file_hooks[file]:
                source_hook = file_hooks[file].get(hook_name)
                inj.write(source_hook.GetInjString() + '\n')

            inj.write('\n')
            
        inj.write("; generate successfully\n")

        QMessageBox.information(self, "Hook Manager", "Generate inj successfully")

    def tbvAllHooksClicked(self, index: QModelIndex):
        if index.column() != 0:
            return

        data = index.data()
        model = mainWindowHelper.clvHooks.model()
        match = model.match(model.index(0, 0), Qt.DisplayRole,
                            data, 1, Qt.MatchContains | Qt.MatchRecursive)
        if len(match) > 0:
            mainWindowHelper.clvHooks.selectionModel().setCurrentIndex(match[0], QItemSelectionModel.Select)
            #mainWindowHelper.clvHooks.selectionModel().select(match[0].parent(), QItemSelectionModel.Select)

    def CopyHook(self, hook : Hook):
        clipboard  = QApplication.clipboard()
        text = hook.GetInjString()
        clipboard.setText(text)
        
    def actCopySource(self, checked : bool):
        try:
            model = mainWindowHelper.tbvAllHooks.model()
            index = mainWindowHelper.tbvAllHooks.selectedIndexes()[0]
            row = index.row()
            self.CopyHook(Hook(model.index(row, 2).data(), model.index(row, 0).data(), model.index(row, 4).data()))
        except AttributeError:
            pass
        

    def actCopyInj(self, checked : bool):
        try:
            model = mainWindowHelper.tbvAllHooks.model()
            index = mainWindowHelper.tbvAllHooks.selectedIndexes()[0]
            row = index.row()
            self.CopyHook(Hook(model.index(row, 1).data(), model.index(row, 0).data(), model.index(row, 3).data()))
        except AttributeError:
            pass

    def actCopyHookName(self, checked : bool):
        model = mainWindowHelper.tbvAllHooks.model()
        index = mainWindowHelper.tbvAllHooks.selectedIndexes()[0]
        row = index.row()
        
        clipboard  = QApplication.clipboard()
        clipboard.setText(model.index(row, 0).data())


# create main window
app = QApplication(sys.argv)

mainWindow = MainWindow()
mainWindowHelper.setupUi(mainWindow)
mainWindow.setFixedSize(mainWindow.size())
mainWindow.show()

copy_source_action = QAction("Copy Source")
copy_inj_action = QAction("Copy Inj")
copy_hookname_action = QAction("Copy Hook Name")

copy_source_action.triggered['bool'].connect(mainWindow.actCopySource)
copy_inj_action.triggered['bool'].connect(mainWindow.actCopyInj)
copy_hookname_action.triggered['bool'].connect(mainWindow.actCopyHookName)

mainWindowHelper.tbvAllHooks.addActions([
    copy_source_action, copy_inj_action, copy_hookname_action
])

# set default dir
mainWindowHelper.txtSource.setText(R"D:/Creative/Git place/Hares_Main/Ares0A")
mainWindowHelper.txtInj.setText(R"D:/Command and Conquer/=World Axletree Reset= V53.5 开发版/Hares.ext.inc")

sys.exit(app.exec_())
