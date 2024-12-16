"""Fill in a module description here"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['add_node_by_path', 'add_node_by_repo', 'extract_class_function_relationships_with_source']

# %% ../nbs/00_core.ipynb 3
import os
import uuid
import tempfile
import networkx as nx
import tree_sitter_python as tspython

from glob import glob
from .utils import clone_repo
from tree_sitter import Language, Parser

def add_node_by_path(path: str, base_dir: str, repo_name:str, g: nx.DiGraph = None):
    """Adds nodes to the graph based on the file path and adds source code for .py files."""
    if g is None:
        g = nx.DiGraph()

    # Remove the base_dir from the path using removeprefix (Python 3.9+)
    path = path.removeprefix(base_dir + '/')

    # Split the remaining path into components
    components = [repo_name] + path.split('/')

    # Traverse the components and add nodes
    current_node = None  # The root node is not predefined

    for i in range(len(components)):
        next_node = '/'.join(components[:i+1])
        g.add_node(next_node, uuid=str(uuid.uuid4()))
        if current_node:
            g.add_edge(current_node, next_node)
        current_node = next_node

    if current_node.endswith('.py'):
        try:
            with open(os.path.join(base_dir, path), 'r') as file:
                source_code = file.read()
            # Add the source code as an attribute to the final node
            g.nodes[current_node]['source'] = source_code
            g = extract_class_function_relationships_with_source(g, current_node)
        except Exception as e:
            print(f"Error reading file {path}: {e}")

    return g
        
def add_node_by_repo(repo_url: str, g: nx.DiGraph = None, ignore_files=['setup.py']):
    """Clones the repository and adds nodes based on the files in the repo."""
    if g is None:
        g = nx.DiGraph()
    repo_name = repo_url.split('/')[-1].replace('.git','')

    with tempfile.TemporaryDirectory() as tempdir:
        # Clone the repository into the temporary directory
        clone_repo(repo_url, tempdir)

        # Get all file paths in the repository (recursively)
        repo_file_paths = glob(f"{tempdir}/**/*.py", recursive=True)

        # Add nodes to the graph for each file path
        for file_path in repo_file_paths:
            if file_path.split('/')[-1] in ignore_files:
                continue
            # Add the node based on the file path, using base_dir as the root
            g = add_node_by_path(file_path, tempdir, repo_name, g)

    return g

def extract_class_function_relationships_with_source(g: nx.DiGraph, root_name:str):
    """
    Extract class and function relationships from a syntax tree into a given graph.

    Args:
        g (nx.DiGraph): A pre-existing directed graph.
        root_node: The root node of the syntax tree, which contains the `source` attribute.
    """
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(g.nodes[root_name]['source'], "utf8"))
    
    def get_source_text(node):
        """Extract the source code corresponding to a node."""
        return bytes(g.nodes[root_name]['source'][node.start_byte:node.end_byte], "utf8")
    
    def traverse(node, current_parent):
        if node.type in ['class_definition', 'function_definition']:
            name_node = node.child_by_field_name('name')
            if name_node:
                name = g.nodes[root_name]['source'][name_node.start_byte:name_node.end_byte]
                full_name = '/'.join([current_parent, name])  # Construct hierarchical name
                source_text = get_source_text(node)
                node_type = 'class' if node.type == 'class_definition' else 'function'
                
                # Add node with attributes
                g.add_node(full_name, 
                           type=node_type, 
                           parent=current_parent, 
                           source=source_text, 
                           )
                
                # Connect to the parent if present
                if current_parent:
                    g.add_edge(current_parent, full_name)

                # If it's a class, traverse its body to extract methods
                if node_type == 'class':
                    body_node = node.child_by_field_name('body')
                    if body_node:  # Recursively traverse the class body
                        traverse(body_node, full_name)

            # Set current_parent to full_name for child functions or classes
            current_parent = full_name if node.type == 'class_definition' else current_parent

        # Recursively traverse other children
        for child in node.children:
            traverse(child, current_parent)
    
    traverse(tree.root_node, root_name)
    return g
    

