import datetime
import json
import os
import sqlite3
import subprocess


class Database:
    def __init__(self, path):
        #save connector to close
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()
        self.cur.execute('PRAGMA foreign_keys = ON')
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS runs (ID INTEGER NOT NULL, date TEXT, type TEXT, project TEXT, project_version TEXT, opov_version TEXT, PRIMARY KEY(ID))')
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS matches (ID INTEGER NOT NULL, matchtype TEXT, file TEXT, line INTEGER, _column INTEGER, code TEXT, is_correct INTEGER,  PRIMARY KEY(ID))')
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS match_entries(runid INTEGER, matchid INTEGER, \
            FOREIGN KEY (runid) REFERENCES runs (ID) ON DELETE CASCADE ON UPDATE CASCADE, \
            FOREIGN KEY (matchid) REFERENCES matches (ID) ON DELETE CASCADE ON UPDATE CASCADE)')
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS appearances (matchid INTEGER, file TEXT, \
            FOREIGN KEY (matchid) REFERENCES matches (ID) ON DELETE CASCADE ON UPDATE CASCADE)')

    def close(self):
        self.conn.commit()
        self.conn.close()

    def add_run(self, target, version, oolint, config="conf.json"):
        with open(config) as confj:
            data = json.load(confj)
            cwd = os.getcwd()
            os.chdir(oolint)
            oolint_version = subprocess.check_output(["git", "describe", "--tags", "--always"]).decode("utf-8").rstrip()
            os.chdir(cwd)
            self.cur.execute(
                'INSERT INTO runs (date, type, project, project_version, opov_version)\
                 VALUES (?, ?, ?, ?, ?)',
                (datetime.datetime.utcnow().isoformat(), data['global']['type'], target,
                 version, oolint_version))

    def add_matches(self, matchlist, delim):
        self.cur.execute('SELECT last_insert_rowid()')
        daata = self.cur.fetchall()
        runid = daata[0][0]
        for match in matchlist:
            filelist = match[5].split(delim)
            # No duplicate matches, instead store them in the match entry table
            self.cur.execute('SELECT rowid FROM matches WHERE matchtype=? AND file=? AND line=? AND _column=? AND code= ?',
                        (match[0], match[1], match[2], match[3], match[4]))
            data = self.cur.fetchall()
            if len(data) == 0:
                self.cur.execute(
                    'INSERT INTO matches (matchtype, file, line, _column, code, is_correct) VALUES (?, ?, ?, ?, ?, ?)',
                    (match[0], match[1], match[2], match[3], match[4], 0))
                self.cur.execute('SELECT last_insert_rowid()')
                currentmatchid = self.cur.fetchall()[0][0]
                for mfile in filelist:
                    if mfile == 'null':
                        continue
                    self.cur.execute(
                        'INSERT INTO appearances (matchid, file) VALUES (?, ?)',
                        (currentmatchid, mfile))

            else:
                currentmatchid = data[0][0]

            self.cur.execute('INSERT INTO match_entries (runid, matchid) VALUES(?, ?)', (runid, currentmatchid))

    def calc_diffs(self, run1, run2):
        self.cur.execute('SELECT * FROM match_entries JOIN matches ON matches.ID = match_entries.matchid \
        WHERE match_entries.runid=? OR match_entries.runid=? GROUP BY match_entries.matchid HAVING COUNT(*) = 1\
                    ORDER BY matches.file, match_entries.runid', (run1, run2))
        return self.cur.fetchall()

    def regressed_matches(self, idn, ido):
        dbt = self.calc_diffs(idn, ido)
        print(dbt)
        retlist = []
        for diff in dbt:
            if diff[0] == idn and diff[8] == 0:
                retlist.append(diff)
            if diff[0] == ido and diff[8] == 1:
                retlist.append(diff)
        return retlist

    def true_positives(self, id):
        self.cur.execute('SELECT matchtype, file, line, _column, code FROM match_entries JOIN matches ON matches.ID = match_entries.matchid WHERE match_entries.runid=? AND matches.is_correct=1', (id,))
        return self.cur.fetchall()

    def false_positives(self, id):
        self.cur.execute(
            'SELECT matchtype, file, line, _column, code FROM match_entries JOIN matches ON matches.ID = match_entries.matchid WHERE match_entries.runid=? AND matches.is_correct=0 ',
            (id,))
        return self.cur.fetchall()

    def false_negatives(self, id):
        self.cur.execute('SELECT type, project, project_version FROM runs WHERE runs.ID=?', (id,))
        target_type, project, version = self.cur.fetchall()[0]
        self.cur.execute('SELECT runs.id, matchtype, file, line, _column, code FROM (runs JOIN match_entries ON runs.ID = match_entries.runid) JOIN matches ON match_entries.matchid = matches.id WHERE matches.is_correct=1\
                         AND (runs.type = ? AND runs.project = ? AND runs.project_version = ?)', (target_type, project, version))
        total = self.cur.fetchall()
        #remove all matches, which are also matched in the given run
        rmlist = []
        for m in total:
            if m[0] == id:
                for k in total:
                    if m[1:6] == k[1:6]:
                        rmlist.append(k)
                rmlist.append(m)
        #then collapse duplicates
        return list(set([m[1:6] for m in total if m not in rmlist]))

    def regressed_matches_for_project(self, target_type, project, project_version):
        self.cur.execute('SELECT MAX(date), runs.ID FROM runs WHERE runs.type = ? AND runs.project = ? AND runs.project_version = ?', (target_type, project, project_version))
        idn = self.cur.fetchall()[0][1]
        self.cur.execute('SELECT MAX(date), runs.ID FROM runs WHERE date <(SELECT MAX(date) FROM runs WHERE runs.type = ? AND runs.project = ? AND runs.project_version = ?)', (target_type, project, project_version))
        ido = self.cur.fetchall()[0][1]
        print((idn,ido))
        return self.regressed_matches(idn, ido)

    def calc_latest_diff(self):
        self.cur.execute('SELECT MAX(date), runs.ID FROM runs')
        idn = self.cur.fetchall()[0][1]
        self.cur.execute('SELECT MAX(date), runs.ID FROM runs WHERE date <(SELECT MAX(date) FROM runs)')
        ido = self.cur.fetchall()[0][1]
        return self.calc_diffs(idn, ido)


#class to avoid redundant database operations
class DatabaseMeasure:
    def __init__(self, db, id):
        self.tp = len(db.true_positives(id))
        self.fp = len(db.false_positives(id))
        self.fn = len(db.false_negatives(id))

    def precision(self):
        return self.tp/(self.tp + self.fp)

    def recall(self):
        return self.tp/(self.tp + self.fn)

    def f1score(self):
        return 2*self.precision()*self.recall()/(self.precision() + self.recall())

