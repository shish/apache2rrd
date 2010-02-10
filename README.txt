                            _____   __________________ 
                           /  _  \  \_____  \______   \
                          /  /_\  \  /  ____/|       _/
                         /    |    \/       \|    |   \
                         \____|__  /\_______ \____|_  /
                                 \/         \/      \/ 
                                 Apache To RRD

Usage:
  a2r -r file.rrd [log file] [log file] [log file] [...]
  a2r -r file.rrd -b -t week -o bandwidth-week.png
  a2r -r file.rrd -u -t year -o useragent-year.png

  -r rrd file to use
     .gz and .bz2 are handled automatically
     for exteral commands, pipe and use "-" for stdin
  -o output file name
  -b output a bandwidth graph
  -u output a user-agent graph
  -t timescale (day, week, month, year)
  -x width
  -y height
  -h help

