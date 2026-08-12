p = "scripts/verify_goal_markets.py"

s = open(p, encoding="utf-8").read()

marker = '    print()\n    print("LAMBDA")'

insert = r'''
    print()
    print("CALIBRATION")
    print("===========")

    for name, key, actual_function in [
        ("OVER 1.5", "over_15", lambda r: r["actual_total"] > 1),
        ("OVER 2.5", "over_25", lambda r: r["actual_total"] > 2),
        ("OVER 3.5", "over_35", lambda r: r["actual_total"] > 3),
        ("BTTS", "btts", lambda r: r["actual_btts"]),
    ]:
        print()
        print(name)

        buckets = [
            (0.00, 0.20),
            (0.20, 0.40),
            (0.40, 0.50),
            (0.50, 0.60),
            (0.60, 0.80),
            (0.80, 1.01),
        ]

        for low, high in buckets:
            rows = [
                r for r in results
                if low <= r[key] < high
            ]

            if not rows:
                continue

            actual_rate = sum(
                actual_function(r)
                for r in rows
            ) / len(rows)

            predicted_rate = sum(
                r[key]
                for r in rows
            ) / len(rows)

            print(
                f"{low:.2f}-{high:.2f}: "
                f"n={len(rows):3d} "
                f"pred={predicted_rate:.4f} "
                f"actual={actual_rate:.4f}"
            )
'''

if marker not in s:
    raise SystemExit("MARKER NOT FOUND")

s = s.replace(marker, insert + "\n" + marker)

open(p, "w", encoding="utf-8").write(s)

print("CALIBRATION ADDED")
