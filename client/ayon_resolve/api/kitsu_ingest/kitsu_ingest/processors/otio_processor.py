import logging
from typing import List, Dict, Optional
import opentimelineio as otio
from ..models.models import Sequence, Shot
from .base import BaseProcessor 

class OtioProcessor(BaseProcessor):
    def __init__(self, edl_path: str, fps: float, output_dir: str = None):
        super().__init__(input_path=edl_path, fps=fps, output_dir=output_dir)

    def process(self) -> List[Sequence]:
        try:
            timeline = otio.adapters.read_from_file(self.input_path)
            
            main_video_track = self._find_main_video_track(timeline)
            if not main_video_track:
                raise ValueError("No main video track found in OTIO file")
            
            shots = self._extract_shots_from_track(main_video_track)
            if not shots:
                raise ValueError("No valid shots found in main video track")
            
            sequences = self._group_shots_by_sequence(shots)
            
            logging.info(f"Extracted {len(shots)} shots across {len(sequences)} sequences from OTIO file")
            return sequences
        
        except Exception as e:
            logging.error(f"Failed to process OTIO file: {e}")
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

    def _extract_shots_from_track(self, track: otio.schema.Track) -> List[Shot]:
        shots = []
        timeline_position = 0
        
        for item in track:
            try:
                extracted_shots = self._process_timeline_item(item, timeline_position)
                shots.extend(extracted_shots)
                
                # Update timeline position
                if hasattr(item, 'duration') and item.duration():
                    timeline_position += item.duration().value
                    
            except Exception as e:
                logging.error(f"Failed to process timeline item '{getattr(item, 'name', 'unnamed')}': {e}")
                continue
        
        return shots

    def _process_timeline_item(self, item, timeline_position: int) -> List[Shot]:
        shots = []
        
        if isinstance(item, otio.schema.Stack):
            raise NotImplementedError("Processing stacks is not yet implemented")
            # shots.extend(self._process_stack(item, timeline_position))
            
        elif isinstance(item, otio.schema.Clip):
            shot = self._process_clip(item, timeline_position)
            if shot:
                shots.append(shot)
                
        elif isinstance(item, otio.schema.Gap):
            logging.debug(f"Skipping gap at timeline position {timeline_position}")
            
        else:
            logging.warning(f"Unknown timeline item type: {type(item).__name__} - '{getattr(item, 'name', 'unnamed')}'")
        
        return shots

    # def _process_stack(self, stack: otio.schema.Stack, timeline_position: int) -> List[Shot]:
    #     # Process a Stack (compound clip) -> extract shots from its video tracks
    #     shots = []
        
    #     video_tracks = [track for track in stack if hasattr(track, 'kind') and track.kind == otio.schema.TrackKind.Video]
        
    #     if not video_tracks:
    #         logging.warning(f"No video tracks found in stack '{stack.name}'")
    #         return shots
        
    #     main_track = video_tracks[0]
        
    #     for clip in main_track:
    #         if isinstance(clip, otio.schema.Clip):
    #             shot = self._create_shot_from_clip(
    #                 clip, 
    #                 timeline_position, 
    #                 stack_name=stack.name,
    #                 stack_source_range=stack.source_range
    #             )
    #             if shot:
    #                 shots.append(shot)
        
    #     return shots

    def _process_clip(self, clip: otio.schema.Clip, timeline_position: int) -> Optional[Shot]:
        return self._create_shot_from_clip(clip, timeline_position)

    def _create_shot_from_clip(self, clip: otio.schema.Clip, timeline_position: int, 
                              stack_name: str = None, stack_source_range = None) -> Optional[Shot]:
        # Create a Shot object from a clip with comprehensive error handling
        try:
            # Use stack name if available, otherwise use clip name
            shot_name = stack_name or clip.name
            
            if not shot_name:
                logging.warning(f"Clip at timeline position {timeline_position} has no name, skipping")
                return None
            
            common_extensions = ['.mp4', '.mov', '.mxf', '.avi', '.wmv', '.mkv', '.m4v']
            for ext in common_extensions:
                if shot_name.lower().endswith(ext):
                    shot_name = shot_name[:-len(ext)]
                    break
            
            source_range = stack_source_range or clip.source_range
            
            if not source_range:
                logging.warning(f"Clip '{shot_name}' has no source range, skipping")
                return None
            
            duration_frames = int(source_range.duration.value)
            
            frame_in = timeline_position
            frame_out = timeline_position + duration_frames - 1
            
            if duration_frames <= 0:
                logging.warning(f"Invalid duration for shot '{shot_name}': {duration_frames}")
                return None
            
            shot = Shot(
                name=shot_name,
                frame_in=frame_in,
                frame_out=frame_out,
                description=shot_name
            )
            
            logging.debug(f"Created shot: {shot_name} [frame_in={frame_in}, frame_out={frame_out}, duration={duration_frames}]")
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


