make check 2>&1 | gawk -f ..\clang-tidy.filter.awk
