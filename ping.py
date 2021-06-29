from pythonping import ping
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
import configparser
import time
import sys
import os
import datetime
import sqlite3
import smtplib
import ssl
import json
from sqlite3 import Error
from email.message import EmailMessage

obj = {}
event_logs = {}

cfg = configparser.RawConfigParser()
cpath = os.path.join(sys.path[0], "config.ini")
cfg.read(cpath)

DATABASE_PATH = cfg.get('PATHS', 'Database')
XML_PATH = cfg.get('PATHS', 'XML')
EVENTXML_PATH = cfg.get('PATHS', 'EventLogXML')
CHECK_INTERVAL = int(cfg.get('TIMER', 'CheckInterval'))

SMTP_SERVER = cfg.get('SMTP', 'Server')
SMTP_PORT = cfg.get('SMTP', 'Port')
SMTP_PASS = cfg.get('SMTP', 'Password')
SMTP_SENDER = cfg.get('SMTP', 'SenderEmail')
SMTP_RECEIVER = [e.strip() for e in cfg.get('SMTP', 'Receivers').split(',')]
SMTP_ENABLED = bool(cfg.get('SMTP', 'SendUpdates'))


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
        event_logs = [dict(row) for row in c2.fetchall()]
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
        event_logs = [dict(row) for row in c.fetchall()]
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
    """ Write to XML file """
    with open(path, 'w') as f:
        f.write(data)


def write_json(path, data):
    """ Write event log json """
    with open(path, 'w') as f:
        json.dump(data, f)


def change_status(i, dt, online):
    """ Changing status online or offline """
    if i['attempt'] >= 2:  # After three conflicting checks in a row, change status
        now = datetime.datetime.now()
        dt_string = now.strftime("%B %d, %Y %#I:%M %p")
        if online:  # We're coming back online, so write an event to know how long it was down
            sql = ''' INSERT INTO events(name,date,duration) VALUES(?,?,?) '''
            write_db((i['name'], str(dt_string), str(datetime.timedelta(seconds=(dt - i['time'])))), sql)
            update_event_dict()
        i['status'] = 'online' if online else 'offline'
        i['css'] = 'table-success' if online else 'table-danger'
        i['time'] = dt
        i['attempt'] = 0
        sql = ''' UPDATE servers SET time = ?, status = ?, css = ? WHERE name = ? '''
        write_db((dt, i['status'], i['css'], i['name']), sql)
        send_alert(i, dt_string, online)
    else:
        i['attempt'] += 1


def send_alert(i, dt_string, online):
    if SMTP_ENABLED:
        msg = EmailMessage()
        msg['From'] = SMTP_SENDER

        if online:
            msg['Subject'] = 'Ping Alert: UP'
            msg.set_content(f'Host is back online: {i["name"]} has been restored at {dt_string}')
        else:
            msg['Subject'] = 'Ping Alert: DOWN'
            msg.set_content(f'Host is down: {i["name"]} is not replying at {dt_string}')

        context = ssl.create_default_context()
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

        try:
            server.ehlo()
            server.starttls(context=context)  # Secure the connection
            server.ehlo()
            server.login(SMTP_SENDER, SMTP_PASS)
            for i in SMTP_RECEIVER:
                msg['To'] = i
                server.send_message(msg)
        except Exception as e:
            print(f'Error sending email: {e}')
        finally:
            server.quit()
    else:
        pass


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
        write_json(EVENTXML_PATH, event_logs)
        write_to_file(XML_PATH, parseString(xml).toprettyxml())
        time.sleep(sec)


if __name__ == '__main__':
    create_connection(DATABASE_PATH)
    monitor_ping(CHECK_INTERVAL)
