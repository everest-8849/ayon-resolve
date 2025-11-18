import os
from pathlib import Path
import subprocess

import pyblish.api
import opentimelineio as otio
import ffmpeg

from ayon_core.pipeline import publish
import ayon_api
from studio_ingest import Ingester


class ExtractShotsIngest(publish.Extractor):
    """
    Extracts shots from OTIO and intermediate video.
    """

    label = "Extract Shots Ingest"
    order = pyblish.api.ExtractorOrder + 0.46
    families = ["ingest"]

    def process(self, instance):
        otio_remap_repre = ayon_api.get_representation_by_name(
            instance.data["representations"], "otio_remap"
        )
        intermediate_repre = ayon_api.get_representation_by_name(
            instance.data["representations"], "intermediate"
        )

        if not otio_remap_repre:
            raise ValueError(
                "No 'otio_remap' representation found on instance.")
        if not intermediate_repre:
            raise ValueError(
                "No 'intermediate' representation found on instance.")

        staging_dir = Path(otio_remap_repre["stagingDir"])
        otio_remap_file = staging_dir / otio_remap_repre["files"]

        intermediate_staging_dir = Path(intermediate_repre["stagingDir"])
        intermediate_video_file = (
            intermediate_staging_dir / intermediate_repre["files"]
        )

        if not otio_remap_file.exists():
            raise FileNotFoundError(
                f"OTIO remap file not found: {otio_remap_file}")

        if not intermediate_video_file.exists():
            raise FileNotFoundError(
                f"Intermediate video file not found: {intermediate_video_file}")

        ingester = Ingester(otio_remap_file, intermediate_video_file, self.log)

        # self.log.info(f"Reading OTIO file: {otio_remap_file}")
        # otio_timeline = otio.adapters.read_from_file(
        #     otio_remap_file.as_posix())

        # shots_dir = staging_dir / "shots"
        # shots_dir.mkdir(exist_ok=True)

        # # Get timeline frame rate
        # timeline_fps = otio_timeline.duration().rate

        # for i, clip in enumerate(otio_timeline.each_clip()):
        #     clip_name = f"{instance.data['folderPath'].replace('/', '_')}_{clip.name or f'shot_{i+1:03d}'}"
        #     output_filename = shots_dir / f"{clip_name}.mov"

        #     start_time = clip.source_range.start_time.to_seconds()
        #     duration = clip.source_range.duration.to_seconds()

        #     self.log.info(
        #         f"Cutting clip '{clip.name}': start={start_time}s, "
        #         f"duration={duration}s"
        #     )

        #     try:
        #         (
        #             ffmpeg.input(
        #                 str(intermediate_video_file),
        #                 ss=start_time
        #             )
        #             .output(
        #                 str(output_filename),
        #                 t=duration,
        #                 c="copy"
        #             )
        #             .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        #         )
        #         self.log.info(f"Successfully created shot: {output_filename}")

        #         # Create a representation for the new shot clip
        #         shot_repre = {
        #             "name": clip.name or f"shot_{i+1:03d}",
        #             "ext": "mov",
        #             "files": output_filename.name,
        #             "stagingDir": shots_dir.as_posix(),
        #             "tags": ["shot_clip"],
        #             "frameStart": clip.source_range.start_time.to_frames(timeline_fps),
        #             "frameEnd": clip.source_range.end_time.to_frames(timeline_fps) - 1,
        #             "fps": timeline_fps,
        #         }
        #         instance.data["representations"].append(shot_repre)

        #     except ffmpeg.Error as e:
        #         self.log.error(f"ffmpeg error cutting clip {clip.name}:")
        #         self.log.error(e.stderr.decode())
        #         raise

        # self.log.info("Finished extracting all shot clips.")
