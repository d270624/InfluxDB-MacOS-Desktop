from PyQt5 import QtCore, QtWidgets


class Import_UI(object):
    import_QWidget = None

    def __init__(self, import_ui):
        import_ui.setObjectName("import_ui")
        import_ui.resize(506, 113)
        import_ui.setMinimumSize(QtCore.QSize(506, 113))
        import_ui.setMaximumSize(QtCore.QSize(506, 113))
        self.gridLayout = QtWidgets.QGridLayout(import_ui)
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtWidgets.QLabel(import_ui)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.browse_button = QtWidgets.QPushButton(import_ui)
        self.browse_button.setObjectName("browse_button")
        self.browse_button.clicked.connect(self.setBrowerPath)
        self.gridLayout.addWidget(self.browse_button, 1, 3, 1, 1)
        self.label = QtWidgets.QLabel(import_ui)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 5, 0, 1, 1)
        self.import_button = QtWidgets.QPushButton(import_ui)
        self.import_button.setObjectName("import_button")
        self.gridLayout.addWidget(self.import_button, 5, 3, 1, 1)
        self.browse_edit = QtWidgets.QLineEdit(import_ui)
        self.browse_edit.setReadOnly(True)
        self.browse_edit.setObjectName("browse_edit")
        self.gridLayout.addWidget(self.browse_edit, 1, 1, 1, 2)

        self.retranslateUi(import_ui)
        QtCore.QMetaObject.connectSlotsByName(import_ui)

    def retranslateUi(self, import_ui):
        _translate = QtCore.QCoreApplication.translate
        import_ui.setWindowTitle(_translate("Import server info", "导入服务器信息"))
        self.label_3.setText(_translate("1. Click Browse and select the template", "1、点击浏览,选择模板"))
        self.label.setText(_translate("2. Click the import", "2、点击导入"))
        self.browse_button.setText(_translate("Browse", "浏览"))
        self.import_button.setText(_translate("Import", "导入"))

    def setBrowerPath(self):
        file_name, filetype = QtWidgets.QFileDialog.getOpenFileName(self.import_QWidget, "浏览", ".",
                                                                    "Select Xlsx Files (*.xlsx)")
        self.browse_edit.setText(file_name)
