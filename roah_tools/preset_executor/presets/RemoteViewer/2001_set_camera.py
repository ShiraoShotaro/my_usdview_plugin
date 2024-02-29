""" 選択中のカメラに切り替える

USDVIEW で選択中のカメラに切り替える.

"""


def main(api):
    from pxr import UsdGeom
    from lb import RemoteViewer

    if not api.prim or not api.prim.IsA(UsdGeom.Camera):
        print("カメラ prim を選択してください.")
        return

    root = RemoteViewer.ViewersRoot.GetViewersRoot(api.stage)
    for child in root.GetPrim().GetChildren():
        viewer = RemoteViewer.ViewerConfig(child)
        if viewer:
            viewer.GetCameraRel().SetTargets([api.prim.GetPath()])
    root.SyncStage()
