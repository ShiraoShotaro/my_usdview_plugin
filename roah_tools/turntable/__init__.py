import os
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QSignalBlocker, Qt
from pxr import UsdGeom, Gf, Sdf


class SignalBlocker:
    def __init__(self, ui):
        self.__blocker = QSignalBlocker(ui)

    def __enter__(self):
        self.__blocker.reblock()

    def __exit__(self, *_):
        self.__blocker.unblock()


class TurntableWindow:
    def __init__(self, api):
        self.api = api
        self.ui = QUiLoader().load(os.path.join(os.path.dirname(__file__), "window.ui"), api.qMainWindow)
        self.ui.setWindowTitle("Turntable UI")

        self.ui.pbAddCamera.clicked.connect(self._pbAddCamera_onClicked)
        self.ui.cbCamera.currentIndexChanged.connect(self._cbCamera_onCurrentIndexChanged)
        self.ui.dsbCenterHeight.valueChanged.connect(self._dsbCenterHeight_onValueChanged)
        self.ui.dsbDistance.valueChanged.connect(self._dsbDistance_onValueChanged)
        self.ui.dsbPitch.valueChanged.connect(self._dspPitch_onValueChanged)
        self.ui.dsbCensorWidth.valueChanged.connect(self._dsbCensorWidth_onValueChanged)
        self.ui.dsbCensorHeight.valueChanged.connect(self._dsbCensorHeight_onValueChanged)
        self.ui.dsbFocalLength.valueChanged.connect(self._dsbFocalLength_onValueChanged)
        self.ui.dsbFocusOffset.valueChanged.connect(self._dsbFocusOffset_onValueChanged)
        self.ui.dsbFstop.valueChanged.connect(self._dsbFstop_onValueChanged)
        self.ui.dsbExposure.valueChanged.connect(self._dsbExposure_onValueChanged)
        self.ui.dsbNear.valueChanged.connect(self._dsbNear_onValueChanged)
        self.ui.dsbFar.valueChanged.connect(self._dsbFar_onValueChanged)
        self.ui.cbAnamorphic.currentIndexChanged.connect(self._cbAnamorphic_onCurrentIndexChanged)
        self.ui.cbAnamorphicPreview.stateChanged.connect(self._cbAnamorphicPreview_onAnamorphicPreview)
        self.ui.sbFrames.valueChanged.connect(self._sbFrames_onValueChanged)

    def _updateUi(self):
        cameras = self._getAllTurntableCamera()
        idx = self.ui.cbCamera.currentIndex()
        with SignalBlocker(self.ui.cbCamera):
            self.ui.cbCamera.clear()
            for camera in cameras:
                self.ui.cbCamera.addItem(camera.GetPath().name, camera.GetPath())
        if idx < len(cameras):
            self.ui.cbCamera.setCurrentIndex(idx)
        else:
            self.ui.cbCamera.setCurrentIndex(-1)
        
    def _getAllTurntableCamera(self):
        camerasPrim = self.api.stage.GetPrimAtPath("/turntableCameras")
        cameraPrims = list()
        if camerasPrim:
            for child in camerasPrim.GetChildren():
                if child.IsA(UsdGeom.Camera):
                    cameraPrims.append(UsdGeom.Camera(child))
        return cameraPrims
    
    def _createFocusOffsetAttr(self, prim):
        return prim.CreateAttribute("focusOffset", Sdf.ValueTypeNames.Float, True)
    
    def _createAnamorphicRatioAttr(self, prim):
        return prim.CreateAttribute("anamorphicRatio", Sdf.ValueTypeNames.Float, False)
    
    def _createAnamorphicPreviewAttr(self, prim):
        return prim.CreateAttribute("anamorphicPreview", Sdf.ValueTypeNames.Bool, False)

    def _pbAddCamera_onClicked(self):
        camerasPrim = self.api.stage.GetPrimAtPath("/turntableCameras")
        if not camerasPrim:
            camerasPrim = UsdGeom.Scope.Define(self.api.stage, "/turntableCameras").GetPrim()
        primName = f"turntable_camera_{len(camerasPrim.GetChildren())}"
        mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
        camera = UsdGeom.Camera.Define(self.api.stage, f"/turntableCameras/{primName}")
        turnOp = camera.AddRotateYOp(UsdGeom.XformOp.PrecisionFloat, "turn")
        turnOp.Set(0, 0)
        turnOp.Set(360, 300)
        camera.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble, "center").Set(Gf.Vec3d(0, 0, 0))
        camera.AddRotateXOp(UsdGeom.XformOp.PrecisionFloat, "pitch").Set(0)
        camera.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble, "distance").Set(Gf.Vec3d(0, 0, 1 / mpu))
        camera.CreateHorizontalApertureAttr().Set(42.67 / 100.0 / mpu)
        camera.CreateVerticalApertureAttr().Set(24.0 / 100.0 / mpu)
        camera.CreateFocalLengthAttr().Set(50 / 100.0 / mpu)
        camera.CreateFocusDistanceAttr().Set(1 / mpu)
        camera.CreateFStopAttr().Set(4.0)
        camera.CreateExposureAttr().Set(0.0)
        camera.CreateClippingRangeAttr().Set(Gf.Vec2f(0.01 / mpu, 1000 / mpu))
        self._createFocusOffsetAttr(camera.GetPrim()).Set(0)
        self._createAnamorphicRatioAttr(camera.GetPrim()).Set(1.0)
        self._createAnamorphicPreviewAttr(camera.GetPrim()).Set(False)

        sc = min(self.api.stage.GetStartTimeCode(), 1)
        ec = max(self.api.stage.GetEndTimeCode(), 300)

        self.api.stage.SetStartTimeCode(sc)
        self.api.stage.SetEndTimeCode(ec)
        self.api._UsdviewApi__appController._reloadFixedUI(False)

        self._updateUi()
        idx = self.ui.cbCamera.findText(primName)
        if idx >= 0:
            self.ui.cbCamera.setCurrentIndex(idx)

    def _cbCamera_onCurrentIndexChanged(self, index):
        enabled = index >= 0
        self.ui.dsbCenterHeight.setEnabled(enabled)
        self.ui.dsbDistance.setEnabled(enabled)
        self.ui.dsbPitch.setEnabled(enabled)
        self.ui.dsbCensorHeight.setEnabled(enabled)
        self.ui.dsbCensorWidth.setEnabled(enabled)
        self.ui.dsbFocalLength.setEnabled(enabled)
        self.ui.dsbFocusOffset.setEnabled(enabled)
        self.ui.dsbFstop.setEnabled(enabled)
        self.ui.dsbExposure.setEnabled(enabled)
        self.ui.dsbNear.setEnabled(enabled)
        self.ui.dsbFar.setEnabled(enabled)
        self.ui.cbAnamorphic.setEnabled(enabled)
        self.ui.cbAnamorphicPreview.setEnabled(enabled)
        
        if index >= 0:
            path = self.ui.cbCamera.itemData(index)
            camera = UsdGeom.Camera.Get(self.api.stage, path)
            if camera:
                ops = camera.GetOrderedXformOps()
                print(ops)

    def _getCurrentSelectedCamera(self):
        cameraPath = self.ui.cbCamera.currentData()
        if cameraPath:
            camera = UsdGeom.Camera.Get(self.api.stage, cameraPath)
            if camera:
                return camera
        return None

    def _dsbCenterHeight_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            ops = camera.GetOrderedXformOps()
            for op in ops:
                if op.GetBaseName() == "center":
                    op.Set(Gf.Vec3d(0, value / mpu, 0))

    def _dsbDistance_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            ops = camera.GetOrderedXformOps()
            for op in ops:
                if op.GetBaseName() == "distance":
                    op.Set(Gf.Vec3d(0, 0, value / mpu))
            foffset = camera.GetPrim().GetAttribute("focusOffset").Get()
            camera.CreateFocusDistanceAttr().Set(value / mpu + foffset)

    def _dspPitch_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            ops = camera.GetOrderedXformOps()
            for op in ops:
                if op.GetBaseName() == "pitch":
                    op.Set(-value)

    def _dsbCensorWidth_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            camera.CreateHorizontalApertureAttr().Set(value / 100.0 / mpu)

    def _dsbCensorHeight_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            camera.CreateVerticalApertureAttr().Set(value / 100.0 / mpu)

    def _dsbFocalLength_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            camera.CreateFocalLengthAttr().Set(value / 100.0 / mpu)

    def _dsbFocusOffset_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            self._createFocusOffsetAttr(camera.GetPrim()).Set(value / mpu)

            ops = camera.GetOrderedXformOps()
            for op in ops:
                if op.GetBaseName() == "distance":
                    camera.CreateFocusDistanceAttr().Set(op.Get()[2] + value / mpu)

    def _dsbFstop_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            camera.CreateFStopAttr().Set(value)

    def _dsbExposure_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            camera.CreateExposureAttr().Set(value)

    def _dsbNear_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            rg = camera.GetClippingRangeAttr().Get()
            camera.CreateClippingRangeAttr().Set(Gf.Vec2f(value / mpu, rg[1]))

    def _dsbFar_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            mpu = UsdGeom.GetStageMetersPerUnit(self.api.stage)
            rg = camera.GetClippingRangeAttr().Get()
            camera.CreateClippingRangeAttr().Set(Gf.Vec2f(rg[0], value / mpu))

    def _cbAnamorphic_onCurrentIndexChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            # The 手抜き
            # x1.33 (hogehoge) から 1.33 を抜き出す
            ratio = float(self.ui.cbAnamorphic.currentText().split(" ")[0][1:])
            self._createAnamorphicRatioAttr(camera.GetPrim()).Set(ratio)
            self.ui.cbAnamorphicPreview.setEnabled(ratio != 1.0)

    def _cbAnamorphicPreview_onAnamorphicPreview(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            self._createAnamorphicPreviewAttr(camera.GetPrim()).Set(value == Qt.Checked)

    def _sbFrames_onValueChanged(self, value):
        camera = self._getCurrentSelectedCamera()
        if camera:
            ops = camera.GetOrderedXformOps()
            for op in ops:
                if op.GetBaseName() == "turn":
                    op.GetAttr().Clear()
                    op.Set(0, 0)
                    op.Set(360, value)

        self.api.stage.SetEndTimeCode(value)
        self.api._UsdviewApi__appController._reloadFixedUI(False)

    def show(self):
        self._updateUi()
        self.ui.show()
    

_window = None


def main(api):
    global _window

    if _window is None:
        _window = TurntableWindow(api)
    
    _window.show()
