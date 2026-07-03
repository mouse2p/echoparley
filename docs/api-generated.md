# Generated API reference

## `echoparley.apidoc`

- `APIEntry` (class): One public module-local function or class and its docstring summary.
- `api_inventory_mapping` (function): Return exhaustive JSON-compatible API entries under schema 1.0.
- `missing_docstrings` (function): Return public names that lack a usable docstring summary.
- `public_api_entries` (function): Inspect public functions and classes defined by one package module.
- `render_api_entry` (function): Render one API entry as a compact Markdown definition item.
- `render_api_reference` (function): Render a complete Markdown reference for distinct module names.
- `render_module_reference` (function): Render all public module-local APIs from live docstrings.

## `echoparley.completion`

- `bash_completion` (function): Generate a dependency-free Bash completion function.
- `command_names` (function): Return sorted subcommand names declared by a parser.
- `command_options` (function): Return sorted long options for each subcommand.
- `completion_assets` (function): Return stable relative filenames and generated contents.
- `zsh_completion` (function): Generate a compact Zsh command completion definition.

## `echoparley.snippets`

- `PythonSnippet` (class): Runnable source plus its one-based Markdown starting line.
- `execute_snippets` (function): Compile and execute each trusted project-documentation snippet independently.
- `extract_python_snippets` (function): Extract fenced blocks labeled `python echoparley-run`.
