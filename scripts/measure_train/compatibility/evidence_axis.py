from enum import Enum
class Outcome(str, Enum):
    PASS="PASS"; FAIL="FAIL"; PENDING="PENDING"; UNKNOWN="UNKNOWN"; UNSUPPORTED="UNSUPPORTED"
class Axis(str, Enum):
    FOCUSED="focused"; REPOSITORY="repository"; RUNTIME="runtime"; ARTIFACT="artifact"; DEPENDENCY="dependency"; RECEIPT="receipt"
