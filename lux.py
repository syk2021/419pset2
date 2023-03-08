from PySide6.QtWidgets import QApplication, QFrame, QLabel, QListWidget
from PySide6.QtWidgets import QMainWindow, QGridLayout, QPushButton, QLineEdit
from PySide6.QtWidgets import QScrollBar, QListWidgetItem
from PySide6.QtCore import Qt
from sys import exit, argv
import json
from socket import socket
from sys import exit, stderr

import argparse


class LuxGUI():
    """A GUI class for Lux."""

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self.app = QApplication(argv)
        self.label = QLineEdit("Label")
        self.classifier = QLineEdit("Classifier")
        self.agent = QLineEdit("Agent")
        self.department = QLineEdit("Department")
        self.layout = QGridLayout()
        self.frame = QFrame()
        self.window = QMainWindow()

        search_button = QPushButton("Search")

        # set layout on frame
        self.frame.setLayout(self.layout)
        # set window title
        self.window.setWindowTitle("Window Title")
        self.window.setCentralWidget(self.frame)

        # Add widgets to layout
        self.layout.addWidget(search_button, 4, 0)
        search_button.clicked.connect(lambda: self.search())
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.classifier, 1, 0)
        self.layout.addWidget(self.agent, 2, 0)
        self.layout.addWidget(self.department, 3, 0)
        # layout.addWidget(qlabel, 6, 0)

        # Sizing the screen
        screen_size = self.app.primaryScreen().availableGeometry()
        # Main window: no wider than 1/2 of width, 1/2 of height
        self.window.resize(screen_size.width()//2, screen_size.height()//2)

        # List of responses we get back
        listwidget = QListWidget()
        item1 = QListWidgetItem("A")
        item2 = QListWidgetItem("B")
        item3 = QListWidgetItem("C")
        item4 = QListWidgetItem("D")
        item4 = QListWidgetItem("D")
        item5 = QListWidgetItem("D")
        item6 = QListWidgetItem("D")
        item7 = QListWidgetItem("D")
        item8 = QListWidgetItem("D")
        item9 = QListWidgetItem("D")

        listwidget.addItem(item1)
        listwidget.addItem(item2)
        listwidget.addItem(item3)
        listwidget.addItem(item4)
        listwidget.addItem(item5)
        listwidget.addItem(item6)
        listwidget.addItem(item7)
        listwidget.addItem(item8)
        listwidget.addItem(item9)

        self.layout.addWidget(listwidget, 8, 0)
        scroll_bar = QScrollBar()
        scroll_bar.setStyleSheet("backgroundL lightgreen;")
        listwidget.addScrollBarWidget(scroll_bar, Qt.AlignLeft)

        self.window.show()
        exit(self.app.exec())

    def search(self):
        """Function that executes when user clicks search button"""
        data_label = self.label.text()
        data_classifier = self.classifier.text()
        data_agent = self.agent.text()
        data_department = self.department.text()
        data_dict = {"id": None, "label": data_label, "classifier": data_classifier,
                     "agt": data_agent, "dep": data_department}
        print(data_dict)
        self.connect_to_server(json.dumps(data_dict))

    def connect_to_server(self, data):
        """Connect lux to server."""
        try:
            with socket() as sock:
                sock.connect((self._host, self._port))

                # write to the server
                out_flo = sock.makefile(mode='w', encoding='utf-8')
                out_flo.write(data + "\n")
                out_flo.flush()

                # read from the server
                in_flo = sock.makefile(mode='r', encoding='utf-8')
                response = in_flo.readline()

                if response == '':
                    print('The echo server crashed', file=stderr)
                else:
                    print(response, end='')
        except Exception as ex:
            print(ex, file=stderr)
            exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='lux.py', allow_abbrev=False)

    parser.add_argument(
        "host", help="the host on which the server is running")

    parser.add_argument(
        "port", help="the port at which the server is listening")

    args = parser.parse_args()

    host = args.host
    port = args.port

    try:
        port = int(port)
        if port < 0:
            raise Exception
    except Exception as err:
        print("Port can only can be a positive integer", file=stderr)
        exit(1)

    LuxGUI(host, port)

    # LuxGUI().connect_to_server(host, port, )
