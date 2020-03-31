import argparse
import os
import sqlite3

import project
from helpers import find_opovlint, write_csv, extract_list, execute_find_type, replace_with
from database import Database

def run():

    rootdir = os.path.dirname(os.path.dirname(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="project to work with (e.g. OpenFOAM, SU2)")
    parser.add_argument("-i", "--install", help="Install the project instead of running?", dest='install', default=False, action="store_true")
    parser.add_argument("-c", "--gencommands", help="Generate compile commands manually?", dest='gencommands', default=False, action="store_true")
    parser.add_argument("--version", help="Project version appendix (e.g. 6 for OpenFOAM-6, releases for SU2 7.0.0)", default="")
    parser.add_argument("-o", "--output", help="Name of output csv file", default="")
    parser.add_argument("-d", "--csvdelimiter", help="Delimiter for csv output", default=";")
    parser.add_argument("--config", help="Name of config file or directory (default = project name + conf)", default="")
    parser.add_argument("--oolint", help="Directory of OO-Lint(if automatic finding fails)", default="")
    parser.add_argument("--db", help="Database to interact with", default="")
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
        if not os.path.exists(pName + "/compile_commands.json"):
            if not os.path.exists("compile_commands/" + pName + ".json"):
                print("No pre-generated compile command database available, generate manually with --gencommands")
            else:
                replace_with("compile_commands/" + pName + ".json", pName + "/compile_commands.json", "[root]", os.getcwd())
        if args.db != "":
            db = Database(args.db)
        target_list = extract_list(pName)
        conf_path = os.path.join(rootdir, "config/" + config)
        #support multiple configs
        if os.path.isdir(conf_path):
            accList = []
            for conf in os.listdir(conf_path):
                accList += execute_find_type(target_list, pName, args.oolint, delim=args.csvdelimiter,
                                            config=conf_path + "/" + conf)
            if args.db != "":
                db.add_run(args.target, args.version, args.oolint, config=conf_path + "/" + conf)
                db.add_matches(accList, args.csvdelimiter)
            if args.output != "":
                 write_csv(accList, simple_columns, output=args.output, delim=args.csvdelimiter)

        else:
            tList = execute_find_type(target_list, pName, args.oolint, delim=args.csvdelimiter, config=conf_path)
            if args.db != "":
                db.add_run(args.target, args.version, args.oolint, config=conf_path)
                db.add_matches(tList, args.csvdelimiter)
            if args.output != "":
                write_csv(tList, simple_columns, output=args.output, delim=args.csvdelimiter)
        if args.db != "":
            db.close()


if __name__ == "__main__":
    run()
