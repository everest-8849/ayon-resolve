from abc import ABC, abstractmethod
from typing import List
import pandas as pd
import os
from datetime import datetime
import logging
from pathlib import Path
import tempfile

from ..models.models import Sequence, Shot

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """
    Abstract base class for processing input files and converting them
    into a list of Sequence objects.
    """

    def __init__(self, input_path: str, fps: float, output_dir: str = None):
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        self.input_path = input_path
        self.fps = fps
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._temp_dir_obj = None 
        self.output_dir = output_dir or self._create_output_dir()

    def _create_output_dir(self) -> str:
        self._temp_dir_obj = tempfile.TemporaryDirectory(
            prefix=f"kitsu_ingest_{self.timestamp}_",
            dir=os.getcwd()
        )
        output_dir = self._temp_dir_obj.name
        return output_dir

    @abstractmethod
    def process(self) -> List[Sequence]:
        """
        Parses the input file and returns a list of Sequence objects.
        """
        pass

    def save_to_csv(self, sequences: List[Sequence]) -> str:
        all_shots_data = []
        for sequence in sequences:
            for shot in sequence.shots:
                shot_dict = shot.model_dump() # pydantic -> dict conversion
                shot_dict['Sequence'] = sequence.name
                shot_dict['FPS'] = sequence.fps
                shot_dict['Nb Frames'] = shot.duration
                all_shots_data.append(shot_dict)

        if not all_shots_data:
            raise ValueError("No shots found in any sequence. CSV file will not be generated.")

        df = pd.DataFrame(all_shots_data)
        df.rename(columns={'name': 'Name', 'description': 'Description', 'frame_in': 'Frame In', 'frame_out': 'Frame Out'}, inplace=True)
        
        final_columns = ['Sequence', 'Name', 'Frame In', 'Frame Out', 'Nb Frames', 'FPS', 'Description']
        df = df.reindex(columns=final_columns)

        input_filename = os.path.splitext(os.path.basename(self.input_path))[0]
        output_filename = f"{input_filename}_kitsu_{self.timestamp}.csv"
        output_path = os.path.join(self.output_dir, output_filename)

        df.to_csv(output_path, index=False)
        logging.info(f"Processed data for {len(sequences)} sequence(s) saved to: {output_path}")
        self.processed_edl_path = output_path
        return output_path

    def cleanup(self):
        if self._temp_dir_obj:
            try:
                self._temp_dir_obj.cleanup()
                logger.info(f"Cleaned up temporary directory: {self.output_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory: {e}")
            finally:
                self._temp_dir_obj = None

    def __del__(self):
        # destructor
        if hasattr(self, '_temp_dir_obj'):
            self.cleanup()