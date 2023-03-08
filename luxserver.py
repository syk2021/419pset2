from contextlib import closing
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from sys import exit, argv, stderr
from os import name
import argparse
from query import LuxDetailsQuery, NoSearchResultsError, LuxQuery
import sys
import sqlite3
import json

DB_NAME = "./lux.sqlite"


class Server():
    """Class that represents a server connection that query the database"""

    def __init__(self, port):
        """Initalizes the server with the port being given and call a function to open the socket 
        and start listening.

        Args:
            port (int): port for server

        """

        self._port = port
        self.open_socket()

    def open_socket(self):
        """Open the socket, bind to the port and starts listening on the port"""

        # create a socket and bind to the port
        try:
            server_sock = socket()
            if name != 'nt':
                server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                server_sock.bind(('', self._port))
                server_sock.listen()

            self.handle_connection(server_sock)
        except Exception as ex:
            print(ex, file=stderr)
            exit(1)

    def handle_connection(self, server_sock):
        """Takes in a socket and accept a connection to the server and calls a function
        that handles the communication between server and client.

        Args:
            server_sock: server socket
        """

        # accept the connection and calls handle_client
        while True:
            try:
                sock, client_addr = server_sock.accept()
                with closing(sock):
                    print('Server IP address and port:', sock.getsockname())
                    print('Client IP address and port:', client_addr)
                    self.handle_client(sock)
            except Exception as ex:
                print(ex, file=stderr)

    def handle_client(self, sock):
        """Takes in a sock, read the input from the client, query the database 
        with the given args and returns to the client the query results. 

        If id is given, then we query by id otherwise we query by the filter (agt, dep, classifers, lebel)

        Args:
            sock: sock from server_sock
        """

        query_by_filter = LuxDetailsQuery(DB_NAME)
        query_by_id = LuxQuery(DB_NAME)

        # reads in from the client
        in_flo = sock.makefile(mode='r', encoding='utf-8')
        in_flo_input = in_flo.readline()
        in_flo_input = json.load(in_flo_input)

        print('\nRead from client id: ' + in_flo_input, end='')

        # query the database by id if given otherwise by filters
        try:
            if in_flo_input['id']:
                response = query_by_id.search(in_flo_input['id']) + "\n"
                client_response = f"Wrote to client: query by id"
            else:
                response = query_by_filter.search(agt=in_flo_input['agt'], dep=in_flo_input['dep'],
                                                  classifier=in_flo_input['classifier'], label=in_flo_input['label'])
                client_response = f"Wrote to client: query by filter "
        except NoSearchResultsError:
            response = "Invalid id\n"
            cilent_response = f"\nWrote to client: invalid id\n"
        except sqlite3.Error as err:
            response = str(err) + "\n"
            cilent_response = f"Wrote to client: {err}\n"

        # return the results of querying the database
        out_flo = sock.makefile(mode='w', encoding='utf-8')
        out_flo.write(response)
        out_flo.flush()

        print(cilent_response)


if __name__ == '__main__':

    # parse the port argument
    parser = argparse.ArgumentParser(
        prog='luxdetails.py', allow_abbrev=False, description='Server for the YUAG application')

    parser.add_argument(
        "port", help="the port at which the server should listen",)

    args = parser.parse_args()
    port = args.port

    # make sure that port is valid
    try:
        port = int(port)
        if port < 0:
            raise Exception
    except Exception as err:
        print("Port can only can be a positive integer", file=stderr)
        exit(1)

    # starts the server with the port
    try:
        Server(port)
    except Exception as err:
        print("The server has crashed, error: ", err, file=stderr)
        exit(1)
