#!/usr/bin/awk -f
BEGIN {
    FS = ",";
    target_month = ARGV[1]
    ARGV[1] = "lifetracker.csv"
    if (length(target_month) == 1) target_month = "0" target_month;
    print "" > "plotdata.csv"
}
{
    split($1, date_parts, "-")
    if (date_parts[2] == target_month) {
        sum[$1] += $3
        dates[$1] = 1
    }
}
END {
    total_min = 0
    total_hr = 0
    day_count = 0
    # Collect sorted date keys
    n = asorti(dates, sorted_dates)
    for (i = 1; i <= n; i++) {
        d = sorted_dates[i]
        if (sum[d] > 0) {
            total_min += sum[d]
            hrs = sum[d] / 60
            total_hr += hrs
            day_count++
	    printf "%s,%d,%.2f\n", d, sum[d], hrs
            printf "%s,%d,%.2f\n", d, sum[d], hrs >> "plotdata.csv"
        }
    }
    printf "Number of days: %d\n", day_count
    printf "Grand Total: %d min (%.2f hours)\n", total_min, total_hr
    system("python3 plotg.py")
    system("am start -a android.intent.action.VIEW \
    -d file:///storage/emulated/0/daily_activity_plot.png \
    -t image/png")
}

