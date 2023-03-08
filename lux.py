from PySide6.QtWidgets import QApplication, QFrame, QLabel, QListWidget
from PySide6.QtWidgets import QMainWindow, QGridLayout, QPushButton, QLineEdit
from PySide6.QtWidgets import QScrollBar, QListWidgetItem, QGridLayout
from PySide6.QtCore import Qt
from sys import exit, argv, stderr
from socket import socket
from dialog import FW_FONT, FixedWidthMessageDialog
import json
import argparse
from table import Table


class LuxGUI():
    """A GUI class for Lux."""

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self.app = QApplication(argv)
        self.label = QLineEdit()
        self.classifier = QLineEdit()
        self.agent = QLineEdit()
        self.department = QLineEdit()
        self.layout = QGridLayout()
        self.frame = QFrame()
        self.window = QMainWindow()
        # self.search_results is a dictionary from json.loads()
        self.search_results = None
        self.list_widget = QListWidget()

        # when list widget item is clicked, display dialog
        self.list_widget.itemDoubleClicked.connect(self.list_item_clicked)

        # set layout on frame
        self.frame.setLayout(self.layout)
        # set window title
        self.window.setWindowTitle("Window Title")
        self.window.setCentralWidget(self.frame)

        # Add widgets to layout
        label_label = QLabel("Label:")
        self.layout.addWidget(label_label, 0, 0)
        self.layout.addWidget(self.label, 0, 1)

        label_classifier = QLabel("Classifier:")
        self.layout.addWidget(label_classifier, 1, 0)
        self.layout.addWidget(self.classifier, 1, 1)

        label_agent = QLabel("Agent:")
        self.layout.addWidget(label_agent, 2, 0)
        self.layout.addWidget(self.agent, 2, 1)

        label_department = QLabel("Department:")
        self.layout.addWidget(label_department, 3, 0)
        self.layout.addWidget(self.department, 3, 1)

        search_button = QPushButton("Search")
        self.layout.addWidget(search_button, 4, 1)
        search_button.clicked.connect(lambda: self.search())

        # Sizing the screen
        screen_size = self.app.primaryScreen().availableGeometry()
        # Main window: no wider than 1/2 of width, 1/2 of height
        self.window.resize(screen_size.width()//2, screen_size.height()//2)

        # List of responses we get back
        self.layout.addWidget(self.list_widget, 8, 0)
        scroll_bar = QScrollBar()
        scroll_bar.setStyleSheet("backgroundL lightgreen;")
        # self.list_widget.addScrollBarWidget(scroll_bar, Qt.AlignLeft)

        self.window.show()
        exit(self.app.exec())

    def search(self):
        """Function that executes when user clicks search button"""
        data_label = self.parse_label_data(self.label)
        data_classifier = self.parse_label_data(self.classifier)
        data_agent = self.parse_label_data(self.agent)
        data_department = self.parse_label_data(self.department)
        data_dict = {"id": None, "label": data_label, "classifier": data_classifier,
                     "agt": data_agent, "dep": data_department}
        print(data_dict)

        self.search_results = self.connect_to_server(json.dumps(data_dict))

        # now show the search results
        # get back: id, label, agent, date, dep, classifiers
        data = self.search_results['data']
        print(data)
        strings = []
        # Refresh list widgets, in case we had previous search
        self.list_widget.clear()

        # object label, object date, comma separated list of all agents that produced the object,
        # part they produced, comma separated list of classifiers they used for the object

        for row in data:
            # ljust adds space to the right of the string
            # object label
            classifiers = row[5].split('|')
            classifier_string = ', '.join(classifiers)

            one_string = f"{row[1]}".ljust(250, ' ')
            # object date
            one_string += f"{row[3]}".ljust(40, ' ')

            # comma separated list of classifiers used for that object

            # part, agent
            part_agent = row[2].split("(")
            part_agent[1] = part_agent[1][:-1]

            one_string += part_agent[0].ljust(70, ' ')
            one_string += part_agent[1].ljust(70, ' ')

            one_string += classifier_string

            strings.append(one_string)
            item = QListWidgetItem(one_string)
            item.setFont(FW_FONT)
            # store data associated with that widget item (id)
            # for use in double click
            item.setData(Qt.UserRole, row[0])
            self.list_widget.addItem(item)

        # can delete this for loop once search is working
        print("")
        for string in strings:
            print(len(string))
            print(string)

    def parse_label_data(self, line_edit_object):
        """Function used to fetch text data from QLineEdit object.
        If empty string, replace with None to use in query."""
        input_data = line_edit_object.text()
        if input_data == "":
            input_data = None
        return input_data

    def list_item_clicked(self, item):
        """When list item is double clicked, display dialog."""
        # id, label, date
        selected_id = item.data(Qt.UserRole)

        data_dict = {"id": selected_id}
        # dialog_data is a dictionary
        dialog_data = self.connect_to_server(json.dumps(data_dict))
        dialog_data_obj_dict = dialog_data['object']
        dialog_data_agt_dict = dialog_data['agents']
        print(dialog_data)

        space_between_headers = "\n\n"
        res = ""
        # Object Information
        res += "Object Information\n"
        res += str(Table(["Accession No.", "Label", "Date", "Place"],
                         [[str(selected_id), dialog_data_obj_dict['label'],
                           dialog_data_obj_dict['date'], dialog_data_obj_dict['place']]]))
        # Produced By
        res += space_between_headers
        res += "Produced By\n"
        res += str(Table(["Part", "Name", "Nationalities", "Timespan"],
                         [[dialog_data_agt_dict[0][0], dialog_data_agt_dict[0][1],
                           dialog_data_agt_dict[0][3], dialog_data_agt_dict[0][2]]]))

        # Classification
        res += space_between_headers
        res += "Classification\n"
        res += ', '.join(dialog_data_obj_dict['classifier'])

        # Information
        res += space_between_headers
        res += "Information\n"
        # ref_rows is a list of list, with each element as a pair of ref type and ref content
        ref_rows = []
        for index, ref_type in enumerate(dialog_data_obj_dict['ref_type']):
            ref_rows.append(
                [ref_type, dialog_data_obj_dict['ref_content'][index]])
        res += str(Table(['Type', 'Content'], ref_rows))

        # Display dialog item
        dialog_item = FixedWidthMessageDialog("Title", res)
        dialog_item.setFont(FW_FONT)
        dialog_item.exec()

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
            return json.loads(response)
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
        if port < 0 or port > 65535:
            raise Exception
    except Exception as err:
        print("error: port must be an integer 0-65535", file=stderr)
        exit(1)

    LuxGUI(host, port)
