# test.awk
BEGIN {
    #print "Total arguments (ARGC) = " ARGC
    maxlen = 0 ;
    for (i = 0; i < ARGC; i++) {
        if (maxlen < length(ARGV[i]))
            maxlen = length(ARGV[i])
        # printf "ARGV[%d] = %s [%u]\n", i, ARGV[i], length(ARGV[i])
    }
    printf("max file length: %u bytes", maxlen)
    
}
