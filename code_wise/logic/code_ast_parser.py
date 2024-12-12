import ast
from dataclasses import dataclass
import os
import random
from typing import NamedTuple, Optional, Dict, List, Tuple


class MethodIdentifier(NamedTuple):
    module_name: str
    method_name: str


class MethodPointer(NamedTuple):
    method_id: MethodIdentifier
    function_node: ast.FunctionDef
    file_path: str


class CallSiteInfo(NamedTuple):
    call_node: ast.Call
    function_node: ast.FunctionDef
    file_path: str


def find_enclosing_function(call_node: ast.Call) -> Optional[ast.FunctionDef]:
    # Traverse up the tree until we find a FunctionDef node
    current_node = call_node
    while current_node:
        if isinstance(current_node, ast.FunctionDef):
            return current_node
        current_node = current_node.parent  # Move to the parent node
    print(f"Returning none for call node {call_node}")
    return None  # Return None if no enclosing function is found


def set_parent_pointers(node: ast.Module, parent: ast.Module = None):
    # Recursively set parent pointers for all child nodes
    for child in ast.iter_child_nodes(node):
        child.parent = parent
        set_parent_pointers(child, child)


def print_enclosing_function_definition_from_file(enclosing_function: ast.FunctionDef, file_path: str):
    with open(file_path, "r") as file:
        source_code = file.read()
        print_enclosing_function_definition(enclosing_function, source_code)


def print_enclosing_function_definition(enclosing_function: ast.FunctionDef, source_code: str):
    # Find the enclosing function
    if enclosing_function:
        # Print the function definition
        function_code = ast.get_source_segment(source_code, enclosing_function)
        print(function_code)
    else:
        print("No enclosing function found.")


def get_method_body(node: ast.FunctionDef, file_path: str) -> str:
    with open(file_path, "r") as file:
        source_code = file.read()
        return ast.get_source_segment(source_code, node)


class MethodUsageCollector(ast.NodeVisitor):
    def __init__(self, root_directory: str, target_file: str):
        self.root_directory = root_directory
        self.target_file = target_file
        self.import_map = {}  # Maps import names/aliases to full module paths

        self.method_to_module: Dict[str, str] = {}
        self.method_definitions: Dict[MethodIdentifier, ast.FunctionDef] = {}  # Maps method identifier to AST node
        self.method_file_path_mapping: Dict[MethodIdentifier, str] = {}  # Maps method identifier to AST node
        self.method_usages: Dict[MethodIdentifier, List[CallSiteInfo]] = (
            {}
        )  # Maps method identifier to list of usage nodes
        self.current_file = ""
        self.current_module_name = ""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self.import_map[name] = alias.name  # Map alias or name to the full module path

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            full_import_path = f"{module}.{alias.name}" if module else alias.name
            self.import_map[name] = full_import_path

    def collect_method_definitions(self, node: ast.Module) -> None:
        if isinstance(node, ast.FunctionDef):
            module_name = self.current_module_name
            print(node.name)
            self.method_to_module[node.name] = module_name
            method_identifier = MethodIdentifier(module_name, method_name=str(node.name))
            self.method_definitions[method_identifier] = node
            self.method_file_path_mapping[method_identifier] = node.source_file
        for child_node in ast.iter_child_nodes(node):
            child_node.source_file = node.source_file
            self.collect_method_definitions(child_node)

    def resolve_call_identifier(self, node: ast.Call) -> Optional[MethodIdentifier]:
        """
        Resolves the module and method name for a given call node.
        """
        method_name = ""
        module_name = ""

        if isinstance(node.func, ast.Name):
            # Direct function call, e.g., `function_name(...)`
            method_name = node.func.id
            module_name = self.import_map.get(method_name, self.current_module_name)

        elif isinstance(node.func, ast.Attribute):
            # Attribute function call, e.g., `module_name.function_name(...)`
            attribute_chain = []
            current_node = node.func

            # Traverse up the attribute chain (e.g., `module.submodule.function_name`)
            while isinstance(current_node, ast.Attribute):
                attribute_chain.insert(0, current_node.attr)
                current_node = current_node.value

            if isinstance(current_node, ast.Name):
                base_name = current_node.id
                attribute_chain.insert(0, base_name)

                # Check if the base name is an imported module or alias
                module_name = self.import_map.get(base_name, self.current_module_name)
                if module_name == self.current_module_name:
                    # Fallback to local reference if not found in imports
                    module_name = ".".join(attribute_chain[:-1])
                method_name = attribute_chain[-1]

        if not method_name:
            return None

        return MethodIdentifier(module_name, method_name)

    def visit_Call(self, node: ast.Call) -> None:
        # Resolve the method identifier for this call
        method_identifier = self.resolve_call_identifier(node)
        if method_identifier and method_identifier.method_name == "deactivate_email_spammer":
            print(f"{method_identifier=}")
        # Check if the call matches a method in the target file
        if method_identifier and method_identifier in self.method_definitions:
            if method_identifier not in self.method_usages:
                self.method_usages[method_identifier] = []

            if len(self.method_usages[method_identifier]) < 10:
                call_site_info = CallSiteInfo(
                    call_node=node,
                    function_node=find_enclosing_function(node),
                    file_path=self.current_file
                )
                self.method_usages[method_identifier].append(call_site_info)
        self.generic_visit(node)

    def parse_target_file(self):
        self.set_current_file(self.target_file)
        with open(self.target_file, "r") as file:
            node = ast.parse(file.read())
            set_parent_pointers(node)
            node.source_file = self.target_file
            self.collect_method_definitions(node)

    def parse_repo_files(self):
        for subdir, _, files in os.walk(self.root_directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    file_path = os.path.join(subdir, file)
                    self.set_current_file(file_path)
                    with open(file_path, "r") as f:
                        node = ast.parse(f.read())
                        set_parent_pointers(node)
                        node.source_file = file_path
                        self.visit(node)

    def set_current_file(self, file_path: str) -> None:
        self.current_file = file_path
        self.current_module_name = self.current_filepath_to_module_name()

    def get_usages(self) -> Dict[MethodPointer, List[CallSiteInfo]]:
        return {
            MethodPointer(
                method_id=method,
                function_node=self.method_definitions[method],
                file_path=self.method_file_path_mapping[method],
            ): random.sample(self.method_usages[method], min(10, len(self.method_usages[method])))
            for method in self.method_usages
        }

    def current_filepath_to_module_name(self) -> str:
        if self.current_file.startswith(self.root_directory):
            # Remove the root directory and extension
            relative_path = self.current_file[len(self.root_directory) :].rstrip(".py")
            return relative_path.replace(os.sep, ".").lstrip(".")
        return "unknown_module"


# Usage
def collect_method_usages(root_dir: str, file_path: str) -> Dict[MethodPointer, List[CallSiteInfo]]:
    collector = MethodUsageCollector(root_directory=root_dir, target_file=file_path)
    collector.parse_target_file()  # Collect definitions in target file
    collector.parse_repo_files()  # Find usage of each method in the repo
    return collector.get_usages()


def main():
    result = collect_method_usages(
        "/Users/behrooz/Work/recall-api", "/Users/behrooz/Work/recall-api/api/spam/logic/spam_prevention.py"
    )
    for method_pointer, call_site_infos in result.items():
        print("******* Function Definition Start ***********")
        print_enclosing_function_definition_from_file(method_pointer.function_node, method_pointer.file_path)
        print("******* Function Definition End ***********")
        print("******* Function Usage Start ***********")
        for call_site_info in call_site_infos:
            print_enclosing_function_definition_from_file(call_site_info.function_node, call_site_info.file_path)
        print("******* Function Usage End ***********")


if __name__ == "__main__":
    main()
