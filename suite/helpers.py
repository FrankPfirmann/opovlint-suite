import subprocess
import os
import json
import datetime
from operator import itemgetter

#TODO:remove debug_i

def extract_list(makeloc):
    targetlist = []
    with open(makeloc + "/compile_commands.json") as cjson:
        data = json.load(cjson)
        debug_i = 0
        for p in data:
            debug_i += 1
            if debug_i > 10:
                break
            targetlist.append(p['file'])
    return targetlist


def is_same_match(x, y):
    for it in range(0, 5):
        if x[it] != y[it]:
            return False
    return True


def find_opovlint():
    for root, dirs, files in os.walk("/"):
        if "opovlint" in dirs:
            return os.path.join(root, "opovlint")


def execute_find_type(tlist, pname, oolint, delim=";", linedelim="@", config="conf.json"):
    matchlist = []
    find_type = oolint + "/bin/find-type"
    for target in tlist:
        t = subprocess.check_output([find_type, target.rstrip(), "-config=" + config]).decode("utf-8").rstrip()
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


def write_csv(matchlist, columnlist, output="result", delim=";", sort=True):
    if sort:
        sortedlist = sorted(matchlist, key=itemgetter(0, 1, 2, 3))
    else:
        sortedlist = matchlist
    if not os.path.isdir("data"):
        os.mkdir("data")
    f = open("data/" + output + ".csv", "w")
    titlestring = ""
    for c in columnlist:
        if c == columnlist[-1]:
            titlestring = titlestring + c + " \n"
        else:
            titlestring = titlestring + c + delim
    f.write(titlestring)
    f.close()
    f = open("data/" + output + ".csv", "a")
    for match in sortedlist:
        for i in match:
            f.write(str(i))
            f.write(delim)
        f.write("\n")
    f.close


def replace_with(fi, ou, x, y):
    lines = []
    f = open(fi, "r")
    for line in f:
        line = line.replace(x, y)
        lines.append(line)
    f.close()
    with open(ou, "w") as f:
        for line in lines:
            f.write(line)
    f.close()


def add_run_to_db(cursor, target, version, oolint, config="conf.json"):
    with open(config) as confj:
        data = json.load(confj)
        cwd = os.getcwd()
        os.chdir(oolint)
        oolint_version = subprocess.check_output(["git", "describe", "--tags" , "--always"]).decode("utf-8").rstrip()
        os.chdir(cwd)
        cursor.execute(
            'INSERT INTO runs (date, type, tolerated_type, project, project_version, opov_version)\
             VALUES (?, ?, ?, ?, ?, ?)',
            (datetime.datetime.utcnow().isoformat(), data['global']['type'], data['global']['tolerated_type'], target,
             version, oolint_version))


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


def calc_diffs(run1, run2, cur):
    cur.execute('SELECT * FROM match_entries JOIN matches ON matches.rowid = match_entries.matchid \
    WHERE match_entries.runid=? OR match_entries.runid=? GROUP BY match_entries.matchid HAVING COUNT(*) = 1\
                ORDER BY matches.file, match_entries.runid', (run1, run2));
    return cur.fetchall()



