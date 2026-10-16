from enum import Enum

class OrderType(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TaskType(str, Enum):
    PICKING = "PICKING"
    PUTAWAY = "PUTAWAY"
    REPLENISHMENT = "REPLENISHMENT"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"