"""
Pulumi Python program to deploy resources for a given environment (defined via Pulumi stack)
"""

import importlib
import os


def import_subfolders():
    """
    Import and execute all functions from Python modules in the current directory's subdirectories.

    This function iterates through subdirectories in the current directory,
    identifies Python files, imports the modules, and executes all callable
    functions within those modules.

    Parameters:
        None

    Returns:
        None

    Example:
        If this script is run as the main module, it will import and execute all relevant functions
        in the current directory's subdirectories.

    Usage:
        if __name__ == '__main__':
            import_and_execute_functions()
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for folder_name in os.listdir(current_dir):
        folder_path = os.path.join(current_dir, folder_name)
        if os.path.isdir(folder_path):
            module_names = [
                file_name[:-3]
                for file_name in os.listdir(folder_path)
                if file_name.endswith('.py')
                and file_name != '__init__.py'
                and folder_name != 'modules'
            ]
            for module_name in module_names:
                module = importlib.import_module(
                    f'{folder_name}.{module_name}'
                )
                for func_name in dir(module):
                    if callable(getattr(module, func_name)):
                        getattr(module, func_name)()


if __name__ == '__main__':
    import_subfolders()
