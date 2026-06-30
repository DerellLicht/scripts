::  Filter out the "note:" fields from clang-tidy output
make check 2>&1 | gawk -f ..\clang-tidy.filter.awk
