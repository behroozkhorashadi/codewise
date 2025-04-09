import argparse
try: # conditionally import so tests don't fail
    import tkinter as tk
    from tkinter import messagebox, filedialog
except ImportError:
    tk = None
    messagebox = None
    filedialog = None

from code_wise.logic.code_ast_parser import collect_method_usages, get_method_body
from code_wise.llm.code_eval_prompt import generate_code_evaluation_prompt
from code_wise.llm.llm_integration import get_method_ratings

def evaluate_code():
    pass

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect method usages in a given project directory and file."
    )
    parser.add_argument("root_directory", type=str, help="The root directory of the project.")
    parser.add_argument("file_path", type=str, help="The file path to analyze.")
    return parser.parse_args()

def select_root_directory():
    """Opens a file dialog to select the root directory."""
    selected_directory = filedialog.askdirectory()
    if selected_directory:
        root_dir_entry.delete(0, tk.END)
        root_dir_entry.insert(0, selected_directory)

def select_file():
    """Opens a file dialog to select the file path."""
    selected_file = filedialog.askopenfilename()
    if selected_file:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, selected_file)

def on_submit():
    """Callback to handle submission of inputs from the GUI."""
    root_directory = root_dir_entry.get()
    file_path = file_path_entry.get()

    if not root_directory or not file_path:
        messagebox.showerror("Input Error", "Both fields must be filled out!")
        return

    output_text.delete("1.0", tk.END)

    try:
        result = collect_method_usages(root_directory, file_path)
        function_def = ''
        openai_prompt = ''
        usage_examples = ''

        for method_pointer, call_site_infos in result.items():
            function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)
            for call_site_info in call_site_infos:
                usage_examples += f'{get_method_body(call_site_info.function_node, call_site_info.file_path)}\n'
            
            openai_prompt = generate_code_evaluation_prompt(function_def, usage_examples)
            api_response = get_method_ratings(openai_prompt)
            output_text.insert(tk.END, f"Response:\n{api_response}\n")
            output_text.yview(tk.END)  # Scroll to the end of response
            break
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return

    messagebox.showinfo("Success", "Process completed successfully!")

def main():
    app = tk.Tk()
    app.title("Codewise")
    app.geometry("800x500")
    app.configure(bg="#2c3e50")
    app.columnconfigure(0, weight=1)
    app.rowconfigure(6, weight=1)

    global root_dir_entry, file_path_entry, output_text

    tk.Label(app, text="Root Directory:", fg="white", bg="#2c3e50", font=("Arial", 12, "bold")).pack(pady=(10, 0))
    root_frame = tk.Frame(app, bg="#2c3e50")
    root_frame.pack(fill=tk.X, padx=10)
    root_dir_entry = tk.Entry(root_frame, width=60, font=("Arial", 12))
    root_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=5)
    tk.Button(root_frame, text="Browse", command=select_root_directory, bg="#16a085", fg="black", font=("Arial", 10, "bold"), relief=tk.FLAT).pack(side=tk.RIGHT)

    tk.Label(app, text="File Path:", fg="white", bg="#2c3e50", font=("Arial", 12, "bold")).pack(pady=(10, 0))
    file_frame = tk.Frame(app, bg="#2c3e50")
    file_frame.pack(fill=tk.X, padx=10)
    file_path_entry = tk.Entry(file_frame, width=60, font=("Arial", 12))
    file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=5)
    tk.Button(file_frame, text="Browse", command=select_file, bg="#16a085", fg="black", font=("Arial", 10, "bold"), relief=tk.FLAT).pack(side=tk.RIGHT)

    tk.Button(app, text="Submit", command=on_submit, bg="#e74c3c", fg="black", font=("Arial", 12, "bold"), relief=tk.FLAT, width=20, height=2).pack(pady=(20, 10))

    tk.Label(app, text="API Response:", fg="white", bg="#2c3e50", font=("Arial", 12, "bold")).pack(pady=(10, 0))
    text_frame = tk.Frame(app)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    output_text = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 12), bg="#ecf0f1")
    output_text.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(text_frame, command=output_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    output_text.config(yscrollcommand=scrollbar.set)

    app.mainloop()

if __name__ == "__main__":
    main()
