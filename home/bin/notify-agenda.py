#!/usr/bin/env python

from org_agenda import AgendaParser, HeadlineParser, mark_done

from datetime import datetime
from threading import Thread
import subprocess
import os
import stat
import io

FIFO = '/tmp/agenda.io'
NOTIFICATION_ID = str(0xd057)

def notification_id_inc():
    global NOTIFICATION_ID
    NOTIFICATION_ID = str(int(NOTIFICATION_ID) + 1)
def notification_id_reset():
    global NOTIFICATION_ID
    NOTIFICATION_ID = str(0xd057)

def make_fifo():
    global FIFO
    os.mkfifo(FIFO, 0o666)

def wait_action(proc, event):
    action = io.TextIOWrapper(proc.stdout, "utf-8").readline()
    if 'default' in action:
        mark_done(event.file, event.text)

def notify(event, expired = None):
    global NOTIFICATION_ID
    expire_time = str(1*60*1000)
    app_name = 'Org Agenda'
    title = event.type
    body = '<b>' + event.time + '</b> ' + event.text + '\n' + HeadlineParser(event.text).get_content()
    if expired != None:
        body += '\nEXPIRED FOR ' + str(-expired//60) + 'h ' + str(-expired%60) + 'm'
    proc = subprocess.Popen(['dunstify', 
        title, body, 
        '-a', app_name, 
        '-t', expire_time, 
        '-r', NOTIFICATION_ID,
        '-A', 'default,Mark DONE '+event.text], stdout=subprocess.PIPE)
    Thread(target = wait_action, args=(proc, event)).start()

def notify_work():
    agenda = AgendaParser().get_iter()
    for e in agenda:
        if e.time != '':
            date = e.date.split('-')
            if len(date) >= 3:
                day = int(date[2])
            else:
                day = datetime.now().day
            time = e.time.split('-')[0]
            (hour, minutes) = map(int, time.split(':'))
            time = hour*60 + minutes + (day - datetime.now().day)*60*24
            now = datetime.now().hour*60 + datetime.now().minute
            diff = time - now
            if 0 <= diff <= 10:
                print(diff)
                notify(e)
            if diff < 0:
                print(date)
                notify(e, diff)
            notification_id_inc()

def bar_work():
    agenda = AgendaParser().get_iter()
    if os.path.exists(FIFO):
        if not stat.S_ISFIFO(os.stat(FIFO).st_mode):
            make_fifo()
    else:
        make_fifo()

    event = None
    for e in agenda:
        if e.file == 'Study':
            event = e
            break
    if event == None:
        data = 'Chill'
    else:
        if event.time == '':
            time = 'Whole day'
        else:
            time = event.time
        data = time + ' ' + event.text

    open(FIFO, 'w').write(data + '\n')


if __name__ == '__main__':
    for i in range(10):
        proc = subprocess.Popen(['dunstify', '-C', NOTIFICATION_ID])
        notification_id_inc()
    notification_id_reset()
    bar_work()
    notify_work()
