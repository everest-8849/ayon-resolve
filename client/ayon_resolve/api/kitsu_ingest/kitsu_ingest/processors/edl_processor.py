import logging
from typing import List, Dict, Optional
import opentimelineio as otio
from ..models.models import Sequence, Shot
from .base import BaseProcessor 

class EdlProcessor(BaseProcessor):
    def __init__(self, edl_path: str, fps: float, output_dir: str = None):
        super().__init__(input_path=edl_path, fps=fps, output_dir=output_dir)

    def process(self) -> List[Sequence]:
        try:
            timeline = otio.adapters.read_from_file(self.input_path, rate=self.fps)
            
            main_video_track = self._find_main_video_track(timeline)
            if not main_video_track:
                raise ValueError("No main video track found in EDL file")
            
            shots = self._extract_shots_from_track(main_video_track, timeline)
            if not shots:
                raise ValueError("No valid shots found in main video track")
            
            sequences = self._group_shots_by_sequence(shots)
            
            logging.info(f"Extracted {len(shots)} shots across {len(sequences)} sequences from EDL file")
            return sequences
        
        except Exception as e:
            logging.error(f"Failed to process EDL file: {e}")
            raise

    def _find_main_video_track(self, timeline) -> Optional[otio.schema.Track]:
        main_track_names = ['main', 'Main', 'MAIN', 'V1', 'v1', 'Video 1', 'video1']
        
        video_tracks = [track for track in timeline.tracks if track.kind == otio.schema.TrackKind.Video]
        
        if not video_tracks:
            logging.error("No video tracks found in timeline")
            return None
        
        for track in video_tracks:
            if track.name in main_track_names:
                logging.info(f"Found main video track: '{track.name}'")
                return track
        
        main_track = video_tracks[0]
        logging.warning(f"No track named 'main' found, using first video track: '{main_track.name}'")
        return main_track

    def _extract_shots_from_track(self, track: otio.schema.Track, timeline) -> List[Shot]:
        shots = []
        
        for item in track:
            try:
                extracted_shots = self._process_timeline_item(item, timeline)
                shots.extend(extracted_shots)
                    
            except Exception as e:
                logging.error(f"Failed to process timeline item '{getattr(item, 'name', 'unnamed')}': {e}")
                continue
        
        return shots

    def _process_timeline_item(self, item, timeline) -> List[Shot]:
        shots = []
        
        if isinstance(item, otio.schema.Stack):
            logging.warning(f"Processing stacks is not yet implemented for item '{getattr(item, 'name', 'unnamed')}'")
            
        elif isinstance(item, otio.schema.Clip):
            shot = self._process_clip(item, timeline)
            if shot:
                shots.append(shot)
                
        elif isinstance(item, otio.schema.Gap):
            logging.debug(f"Skipping gap item")
            
        else:
            logging.warning(f"Unknown timeline item type: {type(item).__name__} - '{getattr(item, 'name', 'unnamed')}'")
        
        return shots

    def _process_clip(self, clip: otio.schema.Clip, timeline) -> Optional[Shot]:
        return self._create_shot_from_clip(clip, timeline)

    def _create_shot_from_clip(self, clip: otio.schema.Clip, timeline) -> Optional[Shot]:
        try:
            range_in_timeline = timeline.range_of_child(clip)
            
            timeline_rate = timeline.duration().rate
            
            record_in_frames = int(range_in_timeline.start_time.to_frames(timeline_rate))
            record_out_frames = int(range_in_timeline.end_time_exclusive().to_frames(timeline_rate))
            
            shot_name = clip.name or "Unnamed Clip"
            if '.' in shot_name and not shot_name.endswith('.'):
                shot_name = shot_name.rsplit('.', 1)[0]
            
            shot = Shot(
                name=shot_name,
                frame_in=record_in_frames,
                frame_out=record_out_frames - 1,  # Subtract 1 for inclusive out frame
                description=shot_name
            )
            
            logging.debug(f"Created shot: {shot_name} [frame_in={record_in_frames}, frame_out={record_out_frames - 1}]")
            return shot
                                    
        except Exception as e:
            logging.error(f"Failed to create shot from clip '{getattr(clip, 'name', 'unnamed')}': {e}")
            return None

    def _group_shots_by_sequence(self, shots: List[Shot]) -> List[Sequence]:
        sequences = {}
        
        for shot in shots:
            sequence_name = self._extract_sequence_name(shot.name)
            
            if sequence_name not in sequences:
                sequences[sequence_name] = Sequence(name=sequence_name, fps=self.fps, shots=[])
            
            sequences[sequence_name].shots.append(shot)
        
        sorted_sequences = []
        for seq_name in sorted(sequences.keys()):
            sequence = sequences[seq_name]
            sequence.shots.sort(key=lambda s: s.frame_in)
            sorted_sequences.append(sequence)
        
        return sorted_sequences

    def _extract_sequence_name(self, shot_name: str) -> str:
        if '-' in shot_name:
            return shot_name.split('-')[0]
        elif '_' in shot_name:
            return shot_name.split('_')[0]
        else:
            return "DEFAULT_SEQUENCE"


