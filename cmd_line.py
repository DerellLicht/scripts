# usage: python cmd_line.py [args]
import json, re, os, sys, argparse
from pathlib import Path

# SRC = "conversations 07.09.26.json"
# OUT_DIR = "."

# print("\n".join(written))

# print(sys.argv)
# print("cmd: ",sys.argv[0],", args: ", sys.argv[1])

SRC=sys.argv[1]
# SRC="test"
# print("opening: ", SRC)

# parser = argparse.ArgumentParser("read/verify input filename")
# parser.add_argument(SRC, help="input filename")
# args = parser.parse_args()

# print("Input:", SRC)

# File path
a = Path(SRC)

# Check if the file exists
if a.exists():
    print(a,": File exists")
else:
    print(SRC,": File does not exist")
