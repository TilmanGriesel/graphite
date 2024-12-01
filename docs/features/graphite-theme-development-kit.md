# Graphite Theme Development Kit

This guide provides an overview of the tools and processes designed to help you create and maintain consistent theme variants with ease.

## Overview

The development kit includes:
- **Token Abstraction**: Simplifies theme consistency across variants.
- **Theme Assembler Script**: Automates the regeneration of theme files after changes.
- **Source Directory**: Contains all source components (`src/` folder).
- **Tools Directory**: Houses utility scripts (`tools/` folder).

### Quick Tips
- Avoid editing files directly in the `themes/` directory.
- Use the provided `theme_assembler.py` script to apply changes from the `src/` folder.
- This setup is also an excellent foundation for developing custom themes rapidly.

## Setup and Usage

1. **Install Requirements**: Ensure you have Python 3 and `pre-commit` installed.
2. **Modify Source Components**: Make updates in the `src/` directory.
3. **Regenerate Themes**: Run the theme assembler script:
   ```bash
   make theme
   ```
4. **Clean Theme Directory**: Remove generated files before rebuilding:
   ```bash
   make clean
   ```
5. **Format YAML Files**: Ensure consistent formatting:
   ```bash
   make format
   ```
6. **Develop Documentation**: Start a local Vitepress instance for documentation development:
   ```bash
   make docs-dev
   ```

## Makefile Targets

The included `Makefile` simplifies common tasks:

| Target     | Description                                       |
|------------|---------------------------------------------------|
| `all`      | Format YAML files and assemble themes (default).  |
| `theme`    | Run the theme assembler script.                   |
| `clean`    | Remove all generated files in the `themes/` folder. |
| `dev`      | Execute the `rebuild_dev.sh` script.              |
| `docs-dev` | Launch a local Vitepress server.                  |
| `format`   | Format all YAML files in `src/` and `themes/`.    |
| `help`     | Display available Makefile targets.               |

## File Structure

- **`src/`**: Source components for your themes.
- **`tools/`**: Scripts, including `theme_assembler.py`, to automate tasks.
- **`themes/`**: Generated theme files (do not edit directly).
- **`docs/`**: Vitepress documentation and statics assets.
- **`.github/`**: GitHub workflows and more.

## Getting Started

1. Clone the repository.
2. Make your changes in the `src/` folder.
3. Use the Makefile commands to assemble, format, and test your themes.

---

### Contribute

This kit is designed to evolve! Feel free to contribute by sharing feedback, submitting issues, or creating pull requests.

