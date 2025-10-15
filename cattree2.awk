#!/usr/bin/awk -f
BEGIN {
    FS = ",";
    month = sprintf("%02d", ARGV[1]);
    ARGV[1] = "";
    file = "lifetracker.csv";

    print "Category,Activity,Minutes" > "cattree.csv"

    while ((getline line < file) > 0) {
        split(line, f, FS);
        split(f[1], d, "-");
        if (d[2] != month) continue;
        cat = f[4];
        act = f[2];
        min = f[3] + 0;
        sum[cat, act] += min;
        categories[cat] = 1;
        activities[cat, act] = 1;
    }
    close(file);

    for (key in sum) {
        split(key, arr, SUBSEP);
        print arr[1] "," arr[2] "," sum[key] >> "cattree.csv";
    }

    system("python plot_cattree.py");
}

