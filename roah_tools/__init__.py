from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer


def printMessage(usdviewApi):
    print("Hello, World!")


def showTurntableUI(usdviewApi):
    from roah_tools.turntable import main as turntableMain
    turntableMain(usdviewApi)


class RoahToolsPluginContainer(PluginContainer):

    def registerPlugins(self, plugRegistry, usdviewApi):

        self._printMessage = plugRegistry.registerCommandPlugin(
            "roah_tools.PrintMessage",
            "[TUTORIAL] Print Message",
            printMessage)
        
        self._turntable = plugRegistry.registerCommandPlugin(
            "roah_tools.ShowTurntableUI",
            "Show Turntable UI",
            showTurntableUI)

    def configureView(self, plugRegistry, plugUIBuilder):
        roahToolsMenu = plugUIBuilder.findOrCreateMenu("RoahTools")
        roahToolsMenu.addItem(self._printMessage)
        roahToolsMenu.addItem(self._turntable)

Tf.Type.Define(RoahToolsPluginContainer)
