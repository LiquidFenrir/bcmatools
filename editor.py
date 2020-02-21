import sys
import os
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QSizePolicy
from PySide2.QtWidgets import QListView
from PySide2.QtWidgets import QTreeView
from PySide2.QtWidgets import QTreeWidgetItem
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtWidgets import QGraphicsView
from PySide2.QtWidgets import QDockWidget
from PySide2.QtGui import QStandardItem
from PySide2.QtGui import QStandardItemModel
from PySide2.QtCore import Slot
from PySide2.QtCore import Qt

APP_VER_REV = 0
APP_VER_MINOR = 0
APP_VER_MAJOR = 0
APP_VERSION = "v{}.{}.{}".format(APP_VER_MAJOR, APP_VER_MINOR, APP_VER_REV)

APP_NAME = "3DS Manual Editor"
APP_FULL_NAME = "{} {}".format(APP_NAME, APP_VERSION)

class LangInfo:
    REGIONS = ("EUR", "USA", "CHN", "TWN", "JPN", "KOR")
    LANGS = {
        "EUR": ("fr", "en", "ru", "pt", "nl", "es", "it", "de"),
        "USA": ("en", "es", "fr"),
        "JPN": ("ja"),
        "TWN": ("tc"),
        "CHN": ("sc"),
        "KOR": ("ko"),
    }

    LONG_TO_SHORT = {
        "French": "fr",
        "English": "en",
        "Spanish": "es",
        "Italian": "it",
        "Portuguese": "pt",
        "German": "de",
        "Dutch": "nl",
        "Russian": "ru",
        "Japanese": "ja",
        "Traditional Chinese": "tc",
        "Simplified Chinese": "sc",
        "Korean": "ko",
    }

    SHORT_TO_TRANSLATED = {
        "fr": "Français",
        "en": "English",
        "es": "Español",
        "it": "Italiano",
        "pt": "Português",
        "de": "Deutsch",
        "nl": "Nederlands",
        "ru": "Русский",
        "ja": "日本語",
        "tc": "繁體中文",
        "sc": "简体中文",
        "ko": "한국어",
    }

class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setWindowTitle(APP_FULL_NAME)

        self.createMenus()
        self.createStatus()
        self.createContent()
        self.createDocks()

    def createMenus(self):
        bar = self.menuBar()

        fileMenu = bar.addMenu("File")
        fileMenu.addAction("Save")  # save the opened project to a .man3 file
        fileMenu.addAction("Open")  # open a .man3 file to edit further (it's a zip containing the xml for each region/lang, and the added images)
        fileMenu.addAction("Export")  # generate the complete bcma xml from the shortened version and generate a BCMA from that
        fileMenu.addSeparator()
        fileMenu.addAction("Quit").triggered.connect(self.exit_app)

        editMenu = bar.addMenu("Edit")
        aboutMenu = bar.addMenu("About")

    def createStatus(self):
        self.statusBar().showMessage("Welcome to {}".format(APP_FULL_NAME))
    def createContent(self):
        # self.drawingScene = QGraphicsScene()
        self.drawingArea = QGraphicsView()
        self.drawingArea.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.setCentralWidget(self.drawingArea)

    def createDocks(self):
        pol = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.objectEditor = QTreeView()
        self.imagesList = QTreeView()
        self.pagesTree = QTreeView()

        self.objectEditor.setSizePolicy(pol)
        self.imagesList.setSizePolicy(pol)
        self.pagesTree.setSizePolicy(pol)

        self.added_images = {"Common": {}}
        self.imagesModel = QStandardItemModel()
        rootItem = self.imagesModel.invisibleRootItem()
        rootItem.appendRow(QStandardItem("Common"))
        for lang in LangInfo.LONG_TO_SHORT.keys():
            branchWidget = QStandardItem(lang)
            branchWidget.setEditable(False)
            self.added_images[lang] = (branchWidget, {})
            rootItem.appendRow(branchWidget)
        self.imagesList.setModel(self.imagesModel)
        self.imagesList.setHeaderHidden(True)

        self.pagesTree.setSortingEnabled(False) 

        feats = QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable
        areas = Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea

        dock =  QDockWidget("Selected object information", parent=self)
        dock.setAllowedAreas(areas)
        dock.setFeatures(feats)
        dock.setWidget(self.objectEditor)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        dock =  QDockWidget("Images available", parent=self)
        dock.setAllowedAreas(areas)
        dock.setFeatures(feats)
        dock.setAllowedAreas(areas)
        dock.setWidget(self.imagesList)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        dock =  QDockWidget("Pages by language", parent=self)
        dock.setAllowedAreas(areas)
        dock.setFeatures(feats)
        dock.setAllowedAreas(areas)
        dock.setWidget(self.pagesTree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    @Slot()
    def exit_app(self, checked):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainwindow = MyMainWindow()
    mainwindow.show()

    sys.exit(app.exec_())
