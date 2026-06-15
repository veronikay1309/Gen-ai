import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineMetrics:
    """
    Tracks key performance and quality metrics for a single pipeline run.
    """
    pipeline_name: str
    records_extracted: int = 0
    records_after_transform: int = 0
    records_loaded: int = 0
    records_failed: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    def finish(self):
        """Marks the pipeline run as complete and records the end time."""
        self.end_time = time.time()

    @property
    def duration_seconds(self) -> float:
        end = self.end_time or time.time()
        return round(end - self.start_time, 3)

    @property
    def records_per_second(self) -> float:
        if self.duration_seconds == 0:
            return 0.0
        return round(self.records_loaded / self.duration_seconds, 2)

    @property
    def success_rate(self) -> float:
        total = self.records_extracted
        if total == 0:
            return 0.0
        return round((self.records_loaded / total) * 100, 2)

    def summary(self) -> dict:
        return {
            "pipeline": self.pipeline_name,
            "records_extracted": self.records_extracted,
            "records_after_transform": self.records_after_transform,
            "records_loaded": self.records_loaded,
            "records_failed": self.records_failed,
            "success_rate_pct": self.success_rate,
            "duration_seconds": self.duration_seconds,
            "records_per_second": self.records_per_second,
        }

    def print_summary(self):
        s = self.summary()
        print("\n=================== PIPELINE METRICS ===================")
        print(f"  Pipeline:           {s['pipeline']}")
        print(f"  Records Extracted:  {s['records_extracted']:,}")
        print(f"  After Transform:    {s['records_after_transform']:,}")
        print(f"  Records Loaded:     {s['records_loaded']:,}")
        print(f"  Records Failed:     {s['records_failed']:,}")
        print(f"  Success Rate:       {s['success_rate_pct']}%")
        print(f"  Duration:           {s['duration_seconds']}s")
        print(f"  Throughput:         {s['records_per_second']} records/sec")
        print("=========================================================\n")
