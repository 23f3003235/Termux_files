#!/usr/bin/awk -f
BEGIN {
  FS = ",";
  target_month = ARGV[1]
  ARGV[1] = "lifetracker.csv"  # Automatically use lifetracker.csv for data
  if (length(target_month) == 1) target_month = "0" target_month
}

{
  split($1, date_parts, "-")
  # Only sum rows where month matches the filter
  if (date_parts[2] == target_month) {
    sum[$1] += $3  # $3 is the minutes column based on your data format
  }
}

END {
  total_min = 0
  total_hr = 0
  day_count = 0

  for (d in sum) {
    if (sum[d] > 0) {
      total_min += sum[d]
      hrs = sum[d] / 60
      total_hr += hrs
      day_count++
      printf "%s,%d,%.2f\n", d, sum[d], hrs
    }
  }

  printf "Number of days: %d\n", day_count
  printf "Grand Total: %d min (%.2f hours)\n", total_min, total_hr
}

