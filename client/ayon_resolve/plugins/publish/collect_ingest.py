import pyblish.api

import ayon_api

from ayon_resolve.api.lib import maintain_current_timeline

class IngestInstances(pyblish.api.InstancePlugin):
    """Collect all Track items selection."""

    order = pyblish.api.CollectorOrder - 0.49
    label = "Collect Ingest Instances"
    families = ["ingest"]

    def process(self, instance):
        # project_name = instance.context.data["projectName"]
        # version = instance.data.get("version")

        media_pool_item = instance.data["transientData"]["timeline_pool_item"]

        # versioning ingest products ? (see editorial_pkg for details)

        with maintain_current_timeline(media_pool_item) as timeline:
            instance.data.update(
                {
                    "mediaPoolItem": media_pool_item,
                    "item": media_pool_item,
                    "fps": timeline.GetSetting("timelineFrameRate"),
                    "frameStart": timeline.GetStartFrame(),
                    "frameEnd": timeline.GetEndFrame()
                }
            )
