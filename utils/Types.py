"""Define utils Types to handle Dataset_original"""

from enum import Enum
from typing import Tuple


class Particle:
    def __init__(self, t: int, x: float, y: float, z: float) -> None:
        self.t = t
        self.x = x
        self.y = y
        self.z = z

    def get_coords(self) -> Tuple[int, float, float, float]:
        return self.t, self.x, self.y, self.z


class SNR(Enum):
    TYPE_1 = 'snr_1'
    TYPE_2 = 'snr_2'
    TYPE_4 = 'snr_4'
    TYPE_7 = 'snr_7'


class Density(Enum):
    HIGH = 'density_high'
    MID = 'density_mid'
    LOW = 'density_low'
