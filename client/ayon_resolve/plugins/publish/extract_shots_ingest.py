import os
from pathlib import Path
import opentimelineio as otio
from ayon_core.pipeline import publish
from studio_ingest import Ingester
import pyblish.api


class ExtractShotsIngest(publish.Extractor):
    """
    Extracts shots from OTIO and intermediate video.
    """

    label = "Extract Shots Ingest"
    order = pyblish.api.ExtractorOrder + 0.46
    families = ["ingest"]

    def process(self, instance):
        otio_file_path = None
        intermediate_file_path = None

        for repre in instance.data.get("representations", []):
            if repre["name"] == "otio_remap":
                otio_file_path = os.path.join(repre["stagingDir"], repre["files"])
            elif repre["name"] == "intermediate":
                files = repre["files"]
                if isinstance(files, list):
                    files = files[0]
                intermediate_file_path = os.path.join(repre["stagingDir"], files)

        if not otio_file_path:
            raise RuntimeError("Missing OTIO file representation ('otio_remap')")
        if not intermediate_file_path:
            raise RuntimeError("Missing intermediate video file representation ('intermediate')")

        self.log.info(f"Ingesting OTIO: {otio_file_path}")
        self.log.info(f"Ingesting Video: {intermediate_file_path}")

        staging_dir = Path(otio_file_path).parent

        ingester = Ingester(
            metadata=otio_file_path,
            intermediate=intermediate_file_path,
            project_name=instance.context.data["projectName"],
            staging_dir=staging_dir,
            log=self.log,
        )
        ingester.run()

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
