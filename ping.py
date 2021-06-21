from pythonping import ping
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
import configparser
import time
import sys
import os
import datetime
import sqlite3
from sqlite3 import Error

obj = {}
event_logs = {}

cfg = configparser.RawConfigParser()
cpath = os.path.join(sys.path[0], "config.ini")
cfg.read(cpath)

DATABASE_PATH = cfg.get('PATHS', 'Database')
XML_PATH = cfg.get('PATHS', 'XML')
EVENTXML_PATH = cfg.get('PATHS', 'EventLogXML')
CHECK_INTERVAL = int(cfg.get('TIMER', 'CheckInterval'))


def create_connection(db):
    """ Initiates connection to the database and pulls database into dictionary on lanch """
    global obj
    global event_logs
    conn = None
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c2 = conn.cursor()
        c.execute('SELECT * FROM servers')
        obj = {'servers': [dict(row) for row in c.fetchall()]}
        c2.execute('SELECT * FROM events')
        event_logs = {'events': [dict(row) for row in c2.fetchall()]}
    except Error as e:
        print(f'Connection error: {e}')
    finally:
        if conn:
            conn.close()


def update_event_dict():
    global event_logs
    """ Updates the event_log after every event """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM events')
        event_logs = {'events': [dict(row) for row in c.fetchall()]}
    except Error as e:
        print(f'Event update error: {e}')
    finally:
        if conn:
            conn.close()


def write_db(data, sql):
    """ Writes the timestamp only on status change """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
    except Error as e:
        print(f'Write error: {e}')
    finally:
        if conn:
            conn.close()


def write_to_file(path, data):
    """ Write to event log or XML file """
    with open(path, 'w') as f:
        f.write(data)


def change_status(i, dt, online):
    """ Changing status online or offline """
    if i['attempt'] >= 2:  # After three conflicting checks in a row, change status
        if online:
            now = datetime.datetime.now()
            dt_string = now.strftime("%B %d, %Y %#I:%M %p")
            sql = ''' INSERT INTO events(name,date,duration) VALUES(?,?,?) '''
            write_db((i['name'], str(dt_string), str(datetime.timedelta(seconds=(dt - i['time'])))), sql)
            update_event_dict()
        i['status'] = 'online' if online else 'offline'
        i['css'] = 'table-success' if online else 'table-danger'
        i['time'] = dt
        i['attempt'] = 0
        sql = ''' UPDATE servers SET time = ?, status = ?, css = ? WHERE name = ? '''
        write_db((dt, i['status'], i['css'], i['name']), sql)
    else:
        i['attempt'] += 1


def monitor_ping(sec):
    while True:
        for i in obj['servers']:
            now = datetime.datetime.now()
            dt = int(datetime.datetime.timestamp(now))
            r = ping(i['ip'], count=1)
            if r.success() and i['status'] == 'online':
                i['attempt'] = 0
            elif r.success() and i['status'] != 'online':  # An OK check and previous check was NOT OK
                change_status(i, dt, True)
            elif not r.success() and i['status'] == 'offline':
                i['attempt'] = 0
            elif not r.success() and i['status'] != 'offline':  # A NOT OK check and previous check was OK
                change_status(i, dt, False)
            i['duration'] = str(datetime.timedelta(seconds=(dt - i['time'])))  # Writes datetime readable for dict > XML
            sql = ''' UPDATE servers SET duration = ?, attempt = ? WHERE name = ? '''
            write_db(((dt - i['time']), i['attempt'], i['name']), sql)  # Writes datetime as seconds for database
        xml = dicttoxml(obj, attr_type=False)
        eventxml = dicttoxml(event_logs, attr_type=False)
        write_to_file(EVENTXML_PATH, parseString(eventxml).toprettyxml())
        write_to_file(XML_PATH, parseString(xml).toprettyxml())
        time.sleep(sec)


if __name__ == '__main__':
    create_connection(DATABASE_PATH)
    monitor_ping(CHECK_INTERVAL)
