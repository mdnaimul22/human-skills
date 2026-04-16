#!/usr/bin/env python3
"""
zram-optimizer Multi-Tool Evaluator CLI

Commands:
  run <pressure_gb>    - Run the deterministic multi-metric performance evaluator
  bench                - Run the multi-profile automated benchmark suite
  deploy <alg> ...     - Apply the winning configuration permanently
  status               - Print current zram and swap runtime status
"""

import sys
import os
import subprocess
import time
import csv
import glob
import argparse
import io
import contextlib

from pathlib import Path
from helpers.tool import Tool, Response


_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR.parent.parent
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))


# ──────────────────────────────────────────────
# 0. CONFIGURATION & PARAMETERS
# ──────────────────────────────────────────────

class CONFIG:
    # Parameters
    CHUNK_SIZE = 64 * 1024 * 1024                            # Individual memory block size (64 MB) for pressure testing
    DEFAULT_PRESSURE_GB = 4.0                                # Default memory pressure to simulate if not specified
    
    # Scoring Weights (Must sum to 1.0), These define horizontal importance for the Final Score Calculation
    WEIGHT_ALLOC   = 0.25                                    # Importance of initial memory allocation speed
    WEIGHT_READ    = 0.30                                    # Importance of sequential page reading throughput
    WEIGHT_RANDOM  = 0.25                                    # Importance of non-linear random access latency/speed
    WEIGHT_PROCESS = 0.20                                    # Importance of data transformation (XOR) efficiency
    
    # Benchmarking Matrix
    BENCH_ALGORITHMS = ["lz4", "lzo-rle", "zstd"]            # List of compression algorithms to test
    BENCH_PRIORITIES = [200, 500, 1000]                      # Priority levels to test (higher = used first)
    BENCH_SWAPPINESS = [150, 180, 200, 220, 250]             # Kernel swappiness thresholds to iterate
    BENCH_PAGE_CLUSTER = [0, 1]                              # Number of pages to read-ahead (0 is best for zram)
    
    # File Paths
    RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results.csv") # Benchmark output
    
    # System Defaults (for cleanup/restoration after benchmarking)
    SYS_DEFAULT_SWAPPINESS = 150                             # Standard Linux default swappiness
    SYS_DEFAULT_PAGE_CLUSTER = 3                             # Standard Linux default page-cluster
    
    # Internal Evaluator Constants
    DETERMINISTIC_SEED = 42                                  # Fixed seed for PRNG to ensure reproducible benchmark results
    DATA_PROCESS_XOR_KEY = 0xAA                              # Hex key used for simulating data processing overhead


# ──────────────────────────────────────────────
# 1. EVALUATOR LOGIC (run command)
# ──────────────────────────────────────────────

def create_template(size: int) -> bytearray:
    pattern = bytes(range(256))
    repeats = size // len(pattern) + 1
    return bytearray((pattern * repeats)[:size])

def deterministic_indices(n: int, count: int) -> list:
    indices = []
    x = CONFIG.DETERMINISTIC_SEED  # fixed seed
    for _ in range(count):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        indices.append(x % n)
    return indices

def benchmark_memory(pressure_gb: float) -> dict:
    total_bytes = int(pressure_gb * 1024 * 1024 * 1024)
    num_chunks = max(1, total_bytes // CONFIG.CHUNK_SIZE)
    total_data_gb = (num_chunks * CONFIG.CHUNK_SIZE) / (1024 ** 3)
    template_chunk = create_template(CONFIG.CHUNK_SIZE)

    chunks = []
    t0 = time.perf_counter()
    for _ in range(num_chunks):
        chunks.append(bytearray(template_chunk))
    alloc_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    checksum = 0
    for chunk in chunks:
        for offset in range(0, len(chunk), 4096):  # touch every page (4K)
            checksum += chunk[offset]
    seq_read_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    access_indices = deterministic_indices(num_chunks, num_chunks * 3)
    byte_offsets = deterministic_indices(CONFIG.CHUNK_SIZE, num_chunks * 3)
    t0 = time.perf_counter()
    for i in range(len(access_indices)):
        ci = access_indices[i]
        bi = byte_offsets[i]
        checksum += chunks[ci][bi]
    random_access_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for chunk in chunks:
        # XOR first 4K of every chunk (simulates data processing)
        for j in range(0, 4096, 256):
            for k in range(256):
                chunk[j + k] ^= CONFIG.DATA_PROCESS_XOR_KEY
    data_process_time = time.perf_counter() - t0

    # Prevent optimization
    _ = checksum

    alloc_speed = total_data_gb / alloc_time if alloc_time > 0 else 0
    seq_read_speed = total_data_gb / seq_read_time if seq_read_time > 0 else 0
    random_access_speed = total_data_gb / random_access_time if random_access_time > 0 else 0
    data_process_speed = total_data_gb / data_process_time if data_process_time > 0 else 0

    total_time = alloc_time + seq_read_time + random_access_time + data_process_time

    final_score = (
        alloc_speed * CONFIG.WEIGHT_ALLOC
        + seq_read_speed * CONFIG.WEIGHT_READ
        + random_access_speed * CONFIG.WEIGHT_RANDOM
        + data_process_speed * CONFIG.WEIGHT_PROCESS
    )

    return {
        "alloc_speed": alloc_speed,
        "seq_read_speed": seq_read_speed,
        "random_access_speed": random_access_speed,
        "data_process_speed": data_process_speed,
        "alloc_time": alloc_time,
        "seq_read_time": seq_read_time,
        "random_access_time": random_access_time,
        "data_process_time": data_process_time,
        "total_time": total_time,
        "final_score": final_score,
    }

def cmd_run(args):
    """Run the evaluator payload."""
    m = benchmark_memory(args.pressure_gb)
    print(f"ALLOC_SPEED_GBs {m['alloc_speed']:.4f}")
    print(f"SEQ_READ_SPEED_GBs {m['seq_read_speed']:.4f}")
    print(f"RANDOM_ACCESS_GBs {m['random_access_speed']:.4f}")
    print(f"DATA_PROCESS_GBs {m['data_process_speed']:.4f}")
    print(f"ALLOC_TIME_s {m['alloc_time']:.4f}")
    print(f"SEQ_READ_TIME_s {m['seq_read_time']:.4f}")
    print(f"RANDOM_ACCESS_TIME_s {m['random_access_time']:.4f}")
    print(f"DATA_PROCESS_TIME_s {m['data_process_time']:.4f}")
    print(f"TOTAL_TIME_s {m['total_time']:.4f}")
    print(f"FINAL_SCORE {m['final_score']:.4f}")


# ──────────────────────────────────────────────
# 2. BENCHMARK HARNESS LOGIC (bench command)
# ──────────────────────────────────────────────

def get_disk_size() -> str:
    try:
        mem_gb = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / (1024**3)
        size = min(int(mem_gb * 0.55), 8)
        return f"{max(size, 2)}G"
    except Exception:
        return "4G"

def get_pressure_gb() -> float:
    try:
        mem_gb = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / (1024**3)
        return round(mem_gb * 0.3, 1)
    except Exception:
        return CONFIG.DEFAULT_PRESSURE_GB

def sh_run(cmd: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)

def nuclear_cleanup():
    sh_run("swapoff -a")
    for dev in sorted(f"/dev/{d}" for d in os.listdir("/dev") if d.startswith("zram")):
        sh_run(f"swapoff {dev}")
        sh_run(f"zramctl --reset {dev}")
    sh_run("sync")
    sh_run("bash -c 'echo 3 > /proc/sys/vm/drop_caches'")
    time.sleep(3)

def setup_zram(algorithm: str, priority: int, disk_size: str) -> str:
    cores = os.cpu_count() or 4
    result = sh_run(f"zramctl --find --size {disk_size} --streams {cores} --algorithm {algorithm}", check=True)
    dev = result.stdout.strip()
    sh_run(f"mkswap {dev}", check=True)
    sh_run(f"swapon {dev} -p {priority}", check=True)
    return dev

def set_kernel_params(swappiness: int, page_cluster: int):
    sh_run(f"bash -c 'echo {swappiness} > /proc/sys/vm/swappiness'")
    sh_run(f"bash -c 'echo {page_cluster} > /proc/sys/vm/page-cluster'")

def run_evaluator_subprocess(pressure_gb: float) -> dict:
    """Run `evaluator.py run` as isolated subprocess to avoid GC issues."""
    script_path = os.path.abspath(__file__)
    result = sh_run(f"{sys.executable} {script_path} run {pressure_gb}")
    metrics = {
        "ALLOC_SPEED": 0.0,
        "SEQ_READ_SPEED": 0.0,
        "RANDOM_ACCESS": 0.0,
        "DATA_PROCESS": 0.0,
        "FINAL_SCORE": 0.0
    }
    
    if result.returncode != 0:
        print(f"  [ERROR] Evaluator failed: {result.stderr.strip()}", file=sys.stderr)
        return metrics

    for line in result.stdout.strip().split("\n"):
        parts = line.split()
        if len(parts) == 2:
            key, val = parts[0], parts[1]
            if key == "ALLOC_SPEED_GBs": metrics["ALLOC_SPEED"] = float(val)
            elif key == "SEQ_READ_SPEED_GBs": metrics["SEQ_READ_SPEED"] = float(val)
            elif key == "RANDOM_ACCESS_GBs": metrics["RANDOM_ACCESS"] = float(val)
            elif key == "DATA_PROCESS_GBs": metrics["DATA_PROCESS"] = float(val)
            elif key == "FINAL_SCORE": metrics["FINAL_SCORE"] = float(val)
            
    return metrics

def cmd_bench(args):
    if os.geteuid() != 0:
        print("ERROR: This command must be run as root (sudo).", file=sys.stderr)
        sys.exit(1)

    disk_size = get_disk_size()
    pressure_gb = get_pressure_gb()
    results_file = CONFIG.RESULTS_FILE

    algorithms = CONFIG.BENCH_ALGORITHMS
    swap_priority_values = CONFIG.BENCH_PRIORITIES
    swappiness_values = CONFIG.BENCH_SWAPPINESS
    page_cluster_values = CONFIG.BENCH_PAGE_CLUSTER

    configs = [(alg, prio, swap, pc) for alg in algorithms for prio in swap_priority_values for swap in swappiness_values for pc in page_cluster_values]
    total_tests = len(configs)
    
    print(f"===========================================")
    print(f" Starting Z-Ram Benchmark Suite ")
    print(f"===========================================")
    print(f" Disk Size: {disk_size} | Pressure: {pressure_gb}GB | Total Tests: {total_tests}")
    print(f" Algorithms:   {algorithms}")
    print(f" Priorities:   {swap_priority_values}")
    print(f" Swappiness:   {swappiness_values}")
    print(f" Page-Cluster: {page_cluster_values}")
    print(f"===========================================")

    results = []
    start_time_bench = time.perf_counter()
    
    with open(results_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Rank", "Algorithm", "Priority", "Swappiness", "PageCluster", "FinalScore", "Alloc(GB/s)", "SeqRead(GB/s)", "Random(GB/s)", "Process(GB/s)"])

        for i, (alg, prio, swap, pc) in enumerate(configs, 1):
            print(f"\n[{i}/{total_tests}] Testing => Algorithm: {alg}")
            print(f"  ├─ Swap Priority: {prio} | Page-Cluster: {pc} | Swappiness: {swap}")
            
            # Calculate ETA
            if i > 1:
                elapsed_so_far = time.perf_counter() - start_time_bench
                avg_time_per_test = elapsed_so_far / (i - 1)
                remaining_tests = total_tests - (i - 1)
                eta_total_sec = avg_time_per_test * remaining_tests
                eta_min = int(eta_total_sec // 60)
                eta_sec = int(eta_total_sec % 60)
                print(f"  ├─ [Please Wait] Estimated Time Remaining: {eta_min}m {eta_sec}s")
            else:
                print(f"  ├─ [Please Wait] Calculating Estimated Time...")

            nuclear_cleanup()
            
            try:
                dev = setup_zram(alg, prio, disk_size)
            except subprocess.CalledProcessError as e:
                print(f"  [SKIP] Failed to create zram: {e.stderr.strip()}")
                continue

            set_kernel_params(swap, pc)

            metrics = run_evaluator_subprocess(pressure_gb)
            
            print(f"  ├─ Alloc Speed:  {metrics['ALLOC_SPEED']:.3f} GB/s")
            print(f"  ├─ Seq Read:     {metrics['SEQ_READ_SPEED']:.3f} GB/s")
            print(f"  ├─ Random Accs:  {metrics['RANDOM_ACCESS']:.3f} GB/s")
            print(f"  ├─ Data Process: {metrics['DATA_PROCESS']:.3f} GB/s")
            print(f"  └─ FINAL SCORE:  {metrics['FINAL_SCORE']:.4f} Weighted Peak")

            results.append({
                "alg": alg, "prio": prio, "swap": swap, "pc": pc,
                "score": metrics["FINAL_SCORE"],
                "alloc": metrics["ALLOC_SPEED"],
                "read": metrics["SEQ_READ_SPEED"],
                "rand": metrics["RANDOM_ACCESS"],
                "proc": metrics["DATA_PROCESS"]
            })

            sh_run(f"swapoff {dev}")
            sh_run(f"zramctl --reset {dev}")

    nuclear_cleanup()
    sh_run(f"bash -c 'echo {CONFIG.SYS_DEFAULT_SWAPPINESS} > /proc/sys/vm/swappiness'")
    sh_run(f"bash -c 'echo {CONFIG.SYS_DEFAULT_PAGE_CLUSTER} > /proc/sys/vm/page-cluster'")

    results.sort(key=lambda x: x["score"], reverse=True)

    with open(results_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Rank", "Algorithm", "Priority", "Swappiness", "PageCluster", "FinalScore", "Alloc(GB/s)", "SeqRead(GB/s)", "Random(GB/s)", "Process(GB/s)"])
        for rank, r in enumerate(results, 1):
            writer.writerow([rank, r["alg"], r["prio"], r["swap"], r["pc"], f"{r['score']:.4f}", f"{r['alloc']:.3f}", f"{r['read']:.3f}", f"{r['rand']:.3f}", f"{r['proc']:.3f}"])

    print(f"\n================================================")
    print(f" BENCHMARK COMPLETE — TOP 5 CONFIGURATIONS ")
    print(f"================================================")
    print(f"Rank | Algorithm | Prio | Swap | PC | Final Score | Alloc | Read  | Random | Process")
    print(f"-----|-----------|------|------|----|-------------|-------|-------|--------|--------")
    for r in enumerate(results[:5], 1):
        rank = r[0]
        v = r[1]
        print(f" #{rank:<2} | {v['alg']:<9} | {v['prio']:<4} | {v['swap']:<4} | {v['pc']:<2} | {v['score']:<11.4f} | {v['alloc']:.2f}  | {v['read']:.2f}  | {v['rand']:.2f}   | {v['proc']:.2f}")
    
    if results:
        winner = results[0]
        print(f"\n================================================")
        print(f" ⭐ BENCHMARK WINNER & DEPLOYMENT SUGGESTION ⭐ ")
        print(f"================================================")
        print(f"Optimal configuration for this system is:")
        print(f"  • Algorithm:    {winner['alg']}")
        print(f"  • Priority:     {winner['prio']}")
        print(f"  • Swappiness:   {winner['swap']}")
        print(f"  • Page-Cluster: {winner['pc']}")
        print(f"")
        script_name = os.path.basename(sys.argv[0])
        print(f"To deploy this winner permanently, run:")
        print(f"  sudo python3 {script_name} deploy {winner['alg']} {disk_size} {winner['prio']} {winner['swap']} {winner['pc']}")
        print(f"")
        print(f"Full ranked results saved to: {results_file}")


# ──────────────────────────────────────────────
# 3. DEPLOY & STATUS LOGIC (deploy, status commands)
# ──────────────────────────────────────────────

def cmd_deploy(args):
    if os.geteuid() != 0:
        print("ERROR: This command must be run as root (sudo).", file=sys.stderr)
        sys.exit(1)

    print("============================================")
    print("  zram Deployment")
    print("============================================")
    print(f"  Algorithm:    {args.algorithm}")
    print(f"  Disk Size:    {args.disk_size}")
    print(f"  Mem Limit:    {args.disk_size}")
    print(f"  Priority:     {args.priority}")
    print(f"  Swappiness:   {args.swappiness}")
    print(f"  Page Cluster: {args.page_cluster}")
    print("============================================")

    print("\n[1/4] Disabling all existing swap...")
    sh_run("swapoff -a -v")

    for dev in glob.glob("/dev/zram*"):
        if os.path.exists(dev):
            sh_run(f"swapoff {dev}")
            sh_run(f"zramctl --reset {dev}")
    
    sh_run("sync")
    sh_run("bash -c 'echo 3 > /proc/sys/vm/drop_caches'")
    time.sleep(2)
    print("  Done.")

    print("\n[2/4] Writing optimized /etc/ztab...")
    ztab_content = f"# swap  alg             mem_limit       disk_size       swap_priority   page-cluster    swappiness\nswap    {args.algorithm}             {args.disk_size}              {args.disk_size}              {args.priority}             {args.page_cluster}               {args.swappiness}\n"
    
    with open("/etc/ztab", "w") as f:
        f.write(ztab_content)
    
    print("  Written:")
    print(ztab_content.strip())
    print()

    print("[3/4] Restarting zram-config service...")
    sh_run("systemctl stop zram-config")
    time.sleep(1)
    sh_run("systemctl start zram-config")
    print("  Service restarted.")

    print("\n[4/4] Verifying deployment...")
    cmd_status(args)

    print("\n============================================")
    print("  Deployment COMPLETE")
    print("  Your system is now running optimized zram.")
    print("============================================")


def cmd_status(args):
    print("\n--- zramctl ---")
    print(sh_run("zramctl").stdout.strip())
    
    print("\n--- swapon -s ---")
    print(sh_run("swapon -s").stdout.strip())
    
    print("\n--- Kernel Parameters ---")
    try:
        with open("/proc/sys/vm/swappiness", "r") as f:
            swap_val = f.read().strip()
        print(f"  vm.swappiness = {swap_val}")
    except:
        pass
    try:
        with open("/proc/sys/vm/page-cluster", "r") as f:
            pc_val = f.read().strip()
        print(f"  vm.page-cluster = {pc_val}")
    except:
        pass

    print("\n--- Memory Overview ---")
    print(sh_run("free -h").stdout.strip())


# ──────────────────────────────────────────────
# MAIN CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="zram-optimizer: A-to-Z High-Performance zram Engine",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    parser_run = subparsers.add_parser("run", help="Run the deterministic memory pressure evaluator")
    parser_run.add_argument("pressure_gb", type=float, nargs="?", default=CONFIG.DEFAULT_PRESSURE_GB, help=f"GB of memory pressure to simulate (default: {CONFIG.DEFAULT_PRESSURE_GB})")

    # Command: bench
    parser_bench = subparsers.add_parser("bench", help="Run the automated multi-profile zram benchmark harness")

    # Command: deploy
    parser_deploy = subparsers.add_parser("deploy", help="Deploy a specific zram configuration permanently")
    parser_deploy.add_argument("algorithm", type=str, choices=["lz4", "lzo-rle", "zstd", "lzo", "lz4hc"], help="Compression algorithm")
    parser_deploy.add_argument("disk_size", type=str, help="Disk size (e.g. 8G)")
    parser_deploy.add_argument("priority", type=int, help="Swap priority (e.g. 1000)")
    parser_deploy.add_argument("swappiness", type=int, help="Kernel swappiness (e.g. 180)")
    parser_deploy.add_argument("page_cluster", type=int, help="Kernel page-cluster (e.g. 0)")

    # Command: status
    parser_status = subparsers.add_parser("status", help="Print current zram and swap status")

    # Command: help / h (Alias for --help)
    parser_h = subparsers.add_parser("h", help="Show this help message")
    parser_help = subparsers.add_parser("help", help="Show this help message")

    args = parser.parse_args()

    if args.command in ["run"]:
        cmd_run(args)
    elif args.command == "bench":
        cmd_bench(args)
    elif args.command == "deploy":
        cmd_deploy(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command in ["h", "help"]:
        parser.print_help()
    else:
        parser.print_help()
        sys.exit(1)


class ZramOptimizer(Tool):
    """
    Wrapper for zram-optimizer's evaluator.
    Captures stdout to return as a Response string.
    """
    name = "zram_optimizer"
    description = "Optimizes Linux Z-RAM and swap configurations deterministically."
    arguments = {
        "command": "Required. One of: run, bench, deploy, status",
        "pressure_gb": "Optional float (run cmd). GB memory pressure.",
        "algorithm": "Optional string (deploy cmd). lz4, lzo-rle, etc.",
        "disk_size": "Optional string (deploy cmd). e.g., '8G'",
        "priority": "Optional int (deploy cmd).",
        "swappiness": "Optional int (deploy cmd).",
        "page_cluster": "Optional int (deploy cmd)."
    }
    instruction = "For Skill instruction run human-skills --skill_info zram-optimizer"

    async def execute(self, **kwargs) -> Response:
        command = self.args.get("command")
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            class DummyArgs:
                pass
            args = DummyArgs()
            args.command = command
            
            try:
                if command == "run":
                    args.pressure_gb = float(self.args.get("pressure_gb", CONFIG.DEFAULT_PRESSURE_GB))
                    cmd_run(args)
                elif command == "bench":
                    cmd_bench(args)
                elif command == "deploy":
                    args.algorithm = self.args.get("algorithm")
                    args.disk_size = self.args.get("disk_size")
                    args.priority = int(self.args.get("priority", 1000))
                    args.swappiness = int(self.args.get("swappiness", 180))
                    args.page_cluster = int(self.args.get("page_cluster", 0))
                    cmd_deploy(args)
                elif command == "status":
                    cmd_status(args)
                else:
                    return Response(message=f"Unknown command: {command}", break_loop=False)
            except Exception as e:
                print(f"Error executing {command}: {str(e)}")
                
        return Response(message=f.getvalue(), break_loop=False)

if __name__ == "__main__":
    main()
