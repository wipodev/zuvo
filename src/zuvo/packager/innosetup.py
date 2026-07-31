"""
Inno Setup packager module for Windows CLI applications in Zuvo framework.
"""

import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from zuvo.core.config import Config, get_config
from zuvo.utils.exec import run_system_command

_default_console = Console()


def _build_iss_script(config: Config, root: Path, iss_path: Path) -> Path:
    """Generates an Inno Setup script (.iss) tailored for CLI applications."""
    inno_cfg = config.inno
    build_cfg = config.build

    app_id = inno_cfg.get("app_id", "00000000-0000-0000-0000-000000000000")
    title = config.title
    version = config.version
    publisher = config.author or config.title
    publisher_url = inno_cfg.get("app_publisher_url", "")
    copyright_str = config.copyright
    description = config.description or f"Installer for {title}"

    out_dir = root / build_cfg.get("output_dir", "dist")
    out_filename = inno_cfg.get("output_base_filename", f"{config.cli_name}-Setup")
    default_dir = inno_cfg.get("default_dir_name", f"{{autopf}}\\{config.cli_name}")
    license_file = inno_cfg.get("license_file", "")

    # Determinar si el resultado del compilador fue en modo One-Folder (dist_dir/*) o One-File (.exe)
    source_dir = out_dir / f"{config.cli_name}.dist"
    if source_dir.exists():
        files_section = f'Source: "{source_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs'
    else:
        # Fallback a un archivo exe único si PyInstaller/Nuitka compilaron en one-file
        files_section = f'Source: "{out_dir}\\{config.cli_name}.exe"; DestDir: "{{app}}"; Flags: ignoreversion'

    # Manejo opcional de la licencia
    license_line = ""
    if license_file and (root / license_file).exists():
        license_path = (root / license_file).resolve()
        license_line = f'LicenseFile="{license_path}"\nFilesSectionExtra=Source: "{license_path}"; DestDir: "{{app}}"; DestName: "LICENSE.txt"; Flags: ignoreversion'

    # Plantilla ISS optimizada para CLI
    iss_content = f"""
; ==========================================================
; Generated automatically by Zuvo Packager
; Application: {title}
; ==========================================================

[Setup]
AppId={{{app_id}}}
AppName={title}
AppVersion={version}
AppPublisher={publisher}
AppPublisherURL={publisher_url}
VersionInfoCompany={publisher}
VersionInfoCopyright={copyright_str}
VersionInfoDescription={description}
VersionInfoProductName={title}
VersionInfoProductVersion={version}
VersionInfoTextVersion={version}
VersionInfoVersion={version}
{f'LicenseFile={root / license_file}' if license_file and (root / license_file).exists() else ''}
DefaultDirName={default_dir}
DisableProgramGroupPage=yes
DisableDirPage=no
DisableReadyMemo=no
OutputDir={out_dir}
OutputBaseFilename={out_filename}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
{files_section}

[Registry]
; Agrega la ruta de instalacion al PATH del usuario sin requerir administrador
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{{olddata}};{{app}}"; Flags: preservestringtype

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  PathValue, AppDir: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    AppDir := ExpandConstant('{{app}}');
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', PathValue) then
    begin
      if Pos(AppDir, PathValue) > 0 then
      begin
        StringChangeEx(PathValue, ';' + AppDir, '', True);
        StringChangeEx(PathValue, AppDir, '', True);
        RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', PathValue);
      end;
    end;
  end;
end;
"""
    iss_path.write_text(iss_content.strip(), encoding="utf-8")
    return iss_path


def package_innosetup(
    config: Config | None = None,
    console: Console | None = None,
    project_root: Path | str | None = None,
) -> bool:
    """Compiles the Windows installer using Inno Setup (ISCC.exe)."""
    out = console or _default_console
    cfg = config or get_config()
    root = Path(project_root) if project_root else Path.cwd()

    # 1. Resolver ruta del ejecutable ISCC.exe
    configured_iscc = cfg.inno.get("inno_path", "")
    iscc_bin = (
        shutil.which(configured_iscc)
        or shutil.which("ISCC.exe")
        or (Path(configured_iscc) if Path(configured_iscc).exists() else None)
    )

    if not iscc_bin or not Path(iscc_bin).exists():
        out.print(
            Panel(
                f"[bold red]❌ ISCC.exe (Inno Setup) was not found.[/bold red]\n\n"
                f"Configured path: [yellow]{configured_iscc}[/yellow]\n"
                "Ensure Inno Setup 6 is installed and added to your PATH or configured correctly in [cyan][tool.zuvo.inno][/cyan].",
                title="[bold red]Inno Setup Missing[/bold red]",
                border_style="red",
            )
        )
        return False

    # 2. Resumen visual en consola usando Rich
    table = Table(title="📦 Inno Setup Installer Configuration", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold white")

    table.add_row("CLI Name", cfg.cli_name)
    table.add_row("Version", cfg.version)
    table.add_row("Installer Output", f"{cfg.inno.get('output_base_filename')}.exe")
    table.add_row("Target Directory", cfg.inno.get("default_dir_name"))
    table.add_row("ISCC Executable", str(iscc_bin))

    out.print(table)
    out.print()

    # 3. Generación y ejecución
    build_tmp_dir = root / "build"
    build_tmp_dir.mkdir(parents=True, exist_ok=True)
    iss_file = build_tmp_dir / "installer.iss"

    try:
        with out.status("[bold green]Building Inno Setup installer package...", spinner="dots"):
            _build_iss_script(cfg, root, iss_file)
            cmd = [str(iscc_bin), str(iss_file)]
            success = run_system_command(cmd, cwd=root, console=out)

        if success:
            out.print(
                Panel(
                    f"[bold green]✔ Installer generated successfully![/bold green]\n\n"
                    f"Location: [cyan]{root / cfg.build.get('output_dir', 'dist') / cfg.inno.get('output_base_filename')}.exe[/cyan]",
                    title="[bold green]Package Complete[/bold green]",
                    border_style="green",
                )
            )
            return True
        else:
            out.print("[bold red]❌ Failed to build Inno Setup package.[/bold red]")
            return False

    finally:
        if iss_file.exists():
            iss_file.unlink()