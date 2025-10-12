#!/usr/bin/awk -f
BEGIN {
    # Configuration
    input_file = "lifetracker.csv"
    output_file = "checklist.csv"

    # Validate arguments
    if (ARGC != 2) {
        print "Error: Missing month argument"
        print "Usage: ./activity.awk <month_number>"
        print "Example: ./activity.awk 10"
        exit 1
    }

    month_num = ARGV[1] + 0  # Convert to number
    if (month_num < 1 || month_num > 12) {
        print "Error: Month must be between 1 and 12"
        exit 1
    }
    
    month = sprintf("%02d", month_num)  # Format as 2-digit

    # Remove argument so AWK processes input file
    delete ARGV[1]
    ARGV[1] = input_file

    FS = ","
}

{
    split($1, dparts, "-")
    if (dparts[2] == month) {
        dates[$1] = 1
        acts[$4] = 1
        has[$1,$4] = 1
    }
}

END {
    # Check if input file was read
    if (!length(dates)) {
        print "Error: No data found for month " month " (" month_num ") in " input_file
        print "Check if the file exists and has data for the specified month"
        exit 1
    }

    # Create header
    header = "Date"
    for (a in acts) {
        header = header "," a
    }

    # Write to output file
    print header > output_file
    for (d in dates) {
        line = d
        for (a in acts) {
            line = line "," (has[d,a] ? 1 : 0)
        }
        print line > output_file
    }

    print "✅ Successfully generated " output_file " for month " month " (" month_num ")"
    print "📅 Days processed: " length(dates)
    print "🏃 Activities found: " length(acts)
    
    # Generate and open the plot
    system("python checklist_compstats.py")
    system("am start -a android.intent.action.VIEW -d file:///storage/emulated/0/activity_checklist.png -t image/png 2>/dev/null")
}
