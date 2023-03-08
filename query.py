"""Module handling queries for the database."""

from contextlib import closing
from sqlite3 import connect
from datetime import datetime
import json
import sqlite3
from lux_query_sql import QUERY_LUX


class NoSearchResultsError(Exception):
    """Exception class to handle no search results."""


class Query():
    """Abstract Query Class for querying databases.
    Query should be instantiated as LuxQuery or LuxDetailsQuery.
    """

    def __init__(self):
        raise NotImplementedError

    def search(self):
        """Function that executes the query."""

        raise NotImplementedError

    def clean_data(self, data):
        """Function used to clean data."""

        raise NotImplementedError

    def format_data(self, data):
        """Function used to format data."""

        raise NotImplementedError


class LuxQuery(Query):
    """"Class to represent querying the database.
    Stores the database file for opening connection to later on.
    Stores the columns for the output table.
    """

    def __init__(self, db_file):
        """Initalizes the class with the database file and
        the columns and format_str for the output table.
        Args:
            db_file (str): database file
        """

        self._db_file = db_file
        self._columns = ["ID", "Label", "Produced By",
                         "Date", "Member Of", "Classified As"]
        self._format_str = ["w", "w", "w", "w", "w", "p"]

    def search(self, dep=None, agt=None, classifier=None, label=None):
        """Opens a connection to the database and uses the given argument to create a
        SQL statement that query the database satisfying the search criteria.
        Args:
            dep (str): selected department
            agt (str): selected agent
            classifer: selected slassifer
            label: selected label
        Return:
            list: numbers of items returned from query (search count),
            columns for Table, a list of objects
        Arguments are by default None if not passed in.
        If no arguments are passed in output includes first 1000 objects in the database.
        Sort Order:
            Sorted first by object label/date, then by agent name/part,
            then by classifier, then by department name.
        """

        with connect(self._db_file, isolation_level=None, uri=True) as connection:
            with closing(connection.cursor()) as cursor:
                # making query backbone to be used in each of the 4 queries below
                smt_str = QUERY_LUX
                smt_count = 0
                smt_params = []

                # WHERE clause
                if dep or label or agt or classifier:
                    smt_str += " WHERE"
                if dep:
                    smt_str += " department.dep_name LIKE ?"
                    smt_params.append(f"%{dep}%")
                    smt_count += 1
                if label:
                    if smt_count >= 1:
                        smt_str += " AND"
                    smt_str += " objects.label LIKE ?"
                    smt_params.append(f"%{label}%")
                    smt_count += 1
                if agt:
                    if smt_count >= 1:
                        smt_str += " AND"
                    smt_str += " agent.artist LIKE ?"
                    smt_count += 1
                    smt_params.append(f"%{agt}%")
                if classifier:
                    if smt_count >= 1:
                        smt_str += " AND"
                    smt_str += " classifier.classification LIKE ?"
                    smt_count += 1
                    smt_params.append(f"%{classifier}%")

                smt_str += " GROUP BY objects.id, objects.label"

                # create the sort order for the query based on present args
                sort_str = " ORDER BY objects.label, objects.date, "
                sort_list = []
                params_list = {
                    agt: 'agent.artist',
                    classifier:  'classifier.classification',
                    dep: 'department.dep_name',
                }

                for key, value in params_list.items():
                    if key:
                        sort_list.append(value)

                for key, value in params_list.items():
                    if not key:
                        sort_list.append(value)

                param_sort_str = sort_str + ", ".join(sort_list)
                smt_str += param_sort_str
                smt_str += " LIMIT 1000"

                # execute the statement and fetch the results
                cursor.execute(smt_str, smt_params)
                data = cursor.fetchall()
                search_count = len(data)

        return self.convert_to_json(self, search_count, data)

    def convert_to_json(self, search_count, data):
        database_response = {
            "search_count": search_count,
            "columns": self._columns,
            "format_str": self._format_str,
            "data": data
        }

        return json.dumps(database_response)

    def format_data(self, data):
        pass

    def clean_data(self, data):
        pass


class LuxDetailsQuery(Query):
    """"Class to represent querying the database.
    Stores the database file for opening connection to later on.
    Stores the columns for the output table.
    """

    def __init__(self, db_file):
        self._db_file = db_file
        self._columns_produced_by = [
            "Part", "Name", "Timespan", "Nationalities"]
        self._columns_information = ["Type", "Content"]
        self._format_str_produced = ["w", "w", "p", "w"]
        self._format_str_information = ["w", "w"]

    def search(self, obj_id):
        with connect(self._db_file, isolation_level=None, uri=True) as connection:
            with closing(connection.cursor()) as cursor:
                # objects.label, productions.part, agents.name, nationalities.descriptor,
                # agents.begin_date, agents.end_date, classifiers.name
                smt_str = "SELECT DISTINCT objects.label, productions.part, agents.name,"
                smt_str += "agents.begin_date, agents.end_date,"
                smt_str += " nationalities.descriptor, classifiers.name,"
                smt_str += " \"references\".type, \"references\".content, agents.id"
                # joining objects and agents using productions
                smt_str += " FROM objects LEFT OUTER JOIN"
                smt_str += " productions ON productions.obj_id = objects.id"
                smt_str += " LEFT OUTER JOIN agents on productions.agt_id = agents.id"
                # joining nationalities using agents_nationalities
                smt_str += " LEFT OUTER JOIN agents_nationalities"
                smt_str += " ON agents_nationalities.agt_id = agents.id"
                smt_str += " LEFT OUTER JOIN nationalities ON"
                smt_str += " nationalities.id = agents_nationalities.nat_id"
                # joining references
                smt_str += " LEFT OUTER JOIN \"references\" ON \"references\".obj_id = objects.id"
                # joining classifiers using objects_classifiers
                smt_str += " LEFT OUTER JOIN objects_classifiers ON"
                smt_str += " objects_classifiers.obj_id = objects.id"
                smt_str += " LEFT OUTER JOIN classifiers"
                smt_str += " ON classifiers.id = objects_classifiers.cls_id"
                smt_str += " WHERE objects.id = ?"
                smt_params = [obj_id]

                # execute the statement and fetch the results
                cursor.execute(smt_str, smt_params)
                data = cursor.fetchall()
                if not data:
                    raise NoSearchResultsError

        # data formatting
        agent_dict, obj_dict = self.clean_data(data)
        agent_rows_list = self.format_data(agent_dict)
        return self.convert_to_json(agent_rows_list, obj_dict)

    def convert_to_json(self, agents_list, obj_dict):
        database_response = {
            "columns_produced_by": self._columns_produced_by,
            "columns_information": self._columns_information,
            "format_information": self._format_str_information,
            "format_produced": self._format_str_produced,
            "agents": agents_list,
            "object": obj_dict
        }

        return json.dumps(database_response)

    def format_data(self, data):
        """Transform each agent's dictionary into a list to fit the Table class requirements.
        Args:
            data (dict): dictionary of all the agents
        Returns:
            rows_list (list): a list with each object as a list which is a "row" in the Table
        """

        rows_list = []

        # loop through each obj in dictionary and convert the obj's dictionary to a list
        for key in data:

            # no more than 1000 objects in output
            if len(rows_list) == 1000:
                break

            # join appropriate strings together
            if data[key]["nationality"] and data[key]["nationality"][0]:
                data[key]["nationality"] = "|".join(data[key]["nationality"])
            else:
                data[key]["nationality"] = ""

            rows_list.append(list(data[key].values()))

        return rows_list

    def clean_data(self, data):
        """Creates dictionaries for the object queried and the agents associated with that object
        with their relevant information
        (label, part_produced, produced_by, nationality, begin_date, end_date,
        classifier, ref_type, ref_content, agent_id).
        Stores them in master dictionaries (obj_dict, agent_dict). agent_dict has agent's id as key.
        Args:
            data (list): data returned from cursor.fetchall()
        Returns:
            agent_dict (dict):
                key: agent's id
                value: dictionary with all information relevant to the agent
            obj_dict (dict):
                value: dictionary with all information relevant to the obhect
        """

        # master dictionary
        agent_dict = {}
        obj_dict = {}

        # loop through each row in the data, get the relevant data,
        # and store them in the dictionary for the relevant object
        for row in data:
            label = row[0]
            part_produced = row[1]
            produced_by = row[2]
            begin_date = row[3]
            end_date = row[4]
            nationality = row[5]
            classifier = row[6]
            ref_type = row[7]
            ref_content = row[8]
            agent_id = row[9]

            timespan = self.parse_date(begin_date, end_date)

            # create dictionary for object if not already done
            if not obj_dict:
                obj_dict = {
                    "label": label,
                    "classifier": [classifier],
                    "ref_type": [ref_type],
                    "ref_content": [ref_content]
                }
            # if dictionary has already been created, then we append classifiers
            else:
                if classifier not in obj_dict["classifier"]:
                    obj_dict['classifier'].append(classifier)
                # if ref_type not in obj_dict['ref_type'] and :
                obj_dict['ref_type'].append(ref_type)
                if ref_content not in obj_dict['ref_content']:
                    obj_dict['ref_content'].append(ref_content)
                else:
                    if ref_type:
                        obj_dict['ref_type'].pop()

            # if agent has not been stored in agent_dict yet
            if agent_id not in agent_dict:
                agent_dict[agent_id] = {
                    "part": part_produced,
                    "name": produced_by,
                    "timespan": timespan,
                    "nationality": [nationality],
                }
            # if agent has information stored in dictionary, then we append nationality
            else:
                if nationality not in agent_dict[agent_id]['nationality']:
                    agent_dict[agent_id]['nationality'].append(nationality)

        return agent_dict, obj_dict

    def parse_date(self, begin_date, end_date):
        """Given a begin_date (str) and end_date (str)
        formats the timespan needed for table in the form of {begin_year}-{end_year}.
        """

        begin_year = ""
        end_year = ""

        if begin_date:
            begin_date_dt = datetime.strptime(begin_date, '%Y-%m-%d')
            begin_year = begin_date_dt.year

        if end_date:
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_year = end_date_dt.year

        return f"{begin_year}-{end_year}"
