import subprocess
import os
import json
import datetime
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


def find_opovlint():
    for root, dirs, files in os.walk("/"):
        if "opovlint" in dirs:
            return os.path.join(root, "opovlint")


def execute_find_type(tlist, pname, oolint, delim=";", linedelim="@", config="conf.json"):
    matchlist = []
    find_type = oolint + "/bin/find-type"
    i = 0
    for target in tlist:
        if i > 10:
            return matchlist
        t = subprocess.check_output([find_type, target.rstrip(), "-config=" + config]).decode("utf-8").rstrip()
        i += 1
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


