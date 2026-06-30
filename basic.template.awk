# > for %v in (*) do gawk -f basic.template.awk %v
BEGIN {
  linect = 0 ;
}
{   
    linect++; 
}
END { 
    printf("%s: %u lines\n", FILENAME, linect);
}
