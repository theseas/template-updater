#!/usr/bin/env python3
#-*- coding:utf-8 -*-

# activate virtual enviroment
env_path = "/home/theseas/bin/env3.9/bin/activate_this.py"
try:
    exec(open(env_path).read(), {'__file__':env_path})
except:
    stderr.write("Failed to activate virtual enviroment using "+env_path+" file. Exiting...\n");
    exit(4)

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
        self.table = kwargs['table']
        self.identifier = kwargs['identifier']
        self.field = kwargs['field']

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
                sql = 'update {0} set {2}=%s where {1}=%s'.format(self.table, self.identifier, self.field)
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
    parser.add_argument('-t', '--table', dest='table', nargs=1, help='DB table name');
    parser.add_argument('-i', '--identifier', dest='identifier', nargs=1, default='identifier', help='Table identifier field');
    parser.add_argument('-f', '--field', dest='field', nargs=1, default="template", help='DB template field');
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

    table = 'print_templates'
    if(args.table!=None):
        table = args.table[0]
    if(args.identifier!=None):
        identifier = args.identifier
    if(args.field!=None):
        field = args.field
    handler = FileHandler(db=db, table=table, identifier=identifier, field=field);
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
