import argparse
import datetime
import json
import os
import sqlite3
import subprocess
from database import Database, DatabaseMeasure
from helpers import write_csv

parser = argparse.ArgumentParser()
parser.add_argument("--target", help="target type, project, version tuple to get regressed matches", type=str, nargs=3, default=[])
parser.add_argument("-m", "--measures", help="print the precision, recall and f1 score for the run with this id", type=int, default=0)
parser.add_argument("-o", "--output", help="Name of output csv file", default="")
parser.add_argument("-d", "--csvdelimiter", help="Delimiter for csv output", default=";")
parser.add_argument("--db", help="Database to interact with", default="")
parser.add_argument("--diff", help="Differences of runs to show(list of 2 ids)", type=int, nargs=2, default=[])
parser.add_argument("--reg", help="only show regressed matches in diff(new false positives, new false negatives)", dest='reg', default=False, action="store_true")
parser.add_argument("--modules", help="Only test these modules", type=str, default=[])
args = parser.parse_args()

db = Database(args.db)
diffs_columns = ["runid", "matchid", "MatchType", "File", "Line", "Column", "Code", "correct_match"]


def run():
    if len(args.diff) == 2:
        if args.reg:
            out = db.regressed_matches(args.diff[0], args.diff[1], args.modules)
            print(out)
        else:
            out = db.calc_diffs(args.diff[0], args.diff[1], args.modules)
            print(out)
        write_csv(out, diffs_columns, output=args.output, sort=False, delim=args.csvdelimiter)
    elif args.target:
        write_csv(db.regressed_matches_for_project(args.target[0], args.target[1], args.target[2], args.modules),
                  diffs_columns, output=args.output, sort=False, delim=args.csvdelimiter)
    elif args.measures != 0:
        dbm = DatabaseMeasure(db, args.measures, args.modules)
        print("Precision for run " + str(args.measures) + ": " + str(dbm.precision()))
        print("Recall for run " + str(args.measures) + ": " + str(dbm.recall()))
        print("F1score for run " + str(args.measures) + ": " + str(dbm.f1score()))
    else:
        write_csv(db.calc_latest_diff(), diffs_columns, output=args.output, sort=False, delim=args.csvdelimiter)


if __name__ == "__main__":
    run()