# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 23:47:44 2020

@author: Amit
"""

import requests
import pandas as pd
from flask  import Flask, request, session, redirect, jsonify
from flask_cors import CORS
import json, signal
import sqlite3
from sqlite3 import Error as db_conn_error
#import properties
import os.path

# Object to contain teacher each record
class teacher_detail:
    def __init__(self,fname,lname,profpic,email,phone,room,subjects):
        self.fname = fname
        self.lname = lname
        self.profpic = profpic
        self.email = email
        self.phone = phone
        self.room = room
        self.subjects = subjects

# Profile picture to be converted to binary to store in database
def convertToBinaryData(filename):
    #Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData


# Check if profile picture is present, if not then default picture to be provided
def check_photo_to_blob(photo_id):
    # If profile picture is not present
    if 'JPG' not in photo_id.upper() or 'PNG' not in photo_id.upper():
        print('Amit')
        photo = 'amit.JPG'
    else:
        # If profile picture is present
        photo = photo_id
    photo_path = str("C:\\Amit\\Tech Test\\teachers\\") + photo
    # If profile picture is provided but physically the file is not present then assign default photo
    if not os.path.isfile(photo_path):
        photo_path = str("C:\\Amit\\Tech Test\\teachers\\") + 'amit.JPG'
    bin_Photo = convertToBinaryData(photo_path)  
    return bin_Photo

# Check if there reteacher data is already present in database
def check_teacher_in_db(curr, fname,lname,emailid):
    check_qiery = """select exists (select 1 from teachers where 
                    firstname = ?);"""
    if_exist = curr.execute("select * from teachers where email = ?",(emailid))
    # If need to check with some more conditions then below line can be used instead
    #if_exist = curr.execute("select * from teachers where firstname=? and lastname = ? and email = ?",(fname,lname,emailid))
    id_exists = if_exist.fetchone()
    #print(if_exist.fetchone()[0])
    if id_exists:
        return True
    else:
        return False
    #ret_result = if_exist.fetchone()[0]
    #return if_exist.fetchone()

# To retrieve the list of teacher details
def search_teacher_result(curr, query):
    curr.execute(query)
    results = curr.fetchall()
    ret_teachers = []
    for row in results:
        ret_teachers.append(teacher_detail(row[0],row[1],row[2],row[3],row[4],row[5],row[6]))
    return ret_teachers

# No of subjects should be no more than 5
def check_if_5_subs(subs):
    sub_list = subs.split(',')
    no_of_sub = len(sub_list)
    if no_of_sub > 0 and no_of_sub < 6:
        return True
    else:
        return False

# Creation of SQLite DB connection
def create_db_conn_sqlite(db_file_path):
    try:
        # Connecting SQLite local database
        conn = sqlite3.connect(db_file_path)
    except db_conn_error as err:
        print(err)
    return conn

# creation of DB connection mentioning DB file    
def get_DB_Connection():
    dbfile = r"C:\Amit\DB\newdb.db"
    conn = create_db_conn_sqlite(dbfile)
    curr = conn.cursor()
    return curr,conn

# Initiation of Flask    
app = Flask(__name__)
CORS(app)

# For bulk import from CSV file
@app.route('/bulkimport',methods=['GET'])
def bulk_import():
    if 'csvfile' in request.args:
        filepath = request.args['csvfile']
        print('within IF')
    #teacher_file_csv = pd.read_csv("C:\\Amit\\Tech Test\\Teachers.csv")
        teacher_file_csv = pd.read_csv(filepath)
    else:
        # If file path is not provided then this code can be tested by mentioning default path
        print('Within ELSE')
        teacher_file_csv = pd.read_csv("C:\\Amit\\Tech Test\\Teachers.csv")
    #print(teacher_file_csv)
    # Removing spaces from column headings
    teacher_file_csv.rename(columns={"First Name":"First_Name",
                                     "Last Name":"Last_Name",
                                     "Profile picture":"Profile_picture",
                                     "Email Address":"Email_Address",
                                     "Phone Number":"Phone_Number",
                                     "Room Number":"Room_Number",
                                     "Subjects taught":"Subjects"},
                            inplace = True)
    #print(teacher_file_csv)
    curr,conn = get_DB_Connection()
    for row in teacher_file_csv.itertuples():
        
        teacher_photo = check_photo_to_blob(str(row.Profile_picture))
        
        # Creation of data tuple to insert into table
        data_tuple = (str(row.First_Name),str(row.Last_Name), 
                      teacher_photo, str(row.Email_Address),str(row.Phone_Number),
                      str(row.Room_Number),str(row.Subjects))
        
        # Check if the teacher is already exists
        teacher_exists = check_teacher_in_db(curr, str(row.First_Name),
                                             str(row.Last_Name),
                                             str(row.Email_Address))
        
        # Call subject checks to verify number of subject should be no lesser than 5
        subject_checks = check_if_5_subs(str(row.Subjects))
        if subject_checks:
            if teacher_exists:
                print("Teacher is already available in database")
            else:
                sqlite_insert_blob_query = """ INSERT INTO teachers(firstname, lastname, profilepic, email,phone, roomno,subjects) VALUES (?, ?, ?, ?,?,?,?)"""
                curr.execute(sqlite_insert_blob_query, data_tuple)
                conn.commit()
                print("Image and file inserted successfully as a BLOB into a table")
        else:
            print("More than 5 subjects are not allowed")
    curr.close()
    print('All insertion completed')
    return True

# In case of insertion of single teacher record from front end
@app.route('/singletone',methods=['GET'])
def singleinsert():
    if 'fname' in request.args:
        fname = request.args['fname']
    if 'lname' in request.args:
        lname = request.args['lname']
    if 'photo' in request.args:
        photo = request.args['photo']
        # Check profile picture availability
        teacher_photo = check_photo_to_blob(photo)

    if 'email' in request.args:
        email = request.args['email']
    else:
        ret_msg = 'Enter email ID'
    if 'phone' in request.args:
        phone = request.args['phone']
    if 'room' in request.args:
        room = request.args['room']
    if 'subs' in request.args:
        subjects = request.args['subs']
        subject_checks = check_if_5_subs(subjects)
        if not subject_checks:
            ret_msg = 'Enter only 5 subjects'        
    curr,conn = get_DB_Connection()
    teacher_exists = check_teacher_in_db(curr, fname,
                                             lname,
                                             email)
    data_tuple = (fname,lname, 
                      teacher_photo, email,phone,
                      room,subjects)
    if subject_checks:
        if teacher_exists:
            print("Teacher is already available in database")
        else:
            sqlite_insert_blob_query = """ INSERT INTO teachers(firstname, lastname, profilepic, email,phone, roomno,subjects) VALUES (?, ?, ?, ?,?,?,?)"""
            curr.execute(sqlite_insert_blob_query, data_tuple)
            conn.commit()
            print("Image and file inserted successfully as a BLOB into a table")
    else:
        print("More than 5 subjects are not allowed")
    curr.close()

@app.route('/searchteacher',methods=['GET'])
def search_teacher():
    search_by = ''
    if 'lname' in request.args:
        lname_char = request.args['lname']
        search_by = 'lname'
    else:
        search_by = 'subject'
    if 'subs' in request.args:
        sub = request.args['subs']
        search_by = 'subject'
    else:
        search_by = 'lname'
    
    curr,conn = get_DB_Connection()
    # Searching based on last name starting character(s)
    if search_by == 'lname':
        query = "select * from teachers where lastname like '" + str(request.args['lname']) + "%'"
    
    # Searching based on subject(single subject wise search is coded)
    if search_by == 'subject':
        query = "select * from teachers where subjects like '" + str(request.args['subs']) + "%'" + "or subjects like '%," + str(request.args['subs']) + "%'" 
    teacher_output = search_teacher_result(curr,query)
    return teacher_output

app.run()
















