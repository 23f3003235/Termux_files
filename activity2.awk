#!/usr/bin/awk -f
BEGIN {
    # Configuration
    input_file = "lifetracker.csv"
    output_file = "checklist.csv"

    # Validate arguments
    if (ARGC != 3) {
        print "Error: Missing month/year argument";
        print "Usage: ./activity2.awk <month_number> <year>";
        print "Example: ./activity2.awk 10 2025";
        exit 1;
    }

    month_num = ARGV[1] + 0;  # Convert to number
    year_val = ARGV[2];
    if (month_num < 1 || month_num > 12) {
        print "Error: Month must be between 1 and 12";
        exit 1;
    }

    month = sprintf("%02d", month_num);  # Format as 2-digit

    # Remove arguments so AWK processes input file
    delete ARGV[1];
    delete ARGV[2];
    ARGV[1] = input_file;

    FS = ",";
}

{
    split($1, dparts, "-");
    # Expect format: DD-MM-YYYY
    if (length(dparts) >= 3 && dparts[2] == month && dparts[3] == year_val) {
        dates[$1] = 1;
        acts[$4] = 1;
        has[$1, $4] = 1;
    }
}

END {
    # Check if any data found
    if (!length(dates)) {
        print "Error: No data found for month " month " year " year_val " in " input_file;
        print "Check if the file exists and has data for the specified month/year";
        exit 1;
    }

    # Create header
    header = "Date";
    for (a in acts) header = header "," a;

    # Write to output file
    print header > output_file;
    for (d in dates) {
        line = d;
        for (a in acts) line = line "," (has[d,a] ? 1 : 0);
        print line > output_file;
    }

    print "Successfully generated " output_file " for month " month " year " year_val;
    print "Days processed: " length(dates);
    print "Activities found: " length(acts);

    # Generate and open the plot
    system("python3 checklist_compstats.py");
    #system("am start -a android.intent.action.VIEW -d file:///data/data/com.termux/files/home/termux_files/reports/activity_checklist.png -t image/png 2>/dev/null");
}

