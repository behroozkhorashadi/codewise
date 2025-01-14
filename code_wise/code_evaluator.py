

import argparse

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

def main():
    args = parse_arguments()
    print(f"Root Directory: {args.root_directory}, File Path: {args.file_path}")


    # Use the parsed arguments
    root_directory = args.root_directory
    file_path = args.file_path
    result = collect_method_usages(root_directory, file_path)
    function_def = ''
    openai_prompt = ''
    usage_examples = ''

    for method_pointer, call_site_infos in result.items():
        # print("******* Function Definition Start ***********")
        #print_enclosing_function_definition_from_file(method_pointer.function_node, method_pointer.file_path)
        function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)
        # print("******* Function Definition End ***********")
        # print("******* Function Usage Start ***********")
        for call_site_info in call_site_infos:
            #print_enclosing_function_definition_from_file(call_site_info.function_node, call_site_info.file_path)
            usage_examples += f'{get_method_body(call_site_info.function_node, call_site_info.file_path)}/n'
        openai_prompt = generate_code_evaluation_prompt(function_def, usage_examples)
        print(get_method_ratings(openai_prompt))
        break
        # print("******* Function Usage End ***********")


if __name__ == "__main__":
    main()

