import pyblish.api
import os

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishXmlValidationError,
    OptionalPyblishPluginMixin
)

from ayon_resolve import api

class ValidateIngest(pyblish.api.InstancePlugin, OptionalPyblishPluginMixin):
    """
    Validate ingest instance requirements.
    
    Checks that:
    - Timeline and project are available
    - Required Kitsu environment variables are set
    - Instance data contains necessary information
    """
    order = ValidateContentsOrder
    label = "Validate Ingest"
    hosts = ["resolve"]
    families = ["ingest"]

    def process(self, instance):
        project_manager = api.get_project_manager()
        self.validate_resolve_context(project_manager)
        self.validate_kitsu_environment()
        self.validate_timeline_against_task(instance, project_manager)

        self.log.info("Ingest validation passed successfully")

    def validate_resolve_context(self, project_manager):
        try:
            current_project = project_manager.GetCurrentProject()
            timeline = current_project.GetCurrentTimeline()
            
            if not current_project:
                raise PublishXmlValidationError("No current Resolve project found")
            
            if not timeline:
                raise PublishXmlValidationError("No current timeline found in Resolve")
                
        except Exception as exc:
            raise PublishXmlValidationError(
                f"Failed to access Resolve context: {exc}"
            )

    def validate_kitsu_environment(self):
        required_vars = {
            "KITSU_LOGIN": os.environ.get("KITSU_LOGIN"),
            "KITSU_PASSWORD": os.environ.get("KITSU_PWD"), 
            "KITSU_SERVER": os.environ.get("KITSU_SERVER")
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        
        if missing:
            raise PublishXmlValidationError(
                f"Missing required Kitsu environment variables: {', '.join(missing)}"
            )

    def validate_timeline_against_task(self, instance, project_manager):
        try:
            current_project = project_manager.GetCurrentProject()
            timeline = current_project.GetCurrentTimeline()
            
            timeline_fps = timeline.GetSetting("timelineFrameRate")
            if not timeline_fps or timeline_fps <= 0:
                raise PublishXmlValidationError("Invalid timeline frame rate")
            
            context_fps = instance.context.data.get("fps")

            resolution_width = timeline.GetSetting("timelineResolutionWidth")
            resolution_height = timeline.GetSetting("timelineResolutionHeight")
            
            task_entity = instance.context.data.get("taskEntity", {})
            self.log.info(f"Task entity: {task_entity}")
            task_attribs = task_entity.get("attrib", {})
            self.log.info(f"Task attributes: {task_attribs}")
            expected_width = task_attribs.get("resolutionWidth")
            expected_height = task_attribs.get("resolutionHeight")

            self.log.info(f"resolution: {resolution_width}x{resolution_height} vs {expected_width}x{expected_height}")
            
            if expected_width is not None and expected_height is not None:
                if (int(resolution_width) != int(expected_width) or
                    int(resolution_height) != int(expected_height)):
                    raise PublishXmlValidationError(
                        f"Timeline resolution ({resolution_width}x{resolution_height}) "
                        f"does not match task resolution ({expected_width}x{expected_height}). "
                        f"Please adjust timeline settings to match task requirements."
                    )
                
                self.log.info(
                    f"Timeline resolution ({resolution_width}x{resolution_height}) "
                    f"matches task resolution ({expected_width}x{expected_height})"
                )
            else:
                raise PublishXmlValidationError(
                    "Task resolution attributes are missing or invalid."
                )
            
            if context_fps is not None:
                fps_tolerance = 0.01
                if abs(timeline_fps - context_fps) > fps_tolerance:
                    raise PublishXmlValidationError(
                        f"Timeline FPS ({timeline_fps}) does not match "
                        f"task FPS ({context_fps}). "
                        f"Please adjust timeline settings to match task requirements."
                    )
                    
                self.log.info(
                    f"Timeline FPS ({timeline_fps}) matches task FPS ({context_fps})"
                )
            else:
                raise PublishXmlValidationError(
                    "Task FPS attribute is missing or invalid."
                )
            
        except Exception as exc:
            if isinstance(exc, PublishXmlValidationError):
                raise
            raise PublishXmlValidationError(
                f"Failed to validate timeline against task: {exc}"
            )