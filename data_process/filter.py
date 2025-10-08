import json
import sys
import argparse
import sympy as sp
from tqdm import tqdm
from qwen_math_eval_toolkit.grader import math_equal_process
import multiprocessing as mp

sys.set_int_max_str_digits(1000000)

timeout_count = 0
exception_count = 0

def is_valid_entry(entry):
    output = entry.get("output")
    input_val = entry.get("input")
    error = entry.get("error")

    if output in ("", None):
        return False
    if input_val in ("", None):
        return False
    if error is not None:
        return False
    return True

def filter_jsonl(input_file, output_file, rejected_output_file, compare_gt=False, timeout_per_item=3, num_processes=8):
    global timeout_count, exception_count
    raw_total_entries = 0
    total_entries = 0
    valid_entries = 0
    entries = []

    with open(input_file, "r", encoding="utf-8") as fin, \
         open(rejected_output_file, "w", encoding="utf-8") as fout_reject_prepare:
        for line in fin:
            raw_total_entries += 1
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if is_valid_entry(entry):
                    entries.append(entry)
                else:
                    entry["rejection_reason"] = "invalid_entry"
                    fout_reject_prepare.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            except json.JSONDecodeError:
                continue

    print(f"Loaded {len(entries)}/{raw_total_entries} valid entries for filtering.")
    
    if not compare_gt:
        with open(output_file, "w", encoding="utf-8") as fout_valid:
            for entry in entries:
                fout_valid.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        print(f"Saved {len(entries)} entries without ground truth comparison.")
        return

    params = [(idx, str(entry["output"]), str(entry.get("answer", ""))) for idx, entry in enumerate(entries)]

    with mp.Pool(processes=num_processes) as pool, \
         open(output_file, "w", encoding="utf-8") as fout_valid, \
         open(rejected_output_file, "a", encoding="utf-8") as fout_reject:

        results = [pool.apply_async(math_equal_process, args=(param,)) for param in params]

        with tqdm(total=len(entries), desc="Evaluate") as progress_bar:
            for idx, result in enumerate(results):
                try:
                    status = result.get(timeout=timeout_per_item)
                    total_entries += 1
                    if status is True:
                        fout_valid.write(json.dumps(entries[idx], ensure_ascii=False, default=str) + "\n")
                        valid_entries += 1
                    else:
                        entries[idx]["rejection_reason"] = "math_not_equal"
                        fout_reject.write(json.dumps(entries[idx], ensure_ascii=False, default=str) + "\n")
                except Exception as e:
                    exception_count += 1
                    entries[idx]["rejection_reason"] = f"exception: {type(e).__name__}"
                    fout_reject.write(json.dumps(entries[idx], ensure_ascii=False, default=str) + "\n")
                    print(f"Exception in processing entry {idx}: {e}")
                progress_bar.update(1)

    print("\n=== Filter Summary ===")
    print(f"Total entries processed: {total_entries}")
    print(f"Valid entries: {valid_entries}")
    print(f"Exception count: {exception_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter a JSONL dataset by validity and optional math equality check.")
    parser.add_argument("--input", required=True, help="Path to input JSONL file")
    parser.add_argument("--output", required=True, help="Path to output (valid) JSONL file")
    parser.add_argument("--compare_gt", action="store_true", help="Compare with ground truth answer")
    parser.add_argument("--timeout", type=int, default=3, help="Timeout per item (seconds)")
    parser.add_argument("--num_processes", type=int, default=64, help="Number of parallel processes")

    args = parser.parse_args()
    rejected_path = args.output[:-6] + "_rejected.jsonl"

    filter_jsonl(
        input_file=args.input,
        output_file=args.output,
        rejected_output_file=rejected_path,
        compare_gt=args.compare_gt,
        timeout_per_item=args.timeout,
        num_processes=args.num_processes
    )
