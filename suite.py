import subprocess
import os
import argparse
import json
import project
from operator import itemgetter


def extract_list(makeloc):
    targetlist = []
    with open(makeloc + "/compile_commands.json") as cjson:
        data = json.load(cjson)
        for p in data:
            targetlist.append(p['file'])
    return targetlist


def is_same_match(x, y):
    for it in range(0, 5):
        if x[it] != y[it]:
            return False
    return True


def execute_find_type(tlist, pname,  delim=";", config="conf.json"):
    debug_ind = 0
    matchlist = []
    for target in tlist:
        if debug_ind > 50:
            break
        debug_ind += 1
        t = subprocess.check_output(["find-type", target.rstrip(), "-config=" + config]).decode("utf-8").rstrip()
        for m in t.split(delim + delim):
            m = m.replace('\n', '')
            m = m.replace(os.getcwd() + '/' + pname, '')
            elem = m.split(delim)
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


parser = argparse.ArgumentParser()
parser.add_argument("target", help="project to work with")
parser.add_argument("-i", "--install", help="Install the project", default=False)
parser.add_argument("-c", "--gencommands", help="Generate compile commands", default=False)
parser.add_argument("--version", help="Project version", default="")
parser.add_argument("-o", "--output", help="Name of output csv file", default="result")
parser.add_argument("-d", "--csvdelimiter", help="Delimiter for csv output", default=";")
parser.add_argument("--config", help="Name of config file or directory", default="")
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
if args.install or args.gencommands:
    if args.install:
        pr.setup(args.version)
    pr.environ(pName)
    if args.install:
        pr.preconfigure(args.version)
    pr.comgen(pName)
else:
    targetList = extract_list(pName)
    confPath = "config/" + config
    if os.path.isdir(confPath):
        accList = []
        for conf in os.listdir(confPath):
            print(os.listdir(confPath))
            accList += execute_find_type(targetList, pName, delim=args.csvdelimiter, config=confPath+"/"+conf)
            write_csv(accList, output=args.output, delim=args.csvdelimiter)
    else:
        tList = execute_find_type(targetList, pName, delim=args.csvdelimiter, config=confPath)
        write_csv(tList, output=args.output, delim=args.csvdelimiter)
