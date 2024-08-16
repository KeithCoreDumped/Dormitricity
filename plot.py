import datetime as dt
import numpy as np, csv, matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import matplotlib.dates as mdates

# configs
warning_timedelta = dt.timedelta(days=3)
recent_timedelta = dt.timedelta(days=7)
estimate_timedelta = dt.timedelta(days=1)

# reads csv and returns history
def read_csv():
    history: list[tuple[float, dt.datetime, dt.datetime]] = []

    with open(
        "logs/d7fe8b41d5fd171c226357e7060d3b8b011e835d.csv", "rt", encoding="utf-8"
    ) as f:
        reader = csv.reader(f)
        next(reader)
        for rows in reader:
            remain, query_time, request_time = [col.strip() for col in rows]
            remain = float(remain)
            query_time = dt.datetime.fromisoformat(query_time)
            request_time = dt.datetime.fromisoformat(request_time)
            history.append((remain, query_time, request_time))

    return history


# filter out entries within recent_timedelta
def filter_recent(
    history: list[tuple[float, dt.datetime, dt.datetime]]
) -> list[tuple[float, dt.datetime, dt.datetime]]:
    first_idx = 0
    last_datetime = history[-1][1]
    for _, datetime, _ in history:
        if last_datetime - datetime < recent_timedelta:
            break
        first_idx += 1
    return history[first_idx:]


# subtract recharges from remaining, letting values go negtive
def decharge(history: list[tuple[float, dt.datetime, dt.datetime]]):
    def find_smallest_greater(arr, val):
        arr = np.asarray(arr)
        greater_than_val = arr[arr > val]
        if greater_than_val.size == 0:
            return None
        return greater_than_val.min()

    recharge_values = [25, 50, 75, 100, 150, 200]
    last_value = history[0][0]
    recharges: list[tuple[float, int]] = []
    recharged_sum = 0  # to be subtracted from values
    decharged: list[tuple[float, dt.datetime, dt.datetime]] = [
        history[0]
    ]  # history with recharged values removed, values can be below zero
    for i, (value, query_time, request_time) in enumerate(history[1:]):
        if value > last_value:
            # recharge occurs
            delta = value - last_value
            recharged = find_smallest_greater(recharge_values, delta)
            assert (
                recharged
            ), "amount of recharge more than the maximum value of 200 within sample interval"
            # todo: handle cases when the amount is less than a minimum of 25
            recharged_sum += recharged
            recharges.append((recharged, i))
            # print(f"recharged by {recharged}(delta:{delta}) between {last_query} and {query_time}")
        decharged_value = value - recharged_sum
        decharged.append((decharged_value, query_time, request_time))
        last_value = value
    # return decharged, recharges
    # test
    # print("\n".join(map(str, decharged)))
    for recharged, idx in recharges:
        before = history[idx]
        after = history[idx + 1]
        delta = after[0] - before[0]
        before_time = before[1]
        after_time = after[1]
        print(
            f"recharged by {recharged}(delta:{delta}) between {before_time} and {after_time}"
        )

    return decharged, recharges


# costs of each day
def get_cost(history_decharged: list[tuple[float, dt.datetime, dt.datetime]]):
    costs: list[tuple[float, dt.date]] = []
    # complete first and last day

    # interop
    x = [x[1].timestamp() for x in history_decharged]
    y = [x[0] for x in history_decharged]
    interop_f = interp1d(
        x, y, kind="linear", bounds_error=False, fill_value=(y[0], y[-1])
    )
    start_date = history_decharged[0][1].date()
    end_date = history_decharged[-1][1].date() + dt.timedelta(days=1)
    duration_days = (end_date - start_date).days
    for i in range(duration_days):
        date = start_date + dt.timedelta(days=i)
        before_ts = dt.datetime.combine(date, dt.time()).timestamp()
        after_ts = dt.datetime.combine(
            start_date + dt.timedelta(days=i + 1), dt.time()
        ).timestamp()
        before_val = interop_f(before_ts)
        after_val = interop_f(after_ts)
        costs.append((before_val - after_val, date))
    # return costs
    # test
    for cost, date in costs:
        print(f"{cost} kWh spent on {date}")


# plot history diagram with recharge events annotated
def plot_history(
    history: list[tuple[float, dt.datetime, dt.datetime]],
    recharges: list[tuple[float, int]],
):
    # make extended_history
    recharge_dict = dict(map(lambda vi: (vi[1], vi[0]), recharges))

    extended_history: list[tuple[float, dt.datetime, dt.datetime]] = []

    for i, (val, query_time, request_time) in enumerate(history):
        extended_history.append((val, query_time, request_time))
        if i in recharge_dict.keys():
            before = history[i]
            after = history[i + 1]
            mid_val = (before[0] + after[0]) / 2
            mid_time = before[1] + (after[1] - before[1]) / 2
            recharge_val = recharge_dict[i]
            extended_history.append((mid_val - recharge_val / 2, mid_time, None))
            extended_history.append((mid_val + recharge_val / 2, mid_time, None))

    def plot_segment(history_segment: list[tuple[float, dt.datetime, dt.datetime]]):
        values = [item[0] for item in history_segment]
        dates = [item[1] for item in history_segment]
        plt.plot(
            dates,
            values,
            marker="o",
            linestyle="-",
            color="b",
            label="Remaining Amount",
        )

    def plot_recharge(extended_history: list[tuple[float, dt.datetime, dt.datetime]]):
        vbars = list(filter(lambda vqr: vqr[2] is None, extended_history))
        assert len(vbars) % 2 == 0
        for before, after in zip(vbars[0::2], vbars[1::2]):
            plt.plot(
                [before[1], after[1]],  # x-axis
                [before[0], after[0]],  # y-axis
                linestyle="-",
                color="orange",
                label="Recharge",
            )

            # 在垂直条的中间位置添加充电量的注释
            plt.text(
                before[1],  # before[1] == after[1]
                (after[0] + before[0]) / 2,
                f"+{after[0] - before[0]} kWh",
                color="red",
                fontsize=10,
                ha="right",
                va="center",
                rotation="vertical",
            )

    # split extended_history into segments

    values = np.array(list(map(lambda x: x[0], extended_history)))
    lshift = values[1:]
    rcrop = values[:-1]
    diff = rcrop - lshift
    # recharges_count = np.count_nonzero(recharges_event)
    begin_idx = 0

    plot_recharge(extended_history)

    for [i] in (
        np.where(diff < 0) if recharges else []
    ):  # np.where returns [[]] when condition is never satisfied, and [i] fails
        i += 1  # offset 1 from differentiation
        plot_segment(extended_history[begin_idx:i])
        begin_idx = i

    plot_segment(extended_history[begin_idx:])


# plot an arrow to when the estimated exhaustion occurs with text description
def plot_exhaustion(
    history_decharged: list[tuple[float, dt.datetime, dt.datetime]],
    history_last: tuple[float, dt.datetime, dt.datetime],
):
    tlast = history_last[1]
    for i, (v, tq, tr) in enumerate(history_decharged):
        if tlast - tq < estimate_timedelta:
            break
    history_decharged = history_decharged[i:]

    # 分离出电量值和时间戳
    values = np.array([item[0] for item in history_decharged])
    timestamps = np.array([item[1].timestamp() for item in history_decharged])

    # linear fit
    slope, intercept = np.polyfit(timestamps, values, 1)  # k, b

    # calculate offset
    y_est = slope * history_last[1].timestamp() + intercept
    y_actual = history_last[0]
    y_offset = y_actual - y_est
    intercept += y_offset

    # y=kx+b
    # y=0 => kx=-b => x=-b/k
    exhaustion_x = -intercept / slope
    exhaustion_y = 0.0

    begin_x = timestamps[-1]
    begin_y = slope * begin_x + intercept
    begin_x = dt.datetime.fromtimestamp(begin_x)

    # 将时间戳转换为datetime对象
    exhaustion_x = dt.datetime.fromtimestamp(exhaustion_x)
    print(f"exhaustion_x = {exhaustion_x}")

    # time of exhausation threshold = 3 days
    if (exhaustion_x - history_last[1]) >= warning_timedelta:
        exhaustion_x = history_last[1] + warning_timedelta
        exhaustion_y = slope * exhaustion_x.timestamp() + intercept
        plt.text(
            exhaustion_x,
            exhaustion_y + 10,
            f"no exhaustion\nwithin {warning_timedelta.days} days",
            fontsize=10,
            ha="center",
        )
    else:
        time_diff = exhaustion_x - dt.datetime.now()
        plt.annotate(
            f"estimated exhaustion at\n{str(exhaustion_x).split('.')[0]}\nor {str(time_diff).split('.')[0]} later",
            xy=(exhaustion_x, exhaustion_y),  # 箭头指向的位置
            xytext=(exhaustion_x, exhaustion_y + 10),  # 箭头起始位置
            arrowprops=dict(facecolor="red", shrink=0.05, headwidth=10, width=2),
            fontsize=10,
            ha="center",
        )

    # 绘制延长虚线
    plt.plot(
        [begin_x, exhaustion_x],
        [begin_y, exhaustion_y],
        linestyle="--",
        color="gray",
        label="Estimated Exhaustion",
    )
    return exhaustion_x


def plot_watts(history_decharged: list[tuple[float, dt.datetime, dt.datetime]]):
    timestamps = np.array([x[1] for x in history_decharged])
    widths = timestamps[1:] - timestamps[:-1]
    timestamps = timestamps[:-1]
    values = np.array([x[0] for x in history_decharged])
    diffs = values[:-1] - values[1:]
    watts = diffs / [x.total_seconds() for x in widths] * 3.6e6
    plt.bar(timestamps, watts, width=widths, align="edge", color="skyblue")


if __name__ == "__main__":
    # history = [
    #     (10.0, dt.datetime(2024, 8, 8, 0, 0, 0), dt.datetime(2024, 8, 8, 23, 59, 59)),
    #     (8.0, dt.datetime(2024, 8, 9, 0, 0, 0), dt.datetime(2024, 8, 9, 23, 59, 59)),
    #     (6.0, dt.datetime(2024, 8, 10, 0, 0, 0), dt.datetime(2024, 8, 10, 23, 59, 59)),
    #     (4.0, dt.datetime(2024, 8, 11, 0, 0, 0), dt.datetime(2024, 8, 11, 23, 59, 59)),
    #     (2.0, dt.datetime(2024, 8, 12, 0, 0, 0), dt.datetime(2024, 8, 12, 23, 59, 59)),
    #     (25, dt.datetime(2024, 8, 13, 0, 0, 0), dt.datetime(2024, 8, 13, 23, 59, 59)),
    #     (21, dt.datetime(2024, 8, 14, 0, 0, 0), dt.datetime(2024, 8, 13, 23, 59, 59)),
    #     (16, dt.datetime(2024, 8, 15, 0, 0, 0), dt.datetime(2024, 8, 13, 23, 59, 59)),
    #     (11, dt.datetime(2024, 8, 16, 0, 0, 0), dt.datetime(2024, 8, 13, 23, 59, 59)),
    # ]
    history = read_csv()
    history = filter_recent(history)
    decharged, recharges = decharge(history)
    costs = get_cost(decharged)

    plt.figure(1, figsize=(10, 6))
    exhaust_time = plot_exhaustion(decharged, history[-1])
    plot_history(history, recharges)
    print(f"estimate time of exhaustion: {exhaust_time}")

    plt.title("History of Remaining Amount Over Time")
    plt.xlabel("Date")
    plt.ylabel("Remaining Amount (kWh)")

    # auto format x-axis date
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.gcf().autofmt_xdate()

    # plt.legend()

    # plt.show() # we don't have a display to show the plot in github actions
    plt.savefig("images/recent.png", format="png")

    # plot watts
    plt.figure(2, figsize=(10, 6))
    plot_watts(decharged)
    plt.title("History of Power Consumption")
    plt.xlabel("Date")
    plt.ylabel("Power(W)")

    # auto format x-axis date
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.gcf().autofmt_xdate()
    plt.savefig("images/watts.png", format="png")
