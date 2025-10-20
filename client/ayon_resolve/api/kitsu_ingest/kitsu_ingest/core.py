import argparse
# import pyfiglet
import logging
import sys
import os
from typing import List, Tuple
from .processors.pushonly_processor import PushonlyCsvProcessor
from .processors.csv_processor import CsvProcessor
from .processors.edl_processor import EdlProcessor
from .processors.otio_processor import OtioProcessor
from .processors.video_processor import VideoProcessor
from .kitsu.publisher import KitsuPublisher
from .models.models import Project, Sequence, Shot
from .processors.base import BaseProcessor
from .config.config import get_settings, Settings

logger = logging.getLogger(__name__)

try:
    settings = get_settings()
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=settings.log_level.upper(),
            format=settings.log_format
        )
except Exception:
    if not logging.getLogger().handlers:
        logging.basicConfig(level='INFO')

# This program is made to ingest data from various formats into Kitsu 
# It is based on the Kitsu API but creates objects (Project > Sequence > Shot) used to process the data locally
# It is designed using OOP principles to allow for easy extension and modification
# Proudly written at 8449
# ༼ つ ◕_◕ ༽つ 

class Workflow:
    def __init__(self, args, config: Settings):
        self.args = args
        self.config = config
        self.output_dir = None


    def run(self):
        self.config.args = self.args

        if self.args.output_dir:
            self.output_dir = self.args.output_dir
        
        processor = self._initialize_processor()
        logger.info(f"Processing metadata file: {processor.input_path}")
        sequences: List[Sequence] = processor.process()

        if not sequences:
            raise ValueError("No sequences were extracted from the metadata file.")

        project = Project(
            name=self.args.push or "local_project",
            sequences=sequences
        )
        logger.info(f"Created project '{project.name}' with {project.sequence_count} sequence(s) and {project.total_shot_count} total shots.")

        if self.args.video:
           self._process_video(project)

        if self.args.push or self.args.push_only:
            self._verify_local_previews(project, self.output_dir)

            if self.args.metadata:
                processed_csv_path = processor.save_to_csv(project.sequences)
                if not processed_csv_path:
                    raise ValueError("Failed to save the processed CSV file.")
            else: # --push_only 
                processed_csv_path = processor.input_path

            self._publish_to_kitsu(processed_csv_path, project, self.output_dir)

    def _verify_local_previews(self, project: Project, previews_dir: str):
        # match local mp4s with CSV data
        logger.info(f"Verifying local previews in '{previews_dir}' before publishing...")

        if not os.path.isdir(previews_dir):
            if self.args.video or self.args.push_only:
                raise FileNotFoundError(f"Previews directory '{previews_dir}' does not exist.")
            logger.warning(f"Previews directory '{previews_dir}' does not exist. Skipping preview verification.")
            return

        expected_shot_names = {shot.name for seq in project.sequences for shot in seq.shots}
        local_mp4_files = {os.path.splitext(f)[0] for f in os.listdir(previews_dir) if f.lower().endswith(".mp4")}

        if not expected_shot_names and not local_mp4_files:
            logger.info("No shots defined in metadata and no local previews found. Nothing to verify.")
            return

        missing_previews = expected_shot_names - local_mp4_files
        extra_previews = local_mp4_files - expected_shot_names

        is_valid = True
        if missing_previews:
            logger.warning(f"Found {len(missing_previews)} shots from metadata with no matching MP4 file: {sorted(list(missing_previews))}")
            is_valid = False
        if extra_previews:
            logger.warning(f"Found {len(extra_previews)} extra MP4 files with no matching shot in metadata: {sorted(list(extra_previews))}")
            is_valid = False

        if not is_valid:
            if not self.args.force:
                logger.error("Verification failed. Mismatches found between metadata and local preview files. Use --force to publish anyway.")
                raise ValueError("Local verification failed. Aborting publish.")
            else:
                logger.warning("Verification failed, but --force is enabled. Proceeding with publishing.")
        else:
            logger.info("Local verification successful. All shots from metadata have a matching preview file.")

    def _publish_to_kitsu(self, csv_path: str, project: Project, previews_dir: str):
        logger.info(f"Starting push to Kitsu project: {project.name}")
        
        publisher = KitsuPublisher(
            project_name=project.name,
            origin=self.args.origin,
            config=self.config
        )
        if publisher.connect():
            publisher.verify_data_integrity(project.sequences)
            publisher.ensure_sequences_exist(project.sequences)
            publisher.import_shots_from_csv(csv_path)
            publisher.publish_previews(previews_dir)
            logger.info(f"Successfully pushed project '{project.name}' to Kitsu.")
        else:
            logger.error("Failed to connect to Kitsu. Cannot push project.")
            raise ConnectionError("Failed to connect to Kitsu. Please check your credentials and server settings.")

    def _process_video(self, project: Project):
        logger.info(f"Preparing to process video: {self.args.video}")

        all_shots_for_video: List[Tuple[str, Shot]] = []

        for sequence in project.sequences:
            for shot in sequence.shots:
                all_shots_for_video.append((sequence.name, shot))

        if not all_shots_for_video:
            logger.warning("No shots were found to process for the video. Skipping video processing.")
            return

        logger.info(f"Passing a total of {len(all_shots_for_video)} shots to the VideoProcessor.")
        
        video_processor = VideoProcessor(self.args.video, all_shots_for_video, self.output_dir)
        video_processor.process()

    # fetch the latest CSV or EDL file from a folder
    def _fetch_metadata_file_from_folder(self, path):
        if os.path.isdir(path):
            extensions = ('.edl', '.csv', '.otio')
            files = []
            
            for ext in extensions:
                files.extend(
                    os.path.join(path, f) for f in os.listdir(path)
                    if f.lower().endswith(ext) and os.path.isfile(os.path.join(path, f))
                )
            
            if not files:
                raise FileNotFoundError(f"[fetch_metadata_file_from_folder] No .edl, .csv, .otio files found in directory: {path}")
            
            newest_file = max(files, key=os.path.getmtime)
            return newest_file
        else:
            raise FileNotFoundError(f"[fetch_metadata_file_from_folder] Path does not exist: {path}")

            
    def _initialize_processor(self) -> BaseProcessor:
        input_path = None
        output_dir_override = None

        if self.args.metadata:
            input_path = self.args.metadata
            if self.output_dir:
                output_dir_override = self.output_dir
        elif self.args.push_only:
            output_dir_override = self.args.push_only
            input_path = self._fetch_metadata_file_from_folder(output_dir_override)
        else:
            raise ValueError("You must provide either --metadata or --push_only")

        file_ext = os.path.splitext(input_path)[1].lower()
        
        if self.args.push_only:
            return PushonlyCsvProcessor(input_path, self.args.fps, output_dir_override)
        elif file_ext == '.csv':
            return CsvProcessor(input_path, self.args.fps, output_dir_override)
        elif file_ext == '.edl':
            return EdlProcessor(input_path, self.args.fps, output_dir_override)
        elif file_ext == '.otio':
            return OtioProcessor(input_path, self.args.fps, output_dir_override)
        else:
            raise ValueError(f"Unsupported metadata file format: '{file_ext}'. Please use .csv or .edl.")

def get_origin_choice():
    while True:
        print("Please select a project originator:")
        print("1. 8849")
        print("2. EVEREST")
        
        choice = input("Enter your choice (1 or 2): ")
        
        if choice == '1':
            logging.info(f"8849 selected as project originator.")
            return "8849"
        elif choice == '2':
            logging.info(f"EVEREST selected as project originator.")
            return "EVEREST"
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format=settings.log_format
    )

    parser = argparse.ArgumentParser(description='8849 Ingest Tool', formatter_class=argparse.RawTextHelpFormatter)
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-m', '--metadata', help='Path to the breakdown metadata file (.csv or .edl) for local processing.')
    mode_group.add_argument('--push_only', help='Path of a folder containing a metadata file and videos to process and push to Kitsu.')
    
    parser.add_argument('-v', '--video', help='Path to the source video file (only used with --metadata).')
    parser.add_argument('-p', '--push', help='Project name to push to Kitsu.')
    parser.add_argument('--fps', type=float, help=f'Project FPS (default: {settings.default_fps})')
    parser.add_argument('--origin', choices=['8849', 'EVEREST'], help='Project originator (required for pushing to Kitsu).')
    parser.add_argument('--force', action='store_true', help='Force publishing even if verification checks fail.')

    # asciip = pyfiglet.figlet_format("8849 Ingest", font="shadow")
    # print(asciip)

    args = parser.parse_args()

    if args.push_only and not args.push:
        parser.error("--push_only requires --push PROJECT_NAME")

    if args.video and not args.metadata:
        parser.error("--video requires --metadata to define shots and frame ranges")

    if args.origin is None and (args.push or args.push_only):
        args.origin = get_origin_choice()
        if args.origin == "8849":
            args.origin = "From 8849"
        elif args.origin == "EVEREST":
            args.origin = "From EVEREST"
    elif args.origin:
        args.origin = "From " + args.origin

    if not args.fps:
        args.fps = settings.default_fps
        logging.warning("\033[91mNo FPS provided, defaulting to 25\033[0m")
    
    try:
        logger.info("Starting Ingest Workflow...")
        workflow = Workflow(args, settings)
        workflow.run()
        logger.info("Workflow finished successfully.")
        sys.exit(0)
    except (FileNotFoundError, ValueError, ConnectionError) as e:
        logger.critical(f"Error: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
    
    sys.exit(1)