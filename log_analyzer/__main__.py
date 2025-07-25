import os
import re
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime


def analyze_logs(log_dir):
    """
    Analyzes the log files in a directory to count passed and failed tests.
    """
    passed_tests = 0
    failed_tests = 0

    for log_file in log_dir.glob("*.log"):
        with open(log_file, "r") as f:
            content = f.read()
            passed_tests += len(re.findall(r"\[       OK \]", content))
            failed_tests += len(re.findall(r"\[  FAILED  \]", content))

    return passed_tests, failed_tests


def plot_pie_chart(passed_tests, failed_tests, output_dir):
    """
    Plots a pie chart of passed and failed tests.
    """
    labels = "Passed", "Failed"
    sizes = [passed_tests, failed_tests]
    explode = (0, 0.1)  # only "explode" the 2nd slice (i.e. 'Failed')

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct="%1.1f%%", shadow=True, startangle=90)
    ax1.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.savefig(output_dir / "test_results.svg", format="svg")


def parse_system_log(log_file):
    """
    Parses the system log file to extract CPU and memory usage for both system and resymot.
    Handles busybox `top` output format.
    """
    timestamps = []
    cpu_usage = []
    cpu_sys_usage = []
    mem_usage = []
    resymot_cpu = []
    resymot_mem = []

    with open(log_file, "r") as f:
        content = f.read()

    # Regex for busybox top format: CPU: 22.2% usr 74.0% sys  0.0% nic  0.0% idle...
    cpu_re = re.compile(r"CPU: .*?([\d\.]+)% sys .*?([\d\.]+)% idle")

    entries = re.split(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\+\-]\d{2}:\d{2})", content)

    for i in range(1, len(entries), 2):
        timestamp_str = entries[i]
        data_block = entries[i + 1]

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            timestamps.append(timestamp)

            # Parse busybox top format
            cpu_match = cpu_re.search(data_block)
            if cpu_match:
                sys_cpu = float(cpu_match.group(1))
                idle_cpu = float(cpu_match.group(2))
                cpu_usage.append(100 - idle_cpu)
                cpu_sys_usage.append(sys_cpu)
                # For format 2, memory is in KB, so we convert to MB
                mem_data = re.search(r"Mem: (\d+)K used", data_block)
                mem_usage.append(float(mem_data.group(1)) / 1024 if mem_data else None)
            else:
                cpu_usage.append(None)
                cpu_sys_usage.append(None)
                mem_usage.append(None)

            # Resymot CPU and Memory (assuming this format is consistent)
            resymot_cpu_match = re.search(r"Total resymot\.AppImage CPU: ([\d\.]+) %", data_block)
            resymot_cpu.append(float(resymot_cpu_match.group(1)) if resymot_cpu_match else 0)

            resymot_mem_match = re.search(
                r"Total resymot\.AppImage Memory: ([\d\.]+) MB", data_block
            )
            resymot_mem.append(float(resymot_mem_match.group(1)) if resymot_mem_match else 0)

        except (ValueError, AttributeError) as e:
            print(f"Warning: Could not parse data for timestamp {timestamp_str}: {e}")
            continue

    return timestamps, cpu_usage, cpu_sys_usage, mem_usage, resymot_cpu, resymot_mem


def plot_line_charts(
    timestamps, cpu_usage, cpu_sys_usage, mem_usage, resymot_cpu, resymot_mem, output_dir
):
    """
    Plots line charts for CPU and memory usage.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot CPU usage
    ax1.plot(timestamps, cpu_usage, marker="o", linestyle="-", label="System CPU (Active)")
    ax1.plot(timestamps, cpu_sys_usage, marker="s", linestyle="-.", label="System CPU (Sys)")
    ax1.plot(timestamps, resymot_cpu, marker="x", linestyle="--", label="resymot CPU")
    ax1.set_title("CPU Usage Over Time")
    ax1.set_ylabel("CPU Usage (%)")
    ax1.legend()
    ax1.grid(True)

    # Plot Memory usage
    ax2.plot(timestamps, mem_usage, marker="o", linestyle="-", color="r", label="System Memory")
    ax2.plot(timestamps, resymot_mem, marker="x", linestyle="--", color="g", label="resymot Memory")
    ax2.set_title("Memory Usage Over Time")
    ax2.set_ylabel("Memory Usage (MiB)")
    ax2.set_xlabel("Time")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "system_usage.svg", format="svg")


def main():
    """
    Main function to run the log analyzer.
    """
    parser = argparse.ArgumentParser(description="Analyze test logs and generate charts.")
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        default=None,
        help="Path to a specific log directory. Defaults to the newest in 'logs/'.",
    )
    args = parser.parse_args()

    log_dir = args.file
    if log_dir is None:
        log_root_dir = Path("logs")
        if not log_root_dir.is_dir():
            print(f"Error: Log directory '{log_root_dir}' not found.")
            return
        subdirectories = [d for d in log_root_dir.iterdir() if d.is_dir()]
        if not subdirectories:
            print(f"Error: No subdirectories in '{log_root_dir}'.")
            return
        log_dir = max(subdirectories, key=os.path.getmtime)

    if not log_dir.is_dir():
        print(f"Error: '{log_dir}' is not a valid directory.")
        return

    # Test result analysis
    passed, failed = analyze_logs(log_dir)
    if passed + failed > 0:
        plot_pie_chart(passed, failed, log_dir)
        print(f"Pie chart saved to {log_dir / 'test_results.svg'}")
    else:
        print("No test results found.")

    # System log analysis
    try:
        system_log_file = next(log_dir.glob("*_system_log.txt"))
        if system_log_file.is_file():
            (timestamps, cpu, cpu_sys, mem, r_cpu, r_mem) = parse_system_log(system_log_file)
            if timestamps:
                plot_line_charts(timestamps, cpu, cpu_sys, mem, r_cpu, r_mem, log_dir)
                print(f"System usage charts saved to {log_dir / 'system_usage.svg'}")
            else:
                print(f"Could not extract any system usage data from {system_log_file}.")
    except StopIteration:
        print(f"No system log file found in '{log_dir}'.")


if __name__ == "__main__":
    main()
