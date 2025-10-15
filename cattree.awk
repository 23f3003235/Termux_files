#!/usr/bin/awk -f
BEGIN {
    FS = ",";
    month = sprintf("%02d", ARGV[1]);
    year = ARGV[2];
    ARGV[1] = ""; ARGV[2] = "";
    file = "lifetracker.csv";
    outfile = "cattree.txt";
    tree_header = "Category Tree Graph for Month/Year: " month "/" year;
    print tree_header;
    print tree_header > outfile;
    while ((getline line < file) > 0) {
        split(line, f, FS);
        split(f[1], d, "-");
        if (d[2] != month || d[3] != year) continue;
        cat = f[4];
        act = f[2];
        min = f[3] + 0;
        categories[cat] = 1;
        activities[cat, act] = 1;
        count[cat, act]++;
        sum[cat, act] += min;
    }
    close(file);
    for (c in categories) {
        print c;
        print c > outfile;
        for (a in activities) {
            split(a, arr, SUBSEP);
            if (arr[1] == c) {
                line = sprintf("   └─ %s (count: %d, sum of minutes: %d)", arr[2], count[c, arr[2]], sum[c, arr[2]]);
                print line;
                print line > outfile;
            }
        }
        print "";
        print "" > outfile;
    }
    close(outfile);
    
    system("python3 plot_cattree.py");
    system("am start -a android.intent.action.VIEW -d file:///data/data/com.termux/files/home/termux_files/reports/cattree.png -t image/png 2>/dev/null");
}

