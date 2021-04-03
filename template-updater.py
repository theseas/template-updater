#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import pyinotify as notif
import argparse
import mysql.connector
from sys import stderr
from getpass import getpass
from datetime import datetime
import atexit

class FileHandler(notif.ProcessEvent):
    def my_init(self, **kwargs):
        self.db = kwargs['db']

    def process_default(self, event):
        if(event.maskname=='IN_CLOSE_WRITE'):
            now = datetime.now()
            print('\nFile {0} changed at {1}!'.format(event.name, now.strftime('%H:%M:%S')));
            if(not event.name.endswith('.html')):
                print('Not an html template file.')
                return;
            filename = event.name[:-5];
            with open(event.pathname, 'r') as template:
                html = template.read();
                cursor = self.db.cursor()
                sql = 'update print_templates set template=%s where identifier=%s'
                try:
                    cursor.execute(sql, (html, filename));
                    self.db.commit()
                except Exception as e:
                    stderr.write(str(e) + '\n');
                    cursor.close()
                    self.db.close()
                    exit(3)
                print(cursor.rowcount, ' templates updated.');
                cursor.close()


def main():
    parser = argparse.ArgumentParser(description='db & tempalte to update');
    parser.add_argument('-u', '--user', dest='user', nargs=1, help='DB username');
    parser.add_argument('-p', '--password', dest='passwd', nargs='?', help='DB password');
    parser.add_argument('-H', '--host', dest='host', nargs='?', default='localhost', help='DB host');
    parser.add_argument('-D', '--database', dest='database', nargs=1, help='DB name');
    parser.add_argument('-d', '--directory', dest='dir', nargs='?', default='.', help='Path of the directory that contains the templates');
    args = parser.parse_args();

    if(args.passwd==None):
        args.passwd = getpass('Please enter your password: ');
    try:
        db = mysql.connector.connect(
                host=args.host,
                user=args.user[0],
                passwd=args.passwd,
                database=args.database[0]
        );
    except Exception as e:
        stderr.write(str(e) + '\n');
        exit(1);

    handler = FileHandler(db=db);
    wm = notif.WatchManager();
    notifier = notif.Notifier(wm, default_proc_fun=handler);
    atexit.register(cleanup, notifier, db)
    try:
        wm.add_watch(args.dir, notif.ALL_EVENTS, quiet=False);
        notifier.loop();
    except Exception as e:
        stderr.write(str(e) + '\n');
        notifier.stop();
        exit(2);

def cleanup(notifier, db):
    print('\rexiting...')
    notifier.stop()
    db.close()

if __name__=='__main__':
    main();
