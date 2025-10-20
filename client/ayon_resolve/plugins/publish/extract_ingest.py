import os
import pyblish.api
from pathlib import Path

from ayon_core.pipeline import publish
from ayon_resolve import api
from ayon_resolve.otio.davinci_export import create_otio_timeline
from ayon_resolve.api.rendering import (
    set_format_and_codec,
    render_single_timeline
)
from ayon_resolve.api.lib import maintain_page_by_name
import opentimelineio as otio


class ExtractIngest(publish.Extractor):
    label = "Extract Ingest"
    order = pyblish.api.ExtractorOrder + 0.4
    families = ["ingest"]

    def process(self, instance):
        project_manager = api.get_project_manager()
        current_project = project_manager.GetCurrentProject()
        timeline = current_project.GetCurrentTimeline()
        project_name = instance.context.data["projectName"]

        # deliver params
        current_project.SetCurrentRenderFormatAndCodec('mov', 'ProRes422')

        staging_dir = self.staging_dir(instance)
        self.log.info(f"Staging directory: {staging_dir}")
        
        otio_file_path = self.export_timeline_as_otio(
            current_project, timeline, project_name, staging_dir
        )
        
        video_file_path = self.export_timeline_as_video(
            timeline, project_name, staging_dir
        )
        
        instance.data["otioFilePath"] = otio_file_path
        instance.data["videoFilePath"] = video_file_path
        
        self.prepare_kitsu_config(instance, timeline, otio_file_path, video_file_path)
        
        if "representations" not in instance.data:
            instance.data["representations"] = []
        
        otio_representation = {
            "name": "otio",
            "ext": "otio",
            "files": os.path.basename(otio_file_path),
            "stagingDir": staging_dir,
            "tags": ["ingest", "timeline", "metadata"]
        }
        instance.data["representations"].append(otio_representation)
        
        video_representation = {
            "name": "prores",
            "ext": "mov",
            "files": os.path.basename(video_file_path),
            "stagingDir": staging_dir,
            "tags": ["ingest", "video", "prores422"]
        }
        instance.data["representations"].append(video_representation)
        
        self.log.info(f"Extracted OTIO timeline: {otio_file_path}")
        self.log.info(f"Extracted ProRes422 video: {video_file_path}")

    def export_timeline_as_otio(self, project, timeline, project_name, staging_dir):
        otio_filename = f"{project_name}_ingest.otio"
        otio_file_path = os.path.join(staging_dir, otio_filename)
    
        
        try:
            otio_timeline = create_otio_timeline(
                project,
                timeline=timeline
            )
            
            otio.adapters.write_to_file(otio_timeline, otio_file_path)
            
            if not os.path.exists(otio_file_path):
                raise RuntimeError("OTIO file was not created successfully")
                
        except Exception as exc:
            raise RuntimeError(f"Failed to export OTIO timeline: {exc}")
        
        return otio_file_path

    def export_timeline_as_video(self, timeline, project_name, staging_dir):
        video_filename = f"{project_name}_ingest.mov"
        video_file_path = os.path.join(staging_dir, video_filename)
        
        try:
            with maintain_page_by_name("Deliver"):
                staging_path = Path(staging_dir)
            
                timeline_fps = timeline.GetSetting("timelineFrameRate")
                timeline_width = timeline.GetSetting("timelineResolutionWidth")
                timeline_height = timeline.GetSetting("timelineResolutionHeight")
                
                current_project = api.get_current_project()
                render_settings = {
                    "SelectAllFrames": True,
                    "CustomName": video_filename,
                    "ExportVideo": True,
                    "ExportAudio": True,
                    "FormatWidth": timeline_width,
                    "FormatHeight": timeline_height,
                    "FrameRate": timeline_fps,
                    "TargetDir": staging_path.as_posix()
                }
                current_project.SetRenderSettings(render_settings)
                
                if not render_single_timeline(timeline, staging_path):
                    raise RuntimeError("Failed to render timeline to video")
                
                if not os.path.exists(video_file_path):
                    raise RuntimeError("Video file was not created successfully")
                    
        except Exception as exc:
            raise RuntimeError(f"Failed to export ProRes422 video: {exc}")
        
        return video_file_path

    def prepare_kitsu_config(self, instance, timeline, otio_file_path, video_file_path):
        fps = timeline.GetSetting("timelineFrameRate")
        
        kitsu_config = {
            "server": os.environ.get("KITSU_SERVER"),
            "email": os.environ.get("KITSU_LOGIN"),
            "password": os.environ.get("KITSU_PWD"),
            "fps": fps
        }
        
        ingest_args = {
            "metadata": otio_file_path,
            "video": video_file_path,
            "push": instance.data.get("push", False),
            "push_only": instance.data.get("push_only", False),
            "origin": instance.data.get("origin", "From AYON"),
            "force": instance.data.get("force", False),
            "fps": fps
        }
        
        instance.data["kitsuConfig"] = kitsu_config
        instance.data["ingestArgs"] = ingest_args
