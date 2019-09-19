import MySQLdb

dbh = MySQLdb.connect(host="mysqlprod01.austin.utexas.edu",
                      port="3306",
                      user="myUsername",
                      passwd="myPassword",
                      db="myDatabase")
