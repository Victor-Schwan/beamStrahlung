import subprocess
from os import fspath
from pathlib import Path

import law
import luigi

from det_mod_configs import get_paths_and_detector_configs
from framework import AnalysisTask, HTCondorWorkflow
from platform_paths import (
    code_dir,
    construct_beamstrahlung_paths,
    desy_dust_home_path,
    get_path_for_current_machine,
)
from shell_task import ShellTask
from simall import replace_BX_number_in_string

bs_data_paths = construct_beamstrahlung_paths(desy_dust_home_path, True)


class SimulateEvents(AnalysisTask, ShellTask, HTCondorWorkflow, law.LocalWorkflow):
    bunch_crossing_end = luigi.IntParameter(default=2)
    n_events = luigi.IntParameter(default=10)
    guinea_pig_part_per_e = luigi.IntParameter(default=-1)
    submit_jobs = luigi.BoolParameter(default=False)

    bunchcrossing = 1
    bs_dir = code_dir / "beamStrahlung"

    def create_branch_map(self):
        return {
            i: combi
            for i, combi in enumerate(
                self.get_combinations(self.detector_models, self.scenario)
            )
        }

    def output(self):
        det_mod = self.branch_data[0]
        scenario = self.branch_data[1]
        return self.local_target(f"sim_data_{det_mod}_{scenario}.edm4hep.root")

    def build_command(self, fallback_level):
        det_mod = self.branch_data[0]
        scenario = self.branch_data[1]

        executable = "ddsim"
        det_mod_config = get_paths_and_detector_configs()[det_mod]
        raw_arguments = [
            "--steeringFile",
            self.bs_dir / "ddsim_keep_microcurlers_10MeV.py",
            "--compactFile",
            code_dir / f"k4geo/{det_mod_config.get_compact_file_path()}",
            "--inputFile",
            replace_BX_number_in_string(scenario, self.bunchcrossing),
            "--outputFile",
            self.output().path,
            "--numberOfEvents",
            str(self.n_events),
            "--crossingAngleBoost",
            str(det_mod_config.get_crossing_angle()),
        ]
        arguments = [fspath(i) if isinstance(i, Path) else i for i in raw_arguments]

        return " ".join([executable, " ".join(arguments)])


if __name__ == "__main__":
    law.run()
