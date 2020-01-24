# pslist -m | gawk -f add.columns.awk 
#  this parses output of 'pslist -m'
#  it summarizes memory usage in various categories
#      VM      WS    Priv Priv Pk
{ 
   if ( NR > 3 ) {
   num_lines++; 
   sum1 += $3
   sum2 += $4
   sum3 += $5
   sum4 += $6 
   }
}
END { printf("In %d lines: VM=%d, WS=%d, Priv=%d, PrivPk=%d\n", num_lines, sum1, sum2, sum3, sum4) ;
}
 
