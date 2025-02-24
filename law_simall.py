import subprocess
from pathlib import Path

import law
import luigi


class SimulateEvents(law.Task):
    version_name = luigi.Parameter()
    detector_model = luigi.Parameter(default='ILD_l5_v02')
    scenario = luigi.Parameter(default='ILC250')
    bunch_crossing_end = luigi.IntParameter(default=2)
    n_events = luigi.IntParameter(default= 10)
    guinea_pig_part_per_e = luigi.IntParameter(default=-1)
    submit_jobs = luigi.BoolParameter(default=False)

    def output(self):
        out_dir = (
            Path.home()
            / "promotion"
            / "data"
            / "SIM_DATA_SUBDIR_NAME"
            / self.version_name
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        return law.LocalFileTarget(
            str(
                out_dir
                / f"{self.detector_model}-{self.scenario}-bX_{self.bunch_crossing_end:04d}-nEvts_{self.n_events}.edm4hep.root"
            )
        )

    def run(self):
        executable = "ddsim"
        arguments = [
            "--steeringFile",
            "beamStrahlung/ddsim_keep_microcurlers_10MeV.py",
            "--compactFile",
            f"k4geo/{self.detector_model}.xml",
            "--inputFile",
            f"beamstrahlung/{self.scenario}-BX_{self.bunch_crossing_end}.dat",
            "--outputFile",
            self.output().path,
            "--numberOfEvents",
            str(self.n_events),
        ]
        if self.submit_jobs:
            subprocess.run([executable] + arguments, check=True)
        else:
            print("Would run:", executable, " ".join(arguments))


if __name__ == "__main__":
    law.run()
