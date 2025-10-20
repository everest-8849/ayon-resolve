from pydantic import BaseModel, Field, validator
from typing import List

class Shot(BaseModel):
    # Represents a single shot within a sequence
    name: str = Field(description="The unique identifier for the shot, 'SH010'")
    frame_in: int = Field(ge=0, description="The starting frame of the shot (inclusive)")
    frame_out: int = Field(ge=0, description="The ending frame of the shot (inclusive)")
    description: str = Field(default="", description="Optional description for the shot")

    @property
    def duration(self) -> int:
        """Calculates the duration of the shot in frames."""
        return self.frame_out - self.frame_in + 1

    @validator('frame_out')
    def check_frame_out_is_after_frame_in(cls, v, values):
        if 'frame_in' in values and v < values['frame_in']:
            raise ValueError('Frame Out cannot be earlier than Frame In')
        return v

class Sequence(BaseModel):
    # Represents a sequence, a collection of shots
    name: str = Field(description="The name of the sequence, e.g., 'SQ01'")
    fps: float = Field(gt=0, description="The frames per second for the sequence")
    shots: List[Shot] = Field(default_factory=list, description="The list of shots in this sequence")

    @property
    def shot_count(self) -> int:
        """Returns the number of shots in the sequence."""
        return len(self.shots)

    @property
    def total_duration(self) -> int:
        """Returns the total duration of all shots in the sequence, in frames."""
        return sum(shot.duration for shot in self.shots)

class Project(BaseModel):
    # Represents the project, containing one or more sequences, primary data object
    name: str
    sequences: List[Sequence] = Field(default_factory=list)

    @property
    def sequence_count(self) -> int:
        return len(self.sequences)

    @property
    def total_shot_count(self) -> int:
        return sum(seq.shot_count for seq in self.sequences)