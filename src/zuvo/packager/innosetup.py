"""
Inno Setup packager module for Windows CLI applications in Zuvo framework.
"""

import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from zuvo.core.config import Config, get_config
from zuvo.i18n import t
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

    source_dir = out_dir / f"{config.cli_name}.dist"
    if source_dir.exists():
        files_section = f'Source: "{source_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs'
    else:
        files_section = f'Source: "{out_dir}\\{config.cli_name}.exe"; DestDir: "{{app}}"; Flags: ignoreversion'

    license_line = ""
    license_setup_line = ""
    if license_file and (root / license_file).exists():
        license_path = (root / license_file).resolve()
        license_setup_line = f'\nLicenseFile="{license_path}"'
        license_line = f'Source: "{license_path}"; DestDir: "{{app}}"; DestName: "LICENSE.txt"; Flags: ignoreversion'

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
VersionInfoVersion={version}{license_setup_line}
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
{license_line}

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

    configured_iscc = cfg.inno.get("inno_path", "")
    iscc_bin = (
        shutil.which(configured_iscc)
        or shutil.which("ISCC.exe")
        or (Path(configured_iscc) if Path(configured_iscc).exists() else None)
    )

    if not iscc_bin or not Path(iscc_bin).exists():
        out.print(
            Panel(
                f"[bold red]❌ {t('cmd_package_innosetup_err_missing_iscc')}[/bold red]\n\n"
                f"{t('cmd_package_innosetup_configured_path')}: [yellow]{configured_iscc}[/yellow]\n"
                f"{t('cmd_package_innosetup_install_hint')}",
                title=f"[bold red]{t('cmd_package_innosetup_missing_title')}[/bold red]",
                border_style="red",
            )
        )
        return False

    table = Table(
        title=f"📦 {t('cmd_package_innosetup_table_title')}",
        show_header=False,
    )
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold white")

    table.add_row(t("cmd_package_innosetup_prop_cli_name"), cfg.cli_name)
    table.add_row(t("cmd_package_version_label"), cfg.version)
    table.add_row(
        t("cmd_package_innosetup_prop_output"),
        f"{cfg.inno.get('output_base_filename')}.exe",
    )
    table.add_row(
        t("cmd_package_innosetup_prop_target_dir"),
        cfg.inno.get("default_dir_name"),
    )
    table.add_row(t("cmd_package_innosetup_prop_iscc_bin"), str(iscc_bin))

    out.print(table)
    out.print()

    build_tmp_dir = root / "build"
    build_tmp_dir.mkdir(parents=True, exist_ok=True)
    iss_file = build_tmp_dir / "installer.iss"

    out_file_path = (
        root
        / cfg.build.get("output_dir", "dist")
        / f"{cfg.inno.get('output_base_filename')}.exe"
    )

    try:
        with out.status(
            f"[bold green]{t('cmd_package_innosetup_running')}[/bold green]",
            spinner="dots",
        ):
            _build_iss_script(cfg, root, iss_file)
            cmd = [str(iscc_bin), str(iss_file)]
            success = run_system_command(cmd, cwd=root, console=out)

        if success:
            out.print(
                Panel(
                    f"[bold green]✔ {t('cmd_package_innosetup_success_msg')}[/bold green]\n\n"
                    f"{t('cmd_package_innosetup_location_label')}: [cyan]{out_file_path}[/cyan]",
                    title=f"[bold green]{t('cmd_package_innosetup_success_title')}[/bold green]",
                    border_style="green",
                )
            )
            return True
        else:
            out.print(
                f"[bold red]❌ {t('cmd_package_innosetup_failed_msg')}[/bold red]"
            )
            return False

    finally:
        if iss_file.exists():
            try:
                iss_file.unlink()
            except OSError:
                pass