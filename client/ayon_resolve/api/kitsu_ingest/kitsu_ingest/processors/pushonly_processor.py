import os
import pandas as pd
import logging
from typing import List, Dict, Optional

from .base import BaseProcessor
from ..models.models import Shot, Sequence

logger = logging.getLogger(__name__)

SEQUENCE = "SQ01"

class PushonlyCsvProcessor(BaseProcessor):
    def __init__(self, csv_path: str, fps: float, output_dir: Optional[str] = None):
        super().__init__(input_path=csv_path, fps=fps, output_dir=output_dir)

    def process(self) -> List[Sequence]:
        try:
            logging.info(f"Processing source CSV file: {self.input_path}")
            df = pd.read_csv(self.input_path)

            df.columns = df.columns.str.replace(' ', '_') # allows itertuples to access columns with spaces
            
            required_cols = {'Sequence', 'Name', 'Frame_In', 'Frame_Out', 'Nb_Frames', 'FPS', 'Description'}
            if not required_cols.issubset(df.columns):
                raise ValueError(f"CSV is missing one of the required columns: {required_cols - set(df.columns)}")

            sequences_map: Dict[str, Sequence] = {}
            
            for row in df.itertuples(index=False): # Use itertuples for more efficient iteration
                try:
                    seq_name = getattr(row, 'Sequence', SEQUENCE)
                    shot_name = str(row.Name)

                    shot = Shot(
                        name=shot_name,
                        frame_in=int(getattr(row, 'Frame_In')),
                        frame_out=int(getattr(row, 'Frame_Out')),
                        description=getattr(row, 'Description', shot_name)
                    )

                    if seq_name not in sequences_map:
                        sequences_map[seq_name] = Sequence(
                            name=seq_name,
                            fps=self.fps,
                            shots=[]
                        )
                    
                    sequences_map[seq_name].shots.append(shot)

                except (AttributeError, KeyError, ValueError) as e:
                    raise ValueError(f"Invalid data in row: {row}. Error: {e}")
            
            if not sequences_map:
                raise ValueError("No valid sequences or shots found in the CSV data.")

            for seq_name, sequence in sequences_map.items():
                 logging.info(f"Parsed sequence '{seq_name}' with {len(sequence.shots)} shots.")

            logging.info(f"Successfully parsed {len(sequences_map)} sequence(s) from CSV.")
            return list(sequences_map.values())

        except Exception as e:
            logging.error(f"Error processing CSV file '{self.input_path}': {e}")
            raise