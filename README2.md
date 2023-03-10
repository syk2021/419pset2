# Pset 2: Desktop GUI Application

# CPSC 419 PSET 2 PARTNER GROUP 9

Group members: Sophia Kang (yk575), Phuc Duong (phd24)

## Contributions
Sophia Kang Contribution:
- Creating all the required widgets in the GUI
- Parsing the arguments inputted by the user into JSON
- Parsing the data recieved from the server to display in the GUI
- Changing the query to conform to new specs
- pylint on lux.py, query.py, lux_query_sql.py, luxserver.py
- writing docstrings for classes and functions

Phuc Duong contribution:
- Setting up the server by creating the socket, listening and reading in the data
- Parse database results into JSON
- Return JSON data to the client
- Error handling with try except clauses in server and GUI
- pylint on lux.py, query.py, lux_query_sql.py, luxserver.py
- writing docstrings for classes and functions
- readme documentation


## Description of outside help
ULA office hours (parsing data to GUI)

## Description of sources of information that you used while doing the assignment, not direct help from people
None

## Indication of how much time you spent doing the assignment, rounded to the nearest hour
15 hours

## Assessment of the assignment
- Did it help you to learn? / What did it help you to learn?

Network:

It helped us learned how to setup a server in python, listen on a specfic port, read input from the client, and then send information to the client.
Futheremore, it helps us learn how to convert data in to a JSON format in python.

GUI:

It helps learn how to setup widgets, position widgets, and format the data necessary to display to the GUI. 
It also helped us get familar with callback function and understand how to implement it with widgets and GUI.
Overall, it help us get familar with the inversion controlaspect of GUI programming,


- Do you have any suggestions for improvement? Etc.

The specs can be more organized. Information on what is needed should be in one place, rather than all over the README documentation.
For us it seems like whenever we finished one thing, we found more hidden details in the specs that need to be added.

## Any information to graders
For query.py, we have a pylint error that says too many local variables, but we only exceeded the limit by 1 or 3 and have tried to eliminate local variables without making the code unreadable. There is an error with the number of arguments from LuxDetailsQuery, because we inherit from the Query class, but we think this is negligible for the most part. 

For luxserver.py, and lux.py we get a broad-exception-caught error. However, this is extended behavior as we are trying to exit the program safely we want to try to catch a general exception just in case. We have specific exception already when neccessary.

For lux.py, we have too many instance attribute, however this is needed to make the GUI. We also have a lambda may not be necessary, but it's necessary to how the callback works. We also get a super error, for passing in QListWidget, but that is needed for the up and down arrow traversing in a list feature of our program. Finally, we get a redefining err_mess from outer


For all the files we might an import error. However, the import is correct as our program is running proprely so we believe this an error on pylint side.



We have no errors for lux.py, luxdetails.py, and lux_query_sql.py.