#!/usr/bin/awk -f
BEGIN {
    FS = ",";
    target_month = ARGV[1];
    target_year = ARGV[2];
    ARGV[1] = "lifetracker.csv";
    ARGV[2] = "";
    # Month number to name mapping
    monthnames["01"] = "January";   monthnames["02"] = "February"; monthnames["03"] = "March";
    monthnames["04"] = "April";     monthnames["05"] = "May";      monthnames["06"] = "June";
    monthnames["07"] = "July";      monthnames["08"] = "August";   monthnames["09"] = "September";
    monthnames["10"] = "October";   monthnames["11"] = "November"; monthnames["12"] = "December";
    month_name = ""; year_val = "";
    print "Date,Category,Minutes" > "plotdata.csv";
    print "Monthly category-wise consolidation (minutes)";
    print "==============================================";
}
{
    split($1, date_parts, "-");
    if (length(date_parts) >= 3) {
        year = date_parts[3];
        month_num = date_parts[2];
        day = date_parts[1];
        category = $4;
        minutes = $3;
        if (month_num == target_month && year == target_year) {
            month_name = monthnames[month_num];
            year_val = year;
            key = category;
            sum[key] += minutes;
            cats[key] = 1;
        }
    }
}
END {
    total_min = 0;
    for (c in cats) total_min += sum[c];
    printf("\nMonth: %s %s - Total: %d min (%.1f hours)\n", month_name, year_val, total_min, total_min/60);
    print "Category breakdown:";
    print "-------------------";
    # Write data for plotting
    for (c in cats) {
        printf("%s: %d min (%.1f hours)\n", c, sum[c], sum[c]/60);
        printf("%s,%s,%d\n", month_name, c, sum[c]) >> "plotdata.csv";
    }
    # Generate plot and open it
    plot_file = "/data/data/com.termux/files/home/termux_files/reports/category_plot.png";
    system("python3 plot_category.py");
    #system("am start -a android.intent.action.VIEW -d file://" plot_file " -t image/png");
}

