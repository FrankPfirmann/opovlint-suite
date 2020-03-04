import argparse
import datetime
import json
import os
import sqlite3
import subprocess
from database import Database, DatabaseMeasure

parser = argparse.ArgumentParser()
parser.add_argument("target", help="project to work with (e.g. OpenFOAM, SU2)")
parser.add_argument("-i", "--install", help="Install the project instead of running?", default=False)
parser.add_argument("-c", "--gencommands", help="Generate compile commands manually?", default=False)
parser.add_argument("--version", help="Project version appendix (e.g. 6 for OpenFOAM-6, releases for SU2 7.0.0)", default="")
parser.add_argument("-o", "--output", help="Name of output csv file", default="")
parser.add_argument("-d", "--csvdelimiter", help="Delimiter for csv output", default=";")
parser.add_argument("--db", help="Database to interact with", default="")
parser.add_argument("--diff", help="Differences of runs to show(list of 2 ids)", type=int, nargs=2, default=[])
args = parser.parse_args()

db = Database(args.db)
dbm = DatabaseMeasure(db, 2)
print(dbm.recall())
