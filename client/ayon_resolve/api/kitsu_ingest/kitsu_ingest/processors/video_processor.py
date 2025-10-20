import os
import logging
import ffmpeg
from typing import List, Tuple
from ..models.models import Shot

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, video_path: str, shots_data: List[Tuple[str, Shot]], output_dir: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.video_path = video_path
        self.shots_data = sorted(shots_data, key=lambda item: item[1].frame_in)
        self.output_dir = output_dir
        self.processed_files = []

    def process(self):
        if not self.shots_data:
            raise ValueError("No shots provided for processing.")

        logger.info(f"Starting video processing for {len(self.shots_data)} shots from {self.video_path}")

        for idx, (sequence_name, shot) in enumerate(self.shots_data, 1):
            output_filename = f"{shot.name}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            try:
                logger.info(
                    f"Processing shot {idx}/{len(self.shots_data)}: {output_filename} "
                    f"(frames {shot.frame_in} to {shot.frame_out}, duration: {shot.duration}f)"
                )

                input_stream = ffmpeg.input(self.video_path)
                trimmed_stream = (
                    input_stream.video
                    # The 'trim' filter's end_frame is exclusive, so we add 1 to our inclusive frame_out
                    .trim(start_frame=shot.frame_in, end_frame=shot.frame_out + 1)
                    .setpts('PTS-STARTPTS') # Resets the timestamp for the new clip
                )

                (
                    ffmpeg.output(
                        trimmed_stream,
                        output_path,
                        vcodec='libx264',
                        pix_fmt='yuv420p',
                        crf=18
                    )
                    .overwrite_output()
                    .run(quiet=True, capture_stdout=True, capture_stderr=True)
                )
                
                logger.info(f"Exported: {output_path}")
                self.processed_files.append(output_path)

            except ffmpeg.Error as e:
                raise RuntimeError(
                    f"Failed to process shot {idx} ({output_filename}): {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
                ) from e

        logger.info(f"Video processing complete. Exported {len(self.processed_files)} shots.")