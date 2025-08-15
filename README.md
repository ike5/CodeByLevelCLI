# CodeByLevel CLI Guide

## Installation

To install the CodeByLevel CLI, first create and activate a Python virtual environment, then run the following command:

```
pip install -r requirements.txt
```

This will install the necessary dependencies for the CLI.

## Project Initialization

Initialize a new CodeByLevel project in your current directory by running:

```
python main.py init <Enter project name in quotes here>
```

This command sets up the necessary configuration files and directory structure for your project.

## Adding Objects

Add new objects to your project with the following syntax:

```
python main.py add <title> --version <version> --section <section-name> --audience <audience>
```

REQUIRED

- `<title>`: The name of the object
- `<version>`: The version of the documentation. Use the X.X.X form.

OPTIONAL

- `<section-name>`: Optional, add to a section.
- `<audience>`: Professional by default, but can modify for amateur and expert audiences.

Example:

```
python main.py add "Implementing GET methods" --version 1.0.0 --section "API Methods" --audience amateur
```

## Listing Objects

List all objects currently defined in your project by running:

```
python main.py list
```

This command displays a summary of all objects with their types and names.

## Showing Objects

To view detailed information about a specific object, use:

```
python main.py show <object-name>
```

Replace `<object-name>` with the name of the object you want to inspect.

Example:

```
python main.py show User
```

## Building Documentation

Generate project documentation by running:

```
python main.py build
```

This command compiles your objects and creates documentation files in the designated output directory.

## Configuration

You can customize your project settings by editing the `codebylevel.config.json` file created during initialization.
This file allows you to specify options such as:

- Output directory for documentation
- Object types to include
- Formatting preferences

Make sure to review and update this file to tailor the CLI behavior to your needs.
