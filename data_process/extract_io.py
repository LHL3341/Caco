import json
import re
import time
import sys
import traceback
import contextlib
from io import StringIO
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import argparse
import ast

sys.set_int_max_str_digits(1000000)


def extract_code_from_field(code_field):
    pattern = r"```(?:python)?\s*([\s\S]+?)\s*```"
    match = re.search(pattern, code_field)
    if match:
        return match.group(1).strip()
    else:
        return code_field.strip()


def run_exec_in_process(code, return_dict):
    stdout_capture = StringIO()
    global_vars = {}
    unused_params = []

    code_lines = code.strip().split("\n")
    code_lines = [line for line in code_lines if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("import")]

    if len(code_lines) < 6:
        return_dict["error"] = "Code is too short"
        return_dict["input"] = None
        return_dict["output"] = stdout_capture.getvalue().strip()
        return

    try:
        tree = ast.parse(code)
        all_vars = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

        with contextlib.redirect_stdout(stdout_capture):
            exec(code, global_vars)

        input_dict = global_vars.get("input", None)
        for key in input_dict:
            if key not in all_vars:
                unused_params.append(key)

        error_message = None
        if unused_params:
            error_message = f"Unused input parameters: {', '.join(unused_params)}"

        return_dict["input"] = global_vars.get("input", None)
        return_dict["output"] = global_vars.get("output", stdout_capture.getvalue().strip())
        return_dict["error"] = error_message if error_message else None

    except Exception:
        return_dict["input"] = None
        return_dict["output"] = stdout_capture.getvalue().strip()
        return_dict["error"] = traceback.format_exc()


def execute_code(code, timeout_sec=5):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    process = multiprocessing.Process(target=run_exec_in_process, args=(code, return_dict))
    process.start()
    process.join(timeout=timeout_sec)

    if process.is_alive():
        process.terminate()
        process.join()
        return None, None, f"Timeout: execution exceeded {timeout_sec} seconds"

    return return_dict.get("input"), return_dict.get("output"), return_dict.get("error")


def is_too_large(val, max_digits=10000):
    try:
        return isinstance(val, int) and len(str(val)) > max_digits
    except Exception:
        return False


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_for_json(i) for i in obj)
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    else:
        return str(obj)


def process_line(line, extract_code):
    try:
        if isinstance(line, str):
            entry = json.loads(line)
            if not line.strip():
                return None
        elif isinstance(line, dict):
            entry = line
        code_field = entry.get("code", "")
        problem = entry.get("problem", "")
        answer = entry.get("answer", "")

        if extract_code:
            code = extract_code_from_field(code_field)
        else:
            code = code_field

        start_time = time.perf_counter()
        input_val, output_val, error = execute_code(code)
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        too_large_msgs = []
        if is_too_large(input_val):
            too_large_msgs.append(f"input is too large (> {len(str(input_val))} digits)")
            input_val = None
        if is_too_large(output_val):
            too_large_msgs.append(f"output is too large (> {len(str(output_val))} digits)")
            output_val = None

        if too_large_msgs:
            if error:
                error += "\n" + "\n".join(too_large_msgs)
            else:
                error = "\n".join(too_large_msgs)

        entry["code"] = sanitize_for_json(code)
        entry["input"] = sanitize_for_json(input_val)
        entry["output"] = sanitize_for_json(output_val)
        entry["execution_time"] = execution_time
        entry["error"] = error
        entry["problem"] = problem
        entry["answer"] = answer

        return entry
    except Exception as e:
        print("Exception when processing record:", e)
        return None


def process_jsonl_file(input_filename, output_filename, extract_code, max_workers=64):
    with open(input_filename, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()

    with open(output_filename, 'w', encoding='utf-8') as f_out, \
         ProcessPoolExecutor(max_workers=max_workers) as executor:

        futures = {executor.submit(process_line, line, extract_code): line for line in lines}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            try:
                result = future.result()
                if result is not None:
                    f_out.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
                    f_out.flush()
            except Exception as e:
                print("Subtask processing exception:", e)


def parse_args():
    parser = argparse.ArgumentParser(description="Process a JSONL file with code execution.")
    parser.add_argument('--input', type=str, help="Input JSONL file path")
    parser.add_argument('--output', type=str, help="Output JSONL file path")
    parser.add_argument('--extract', action='store_true', help="Whether to extract code from markdown block")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    multiprocessing.set_start_method("fork")

    process_jsonl_file(args.input, args.output, args.extract, max_workers=64)
    print(f"Processing complete. Output saved to {args.output}")
