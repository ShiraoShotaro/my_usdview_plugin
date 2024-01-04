import os
import importlib
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QSignalBlocker, Qt
from PySide2.QtWidgets import (
    QDockWidget, QMenuBar, QMenu, QAction, QTreeWidgetItem,
    QTreeWidget, QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox,
)
from pxr import UsdGeom, Gf, Sdf


class OptionItem:
    def __init__(self, _module, memberName):
        self._module = _module
        self._memberName: str = memberName
        self._member = getattr(_module, memberName)

    def createWidget(self, parent):
        if isinstance(self._member, str):
            widget = QLineEdit(parent)
            widget.setText(str(self._member) if self._member else "")
            return widget
        if isinstance(self._member, bool):  # int より先に
            widget = QCheckBox(parent)
            widget.setText(self._memberName)
            widget.setChecked(bool(self._member) if self._member is not None else False)
            return widget
        if isinstance(self._member, int):
            widget = QSpinBox(parent)
            widget.setValue(int(self._member) if self._member is not None else 0)
            return widget
        if isinstance(self._member, float):
            widget = QDoubleSpinBox(parent)
            widget.setValue(float(self._member) if self._member is not None else 0)
            return widget
        return None
    
    def setOptionValue(self, widget):
        if isinstance(widget, QLineEdit):
            setattr(self._module, self._memberName, widget.text())
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            setattr(self._module, self._memberName, widget.value())
        elif isinstance(widget, QCheckBox):
            setattr(self._module, self._memberName, widget.isChecked())
    
    @property
    def labelText(self):
        if isinstance(self._member, bool):
            return ""
        else:
            return self._memberName


class PresetItem:
    def __init__(self, path: str):
        self._path = path
        print(f"Import: {path}")
        self._spec = importlib.util.spec_from_file_location(os.path.splitext(path)[0], path)
        self._module = importlib.util.module_from_spec(self._spec)
        self._spec.loader.exec_module(self._module)
        self._name = os.path.basename(self._path)
        self._doc = ""

        if self._module.__doc__:
            lines = self._module.__doc__.strip().splitlines()
            self._name = lines[0] if lines else ""
            self._doc = "\n".join(lines[1:]).strip()

        self._options = list()
        for memberName in dir(self._module):
            if not memberName.startswith("_") and memberName != "main":
                member = getattr(self._module, memberName)
                if isinstance(member, (str, int, float, bool)):
                    self._options.append(OptionItem(self._module, memberName))

    @property
    def displayData(self) -> str:
        return self._name
    
    @property
    def toolTipData(self) -> str:
        return self._doc
    
    @property
    def options(self) -> list:
        return self._options
    
    @property
    def title(self) -> str:
        return self._name
    
    @property
    def document(self) -> str:
        return self._doc

    def reload(self):
        self._spec.loader.exec_module(self._module)

    def execute(self, api):
        self._module.main(api)


class OptionsWidget(QWidget):
    def __init__(self, parent, options: list):
        super().__init__(parent)
        self._layout = QFormLayout()
        self._widgets = list()
        self.setLayout(self._layout)
        for option in options:
            labelText = option.labelText
            widget = option.createWidget(self)
            self._layout.addRow(labelText, widget)
            self._widgets.append((option, widget))
    
    def updateOptionValues(self):
        for opt, widget in self._widgets:
            opt.setOptionValue(widget)


class PresetExecutor(QDockWidget):
    def __init__(self, api):
        super().__init__(api.qMainWindow)
        self._api = api
        self._ui = QUiLoader().load(
            os.path.join(os.path.dirname(__file__), "widget.ui"),
            self)
        self.setWidget(self._ui)
        self.setWindowTitle("Preset Executor")

        self._optionWidget = None
        self._currentPreset = None
        self._menuBar = QMenuBar(self._ui)
        self._menu = QMenu(self._menuBar)
        self._menu.setTitle("Files")
        self._reloadAction = QAction("Reload Presets")
        self._reloadAction.triggered.connect(self._reloadPresets)
        self._menu.addAction(self._reloadAction)
        self._menuBar.addMenu(self._menu)
        self._ui.layout().insertWidget(0, self._menuBar)
        self._ui.layout().setStretch(1, 1)
        self._ui.leTitle.setText("")
        self._ui.lbDocument.setText("")

        self._ui.twPresets.itemClicked.connect(self._presetSelected)
        self._ui.pbExecute.clicked.connect(self._executePreset)

        self._reloadPresets()

    def _reloadPresets(self):
        self._ui.twPresets.clear()

        def _traverse(root: str, rootItem):
            for file in os.listdir(root):
                if file.startswith("_"):
                    continue
                path = os.path.join(root, file)
                if os.path.isdir(path):
                    item = QTreeWidgetItem(rootItem)
                    item.setData(0, Qt.DisplayRole, file)
                    item.setData(0, Qt.UserRole, path)
                    _traverse(path, item)
                    if isinstance(rootItem, QTreeWidget):
                        rootItem.addTopLevelItem(item)
                    else:
                        rootItem.addChild(item)

                elif os.path.splitext(file)[1] == ".py":
                    item = QTreeWidgetItem(rootItem)
                    presetItem = PresetItem(path)
                    item.setData(0, Qt.DisplayRole, presetItem.displayData)
                    item.setData(0, Qt.ToolTipRole, presetItem.toolTipData)
                    item.setData(0, Qt.UserRole, presetItem)
                    if isinstance(rootItem, QTreeWidget):
                        rootItem.addTopLevelItem(item)
                    else:
                        rootItem.addChild(item)

        from . import presets as presets_root
        _traverse(os.path.dirname(presets_root.__file__), self._ui.twPresets)

    def _presetSelected(self, item, col):
        if col == 0:
            preset: PresetItem = item.data(0, Qt.UserRole)
            if isinstance(preset, PresetItem):
                oldWidget = self._ui.saOptions.takeWidget()
                if oldWidget:
                    oldWidget.deleteLater()
                if preset:
                    self._optionWidget = OptionsWidget(self._ui.saOptions, preset.options)
                    self._ui.saOptions.setWidget(self._optionWidget)
                    self._ui.leTitle.setText(preset.title)
                    self._ui.lbDocument.setText(preset.document)
                    self._currentPreset = preset

    def _executePreset(self):
        if self._currentPreset is not None:
            import sys
            import datetime

            class _Stdout:
                def __init__(self):
                    self.lines = list()

                def write(self, text):
                    self.lines.append(text)

                def writelines(self, *args):
                    for item in args:
                        self.lines.append(item)

                def open(self):
                    self.lines = list()

                def close(self):
                    pass

                @property
                def text(self) -> str:
                    return "".join(self.lines)

            class _SysoutRedirectScope:
                def __init__(self, redirect_to):
                    self._redirectTo = redirect_to

                def __enter__(self):
                    self._oldStdout = sys.stdout
                    self._oldStderr = sys.stderr
                    sys.stdout = self._redirectTo
                    sys.stderr = self._redirectTo

                def __exit__(self, *_, **__):
                    sys.stdout = self._oldStdout
                    sys.stderr = self._oldStderr

            self._ui.pteOutput.clear()
            self._ui.pteOutput.setStyleSheet("")
            execute_stdout = _Stdout()
            try:
                self._currentPreset.reload()
                self._optionWidget.updateOptionValues()
                with _SysoutRedirectScope(execute_stdout):
                    self._currentPreset.execute(self._api)
                    print(f"-- DONE -- ({datetime.datetime.now()})")
                self._ui.pteOutput.setPlainText(execute_stdout.text)
            except BaseException:
                import traceback
                self._ui.pteOutput.setPlainText(traceback.format_exc())
                self._ui.pteOutput.setStyleSheet("color: #ff8888;")
