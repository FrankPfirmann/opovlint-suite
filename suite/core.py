import argparse
import os, sys
import sqlite3

import project
from helpers import find_opovlint, write_csv, calc_diffs, extract_list, execute_find_type, add_run_to_db, \
    add_matches_to_db, replace_with


def run():

    rootdir = os.path.dirname(os.path.dirname(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="project to work with (e.g. OpenFOAM, SU2)")
    parser.add_argument("-i", "--install", help="Install the project instead of running?", default=False)
    parser.add_argument("-c", "--gencommands", help="Generate compile commands manually?", default=False)
    parser.add_argument("--version", help="Project version appendix (e.g. 6 for OpenFOAM-6)", default="")
    parser.add_argument("-o", "--output", help="Name of output csv file", default="result")
    parser.add_argument("-d", "--csvdelimiter", help="Delimiter for csv output", default=";")
    parser.add_argument("--config", help="Name of config file or directory (default = project name + conf)", default="")
    parser.add_argument("--oolint", help="Directory of OO-Lint(if automatic finding fails)", default="")
    parser.add_argument("--db", help="Database to interact with", default=False)
    parser.add_argument("--diff", help="Differences of runs to show(list of 2 ids)", type=int, nargs=2, default=[])
    args = parser.parse_args()

    if args.oolint == "":
        args.oolint = find_opovlint()
    if args.target == "OpenFOAM":
        pr = project.openFOAM
    elif args.target == "SU2":
        pr = project.su2

    if args.config == "":
        config = args.target + "conf.json"
    else:
        config = args.config

    simple_columns = ["MatchType", "File", "Line", "Column", "Code", "Files"]
    diffs_columns = ["runid", "matchid", "MatchType", "File", "Line", "Column", "Code", "correct_match"]
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
        if args.gencommands:
            pr.comgen(pName)
    else:
        if not os.path.exists(pName + "/compile_commands.json"):
            if not os.path.exists("compile_commands/" + pName + ".json"):
                print("No pre-generated compile command database available, generate manually with --gencommands")
            else:
                replace_with("compile_commands/" + pName + ".json", pName + "/compile_commands.json", "[root]", os.getcwd())
        if args.db != "":
            conn = sqlite3.connect(args.db)
            cur = conn.cursor()

            cur.execute(
                'CREATE TABLE IF NOT EXISTS runs (date TEXT, type TEXT, tolerated_type TEXT, project TEXT, project_version TEXT, opov_version TEXT)')
            cur.execute(
                'CREATE TABLE IF NOT EXISTS matches (matchtype TEXT, file TEXT, line INTEGER, _column INTEGER, code TEXT, is_correct INTEGER)')
            cur.execute(
                'CREATE TABLE IF NOT EXISTS match_entries(runid INTEGER, matchid INTEGER, \
                FOREIGN KEY (runid) REFERENCES runs (ROWID) ON DELETE CASCADE ON UPDATE CASCADE, \
                FOREIGN KEY (matchid) REFERENCES matches (ROWID) ON DELETE CASCADE ON UPDATE CASCADE)')
            cur.execute(
                'CREATE TABLE IF NOT EXISTS appearances (matchid INTEGER, file TEXT, \
                FOREIGN KEY (matchid) REFERENCES matches (ROWID) ON DELETE CASCADE ON UPDATE CASCADE)')
            if len(args.diff) == 2:
                write_csv(calc_diffs(args.diff[0], args.diff[1], cur), diffs_columns, output=args.output, sort=False)
                exit()
        target_list = extract_list(pName)
        conf_path = os.path.join(rootdir, "config/" + config)
        #support multiple configs
        if os.path.isdir(conf_path):
            accList = []
            for conf in os.listdir(conf_path):
                if args.db != "":
                    accList = execute_find_type(target_list, pName, args.oolint, delim=args.csvdelimiter, config=conf_path + "/" + conf)
                    add_run_to_db(cur, args.target, args.version, args.oolint, config=conf_path + "/" + conf)
                    add_matches_to_db(cur, accList, args.csvdelimiter)
                else:
                    accList += execute_find_type(target_list, pName, args.oolint, delim=args.csvdelimiter, config=conf_path + "/" + conf)
                    write_csv(accList, simple_columns, output=args.output, delim=args.csvdelimiter)

        else:
            tList = execute_find_type(target_list, pName, args.oolint, delim=args.csvdelimiter, config=conf_path)
            if args.db != "":
                add_run_to_db(cur, args.target, args.version, args.oolint, config=conf_path)
                add_matches_to_db(cur, tList, args.csvdelimiter)

            else:
                write_csv(tList, simple_columns, output=args.output, delim=args.csvdelimiter)
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


if __name__ == "__main__":
    run()
