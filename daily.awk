awk -F',' '{
  sum[$1]+=$3
} END {
  total_min=0;
  total_hr=0;
  day_count=0;
  for (d in sum) {
    if (sum[d] > 0) {
      total_min += sum[d];
      hrs = sum[d]/60;
      total_hr += hrs;
      day_count++;
      printf "%s,%d,%.2f\n", d, sum[d], hrs;
    }
  }
  printf "Number of days: %d\n", day_count;
  printf "Grand Total: %d min (%.2f hours)\n", total_min, total_hr;
}' lifetracker.csv | sort -r

