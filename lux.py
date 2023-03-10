"""Module for the GUI client side of the application."""

import json
from json import JSONDecodeError
import argparse
import sys


from socket import socket
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QListWidget
from PySide6.QtWidgets import QMainWindow, QGridLayout, QPushButton, QLineEdit
from PySide6.QtWidgets import QListWidgetItem, QErrorMessage
from PySide6.QtCore import Qt

from dialog import FW_FONT, FixedWidthMessageDialog
from table import Table


class InvalidPortError(Exception):
    """Exception class to handle invalid port."""


class SearchingError(Exception):
    """Exception  class when server fail to get a valid response from database"""

    def __init__(self, error_type):
        super().__init__()
        self.err = error_type


class LuxGUI():
    """A GUI class for Lux."""

    def __init__(self, server_host, server_port, platform_os):
        """Initalizes the GUI with the given host and port
        and creates the neccessary widgets and frame for the GUI.

        Args:
            host (str): host to connect to
            port (int): port to connect to
            platform_os (str): OS of user
        """

        self._host = server_host
        self._port = server_port
        self._platform_os = platform_os

        self.app = QApplication(sys.argv)
        self.label = QLineEdit()
        self.classifier = QLineEdit()
        self.agent = QLineEdit()
        self.department = QLineEdit()
        self.layout = QGridLayout()
        self.frame = QFrame()
        self.window = QMainWindow()
        self.window.setWindowTitle("YUAG Application")
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
        search_button.clicked.connect(self.callback_search)

        # Sizing the screen
        screen_size = self.app.primaryScreen().availableGeometry()
        # Main window: no wider than 1/2 of width, 1/2 of height
        self.window.resize(screen_size.width()//2, screen_size.height()//2)

        # List of responses we get back
        self.layout.addWidget(self.list_widget, 8, 0)

        # self.original_keyPressEvent = self.window.keyPressEvent
        # set key press event
        self.window.keyPressEvent = self.on_enter

        self.layout.addWidget(self.list_widget, 8, 0)

        self.window.show()
        sys.exit(self.app.exec())

    def connect_to_server(self, data):
        """Connect lux to server and fetch the data sent from the server.

        Args:
            data (dict): user inputted arguments as a dictionary

        Return:
            json str
        """

        with socket() as sock:
            sock.connect((self._host, self._port))

            # write to the server
            out_flo = sock.makefile(mode='w', encoding='utf-8')
            out_flo.write(data + "\n")
            out_flo.flush()

            # read from the server
            in_flo = sock.makefile(mode='r', encoding='utf-8')
            response = in_flo.readline()

        try:
            response = json.loads(response)
        except JSONDecodeError as json_error:
            raise SearchingError(response) from json_error

        return response

    def parse_label_data(self, line_edit_object):
        """Function used to fetch text data from QLineEdit object.
        If empty string, replace with None to use in query.

        Args:
            line_edit_object: a line edit object

        Return:
            text data from QLineEdit object
        """

        input_data = line_edit_object.text()
        if input_data == "":
            input_data = None
        return input_data

    def callback_search(self):
        """Callback function that executes when user clicks search button.
        It connect to server with the inputted arguments,
        retrieves the data from the server, and parse the data returned.
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
        except SearchingError as err:
            self.error_message.showMessage(str(err.err))
            return
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
        print(self.search_results["data"])
        # switch order of nationalities and timespan
        search_table = Table(self.search_results["columns"], self.search_results["data"],
                             max_width=float('inf'), format_str=['w', 'w', 'w', 'w', 'w'])

        for index, row in enumerate(search_table):
            item = QListWidgetItem(''.join(row))
            item.setData(Qt.UserRole, self.search_results["data"][index][0])
            self.list_widget.addItem(item)

    def callback_list_item_enter(self, event):
        """Callback function for the list widget item that checks if the key press is enter 
        (command + O for Mac). 
        if so, it will treat it as if the item is double clicked.
        If the event is not enter, then it will treat the key press as normal.

        Args:
            event: event from GUI
        """

        # call regular function if key is not return or else will handle it like double click
        if (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_O
                and self._platform_os == "OS X"):
            try:
                self.callback_list_item(self.list_widget.selectedItems()[0])
            except IndexError:
                self.error_message.showMessage("Please select a field!")
        elif event.key() in [Qt.Key.Key_Return, Qt.Key_Enter]:
            try:
                self.callback_list_item(self.list_widget.selectedItems()[0])
            except IndexError:
                self.error_message.showMessage("Please select a field!")
        else:
            super(QListWidget, self.list_widget).keyPressEvent(event)

    def callback_list_item(self, item):
        """Callback function for when list item is double clicked, 
        display dialog with the object's information.

        Args:
            item: list object
        """

        selected_id = item.data(Qt.UserRole)

        data_dict = {"id": selected_id}

        # dialog_data is a dictionary
        try:
            dialog_data = self.connect_to_server(json.dumps(data_dict))
        except SearchingError as err:
            self.error_message.showMessage(str(err.err))
            return
        except Exception as err_message:
            self.error_message.showMessage(str(err_message))
            return

        dialog_data_obj_dict = dialog_data['object']
        dialog_data_agt_dict = dialog_data['agents']

        space_between_headers = "\n\n"
        res = ""

        # Object Information
        res += "Object Information\n"
        res += str(Table(["Accession No.", "Label", "Date", "Place"],
                         [[str(selected_id), dialog_data_obj_dict['label'],
                           dialog_data_obj_dict['date'], dialog_data_obj_dict['place']]],
                         max_width=150))
        # Produced By
        res += space_between_headers
        res += "Produced By\n"

        res += str(Table(["Part", "Name", "Nationalities",
                   "Timespan"], dialog_data_agt_dict, max_width=150))

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
        res += str(Table(['Type', 'Content'], ref_rows, max_width=150))

        # Display dialog item
        dialog_item = FixedWidthMessageDialog("Title", res)
        dialog_item.setFont(FW_FONT)
        dialog_item.exec()

    def on_enter(self, event):
        """Function to detect if enter key is pressed. 
        If the enter (command + O for Mac) key is pressed it will execute callback_search 
        if it's on on a list widget entry.

        Args:
            e: event
        """

        if (event.modifiers() == Qt.ControlModifier
                and event.key() == Qt.Key_O and self._platform_os == "OS X"):
            self.callback_search()
        elif event.key() in [Qt.Key.Key_Return, Qt.Key_Enter]:
            self.callback_search()


if __name__ == '__main__':

    # platform
    platforms = {
        'linux1': 'Linux',
        'linux2': 'Linux',
        'darwin': 'OS X',
        'win32': 'Windows'
    }

    # parse the data
    parser = argparse.ArgumentParser(
        prog='lux.py', description='Client for the YUAG application', allow_abbrev=False)

    parser.add_argument(
        "host", help="the host on which the server is running")

    parser.add_argument(
        "port", help="the port at which the server is listening")

    args = parser.parse_args()

    host = args.host
    port = args.port

    # ensure alid port
    try:
        port = int(port)
        if port < 0 or port > 65535:
            raise InvalidPortError
    except Exception as error_message:
        print("error: port must be an integer 0-65535", file=sys.stderr)
        sys.exit(1)

    # initalizes the GUI
    try:
        LuxGUI(host, port, platforms[sys.platform])
    except Exception as err_mess:
        print(f"The GUI has crashed: {err_mess}", file=sys.stderr)
