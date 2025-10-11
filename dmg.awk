awk -F',' '
BEGIN {
    prev_month = ""
    grand_total = 0
}
{
    date = $1
    min = $2
    month = substr(date, 1, 7)
    day_sum[date] += min
    month_sum[month] += min
    grand_total += min
    date_list[++ndates] = date
    month_for[date] = month
}
END {
    printf "Grand Total: %d min (%.2f hours)\n\n", grand_total, grand_total/60
    for (i=1; i<=ndates; i++) {
        date = date_list[i]
        min = day_sum[date]
        month = month_for[date]
        if (prev_month != "" && month != prev_month) {
            # monthly consolidation after prev month
            printf "Monthly Total for %s: %d min (%.2f hours)\n\n", prev_month, month_sum[prev_month], month_sum[prev_month]/60
        }
        printf "%s: %d min (%.2f hours)\n", date, min, min/60
        prev_month = month
    }
    # Print last monthly summary
    if (prev_month != "")
        printf "Monthly Total for %s: %d min (%.2f hours)\n", prev_month, month_sum[prev_month], month_sum[prev_month]/60
}
' lifetracker_sorted.csv

