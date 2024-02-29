""" RemoteViewer セットアップ

Remote Viewer で HdStorm を選択し, ID を default に, Label に "Preview" を設定する.

"""


def main(api):
    from lb import RemoteViewer
    root = RemoteViewer.ViewersRoot.GetViewersRoot(api.stage)
    for child in root.GetPrim().GetChildren():
        viewer = RemoteViewer.ViewerConfig(child)
        if viewer:
            viewer.CreateIdentifierAttr().Set("default")
            viewer.CreateRenderDelegateIdAttr().Set("HdStormRendererPlugin")
            viewer.CreateLabelAttr().Set("Preview")
