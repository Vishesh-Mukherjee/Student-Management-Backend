#!/bin/python3

import sqlite3


def create_database():

    conn = sqlite3.connect("database.db")  
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            id VARCHAR(36) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            age TINYINT NOT NULL,
            PRIMARY KEY (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructor (
            id VARCHAR(36) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            age TINYINT NOT NULL,
            PRIMARY KEY (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS class (
            id VARCHAR(36) NOT NULL,
            instructor_id VARCHAR(36) NOT NULL,
            department VARCHAR(100) NOT NULL,
            course_code VARCHAR(8) NOT NULL,
            section_number TINYINT NOT NULL,
            class_name VARCHAR(100) NOT NULL,
            current_enrollment INTEGER NOT NULL,
            max_enrollment INTEGER NOT NULL,
            automatic_enrollment_frozen BOOLEAN NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (instructor_id) REFERENCES instructor(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollment (
            id VARCHAR(36) NOT NULL,
            student_id VARCHAR(36) NOT NULL,
            class_id VARCHAR(36) NOT NULL,
            enrolled_on DATE NOT NULL,
            dropped BOOLEAN NOT NULL,
            waiting_list BOOLEAN NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (class_id) REFERENCES class(id),
            FOREIGN KEY (student_id) REFERENCES student(id)
        )
    ''')
    
    conn.commit()
    conn.close()

create_database()
