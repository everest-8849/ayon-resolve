"""This script is used as a startup script in Resolve through a .scriptlib file

It triggers directly after the launch of Resolve and it's recommended to keep
it optimized for fast performance since the Resolve UI is actually interactive
while this is running. As such, there's nothing ensuring the user isn't
continuing manually before any of the logic here runs. As such we also try
to delay any imports as much as possible.

This code runs in a separate process to the main Resolve process.

"""
import os
from ayon_core.lib import Logger
import ayon_resolve.api

log = Logger.get_logger(__name__)


# Undocumented app variable is injected by Resolve automatically
# https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=113252
app: object   # noqa: F821


def ensure_installed_host():
    """Install resolve host with openpype and return the registered host.

    This function can be called multiple times without triggering an
    additional install.
    """
    from ayon_core.pipeline import install_host, registered_host
    host = registered_host()
    if host:
        return host

    # Register injected "app" variable at class level for future uses.
    # For free version of DaVinci Resolve, this seems to be
    # the only way to gather the Resolve/Fusion applications.
    ayon_resolve.api.ResolveHost.set_resolve_modules_from_app(app)  # noqa: F821

    host = ayon_resolve.api.ResolveHost()
    install_host(host)
    return registered_host()


def launch_menu():
    print("Launching Resolve AYON menu..")
    ensure_installed_host()
    ayon_resolve.api.launch_ayon_menu()


def open_workfile(path):
    # Avoid the need to "install" the host
    host = ensure_installed_host()
    host.open_workfile(path)


def main():
    # Open last workfile
    workfile_path = os.environ.get("AYON_RESOLVE_OPEN_ON_LAUNCH")

    if workfile_path and os.path.exists(workfile_path):
        log.info(f"Opening last workfile: {workfile_path}")
        open_workfile(workfile_path)
    else:
        log.info("No last workfile set to open.")
        if settings.get("resolve", {}).get("templated_workfile", {}).get("create_first_version", False):
            log.info("Creating first workfile version on startup.")

            curr_os = sys.platform
            if curr_os == "win32" or curr_os == "cygwin":
                template_path = settings.get("resolve", {}).get("templated_workfile", {}).get("win_template_path", "")
            elif curr_os == "darwin":
                template_path = settings.get("resolve", {}).get("templated_workfile", {}).get("mac_template_path", "")
            else:
                log.warning(f"Unsupported OS: {curr_os}. Cannot create workfile from template.")

            log.info(f"Using template path: {template_path}")

            workfile_path = os.environ.get("AYON_LAST_WORKFILE")
            
            if not workfile_path:
                log.warning("AYON_LAST_WORKFILE environment variable not set. Cannot create workfile from template.")
            else:
                workfile_path_dir = os.path.dirname(workfile_path)

                if template_path and os.path.exists(template_path):
                    try:
                        os.makedirs(workfile_path_dir, exist_ok=True)
                        
                        template_copy = shutil.copy(template_path, workfile_path_dir)
                        os.rename(template_copy, workfile_path)
                        open_workfile(workfile_path)
                        ayon_resolve.api.save_file(workfile_path)
                        log.info(f"Successfully created workfile from template: {workfile_path}")
                    except Exception as e:
                        log.error(f"Failed to create workfile from template: {e}")
                else:
                    log.warning(f"Template path does not exist or is empty: {template_path}")

    # Gathered project settings
    from ayon_core.settings import get_project_settings
    from ayon_core.pipeline.context_tools import get_current_project_name
    project_name = get_current_project_name()
    log.info(f"Current project name in context: {project_name}")

    # Launch AYON menu
    settings = get_project_settings(project_name)
    if settings.get("resolve", {}).get("launch_ayon_menu_on_start", True):
        log.info("Launching AYON menu..")
        launch_menu()


if __name__ == "__main__":
    main()
