# test.awk
BEGIN {
    print "Total arguments (ARGC) = " ARGC
    for (i = 0; i < ARGC; i++) {
        printf "ARGV[%d] = %s\n", i, ARGV[i]
    }
}
