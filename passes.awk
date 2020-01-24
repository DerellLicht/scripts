# as of 01/24/20, I have no idea what the input was for this script,
#    but I will retain it as reference data
# try to find highest pass-count entry in file
# In this case, pass_count will probably equal pass_number,
# but the latter is actually reporting the pass number, so I use that.
BEGIN {
  pass_count = 0 ;
  pass_number = 0 ;
  ltu_found = 0 ;
  pkt_found = 0 ;
  tmo_found = 0 ;
}
{
  if (/Unexpectedly/) {
    ltu_found++ ;
  }
  if (/pkt/) {
    pkt_found++ ;
  }
  if (/timed out/) {
    tmo_found++ ;
  }
  if ($1 == "pass") {
    pass_count++ ;
    pass_number = $2 ;
  }
}
END { 
  printf("number of passes: %u\n", pass_number);
  printf("dropped packets: %u\n", pkt_found);
  printf("LTUs found: %u\n", ltu_found);
  printf("timed_out found: %u\n", tmo_found);
}
