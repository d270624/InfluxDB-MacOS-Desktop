# -*- coding:utf-8 _*-
from PyQt5.QtCore import QThread, pyqtSignal


class Runthread(QThread):  # 步骤1.创建一个线程实例
    signal = pyqtSignal()  # 创建一个自定义信号

    def __init__(self):  # 通过初始化赋值的方式实现UI主线程传递值给子线程
        super(Runthread, self).__init__()

    def run(self):
        self.signal.emit()  # 发射自定义信号
