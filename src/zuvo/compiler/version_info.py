from pathlib import Path
from zuvo.compiler.builder import BuildOptions


def parse_version_tuple(version_str: str) -> tuple[int, int, int, int]:
    """Converts a dot-separated version string into a 4-integer tuple."""
    parts = version_str.split(".")
    integers = []
    for part in parts[:4]:
        try:
            integers.append(int(part))
        except ValueError:
            integers.append(0)

    while len(integers) < 4:
        integers.append(0)

    return (integers[0], integers[1], integers[2], integers[3])


def generate_version_file(opts: BuildOptions, output_path: Path) -> Path:
    """
    Generates a temporary PyInstaller version info file for Windows executables.

    Args:
        opts (BuildOptions): Normalized compilation options.
        output_path (Path): Path where the version_info.txt file should be saved.

    Returns:
        Path: The file path of the generated version file.
    """
    v = parse_version_tuple(opts.version_str)

    content = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v},
    prodvers={v},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', '{opts.company_name}'),
            StringStruct('FileDescription', '{opts.description}'),
            StringStruct('FileVersion', '{opts.version_str}'),
            StringStruct('InternalName', '{opts.exe_name}'),
            StringStruct('LegalCopyright', '{opts.copyright}'),
            StringStruct('OriginalFilename', '{opts.exe_name}'),
            StringStruct('ProductName', '{opts.title}'),
            StringStruct('ProductVersion', '{opts.version_str}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path