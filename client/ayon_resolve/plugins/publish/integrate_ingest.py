import os
import sys
import pyblish.api

from ayon_core.pipeline import publish
from ayon_resolve.api.kitsu_ingest.kitsu_ingest.config.config import get_settings
from ayon_resolve.api.kitsu_ingest.kitsu_ingest.core import Workflow

# from ayon_api import get_addon_settings

from ayon_resolve.version import __version__
from ayon_resolve.constants import ADDON_NAME

from ayon_core.lib.vendor_bin_utils import get_ffmpeg_tool_path


class IntegrateIngest(pyblish.api.InstancePlugin):
    label = "Integrate Ingest"
    order = pyblish.api.IntegratorOrder
    families = ["ingest"]

    def process(self, instance):
        
        # kitsu_config = instance.data.get("kitsuConfig")
        # ingest_args = instance.data.get("ingestArgs")
        # otio_file_path = instance.data.get("otioFilePath")
        # video_file_path = instance.data["videoFilePath"]
        # project_name = instance.context.data["projectName"]

        # if not all([kitsu_config, ingest_args, otio_file_path, video_file_path, project_name]):
        #     raise RuntimeError(
        #         "Missing required data for Kitsu integration. "
        #         "Ensure ExtractIngest plugin ran successfully."
        #     )
        
        # if not os.path.exists(otio_file_path):
        #     raise RuntimeError(f"OTIO file not found: {otio_file_path}")
        
        # # addon_settings = get_addon_settings(ADDON_NAME, __version__)

        # ffmpeg_path = ""
        # ffmpeg_path = get_ffmpeg_tool_path("ffmpeg")
        # if not ffmpeg_path:
        #     raise RuntimeError(f"Could not find ffmpeg path")
        # ffmpeg_path = os.path.dirname(ffmpeg_path)
        # os.environ["PATH"] += os.pathsep + ffmpeg_path
        
        # try:            
        #     config = get_settings()
        #     config.kitsu_server = kitsu_config["server"]
        #     config.kitsu_email = kitsu_config["email"]
        #     config.kitsu_password = kitsu_config["password"]
        #     config.default_fps = kitsu_config["fps"]
            
        #     staging_dir = os.path.dirname(otio_file_path)
            
        #     args = IngestArgs(
        #         metadata=otio_file_path,
        #         push=project_name,
        #         push_only=None,
        #         video=video_file_path,
        #         force=True,
        #         fps=ingest_args["fps"],
        #         origin="From 8849",
        #         output_dir=staging_dir
        #     )
            
        #     try:
        #         workflow = Workflow(args, config)
        #         workflow.run()
        #     except Exception as exc:
        #         raise RuntimeError(f"Kitsu ingest workflow failed: {exc}")
            
        #     instance.data["kitsuWorkflow"] = workflow
        #     self.log.info("Kitsu ingest integration completed successfully")
            
        # except ImportError as exc:
        #     raise RuntimeError(f"Failed to import Kitsu ingest modules: {exc}")
        # except Exception as exc:
        #     raise RuntimeError(f"Kitsu ingest workflow failed: {exc}")
