from PyQt5 import QtGui
from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtWidgets import QPlainTextEdit, QCompleter


class MyCompleter(QCompleter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = QStringListModel()
        model.setStringList(args[0])
        self.setModel(model)


class MyTextEdit(QPlainTextEdit):
    constant = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completer = MyCompleter(self.constant)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def insert_completion(self, completion):
        if completion == self.completer.completionPrefix():
            return
        text_cursor = self.textCursor()
        delete_char_len = len(self.completer.completionPrefix())
        for x in range(delete_char_len):
            text_cursor.deletePreviousChar()

        text_cursor.insertText(completion)
        self.setTextCursor(text_cursor)

    def text_before_cursor(self):
        text_cursor = self.textCursor()
        text_cursor.select(QtGui.QTextCursor.WordUnderCursor)
        return text_cursor.selectedText()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if self.completer.popup().isVisible():
            key = e.key()
            if key in (Qt.Key_Enter, Qt.Key_Return):
                e.ignore()
                return

        super().keyPressEvent(e)

        text_before_cursor = self.text_before_cursor()
        # print('text', self.text_before_cursor())
        if text_before_cursor != self.completer.currentCompletion():
            if text_before_cursor != self.completer.completionPrefix():
                text_before_cursor, self.completer.currentCompletion()
                self.completer.setCompletionPrefix(text_before_cursor)
                self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

                cursor_rectangle = self.cursorRect()
                popup = self.completer.popup()
                cursor_rectangle.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
                self.completer.complete(cursor_rectangle)
        else:
            self.completer.popup().hide()
