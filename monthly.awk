#!/bin/bash
awk -F',' '{
  split($1, date, "-");
  month_key = date[3] "-" date[2];   # YYYY-MM
  day = date[1];

  if ($3 ~ /^[0-9]+$/) {
    sum[month_key] += $3;
    day_seen[month_key "|" day] = 1;  # simulate 2D array
  }
}
END {
  total_min = 0;
  total_hr = 0;

  PROCINFO["sorted_in"] = "@ind_str_asc";

  printf "Monthly Consolidation:\n";
  for (month in sum) {
    if (sum[month] > 0) {
      total_min += sum[month];
      total_hr += sum[month] / 60;

      # count unique days
      day_count = 0;
      for (key in day_seen) {
        split(key, parts, "|");
        if (parts[1] == month)
          day_count++;
      }

      printf "%s: %d min (%.2f hours), %d days\n",
             month, sum[month], sum[month] / 60, day_count;
    }
  }

  printf "Grand Total: %d min (%.2f hours)\n", total_min, total_hr;
}' lifetracker.csv

