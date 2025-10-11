#!/usr/bin/awk -f
BEGIN {
    FS = ","
    target_month = ARGV[1]
    ARGV[1] = "lifetracker.csv"
    if (length(target_month) == 1) target_month = "0" target_month

    # Month number to name mapping
    monthnames["01"] = "January"
    monthnames["02"] = "February"
    monthnames["03"] = "March"
    monthnames["04"] = "April"
    monthnames["05"] = "May"
    monthnames["06"] = "June"
    monthnames["07"] = "July"
    monthnames["08"] = "August"
    monthnames["09"] = "September"
    monthnames["10"] = "October"
    monthnames["11"] = "November"
    monthnames["12"] = "December"

    month_name = ""
    year_val = ""
    print "Monthly category-wise consolidation (minutes):"
    print "=============================================="
}
{
    split($1, date, "-")
    day = date[1]
    month_num = date[2]
    year = date[3]
    if (month_num == target_month) {
        month_name = monthnames[month_num]
        year_val = year
    }
    if (month_num != target_month) next
    min = $3 + 0
    cat = $NF
    sum[cat] += min
    cats[cat] = 1
}
END {
    total_min = 0
    for (c in cats) total_min += sum[c]
    printf("\n%s-%s: %d min (%.2f hours)\n", year_val, target_month, total_min, total_min/60.0)
    for (c in cats) {
        printf("  %s: %d min (%.2f hours)\n", c, sum[c], sum[c]/60.0)
    }
    # Output CSV with month/year in header
    print "Month,Year" > "category_total.csv"
    print month_name "," year_val >> "category_total.csv"
    print "Category,Minutes" >> "category_total.csv"
    for (c in cats) {
        print c "," sum[c] >> "category_total.csv"
    }
    # Compose plot filename and invoke python
    fn = "category_bar_chart_" month_name "_" year_val ".png"
    system("python3 plot_category.py \"" month_name "\" \"" year_val "\" \"" fn "\"")
    system("am start -a android.intent.action.VIEW -d file:///storage/emulated/0/"fn" -t image/png")

}

