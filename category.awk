awk -F',' '
{
    # Extract YYYY-MM from DD-MM-YYYY date format
    split($1, date, "-")
    month = date[3] "-" date[2]  # This gives "YYYY-MM" format
    
    min = $3 + 0
    cat = $NF
    sum[month, cat] += min
    months[month] = 1
    cats[cat] = 1
}
END {
    print "Monthly category-wise consolidation (minutes):"
    print "=============================================="
    
    # Manually specify month order
    month_order["2025-09"] = 1
    month_order["2025-10"] = 2
    
    # Print months in specified order
    for (m in month_order) {
        if (m in months) {
            total_month = 0
            
            # Calculate total for this month
            for (c in cats) {
                if (sum[m, c] > 0) {
                    total_month += sum[m, c]
                }
            }
            
            printf "%s: %d min (%.2f hours)\n", m, total_month, total_month/60
            
            # Print categories for this month
            for (c in cats) {
                if (sum[m, c] > 0) {
                    printf "  %s: %d min (%.2f hours)\n", c, sum[m, c], sum[m, c]/60
                }
            }
            print ""
        }
    }
}
' lifetracker.csv
