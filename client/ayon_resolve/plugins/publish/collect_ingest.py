import pyblish.api

import ayon_api

from ayon_resolve.api.lib import maintain_current_timeline

class IngestInstances(pyblish.api.InstancePlugin):
    """Collect all Track items selection."""

    order = pyblish.api.CollectorOrder - 0.49
    label = "Collect Ingest Instances"
    families = ["ingest"]

    def process(self, instance):
        project_name = instance.context.data["projectName"]

        media_pool_item = instance.data["transientData"]["timeline_pool_item"]

        version = instance.data.get("version")

        print(f"Collecting Ingest Instances for {project_name} - Version: {version}")
        print(instance.data)
        # if version is not None:
        #     version += 1

        #     folder_entity = ayon_api.get_folder_by_path(
        #         project_name=project_name,
        #         folder_path=instance.data["folderPath"],
        #     )
        #     last_version = ayon_api.get_last_version_by_product_name(
        #         project_name=project_name,
        #         product_name=instance.data["productName"],
        #         folder_id=folder_entity["id"],
        #     )
        #     if last_version is not None:
        #         last_version = int(last_version["version"])
        #         if version <= last_version:
        #             version = last_version + 1

        # instance.data["version"] = version

        # with maintain_current_timeline(media_pool_item) as timeline:
        #     instance.data.update(
        #         {
        #             "mediaPoolItem": media_pool_item,
        #             "item": media_pool_item,
        #             "fps": timeline.GetSetting("timelineFrameRate"),
        #             "frameStart": timeline.GetStartFrame(),
        #             "frameEnd": timeline.GetEndFrame()
        #         }
        #     )

        creator_attributes = instance.data.get("creator_attributes", {})
        
        ingest_to_kitsu = creator_attributes.get("ingest", False)
        if ingest_to_kitsu:
            instance.data["families"].append("kitsu")

        self.log.debug(f"Ingest: {instance.data}")
