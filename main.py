# -*- coding:utf-8 _*-

import json
import os
import random
import re
import sqlite3
import sys
import time
import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from influxdb import InfluxDBClient

from create_database import Ui_create_database
from create_ui import Create_Ui_Form
from history_ui import Ui_history_ui
from new_connect_ui import Ui_Form
from ui import MainWindow
from constant import sql_constant
from MyTextEdit import MyTextEdit
import functools


class MyQMainWindow(QMainWindow):
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "确定要退出?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            sys.exit(0)
        else:
            event.ignore()


class InfluxRegister:
    """1、每隔连接的时候到此处注册，返回数据库的专属连接用连接名识别"""
    clients = {}  # 类属性

    def __init__(self):
        self.conn = sqlite3.connect('db/influx.db')

    def create_client(self, name, database=None):
        if name not in self.clients or bool(database):
            c = self.conn.cursor()
            cursor = c.execute(
                "SELECT name, address, port, user, password, ssl_switch, ID from ServerList where name='{}'".format(
                    name))
            data = cursor.fetchone()
            ssl_switch = True if data[5] == 2 else False
            client = InfluxDBClient(host=data[1], port=data[2], username=data[3], password=data[4], database=database,
                                    verify_ssl=ssl_switch, timeout=10)
            self.clients[name] = {"client": client, "data": data}


class InfluxManage(QObject):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        # self.MainWindow = MyQMainWindow()
        self.MainWindow = MainWindow()
        self.MainWindow.show()
        # self.MainWindow.setupUi(self.MainWindow)

        self.MainWindow.actionxinjian.triggered.connect(self.new_connect)

        self.new_ui = Ui_Form()
        self.new_QWidget = QWidget()
        self.new_QWidget.setWindowModality(Qt.ApplicationModal)
        self.new_ui.setupUi(self.new_QWidget)

        self.histroy_ui = Ui_history_ui()
        self.QWidget = QWidget()
        self.QWidget.setWindowModality(Qt.ApplicationModal)
        self.histroy_ui.setupUi(self.QWidget)

        self.create_ui = Create_Ui_Form()
        self.create_QWidget = QWidget()
        self.create_QWidget.setWindowModality(Qt.ApplicationModal)
        self.create_ui.setupUi(self.create_QWidget)

        self.create_database_ui = Ui_create_database()
        self.create_database_QWidget = QWidget()
        self.create_database_QWidget.setWindowModality(Qt.ApplicationModal)
        self.create_database_ui.setupUi(self.create_database_QWidget)

        self.path = os.path.dirname(sys.argv[0])
        self.conn = sqlite3.connect('db/influx.db')
        self.get_server_list()
        self.signal.connect(self.exec_handler)
        self.MainWindow.execAction.triggered.connect(lambda: self.signal.emit())
        self.MainWindow.history_button.triggered.connect(self.show_history)
        self.MainWindow.tabWidget.tabCloseRequested.connect(self.tab_close)

        self.MainWindow.treeView.setContextMenuPolicy(Qt.CustomContextMenu)  # 打开右键菜单的策略
        self.MainWindow.treeView.customContextMenuRequested.connect(self.right_click_menu)  # 绑定事件

        self.influxDbClient = InfluxRegister()
        self.edit_context_menu = QMenu()  # 创建对象
        self.edit_context_flag = False
        self.qt_info = functools.partial(QMessageBox.information, self.MainWindow, '提示信息')
        self.qt_cri = functools.partial(QMessageBox.critical, self.MainWindow, '提示信息')

    def save_history(self, text):
        save_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        c = self.conn.cursor()
        cursor = c.execute("select * from history")
        if text != "":
            if len(cursor.fetchall()) >= 100:
                c.execute("delete from history where time IN (SELECT time from history limit 1)")  # 删除最老的一条
            text = text.replace("'", "''")
            sql = """INSERT INTO history (time , sql) VALUES ('{}','{}')""".format(save_time, text)  # 插入新的
            c.execute(sql)
            self.conn.commit()

    def show_history(self):
        self.QWidget.show()
        c = self.conn.cursor()
        cursor = c.execute("SELECT * from history order by time DESC ")
        data = cursor.fetchall()
        self.histroy_ui.tableWidget.setRowCount(len(data))  # 设置行
        self.histroy_ui.tableWidget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)  # 添加滚动条
        for index, i in enumerate(data):
            for _index, j in enumerate(i):
                newItem = QTableWidgetItem(str(j))
                newItem.setTextAlignment(Qt.AlignCenter)
                self.histroy_ui.tableWidget.setItem(index, _index, newItem)

    def new_connect(self):
        """新建窗口，添加服务器"""
        self.new_QWidget.show()
        self.new_ui.pushButton.disconnect()  # 重新绑定时需要先释放绑定
        self.new_ui.pushButton_2.disconnect()  # 重新绑定时需要先释放绑定
        self.new_ui.pushButton.clicked.connect(self.save_connect)
        self.new_ui.pushButton_2.clicked.connect(self.test_connect)

    def test_connect(self):
        address = self.new_ui.address.text()
        port = self.new_ui.port.text()
        user = self.new_ui.user.text()
        password = self.new_ui.password.text()
        ssl = self.new_ui.checkBox.checkState()
        ssl_switch = True if ssl == 2 else False
        client = InfluxDBClient(host=address, port=port, username=user, password=password,
                                verify_ssl=ssl_switch)
        try:
            client.get_list_database()
            self.qt_info("连接成功")
        except Exception as e:
            self.qt_cri(str(e))

    def save_connect(self, types):
        """ 如果类型为True则编辑服务器"""
        name = self.new_ui.name.text()
        address = self.new_ui.address.text()
        port = self.new_ui.port.text()
        user = self.new_ui.user.text()
        password = self.new_ui.password.text()
        ssl = self.new_ui.checkBox.checkState()
        c = self.conn.cursor()
        if not user:
            user = "null"
        if not password:
            password = "null"

        if not all([name, address, port]):  # 当这三个中不管哪一个为空都不能继续往下执行
            self.qt_cri("名称、地址、端口不可以为空")
            return
        sql = """INSERT INTO ServerList (name, address, user, port, password, ssl_switch) VALUES ('{}','{}','{}',{},'{}',{})""".format(
            name, address, user, port, password, ssl)
        if types == 1:
            old_name = self.MainWindow.treeView.currentItem().text(0)  # 取当前节点的value值
            self.influxDbClient.create_client(old_name)
            clients = self.influxDbClient.clients.get(old_name)
            data = clients.get("data")
            ID = data[-1]
            sql = """UPDATE ServerList SET name="{}", address="{}", user="{}", port="{}", password="{}", ssl_switch="{}" where ID={}""".format(
                name, address, user, port, password, ssl, ID)
        try:
            c.execute(sql)
            self.conn.commit()
            if types:  # 点击编辑时，则删除当前服务器节点，并重新添加节点后高亮
                self.action_handler_1(2)
                rootIndex = self.MainWindow.treeView.indexOfTopLevelItem(self.MainWindow.treeView.currentItem())
                self.MainWindow.treeView.takeTopLevelItem(rootIndex)  # 删除当前服务器节点
                self.get_server_list(True, ID, rootIndex)
            else:  # 否则在保存以后刷新界面，先获取插入的最后一条数据的ID
                sql = """select ID from ServerList where rowid = last_insert_rowid() ;"""
                result = c.execute(sql)
                ID = result.fetchone()[0]
                rootIndex = self.MainWindow.treeView.topLevelItemCount()
                self.get_server_list(True, ID, rootIndex)
            self.new_QWidget.close()
            self.qt_info("保存成功")

        except sqlite3.IntegrityError as e:
            self.qt_info("名称不能重复")
        except ValueError as e:
            self.qt_info(str(e))

    def get_server_list(self, types=False, ID=None, rootIndex=None):
        """ ssl_switch : 开启ssl0 未开启ssl, 2"""
        c = self.conn.cursor()
        sql = "SELECT name, address, port, user, password, ssl_switch from ServerList"
        if types:
            sql = "SELECT name, address, port, user, password, ssl_switch from ServerList WHERE ID={}".format(ID)
        cursor = c.execute(sql)
        for x in cursor:
            if types:
                root = QTreeWidgetItem()
            else:
                root = QTreeWidgetItem(self.MainWindow.treeView)
            root.setText(0, x[0])
            root.setText(1, json.dumps(x))

            icon = QIcon()
            icon.addPixmap(QPixmap("images/server_open.ico"), QIcon.Normal, QIcon.On)
            icon.addPixmap(QPixmap("images/server_close.ico"), QIcon.Normal, QIcon.Off)
            root.setIcon(0, icon)
            if types:
                self.MainWindow.treeView.insertTopLevelItem(rootIndex, root)
                self.MainWindow.treeView.setCurrentItem(root)

        self.MainWindow.treeView.doubleClicked.disconnect()
        self.MainWindow.treeView.doubleClicked.connect(self.double_handler)

    def tab_close(self, index):
        self.MainWindow.tabWidget.removeTab(index)

    def create_table(self, text, name, database, tables_name=None):
        tab = QWidget()
        tab.setObjectName("tab")
        MyTextEdit.constant = sql_constant
        if tables_name:
            MyTextEdit.constant.extend(tables_name)
        self.MainWindow.textEdit = MyTextEdit(tab)
        self.MainWindow.textEdit.setGeometry(QtCore.QRect(0, 0, self.MainWindow.width() - 312, 181))
        self.MainWindow.textEdit.setObjectName("textEdit")
        self.MainWindow.textEdit.setPlainText(text)

        self.MainWindow.tableWidget = QTableWidget(tab)
        self.MainWindow.tableWidget.setGeometry(
            QtCore.QRect(0, 211, self.MainWindow.width() - 315, self.MainWindow.height() - 335))
        self.MainWindow.tableWidget.setObjectName("tableWidget")

        self.MainWindow.QComboBox = QComboBox(tab)
        self.MainWindow.QComboBox.setGeometry(QtCore.QRect(self.MainWindow.width() - 430, 184, 120, 25))
        self.MainWindow.QComboBox.setObjectName("QComboBox")

        self.MainWindow.tabWidget.addTab(tab, "{}.{}".format(name, database))
        current_index = self.MainWindow.tabWidget.count()  # 获取tab数量
        self.MainWindow.tabWidget.setCurrentIndex(current_index - 1)  # 激活最后一个创建的tab

    def group_select(self, series):
        current_text = self.MainWindow.QComboBox.currentText()
        currentTableWidget = self.MainWindow.tabWidget.currentWidget().findChild(QTableWidget, "tableWidget")
        for x in series:
            tags = x.get('tags')
            columns = x.get('columns')
            values = x.get('values')
            for z in tags:
                if tags[z] == current_text:
                    currentTableWidget.setColumnCount(len(columns))  # 设置列
                    currentTableWidget.setRowCount(len(values))  # 设置行
                    currentTableWidget.setHorizontalHeaderLabels(columns)  # 设置标题
                    # currentTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 关闭双击编辑
                    currentTableWidget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)  # 添加滚动条
                    for index, i in enumerate(values):
                        for _index, j in enumerate(i):
                            newItem = QTableWidgetItem(str(j))
                            newItem.setTextAlignment(Qt.AlignCenter)
                            currentTableWidget.setItem(index, _index, newItem)
                    return

    def show_table(self, tables):
        """传入influx数据，table显示数据"""
        currentTableWidget = self.MainWindow.tabWidget.currentWidget().findChild(QTableWidget, "tableWidget")
        flag = True
        try:
            series = tables.get("series")
            if not series:
                currentTableWidget.setColumnCount(1)  # 设置列
                currentTableWidget.setRowCount(1)  # 设置行
                currentTableWidget.setHorizontalHeaderLabels(["返回结果"])  # 设置标题
                currentTableWidget.setItem(0, 0, QTableWidgetItem(""))
            for x in series:
                table_name = x.get('name')
                columns = x.get('columns')
                values = x.get('values')
                tags = x.get('tags')
                if tags:
                    if flag:
                        self.MainWindow.QComboBox.currentIndexChanged.connect(lambda: self.group_select(series))
                        flag = False
                    for n in tags:
                        self.MainWindow.QComboBox.addItem(tags[n])
                currentTableWidget.setColumnCount(len(columns))  # 设置列
                currentTableWidget.setRowCount(len(values))  # 设置行
                currentTableWidget.setHorizontalHeaderLabels(columns)  # 设置标题
                # currentTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 关闭双击编辑
                currentTableWidget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)  # 添加滚动条
                for index, i in enumerate(values):
                    for _index, data_time in enumerate(i):
                        if _index == 0:
                            obj = re.match(
                                "^[1-2][0-9][0-9][0-9]-[0-1]{0,1}[0-9]-[0-3]{0,1}[0-9]T([0-1]?[0-9]|2[0-3]):([0-5]"
                                "[0-9]):([0-5][0-9]).+$",
                                data_time)
                            UTC_FORMAT2 = "2020-12-03T02:52:37.409Z"
                            if obj:
                                data_time = str(data_time).replace("T", " ")
                                data_time = data_time.split(".")[0]
                        newItem = QTableWidgetItem(str(data_time))
                        newItem.setTextAlignment(Qt.AlignCenter)
                        currentTableWidget.setItem(index, _index, newItem)
        except Exception as e:
            self.qt_cri(str(e))

    def double_handler(self):
        """双击服务器节点事件"""
        # treeView层级处理
        index_row = -1
        item = self.MainWindow.treeView.currentItem()
        parent = item.parent()
        if parent is None:
            index_top = self.MainWindow.treeView.indexOfTopLevelItem(item)
        else:
            index_top = self.MainWindow.treeView.indexOfTopLevelItem(parent)
            index_row = parent.indexOfChild(item)
        level = (index_top, index_row)
        # print(level)

        # 每个层级的逻辑处理
        if level == (-1, index_row):  # 当双击表的时候操作的事件
            client, server_name, database_name, table_name = self.table_conn_client()
            text = """SELECT * FROM "{}" WHERE time > now() - 5m""".format(table_name)
            childCount = self.MainWindow.treeView.currentItem().parent().childCount()
            tables_name = set()
            for x in range(childCount):
                name = self.MainWindow.treeView.currentItem().parent().child(x).text(0)
                tables_name.add(name)
            sql = 'SHOW TAG KEYS FROM "{}"'.format(table_name)
            keys_data = client.query(sql)
            sql = 'SHOW FIELD KEYS FROM "{}"'.format(table_name)
            field_data = client.query(sql)
            key_data = [x for x in keys_data]
            field_data = [x for x in field_data]
            new_data = key_data[0]
            new_data.extend(field_data[0])

            f = map(lambda x: {x.get('tagKey'), x.get('fieldKey')}, new_data)  # 同时取tagkey和fieldKey
            var = functools.reduce(lambda x, y: x | y, f)  # 循环获取列表中的集合，并且对之前的集合与后面的集合进行合并。reduce的功能
            tables_name.update(var)  # 更新到主集合中

            self.create_table(text, server_name, database_name, tables_name)

        elif level == (index_top, -1):  # 当双击服务器的时候显示数据库
            childCount = self.MainWindow.treeView.currentItem().childCount()
            if childCount == 0:
                icon = QIcon()
                icon.addPixmap(QPixmap("images/database_open.ico"), QIcon.Normal, QIcon.On)  # 设置打开时的图片样式
                icon.addPixmap(QPixmap("images/database_close.ico"), QIcon.Normal,
                               QIcon.Off)  # 设置关闭的时候图片样式
                try:
                    # 通过value中保存的服务器信息连接服务器并获得client
                    name = self.MainWindow.treeView.currentItem().text(0)  # 取当前节点的value值
                    self.influxDbClient.create_client(name)
                    clients = self.influxDbClient.clients.get(name)
                    client = clients.get("client")
                    database_list = client.get_list_database()
                    for x in database_list:
                        database_name = x.get("name")
                        child = QTreeWidgetItem()
                        child.setText(0, database_name)  # 插入根节点
                        child.setIcon(0, icon)
                        self.MainWindow.treeView.currentItem().addChild(child)
                except Exception as e:
                    self.qt_cri(str(e))

        elif level == (index_top, index_row):  # 当双击数据库的时候显示表
            childCount = self.MainWindow.treeView.currentItem().childCount()
            if childCount == 0:
                name = self.MainWindow.treeView.currentItem().parent().text(0)  # 取服务器名
                database = self.MainWindow.treeView.currentItem().text(0)  # 取数据库名
                self.influxDbClient.create_client(name, database=database)
                clients = self.influxDbClient.clients.get(name)
                client = clients.get("client")
                tables = client.query('show measurements;')
                Children = []
                for x in tables:
                    for i in x:
                        child = QTreeWidgetItem()
                        child.setText(0, i.get("name"))
                        child.setIcon(0, QIcon('images/form.ico'))
                        Children.append(child)
                self.MainWindow.treeView.currentItem().addChildren(Children)

    def status_bar_signal(self, text):
        self.MainWindow.statusBar.showMessage(text)

    def exec_handler(self):
        try:
            text_obj = self.MainWindow.tabWidget.currentWidget().findChild(QPlainTextEdit, "textEdit")
            old_time = time.time() * 1000
            tab_name = self.MainWindow.tabWidget.tabText(self.MainWindow.tabWidget.currentIndex())
            data = tab_name.rsplit(sep='.', maxsplit=1)
            name = data[0]
            database = data[1]
            self.influxDbClient.create_client(name, database=database)
            clients = self.influxDbClient.clients.get(name)
            client = clients.get("client")
            tables = client.query(text_obj.toPlainText())
            now_time = time.time() * 1000
            self.show_table(tables.raw)  # 将查询结果传到show_table，并显示数据到前端
            self.MainWindow.statusBar.showMessage("执行完毕,耗时:{}毫秒".format(int(now_time - old_time)))
            color = ["blue", "green"]
            random.shuffle(color)
            self.MainWindow.statusBar.setStyleSheet("color:{}".format(color[0]))
            self.save_history(text=text_obj.toPlainText())
        except AttributeError:
            self.MainWindow.statusBar.setStyleSheet("color:red")
            self.MainWindow.statusBar.showMessage("没有选择数据库，请先选择数据库")
        except Exception as e:
            self.qt_cri(str(e))
            print('错误所在的行号：', e.__traceback__.tb_lineno)

    def table_conn_client(self):
        server_name = self.MainWindow.treeView.currentItem().parent().parent().text(0)
        database_name = self.MainWindow.treeView.currentItem().parent().text(0)
        table_name = self.MainWindow.treeView.currentItem().text(0)

        self.influxDbClient.create_client(server_name, database=database_name)
        clients = self.influxDbClient.clients.get(server_name)
        client = clients.get("client")
        return client, server_name, database_name, table_name

    def select(self, i):
        client, name, database, db = self.table_conn_client()
        sql = 'SHOW TAG VALUES FROM "{}" WITH KEY = "{}"'.format(db, i)
        new_tables = client.query(sql)
        self.show_table(new_tables.raw)

    def create_form(self, client):
        """创建表的点击事件"""
        json_body = self.create_ui.textEdit.toPlainText()
        try:
            json_body = json.loads(json_body)
            client.write_points(json_body)
            self.qt_info("创建成功")
            self.action_handler_2(0)
        except Exception as e:
            self.qt_cri(str(e))
            print('错误所在的行号：', e.__traceback__.tb_lineno)

    def create_database(self, client):
        database = self.create_database_ui.lineEdit.text()
        try:
            client.create_database(database)  # 创建数据库
            QMessageBox.information(self.MainWindow, 'Message', "创建成功")

            icon = QIcon()
            icon.addPixmap(QPixmap("images/database_open.ico"), QIcon.Normal, QIcon.On)  # 设置打开时的图片样式
            icon.addPixmap(QPixmap("images/database_close.ico"), QIcon.Normal, QIcon.Off)  # 设置关闭的时候图片样式

            child = QTreeWidgetItem()
            child.setText(0, database)  # 插入根节点
            child.setIcon(0, icon)
            self.MainWindow.treeView.currentItem().addChild(child)
        except Exception as e:
            self.qt_cri(str(e))

    def action_handler_1(self, types):
        """服务器层操作：
            1.创建数据库
            2.关闭连接
            3.编辑服务器
            4.删除服务器
          """
        name = self.MainWindow.treeView.currentItem().text(0)
        self.influxDbClient.create_client(name)
        clients = self.influxDbClient.clients.get(name)
        client = clients.get("client")
        if types == 1:
            self.create_database_QWidget.show()
            self.create_database_ui.pushButton.clicked.connect(lambda: self.create_database(client))

        if types == 2:
            client.close()
            del self.influxDbClient.clients[name]
            child = self.MainWindow.treeView.currentItem().childCount()
            while child:
                now_child = self.MainWindow.treeView.currentItem().child(0)
                self.MainWindow.treeView.currentItem().removeChild(now_child)
                child -= 1
            self.MainWindow.treeView.currentItem().setIcon(0, QIcon('images/server_close.ico'))

        if types == 3:
            data = clients.get("data")
            self.new_QWidget.show()
            self.new_QWidget.setWindowTitle("编辑连接")
            self.new_ui.name.setText(data[0])
            self.new_ui.address.setText(data[1])
            self.new_ui.port.setValue(data[2])
            self.new_ui.user.setText(data[3])
            self.new_ui.password.setText(data[4])
            ssl_switch = True if data[5] == 2 else False
            self.new_ui.checkBox.setChecked(ssl_switch)
            self.new_ui.pushButton.disconnect()  # 重新绑定时需要先释放绑定
            self.new_ui.pushButton_2.disconnect()  # 重新绑定时需要先释放绑定
            self.new_ui.pushButton.clicked.connect(lambda: self.save_connect(True))
            self.new_ui.pushButton_2.clicked.connect(self.test_connect)

        if types == 4:
            # 删除数据库中的信息
            data = clients.get("data")
            sql = 'delete from ServerList where id={}'.format(data[-1])

            reply = QMessageBox.question(self.MainWindow, 'Message', "确定要删除？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    c = self.conn.cursor()
                    c.execute(sql)
                    self.conn.commit()
                    self.qt_info("删除成功")
                    self.action_handler_1(2)
                    rootIndex = self.MainWindow.treeView.indexOfTopLevelItem(self.MainWindow.treeView.currentItem())
                    self.MainWindow.treeView.takeTopLevelItem(rootIndex)  # 删除当前服务器节点
                except Exception as e:
                    self.qt_cri(str(e))

    def action_handler_2(self, types):
        """
            数据库层操作
            types : 0 刷新窗口， 1 新建表， 2 删除数据库
        """
        name = self.MainWindow.treeView.currentItem().parent().text(0)
        database = self.MainWindow.treeView.currentItem().text(0)
        self.influxDbClient.create_client(name, database=database)
        clients = self.influxDbClient.clients.get(name)
        client = clients.get("client")
        if types == 0:
            child = self.MainWindow.treeView.currentItem().childCount()
            while child:
                now_child = self.MainWindow.treeView.currentItem().child(0)
                self.MainWindow.treeView.currentItem().removeChild(now_child)
                child -= 1
            tables = client.query('show measurements;')
            for x in tables:
                for i in x:
                    child = QTreeWidgetItem()
                    child.setText(0, i.get("name"))
                    child.setIcon(0, QIcon('images/form.ico'))
                    self.MainWindow.treeView.currentItem().addChild(child)
        if types == 1:
            self.create_QWidget.show()
            self.create_ui.pushButton.clicked.connect(lambda: self.create_form(client))
        if types == 2:
            reply = QMessageBox.question(self.MainWindow, 'Message', "确定要删除？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    client.drop_database(database)  # 删除数据库
                    self.qt_info("删除成功")
                    current_item = self.MainWindow.treeView.currentItem()  # 获取当前节点
                    self.MainWindow.treeView.currentItem().parent().removeChild(current_item)  # 删除父目录下当前节点
                except Exception as e:
                    self.qt_cri(str(e))

    def action_handler_3(self, types):
        """表单层操作"""
        client, name, database, db = self.table_conn_client()
        self.influxDbClient.create_client(name, database=database)
        clients = self.influxDbClient.clients.get(name)
        client = clients.get("client")

        if types == 0:
            sql = 'SHOW TAG KEYS FROM "{}"'.format(db)
            tables = client.query(sql)
            self.create_table(sql, name, database)
            self.show_table(tables.raw)
        elif types == 1:
            tables = client.query('SHOW TAG KEYS FROM "{}"'.format(db))
            self.create_table("", name, database)
            switch = True
            for x in tables:
                for i in x:
                    for z in i:
                        if switch:
                            sql = 'SHOW TAG VALUES FROM "{}" WITH KEY = "{}"'.format(db, i[z])
                            new_tables = client.query(sql)
                            self.show_table(new_tables.raw)
                            switch = False
                        self.MainWindow.QComboBox.addItem(str(i[z]))
            self.MainWindow.QComboBox.currentIndexChanged[str].connect(self.select)
        elif types == 2:
            text = 'SHOW FIELD KEYS FROM "{}"'.format(db)
            tables = client.query(text)
            self.create_table(text, name, database)
            self.show_table(tables.raw)
        elif types == 3:
            client, name, database, db = self.table_conn_client()
            reply = QMessageBox.question(self.MainWindow, 'Message', "确定要删除？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    client.query('drop measurement {}'.format(db))
                    self.qt_cri("删除成功")
                    current_item = self.MainWindow.treeView.currentItem()
                    self.MainWindow.treeView.currentItem().parent().removeChild(current_item)
                except Exception as e:
                    self.qt_cri(str(e))
        else:
            raise ValueError

    def right_click_menu(self, pos):
        index_row = -1
        item = self.MainWindow.treeView.currentItem()
        if not item:
            contextMenu = QMenu()  # 创建对象
            new_conn = contextMenu.addAction(u'新建连接')  # 添加动作
            new_conn.triggered.connect(self.new_connect)
            contextMenu.exec_(self.MainWindow.treeView.mapToGlobal(pos))  # 随指针的位置显示菜单
            contextMenu.show()  # 显示
            return
        try:
            parent = item.parent()
        except Exception as e:
            print(e)
            return
        if parent is None:
            index_top = self.MainWindow.treeView.indexOfTopLevelItem(item)
        else:
            index_top = self.MainWindow.treeView.indexOfTopLevelItem(parent)
            index_row = parent.indexOfChild(item)
        level = (index_top, index_row)
        if level == (-1, index_row):  # 当右击表的时候
            try:
                contextMenu = QMenu()  # 创建对象
                actionA = contextMenu.addAction(u'显示标签键')  # 添加动作
                actionB = contextMenu.addAction(u'显示标签值')
                actionC = contextMenu.addAction(u'显示字段键')
                actionD = contextMenu.addAction(u'删除表')
                actionA.triggered.connect(lambda: self.action_handler_3(0))
                actionB.triggered.connect(lambda: self.action_handler_3(1))
                actionC.triggered.connect(lambda: self.action_handler_3(2))
                actionD.triggered.connect(lambda: self.action_handler_3(3))
                contextMenu.exec_(self.MainWindow.treeView.mapToGlobal(pos))  # 随指针的位置显示菜单
                contextMenu.show()  # 显示
            except Exception as e:
                print(e)
        elif level == (index_top, -1):  # 当右击服务器的时候
            contextMenu = QMenu()  # 创建对象
            actionA = contextMenu.addAction(u'创建数据库')  # 添加动作
            actionB = contextMenu.addAction(u'关闭连接')

            actionC = contextMenu.addAction(u'编辑服务器')  # 添加动作
            actionD = contextMenu.addAction(u'删除服务器')  # 添加动作

            actionA.triggered.connect(lambda: self.action_handler_1(1))
            actionB.triggered.connect(lambda: self.action_handler_1(2))
            actionC.triggered.connect(lambda: self.action_handler_1(3))
            actionD.triggered.connect(lambda: self.action_handler_1(4))

            contextMenu.exec_(self.MainWindow.treeView.mapToGlobal(pos))  # 随指针的位置显示菜单
            contextMenu.show()  # 显示
        elif level == (index_top, index_row):  # 当右击数据库的时候
            contextMenu = QMenu()  # 创建对象
            actionA = contextMenu.addAction(u'刷新')  # 添加动作
            actionB = contextMenu.addAction(u'创建表')  # 添加动作
            actionC = contextMenu.addAction(u'删除数据库')
            actionA.triggered.connect(lambda: self.action_handler_2(0))
            actionB.triggered.connect(lambda: self.action_handler_2(1))
            actionC.triggered.connect(lambda: self.action_handler_2(2))
            contextMenu.exec_(self.MainWindow.treeView.mapToGlobal(pos))  # 随指针的位置显示菜单
            contextMenu.show()  # 显示


if __name__ == '__main__':
    ui = InfluxManage()
    ui.MainWindow.show()  # 显示主框
    sys.exit(ui.app.exec_())
