# hmmm... not sure what this was supposed to do, 
# as of 01/24/20, it doesn't do anything
# 
# gawk -f add.column.awk columns_data_file
#  this parses output of 'pslist -m'
#      VM      WS    Priv Priv Pk
{ 
   num_lines++; 
   sum1 += $1
   sum2 += $2
}
END { printf("In %d lines: mine=%d, total=%d, percent=%.1f\n", num_lines, sum1, sum2, (sum1 * 100 / sum2)) ;
}
 
