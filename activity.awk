BEGIN {
    FS = ",";
    month = sprintf("%02d", ARGV[1]);
    ARGV[1] = "";
}
{
    split($1, dparts, "-")
    if (dparts[2] != month)
        next
    day = $1
    act = $NF
    dates[day] = 1
    acts[act] = 1
    has[day,act] = 1
}
END {
    # Gather sorted dates
    n = 0
    for (d in dates) date_arr[n++] = d
    asort(date_arr)

    # Gather sorted acts for consistent column order
    m = 0
    for (a in acts) act_arr[m++] = a
    asort(act_arr)

    # Print CSV header
    printf "Date"
    for (i=1; i<=length(act_arr); i++) printf ",%s", act_arr[i]
    print ""
    # Print checklist matrix sorted by date
    for (i=1; i<=length(date_arr); i++) {
        d = date_arr[i]
        printf "%s", d
        for (j=1; j<=length(act_arr); j++) {
            a = act_arr[j]
            printf ",%s", (has[d,a]) ? "1" : ""
        }
        print ""
    }
}

