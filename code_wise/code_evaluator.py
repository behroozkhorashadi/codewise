

import argparse

import tkinter as tk
from tkinter import messagebox
print("tkinter is installed and ready to use")

from logic.code_ast_parser import collect_method_usages, print_enclosing_function_definition_from_file, get_method_body

from llm.code_eval_prompt import generate_code_evaluation_prompt

from llm.llm_integration import get_method_ratings

def evaluate_code():
    pass

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect method usages in a given project directory and file."
    )
    # Define positional arguments
    parser.add_argument(
        "root_directory",
        type=str,
        help="The root directory of the project (e.g., '/path/to/project').",
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="The file path to analyze (e.g., '/path/to/project/api/spam/logic/spam_prevention.py').",
    )
    return parser.parse_args()

def on_submit():
    """Callback to handle submission of inputs from the GUI."""
    root_directory = root_dir_entry.get()
    file_path = file_path_entry.get()

    if not root_directory or not file_path:
        messagebox.showerror("Input Error", "Both fields must be filled out!")
        return

    # Clear the output box
    output_text.delete("1.0", tk.END)

    try:
        # Core logic
        result = collect_method_usages(root_directory, file_path)
        function_def = ''
        openai_prompt = ''
        usage_examples = ''

        for method_pointer, call_site_infos in result.items():
            function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)

            for call_site_info in call_site_infos:
                usage_examples += f'{get_method_body(call_site_info.function_node, call_site_info.file_path)}\n'

            openai_prompt = generate_code_evaluation_prompt(function_def, usage_examples)
            api_response = get_method_ratings(openai_prompt)  # API call simulation
            output_text.insert(tk.END, f"Response:\n{api_response}\n")
            break  # Stop after the first result for demonstration
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return

    messagebox.showinfo("Success", "Process completed successfully!")

def main():  # sourcery skip: extract-duplicate-method
    app = tk.Tk()
    app.title("Codewise")
    app.geometry("600x400")

    # Root directory label and entry
    tk.Label(app, text="Root Directory:").pack(pady=(10, 0))
    
    global root_dir_entry
    root_dir_entry = tk.Entry(app, width=70)
    root_dir_entry.pack(pady=(0, 10))

    # File path label and entry
    tk.Label(app, text="File Path:").pack(pady=(10, 0))
    global file_path_entry
    file_path_entry = tk.Entry(app, width=70)
    file_path_entry.pack(pady=(0, 10))

    # Submit button
    tk.Button(app, text="Submit", command=on_submit).pack(pady=(10, 0))

    # Output label
    tk.Label(app, text="API Response:").pack(pady=(10, 0))

    # Output text box
    global output_text
    output_text = tk.Text(app, wrap=tk.WORD, height=10, width=70)
    output_text.pack(pady=(0, 10))

    # Start the GUI event loop
    app.mainloop()
    # args = parse_arguments()
    # print(f"Root Directory: {args.root_directory}, File Path: {args.file_path}")


    # # Use the parsed arguments
    # root_directory = args.root_directory
    # file_path = args.file_path
    # result = collect_method_usages(root_directory, file_path)
    # function_def = ''
    # openai_prompt = ''
    # usage_examples = ''

    # for method_pointer, call_site_infos in result.items():
    #     function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)

    #     for call_site_info in call_site_infos:
    #         usage_examples += f'{get_method_body(call_site_info.function_node, call_site_info.file_path)}/n'
            
    #     openai_prompt = generate_code_evaluation_prompt(function_def, usage_examples)
    #     print(get_method_ratings(openai_prompt))
    #     break
      


if __name__ == "__main__":
    main()

