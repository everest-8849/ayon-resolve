import os
import logging
import gazu
from typing import List
from ..models.models import Sequence
from ..config.config import Settings

logger = logging.getLogger(__name__)
TASK_STATUS_NAME = "Done"

class KitsuPublisher:
    def __init__(self, project_name: str, origin: str, config: Settings):
        self.project_name = project_name
        self.origin = origin
        self.config = config
        self.project = None

    def connect(self) -> bool:
        try:
            logger.info(f"Connecting to Kitsu at {self.config.kitsu_server}...")
            gazu.set_host(self.config.kitsu_server)
            gazu.log_in(self.config.kitsu_email, self.config.kitsu_password)
            
            self.project = gazu.project.get_project_by_name(self.project_name)
            if not self.project:
                raise ValueError(f"Project '{self.project_name}' not found on Kitsu server.")
            
            logger.info(f"Successfully connected to project '{self.project_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kitsu: {e}")
            return False

    def ensure_sequences_exist(self, sequences: List[Sequence]):
        logger.info("Checking for existing sequences in Kitsu...")
        existing_sequences = gazu.shot.all_sequences_for_project(self.project)
        existing_sequence_names = {seq['name'] for seq in existing_sequences}
        
        for sequence in sequences:
            if sequence.name not in existing_sequence_names:
                logger.info(f"Sequence '{sequence.name}' not found. Creating it now...")
                try:
                    gazu.shot.new_sequence(self.project, sequence.name)
                    logger.info(f"Successfully created sequence '{sequence.name}'.")
                except Exception as e:
                    raise RuntimeError(f"Failed to create sequence '{sequence.name}': {e}") from e
            else:
                logger.info(f"Sequence '{sequence.name}' already exists.")

    def import_shots_from_csv(self, csv_path: str):
        logger.info(f"Importing shots from CSV: {csv_path}")
        try:
            gazu.shot.import_shots_with_csv(self.project, csv_path)
            logger.info("Shot import complete.")
        except Exception as e:
            logger.error(f"Failed to import shots from CSV: {e}")
            raise

    def verify_data_integrity(self, sequences: List[Sequence]):
        # Verify shot names (local vs kitsu)
        logger.info("Verifying data integrity...")
        local_shot_names = {shot.name for seq in sequences for shot in seq.shots}

        kitsu_shots = gazu.shot.all_shots_for_project(self.project)
        kitsu_shot_names = {shot['name'] for shot in kitsu_shots}
        
        if not len(kitsu_shot_names):
            logger.info("Empty Kitsu project, skipping verification.")
            return

        local_shots_not_in_kitsu = local_shot_names - kitsu_shot_names
        missing_kitsu_shots = kitsu_shot_names - local_shot_names

        is_valid = True
        if local_shots_not_in_kitsu:
            logger.warning(f"Missing local shots that are not in Kitsu: {local_shots_not_in_kitsu}")
            is_valid = False
        
        if missing_kitsu_shots:
            logger.warning(f"Missing Kitsu shots that are not in local data: {missing_kitsu_shots}")
            is_valid = False
        
        if not is_valid:
            if self.config.args.force:
                logger.info("Force mode enabled, proceeding despite verification issues.")
            else:
                raise RuntimeError("Data verification failed. Missing shots detected. Use --force to bypass this check.")
        
        # user_validation = True
        # if kitsu_shot_names == local_shot_names:
        #     user_validation = self._get_user_validation()

        # if user_validation:
        self._verify_metadata(sequences, kitsu_shots)

    def _verify_metadata(self, sequences: List[Sequence], kitsu_shots: set):
        # Verify shots metadata (local vs kitsu)
        local_shot_map = {shot.name: shot for seq in sequences for shot in seq.shots}
        kitsu_shot_map = {shot['name']: shot for shot in kitsu_shots}

        mismatch_errors = []

        common_shot_names = local_shot_map.keys() & kitsu_shot_map.keys() # create intersection (both values must exist)

        if not common_shot_names:
            logger.warning("No common shots found between local data and Kitsu. Skipping metadata verification.")
            return

        for name in common_shot_names:
            local_shot = local_shot_map[name]
            kitsu_shot = kitsu_shot_map[name]
            
            local_fps = next((seq.fps for seq in sequences if local_shot in seq.shots), None) # next == get the first valid match

            kitsu_frame_in = kitsu_shot.get('data', {}).get('frame_in')
            if kitsu_frame_in is not None and str(local_shot.frame_in) != str(kitsu_frame_in):
                mismatch_errors.append(
                    f"- {name}: Local frame_in ({local_shot.frame_in}) != Kitsu frame_in ({kitsu_frame_in})"
                )
            
            kitsu_frame_out = kitsu_shot.get('data', {}).get('frame_out')
            if kitsu_frame_out is not None and str(local_shot.frame_out) != str(kitsu_frame_out):
                mismatch_errors.append(
                    f"- {name}: Local frame_out ({local_shot.frame_out}) != Kitsu frame_out ({kitsu_frame_out})"
                )

            kitsu_fps = kitsu_shot.get('fps')
            if local_fps and kitsu_fps and local_fps != kitsu_fps:
                 mismatch_errors.append(
                    f"- {name}: Local FPS ({local_fps}) != Kitsu FPS ({kitsu_fps})"
                )

        if not mismatch_errors:
            logger.info("Metadata verification successful. All common shots match.")
            return

        error_summary = "\n".join(mismatch_errors)
        logger.warning(f"Found {len(mismatch_errors)} metadata mismatches:\n{error_summary}")

        if not self.config.args.force:
            raise RuntimeError("Metadata verification failed. Use --force to bypass this check.")
        else:
            logger.warning("Force mode enabled, proceeding despite metadata mismatches.")

    def publish_previews(self, previews_dir: str):
        # Fetch local mp4s and kitsu shots
        logger.info("Starting preview publishing process...")
        
        mp4_files = [f for f in os.listdir(previews_dir) if f.lower().endswith(".mp4")]
        if not mp4_files:
            raise RuntimeError(
                f"No MP4 files found in the previews directory: {previews_dir}. "
                "Ensure that the directory contains valid MP4 files."
            ) from e

        all_kitsu_shots = gazu.shot.all_shots_for_project(self.project)

        kitsu_shot_map = {shot['name']: shot for shot in all_kitsu_shots}

        try:
            task_type = gazu.task.get_task_type_by_name(self.origin)
            task_status = gazu.task.get_task_status_by_name(TASK_STATUS_NAME)
        except Exception as e:
            raise RuntimeError(
                f"Failed to find required Task Type or Task Status. Ensure they exist in Kitsu for project '{self.project_name}'."
            ) from e
        
        for file_name in mp4_files:
            unique_shot_name = os.path.splitext(file_name)[0]
            kitsu_shot = kitsu_shot_map.get(unique_shot_name)

            if not kitsu_shot:
                if self.config.args.force:
                    logger.warning(f"Shot '{unique_shot_name}' not found in Kitsu. Publishing as new shot.")
                else:
                    raise RuntimeError(
                        f"Shot '{unique_shot_name}' not found in Kitsu. Ensure the shot exists and is correctly named."
                    ) from e

            try:
                task = gazu.task.get_task_by_name(kitsu_shot, task_type)
                if not task:
                    logger.warning(f"No task of type '{self.origin}' found for shot: {unique_shot_name}")
                    raise RuntimeError(
                        f"No task of type '{self.origin}' found for shot: {unique_shot_name}. "
                        "Ensure the task type exists and is correctly set up in Kitsu."
                    ) from e

                video_path = os.path.join(previews_dir, file_name)
                logger.info(f"Publishing preview for: {unique_shot_name}")

                comment = gazu.task.add_comment(task=task, task_status=task_status, comment="Kitsu Ingester | Auto-published preview.")
                preview = gazu.task.add_preview(task=task, comment=comment, preview_file_path=video_path)
                gazu.task.set_main_preview(preview)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to publish preview for {unique_shot_name}: {e}"
                ) from e
            
    def _get_user_validation(self) -> bool:
        while True:
            print("Every shot in Kitsu matches the local data.")
            print("Pushing the project will iterate a new version on Kitsu. Continue? (y/n)")
            user_input = input().strip().lower()
            if user_input in ['y', 'yes']:
                return True
            elif user_input in ['n', 'no']:
                raise RuntimeError("User cancelled the operation. No changes made to Kitsu.")
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
