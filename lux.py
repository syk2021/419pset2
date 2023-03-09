from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QListWidget
from PySide6.QtWidgets import QMainWindow, QGridLayout, QPushButton, QLineEdit
from PySide6.QtWidgets import QScrollBar, QListWidgetItem, QGridLayout, QErrorMessage
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
        """Initalizes the GUI with the given host and port and creates the neccessary widgets and frame for the GUI"""

        self._host = host
        self._port = port
        self._selected_id = None

        # self.search_results is a dictionary from json.loads()
        self.search_results = None

        self.app = QApplication(argv)
        self.label = QLineEdit()
        self.classifier = QLineEdit()
        self.agent = QLineEdit()
        self.department = QLineEdit()
        self.layout = QGridLayout()
        self.frame = QFrame()
        self.window = QMainWindow()
        self.error_message = QErrorMessage()

        self.list_widget = QListWidget()
        self.list_widget.setFont(FW_FONT)

        # When list widget item is clicked, display dialog
        self.list_widget.itemDoubleClicked.connect(self.callback_list_item)

        # Set layout on frame
        self.frame.setLayout(self.layout)

        # Set window title
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
        search_button.clicked.connect(lambda: self.callback_search())

        # Sizing the screen
        screen_size = self.app.primaryScreen().availableGeometry()
        # Main window: no wider than 1/2 of width, 1/2 of height
        self.window.resize(screen_size.width()//2, screen_size.height()//2)

        # List of responses we get back
        self.layout.addWidget(self.list_widget, 8, 0)
        scroll_bar = QScrollBar()
        scroll_bar.setStyleSheet("background lightgreen;")

        # Set the tab order for the labels and search button (TODO)
        self.window.setTabOrder(self.label, self.classifier)
        self.window.setTabOrder(self.classifier, self.agent)
        self.window.setTabOrder(self.agent, self.department)
        self.window.setTabOrder(self.department, search_button)

        # set key press event
        self.window.keyPressEvent = self.on_enter

        self.layout.addWidget(self.list_widget, 8, 0)

        self.window.show()
        exit(self.app.exec())

    def on_enter(self, e):
        """Callback function for when enter is pressed."""

        if e.key() == Qt.Key.Key_Return:
            self.callback_search()

    def callback_search(self):
        """Callback function that executes when user clicks search button.
        It connect to server with the inputted arguments, retrieves the data from the server, and parse the data returned.
        """

        # Parse the data inputted by the user and creates a dict for it
        data_label = self.parse_label_data(self.label)
        data_classifier = self.parse_label_data(self.classifier)
        data_agent = self.parse_label_data(self.agent)
        data_department = self.parse_label_data(self.department)
        data_dict = {"id": None, "label": data_label, "classifier": data_classifier,
                     "agt": data_agent, "dep": data_department}

        # Connect to the server and get back the results
        try:
            self.search_results = self.connect_to_server(json.dumps(data_dict))
        except Exception as err:
            self.error_message.showMessage(str(err))
            return

        # Error Handling for when search result is not present (TODO)
        if not self.search_results:
            self.error_message.showMessage(
                "The server has crashed")
            return

        # Now show the search results
        # Refresh list widgets, in case we had previous search
        self.list_widget.clear()
        search_table = Table(self.search_results["columns"], self.search_results["data"],
                             max_width=100000000, format_str=['w', 'w', 'w', 'w', 'w', 'w'])

        # Add ListWidgetItem for each row
        for index, row in enumerate(search_table):
            item = QListWidgetItem(''.join(row))
            item.setData(Qt.UserRole, self.search_results["data"][index][0])
            self.list_widget.addItem(item)

    def parse_label_data(self, line_edit_object):
        """Function used to fetch text data from QLineEdit object.
        If empty string, replace with None to use in query."""

        input_data = line_edit_object.text()
        if input_data == "":
            input_data = None
        return input_data

    def callback_list_item(self, item):
        """Callback function for when list item is double clicked, display dialog."""

        # id, label, date
        selected_id = item.data(Qt.UserRole)

        data_dict = {"id": selected_id}

        # dialog_data is a dictionary
        try:
            dialog_data = self.connect_to_server(json.dumps(data_dict))
        except Exception as err:
            self.error_message.showMessage(str(err))
            return

        dialog_data_obj_dict = dialog_data['object']
        dialog_data_agt_dict = dialog_data['agents']

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
        """Connect lux to server and fetch the data sent from the server"""

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


if __name__ == '__main__':

    # Parse the arguments
    parser = argparse.ArgumentParser(
        prog='lux.py', allow_abbrev=False)

    parser.add_argument(
        "host", help="the host on which the server is running")

    parser.add_argument(
        "port", help="the port at which the server is listening")

    args = parser.parse_args()

    host = args.host
    port = args.port

    # Ensure port is valid
    try:
        port = int(port)
        if port < 0 or port > 65535:
            raise Exception
    except Exception as err:
        print("Error: port must be an integer 0-65535", file=stderr)
        exit(1)

    # Set up the GUI
    LuxGUI(host, port)


class LuxGUI():
    """A GUI class for Lux."""

    def __init__(self, host, port):
        """Initalizes the GUI with the given host and port and creates the neccessary widgets and frame for the GUI"""

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
        self.error_message = QErrorMessage()
        # store selected id
        self._selected_id = None

        # self.search_results is a dictionary from json.loads()
        self.search_results = None
        self.list_widget = QListWidget()
        self.list_widget.setFont(FW_FONT)

        # When list widget item is clicked, display dialog
        self.list_widget.itemDoubleClicked.connect(self.callback_list_item)
        # install event filter for pressing enter in list widget item
        # self.list_widget.itemPressed.connect(self.callback_list_item_enter)
        self.list_widget.keyPressEvent = self.callback_list_item_enter
        # Set layout on frame
        self.frame.setLayout(self.layout)

        # Set window title
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
        search_button.clicked.connect(lambda: self.callback_search())

        # Sizing the screen
        screen_size = self.app.primaryScreen().availableGeometry()
        # Main window: no wider than 1/2 of width, 1/2 of height
        self.window.resize(screen_size.width()//2, screen_size.height()//2)

        # List of responses we get back
        self.layout.addWidget(self.list_widget, 8, 0)
        scroll_bar = QScrollBar()
        scroll_bar.setStyleSheet("background lightgreen;")

        # Set the tab order for the labels and search button (TODO)
        self.window.setTabOrder(self.label, self.classifier)
        self.window.setTabOrder(self.classifier, self.agent)
        self.window.setTabOrder(self.agent, self.department)
        self.window.setTabOrder(self.department, search_button)

        # set key press event
        self.window.keyPressEvent = self.on_enter

        self.layout.addWidget(self.list_widget, 8, 0)

        self.window.show()
        exit(self.app.exec())

    def on_enter(self, e):
        if e.key() == Qt.Key.Key_Return:
            self.callback_search()

    def callback_search(self):
        """Callback function that executes when user clicks search button.
        It connect to server with the inputted arguments, retrieves the data from the server, and parse the data returned."""

        # Parse the data inputted by the user and creates a dict for it
        data_label = self.parse_label_data(self.label)
        data_classifier = self.parse_label_data(self.classifier)
        data_agent = self.parse_label_data(self.agent)
        data_department = self.parse_label_data(self.department)
        data_dict = {"id": None, "label": data_label, "classifier": data_classifier,
                     "agt": data_agent, "dep": data_department}

        # Connect to the server and get back the results
        try:
            self.search_results = self.connect_to_server(json.dumps(data_dict))
        except Exception as err:
            self.error_message.showMessage(str(err))
            return

        # Error Handling for when search result is not present (TODO)
        if not self.search_results:
            self.error_message.showMessage(
                "The server has crashed")
            return

        # Now show the search results
        # Refresh list widgets, in case we had previous search
        self.list_widget.clear()
        search_table = Table(self.search_results["columns"], self.search_results["data"],
                             max_width=100000000, format_str=['w', 'w', 'w', 'w', 'w', 'w'])

        for index, row in enumerate(search_table):
            item = QListWidgetItem(''.join(row))
            item.setData(Qt.UserRole, self.search_results["data"][index][0])
            self.list_widget.addItem(item)

    def parse_label_data(self, line_edit_object):
        """Function used to fetch text data from QLineEdit object.
        If empty string, replace with None to use in query."""

        input_data = line_edit_object.text()
        if input_data == "":
            input_data = None
        return input_data

    def callback_list_item_enter(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.callback_list_item(self.list_widget.selectedItems()[0])

    def callback_list_item(self, item):
        """Callback function for when list item is double clicked, display dialog."""

        selected_id = item.data(Qt.UserRole)

        data_dict = {"id": selected_id}

        # dialog_data is a dictionary
        try:
            dialog_data = self.connect_to_server(json.dumps(data_dict))
        except Exception as err:
            self.error_message.showMessage(str(err))
            return

        dialog_data_obj_dict = dialog_data['object']
        dialog_data_agt_dict = dialog_data['agents']

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
        """Connect lux to server and fetch the data sent from the server"""

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


# Question - once we query the data,and the server disocnnect, should we still be able to display it?
