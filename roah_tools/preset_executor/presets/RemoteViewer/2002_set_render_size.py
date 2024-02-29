""" Remote Viewer の描画解像度を切り替える.

"""


renderWidth: int = 3840
renderHeight: int = 1600


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
            viewer.CreateRenderWidthAttr().Set(renderWidth)
            viewer.CreateRenderHeightAttr().Set(renderHeight)
