# try to find highest pass-count entry in file
# In this case, pass_count will probably equal pass_number,
# but the latter is actually reporting the pass number, so I use that.
BEGIN {
  pass_number = 0 ;
  ltu_found = 0 ;
  pkt_found = 0 ;
  tmo_found = 0 ;
  failed_found = 0 ;
  read_ver_tmo = 0 ;
  start_time_found = 0 ;
  start_date = "";
  start_time = "";
  end_date = "";
  end_time = "";
}
{
  if (start_time_found == 0) {
    # Connecting to 2E:E1:FF:BF:08:B0 at 8/6/2015 16:58:3.74
    if ($1 == "Connecting"  &&  $2 == "to") {
      start_time_found = 1 ;
      start_date = $5;
      start_time = $6;
    }
  }
  # 08/06/15, 17:19:52: BLE Stream setup successful
  if ($3 == "BLE"  &&  $4 == "Stream"  &&  $5 == "setup"  &&  $6 == "successful") {
    end_date = $1;
    end_time = $2;
    slen = length(end_time);
    end_time = substr(end_time, 1, slen-1);
  }
  
  if (/Unexpectedly/) {
    ltu_found++ ;
  }
  if (/pkt/) {
    pkt_found++ ;
  }
  if (/Read ver timeout/) {
    read_ver_tmo++ ;
  }
  if (/cmd timed out/) {
    tmo_found++ ;
  }
  if (/failed/) {
    failed_found++ ;
  }
  if ($1 == "pass") {
    pass_number = $2 ;
  }
}
END { 
  printf("number of passes: %u\n", pass_number);
  if (start_time_found) {
    printf("Starting Run: %s, %s\n", start_date, start_time);
    printf("Ending Run:   %s %s\n", end_date, end_time);
  }
  printf("dropped packets: %u\n", pkt_found);
  printf("ReadVer tmo: %u\n", read_ver_tmo);
  printf("LTUs: %u\n", ltu_found);
  printf("cfg cmd timed_out: %u\n", tmo_found);
  printf("failed: %u\n", failed_found);
}