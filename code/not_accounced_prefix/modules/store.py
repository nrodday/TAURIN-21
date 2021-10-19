import mysql.connector
import configparser
import csv
import os.path
from pathlib import Path


config = configparser.ConfigParser()
config.read('config.ini')


# Usage
# testdata = {"test1": "asdf1", "test2": "asdf2", "testint1": 1, "testint2": "2"}
# insert("table", testdata)
def insert(table, data):
    try:
        mydb = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            database=config['mysql']['database'],
            password=config['mysql']['password']
        )

        mycursor = mydb.cursor()

        columns = []
        values = []

        for field in data:
            columns.append(field)
            values.append(data[field])

        col = "("+str(columns).split("[")[1].split("]")[0]+")"
        col = col.replace("'", "`")
        vals = str(values)[1:-1]

        command = "INSERT INTO " + table + " " + col + " VALUES (" + vals + ")"

        if config['general']['debug'] == "True":
            print(vals)
            print(command)

        mycursor.execute(command)
        mydb.commit()

        mycursor.close()
        mydb.close()

    except mysql.connector.errors.ProgrammingError as error:
        print("Something is wrong with the mysql configuration: "+str(error))
        raise ConnectionError("Could not connect to database!")
    except mysql.connector.errors.DatabaseError as error:
        print("Something is wrong with the mysql service: "+str(error))
        raise ConnectionError("Could not connect to database!")


# Usage
# testdata = {"test1": "asdf1", "test2": "asdf2", "testint1": 1, "testint2": "2"}
# write("hlavacek", data)
def write(methodology, data):
    columns = []

    for field in data:
        columns.append(field)

    Path("results").mkdir(parents=False, exist_ok=True)

    file_exists = os.path.isfile('results/' + methodology + '.csv')

    if not file_exists:
        with open('results/' + methodology + '.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()

            content = {}
            for field in data:
                content[field] = data[field]

            writer.writerow(content)
    else:
        with open('results/' + methodology + '.csv', 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)

            content = {}
            for field in data:
                content[field] = data[field]

            writer.writerow(content)
