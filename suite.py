import subprocess
import os
import argparse
import json
import project
import sqlite3
import datetime
from operator import itemgetter


def extract_list(makeloc):
    targetlist = []
    with open(makeloc + "/compile_commands.json") as cjson:
        data = json.load(cjson)
        debug_i = 0
        for p in data:
            debug_i += 1
            if debug_i > 40:
                break
            targetlist.append(p['file'])
    return targetlist


def is_same_match(x, y):
    for it in range(0, 5):
        if x[it] != y[it]:
            return False
    return True


def execute_find_type(tlist, pname, delim=";", linedelim="@", config="conf.json"):
    matchlist = []
    for target in tlist:
        t = subprocess.check_output(["find-type", target.rstrip(), "-config=" + config]).decode("utf-8").rstrip()
        for m in t.split(linedelim):
            m = m.replace('\n', '')
            m = m.replace(os.getcwd() + '/' + pname, '')
            elem = m.split(delim)
            if len(elem) == 6 and elem[5] == '':
                elem[5] = 'null'
            foundsame = False
            if len(elem) > 4:
                for match in matchlist:
                    if is_same_match(elem, match):
                        foundsame = True
                        match[5] = match[5] + delim + elem[5]
                if not foundsame:
                    matchlist.append(elem)
    return matchlist


def write_csv(matchlist, output="result", delim=";"):
    sortedlist = sorted(matchlist, key=itemgetter(0, 1, 2, 3))
    f = open("data/" + output + ".csv", "w")
    f.write("MatchType" + delim + "File" + delim + "Line" + delim + "Column" + delim + "Code" + delim + "Files \n")
    f.close()
    f = open("data/" + output + ".csv", "a")
    for match in sortedlist:
        for i in match:
            f.write(i)
            f.write(delim)
        f.write("\n")
    f.close


def replace_with(fi, x, y):
    lines = []
    f = open(fi, "r")
    for line in f:
        line = line.replace(x, y)
        lines.append(line)
    f.close()
    with open(fi, "w") as f:
        for line in lines:
            f.write(line)
    f.close()


def add_run_to_db(cursor, target, version, config="conf.json"):
    with open(config) as confj:
        data = json.load(confj)
        # TODO:add opov version
        cursor.execute(
            'INSERT INTO runs (date, type, tolerated_type, project, project_version, opov_version) VALUES (?, ?, ?, ?, ?, ?)',
            (datetime.datetime.now().isoformat(), data['global']['type'], data['global']['tolerated_type'], target,
             version, 0.0))


def add_matches_to_db(cur, matchlist, delim):
    cur.execute('SELECT last_insert_rowid()')
    daata = cur.fetchall()
    runid = daata[0][0]
    for match in matchlist:
        filelist = match[5].split(delim)
        # No duplicate matches, instead store them in the match entry table
        cur.execute('SELECT rowid FROM matches WHERE matchtype=? AND file=? AND line=? AND _column=? AND code= ?',
                    (match[0], match[1], match[2], match[3], match[4]))
        data = cur.fetchall()
        if len(data) == 0:
            cur.execute(
                'INSERT INTO matches (matchtype, file, line, _column, code) VALUES (?, ?, ?, ?, ?)',
                (match[0], match[1], match[2], match[3], match[4]))
            cur.execute('SELECT last_insert_rowid()')
            currentmatchid = cur.fetchall()[0][0]
            for mfile in filelist:
                if mfile == 'null':
                    continue
                cur.execute(
                    'INSERT INTO appearances (matchid, file) VALUES (?, ?)',
                    (currentmatchid, mfile))

        else:
            currentmatchid = data[0][0]

        cur.execute('INSERT INTO match_entries (runid, matchid) VALUES(?, ?)', (runid, currentmatchid))


parser = argparse.ArgumentParser()
parser.add_argument("target", help="project to work with")
parser.add_argument("-i", "--install", help="Install the project", default=False)
parser.add_argument("-c", "--gencommands", help="Generate compile commands", default=False)
parser.add_argument("--version", help="Project version", default="")
parser.add_argument("-o", "--output", help="Name of output csv file", default="result")
parser.add_argument("-d", "--csvdelimiter", help="Delimiter for csv output", default=";")
parser.add_argument("--config", help="Name of config file or directory (default = project name + conf)", default="")
parser.add_argument("--dbmode", help="Whether to interact with the database or not", default=False)
args = parser.parse_args()

if args.target == "OpenFOAM":
    pr = project.openFOAM
elif args.target == "SU2":
    pr = project.su2

if args.config == "":
    config = args.target + "conf.json"
else:
    config = args.config

pName = args.target
if args.version != "":
    pName = pName + "-" + args.version
elif args.target == "SU2":
    args.version = "6.2.0"
if args.install or args.gencommands:
    if args.install:
        pr.setup(args.version)
    pr.environ(pName)
    if args.install:
        pr.preconfigure(args.version)
    pr.comgen(pName)
else:
    if args.dbmode:
        conn = sqlite3.connect("opovdb.db")
        cur = conn.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS runs (date TEXT, type TEXT, tolerated_type TEXT, project TEXT, project_version TEXT, opov_version TEXT)')
        cur.execute(
            'CREATE TABLE IF NOT EXISTS matches (matchtype TEXT, file TEXT, line INTEGER, _column INTEGER, code TEXT)')
        cur.execute(
            'CREATE TABLE IF NOT EXISTS match_entries(runid INTEGER, matchid INTEGER, \
            FOREIGN KEY (runid) REFERENCES runs (ROWID) ON DELETE CASCADE ON UPDATE CASCADE, \
            FOREIGN KEY (matchid) REFERENCES matches (ROWID) ON DELETE CASCADE ON UPDATE CASCADE)')
        cur.execute(
            'CREATE TABLE IF NOT EXISTS appearances (matchid INTEGER, file TEXT, \
            FOREIGN KEY (matchid) REFERENCES matches (ROWID) ON DELETE CASCADE ON UPDATE CASCADE)')
    targetList = extract_list(pName)
    confPath = "config/" + config
    if os.path.isdir(confPath):
        accList = []
        for conf in os.listdir(confPath):
            if args.dbmode:
                accList = execute_find_type(targetList, pName, delim=args.csvdelimiter, config=confPath + "/" + conf)
                add_run_to_db(cur, args.target, args.version, config=confPath)
                add_matches_to_db(cur, accList, args.csvdelimiter)
            else:
                accList += execute_find_type(targetList, pName, delim=args.csvdelimiter, config=confPath + "/" + conf)
                write_csv(accList, output=args.output, delim=args.csvdelimiter)

    else:
        tList = execute_find_type(targetList, pName, delim=args.csvdelimiter, config=confPath)
        if args.dbmode:
            add_run_to_db(cur, args.target, args.version, config=confPath)
            add_matches_to_db(cur, tList, args.csvdelimiter)
            cur.execute('SELECT * FROM runs')
            data2 = cur.fetchall()
            print(data2)
            cur.execute('SELECT * FROM matches')
            data3 = cur.fetchall()
            print(data3)
            cur.execute('SELECT * FROM appearances')
            data3 = cur.fetchall()
            print(data3)
            cur.execute('SELECT * FROM match_entries')
            data3 = cur.fetchall()
            print(data3)
            conn.commit()
            conn.close()
        else:
            write_csv(tList, output=args.output)
