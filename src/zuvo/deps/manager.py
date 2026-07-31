"""
Format-preserving dependency manager for Zuvo projects via pyproject.toml.
"""

from pathlib import Path
import tomlkit


def read_pyproject(path: Path) -> tomlkit.TOMLDocument:
    """
    Reads a pyproject.toml file into a format-preserving TOML Document.

    Args:
        path (Path): Path to the pyproject.toml file.

    Returns:
        tomlkit.TOMLDocument: TOML document AST, or an empty document if missing.
    """
    if not path.exists():
        return tomlkit.document()

    content = path.read_text(encoding="utf-8")
    return tomlkit.parse(content)


def write_pyproject(path: Path, doc: tomlkit.TOMLDocument) -> None:
    """
    Writes the modified TOML Document back to disk preserving structure and comments.

    Args:
        path (Path): Path to the target pyproject.toml file.
        doc (tomlkit.TOMLDocument): Document structure to persist.
    """
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def get_dependencies(doc: tomlkit.TOMLDocument, is_dev: bool = False) -> list[str]:
    """
    Retrieves the target dependency list from the TOML Document.

    Args:
        doc (tomlkit.TOMLDocument): TOML Document object.
        is_dev (bool): If True, targets [project.optional-dependencies].dev.

    Returns:
        list[str]: Current list of dependency strings.
    """
    project = doc.get("project", {})

    if is_dev:
        opt_deps = project.get("optional-dependencies", {})
        return list(opt_deps.get("dev", []))

    return list(project.get("dependencies", []))


def add_dependencies(
    doc: tomlkit.TOMLDocument, packages: list[str], is_dev: bool = False
) -> bool:
    """
    Adds non-duplicate package specifications to the specified dependency array.

    Args:
        doc (tomlkit.TOMLDocument): Target TOML document to mutate.
        packages (list[str]): Packages or specifiers to add.
        is_dev (bool): If True, targets [project.optional-dependencies].dev.

    Returns:
        bool: True if at least one dependency was added, False otherwise.
    """
    changed = False

    if "project" not in doc:
        doc["project"] = tomlkit.table()

    project = doc["project"]

    if is_dev:
        if "optional-dependencies" not in project:
            project["optional-dependencies"] = tomlkit.table()

        opt_deps = project["optional-dependencies"]

        if "dev" not in opt_deps:
            opt_deps["dev"] = tomlkit.array()

        dev_array = opt_deps["dev"]
        for pkg in packages:
            if pkg not in dev_array:
                dev_array.append(pkg)
                changed = True
    else:
        if "dependencies" not in project:
            project["dependencies"] = tomlkit.array()

        deps_array = project["dependencies"]
        for pkg in packages:
            if pkg not in deps_array:
                deps_array.append(pkg)
                changed = True

    return changed


def remove_dependencies(
    doc: tomlkit.TOMLDocument, packages: list[str], is_dev: bool = False
) -> bool:
    """
    Removes package specifications from the specified dependency array.

    Args:
        doc (tomlkit.TOMLDocument): Target TOML document to mutate.
        packages (list[str]): Packages or specifiers to remove.
        is_dev (bool): If True, targets [project.optional-dependencies].dev.

    Returns:
        bool: True if at least one dependency was removed, False otherwise.
    """
    changed = False
    project = doc.get("project", {})

    if is_dev:
        opt_deps = project.get("optional-dependencies", {})
        dev_array = opt_deps.get("dev", [])
        for pkg in packages:
            if pkg in dev_array:
                dev_array.remove(pkg)
                changed = True
    else:
        deps_array = project.get("dependencies", [])
        for pkg in packages:
            if pkg in deps_array:
                deps_array.remove(pkg)
                changed = True

    return changed