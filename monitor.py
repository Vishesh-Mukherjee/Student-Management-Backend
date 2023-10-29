#!/bin/python3

import sqlite3
from tabulate import tabulate
from time import sleep
from os import system

conn = sqlite3.connect("database.db")
conn.row_factory = sqlite3.Row

def monitor(table_name):
    cursor = conn.execute(f"SELECT * FROM {table_name}")
    headers = list(map(lambda x: x[0], cursor.description))
    data = cursor.fetchall()
    rows = []
    for row in data:
        rows.append(row)
    print_table(rows, headers, table_name)

def print_table(rows, headers, table_name):
    print(table_name.upper())
    print(tabulate(rows, headers=headers, tablefmt="grid"), end="\n\n")

def run():
    while(True):
        try:
            monitor("class")
            monitor("enrollment")
            monitor("instructor")
            monitor("student")
        except Exception as e:
            print(e)
        sleep(1)
        system("clear")
        
run()
