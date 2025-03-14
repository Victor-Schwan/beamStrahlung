# coding: utf-8

"""
Law example tasks to demonstrate HTCondor workflows at NAF.

In this file, some really basic tasks are defined that can be inherited by
other tasks to receive the same features. This is usually called "framework"
and only needs to be defined once per user / group / etc.
"""

import os
from itertools import product
from typing import Iterable, List, Tuple, Union

import law
import luigi

from det_mod_configs import (
    CHOICES_DETECTOR_MODELS,
    DEFAULT_DETECTOR_MODELS,
)
from platform_paths import construct_beamstrahlung_paths, desy_dust_home_path

# the htcondor workflow implementation is part of a law contrib package
# so we need to explicitly load it
law.contrib.load("htcondor")

data_dir_path_env_var = "dtDir"


class BaseTask(law.Task):
    """
    Base task that we use to force a version parameter on all inheriting tasks, and that provides
    some convenience methods to create local file and directory targets at the default data path.
    """

    version = luigi.Parameter()

    def store_parts(self):
        parts = (self.__class__.__name__,)
        if self.version is not None:
            parts += (self.version,)
        return parts

    def local_path(self, *path):
        # DATA_PATH is defined in setup.sh
        parts = [str(p) for p in self.store_parts() + path]
        return os.path.join(os.environ[data_dir_path_env_var], *parts)

    def local_target(self, *args):
        cls = law.LocalFileTarget if args else law.LocalDirectoryTarget
        return cls(self.local_path(*args))

    def list2str(self, list_name):
        return "".join([f"_{ele}" for ele in getattr(self, list_name)])


class HTCondorWorkflow(law.htcondor.HTCondorWorkflow):
    """
    Batch systems are typically very heterogeneous by design, and so is HTCondor. Law does not aim
    to "magically" adapt to all possible HTCondor setups which would certainly end in a mess.
    Therefore we have to configure the base HTCondor workflow in law.contrib.htcondor to work with
    the NAF environment. In most cases, like in this example, only a minimal amount of
    configuration is required.
    """

    max_runtime = law.DurationParameter(
        default=1.0,
        unit="h",
        significant=False,
        description="maximum runtime; default unit is hours; default: 1",
    )

    def htcondor_output_directory(self):
        # the directory where submission meta data should be stored
        return law.LocalDirectoryTarget(self.local_path())

    def htcondor_bootstrap_file(self):
        # each job can define a bootstrap file that is executed prior to the actual job
        # configure it to be shared across jobs and rendered as part of the job itself
        bootstrap_file = law.util.rel_path(__file__, "law_bootstrap.sh")
        return law.JobInputFile(bootstrap_file, share=True, render_job=True)

    def htcondor_job_config(self, config, job_num, branches):
        # render_variables are rendered into all files sent with a job
        config.render_variables["analysis_path"] = os.getenv("ANALYSIS_PATH")

        # copy the entire environment
        config.custom_content.append(("getenv", "true"))

        return config


bs_data_paths = construct_beamstrahlung_paths(desy_dust_home_path, True)

# single source of truth, keys of bs_data_paths become values of tuple
CHOICES_SCENARIOS = tuple(bs_data_paths)
DEFAULT_SCENARIOS = ["FCC091", "FCC240"]


class AnalysisTask(BaseTask):
    detector_models = luigi.ChoiceListParameter(
        default=["ILD_FCCee_v02", "ILD_FCCee_v01"], choices=CHOICES_DETECTOR_MODELS
    )
    scenario = luigi.ChoiceListParameter(
        choices=CHOICES_SCENARIOS,
        default=DEFAULT_SCENARIOS,
        description="Accelerator configurations to analyze (choose one or more)",
    )

    @staticmethod
    def get_combinations(
        collection_a: Union[str, Iterable[str]], collection_b: Union[str, Iterable[str]]
    ) -> List[Tuple[str, str]]:
        """
        Generate all possible pairwise combinations of elements from two collections.

        Both inputs can be either a string (interpreted as a single-element collection)
        or any iterable of strings (e.g., tuple, list, set, generator).
        The function returns a list of tuples representing the Cartesian product.

        Args:
            collection_a (Union[str, Iterable[str]]): First input, either a string or an iterable of strings.
            collection_b (Union[str, Iterable[str]]): Second input, either a string or an iterable of strings.

        Returns:
            List[Tuple[str, str]]: List of all possible (collection_a, collection_b) pairs.
        """

        collection_a = (
            (collection_a,) if isinstance(collection_a, str) else collection_a
        )
        collection_b = (
            (collection_b,) if isinstance(collection_b, str) else collection_b
        )

        return list(product(collection_a, collection_b))

        def store_parts(self):
            return super().store_parts() + (
                f"det_mod{self.list2str('detector_models')}",
                f"scenario{self.list2str('scenario')}",
            )


class TestAT(BaseTask):
    detector_models = luigi.Parameter(default="ILD_FCCee_v02")
    scenario = luigi.Parameter(default="FCC091")
