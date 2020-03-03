from suite.helpers import replace_with
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("target", help="project to extract the compile commands of")
args = parser.parse_args()
pName = args.target
replace_with(pName + "/compile_commands.json", "compile_commands/" + pName + ".json", os.getcwd(), "[root]")