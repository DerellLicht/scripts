# filesize.awk
@load "filefuncs"
BEGIN {
    print "Total filenames (ARGC) = " ARGC
    for (i = 1; i < ARGC; i++) {
        ret = stat(ARGV[i], data)
        printf ("ARGV[%d]: %s, ret: %d, size: %u\n", i, ARGV[i], ret, data["size"])
    }
}

