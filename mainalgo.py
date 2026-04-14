import ast
import os
import re
from typing import List, Tuple

def get_source_files(repo_path: str) -> List[str]:
    """Get all source files in the repository."""
    source_files = []
    source_extensions = {".py", ".js", ".c", ".cpp", ".java", ".ts", ".go", ".rb", ".json", ".html", ".h", ".hpp", ".md"}

    for root, dirs, files in os.walk(repo_path):
         # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.startswith('.'):
                continue
            ext = os.path.splitext(file)[1]
            if ext in source_extensions:
                source_files.append(os.path.join(root, file))

    return source_files

def analyze_python(filepath: str) -> Tuple[List[Tuple], List[Tuple]]:
    """Extract purpose info and system info from Python files with locations."""
    purpose_info = []
    systems = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            lines = source.splitlines()
        tree = ast.parse(source)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return purpose_info, systems

    # Helper function to get line number for a node
    def get_line_number(node):
        return getattr(node, 'lineno', None)

    # Helper function to get context around a line
    def get_context(lines, line_num, context_lines=2):
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return '\n'.join(lines[start:end])

    # Module-level docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        # Module docstring is usually at line 1 or 2
        purpose_info.append(("module_doc", module_doc, filepath, 1, get_context(lines, 1)))

    # Walk functions, classes, and imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc:
                line_num = get_line_number(node)
                context = get_context(lines, line_num) if line_num else ""
                purpose_info.append((node.name, doc, filepath, line_num, context))

    return purpose_info, systems

# Regex patterns for comments
COMMENT_PATTERNS = {
    ".js": r"//.*|/\*[\s\S]*?\*/",
    ".c": r"//.*|/\*[\s\S]*?\*/",
    ".cpp": r"//.*|/\*[\s\S]*?\*/",
    ".java": r"//.*|/\*[\s\S]*?\*/",
    ".ts": r"//.*|/\*[\s\S]*?\*/",
    ".go": r"//.*|/\*[\s\S]*?\*/",
    ".rb": r"#.*",
    ".py": r"#.*",
    ".md": r"(?i)^readme(?:\.[a-z0-9]+)?$",# Added for Python single-line comments
}

SYSTEM_KEYWORDS = ["windows", "linux", "darwin", "mac", "macos", "unix", "posix"]

def analyze_other(filepath: str) -> Tuple[List[Tuple], List[Tuple]]:
    """Extract comments and system info from non-Python source files with locations."""
    purpose_info = []
    systems = []

    ext = os.path.splitext(filepath)[1]
    pattern = COMMENT_PATTERNS.get(ext)
    if not pattern:
        return purpose_info, systems

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
            lines = code.splitlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return purpose_info, systems

    # Extract comments with line numbers
    for line_num, line in enumerate(lines, 1):
        if ext == ".py":
            # Python single-line comments
            if '#' in line:
                comment_start = line.find('#')
                comment = line[comment_start:].strip()
                if comment:
                    purpose_info.append(("comment", comment, filepath, line_num, line.strip()))
        else:
            # For other languages using regex
            if re.match(pattern.split('|')[0].replace('.*', ''), line.strip()):
                purpose_info.append(("comment", line.strip(), filepath, line_num, line.strip()))

    # Look for system keywords with line numbers
    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()
        for kw in SYSTEM_KEYWORDS:
            if kw in line_lower:
                # Find the exact position in the line
                kw_pos = line_lower.find(kw)
                context = line.strip()
                systems.append((kw, filepath, line_num, context))

    return purpose_info, systems

def analyze_repo(repo_path: str) -> Tuple[List[Tuple], List[Tuple]]:
    """Analyze all source files in a repo for purpose and supported systems."""
    files = get_source_files(repo_path)
    summary_purpose = []
    summary_systems = []

    for file in files:
        print(f"Analyzing: {file}")
        ext = os.path.splitext(file)[1]
        if ext == ".py":
            purpose, systems = analyze_python(file)
        else:
            purpose, systems = analyze_other(file)

        summary_purpose.extend(purpose)
        summary_systems.extend(systems)

    # Check README.md for extra purpose info
    readme_path = os.path.join(repo_path, "README.md") # Changed from 'README' to 'README.md'
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                lines = text.splitlines()
            # Add first few lines of README with location info
            for i, line in enumerate(lines[:10], 1):
                if line.strip():
                    summary_purpose.append(("README", line.strip(), readme_path, i, line.strip()))
        except Exception as e:
            print(f"Error reading README: {e}")

    # Check setup.py for system info hints
    setup_path = os.path.join(repo_path, "setup.py")
    if os.path.exists(setup_path):
        try:
            with open(setup_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                lines = text.splitlines()
            # Look for system-related content in setup.py
            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                if any(kw in line_lower for kw in SYSTEM_KEYWORDS):
                    summary_systems.append(("setup.py", line.strip(), setup_path, i, line.strip()))
        except Exception as e:
            print(f"Error reading setup.py: {e}")

    return summary_purpose, summary_systems

def print_results(purpose: List[Tuple], systems: List[Tuple]):
    """Print the analysis results in a formatted way."""
    print("\n" + "="*80)
    print("PURPOSE INFO (showing first 20 items)")
    print("="*80)

    if not purpose:
        print("No purpose information found.")
    else:
        for i, p in enumerate(purpose[:20], 1):
            if len(p) == 5:  # With location info
                p_type, content, filepath, line_num, context = p
                print(f"\n{i}. TYPE: {p_type}")
                print(f"   FILE: {filepath}:{line_num}")
                print(f"   CONTENT: {content[:200]}{'...' if len(content) > 200 else ''}")
                print(f"   CONTEXT: {context[:100]}{'...' if len(context) > 100 else ''}")
            else:  # Fallback for old format
                print(f"\n{i}. {p}")

    print("\n" + "="*80)
    print("SYSTEM INFO (showing first 20 items)")
    print("="*80)

    if not systems:
        print("No system information found.")
    else:
        for i, s in enumerate(systems[:750], 1):
            if len(s) == 4:  # With location info
                system, filepath, line_num, context = s
                print(f"\n{i}. SYSTEM: {system}")
                print(f"   FILE: {filepath}:{line_num}")
                print(f"   CONTEXT: {context[:100]}{'...' if len(context) > 100 else ''}")
            else:  # Fallback for old format
                print(f"\n{i}. {s}")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total purpose items found: {len(purpose)}")
    print(f"Total system references found: {len(systems)}")

    # Count by file type
    file_types = {}
    for p in purpose:
        if len(p) >= 3:
            filepath = p[2]
            ext = os.path.splitext(filepath)[1]
            file_types[ext] = file_types.get(ext, 0) + 1
    print(f"Files analyzed by type: {dict(file_types)}")

# Example usage
if __name__ == "__main__":
    repo_path = "./yabai"  # Path to your cloned repo
    purpose, systems = analyze_repo(repo_path)
    print_results(purpose, systems)
    top_20_systems = systems[:750]
