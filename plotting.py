from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

from det_mod_configs import detector_model_configurations
from utils import add_spherical_coordinates_in_place
from vicbib import BasePlotter
from scale_hit_rate import scale_sr_hits

def plotting(
    pos_dict: Dict[str, Dict[str, np.ndarray]],
    time_dict: Dict[str, np.ndarray],
    num_bunch_crossings: int = 1,
    show_plots: bool = False,
    save_plots: bool = False,
    save_dir: Path | str = None,
    make_theta_hist: bool = False,
    det_mod: str = "",
    scenario: str = "",
    background: str = "",
) -> None:
    """
    Generate and display plots of position and timing data for various detectors.

    Parameters:
        pos_dict (Dict[str, Dict[str, np.ndarray]]): Dictionary with detector
            keys mapping to sub-dictionaries containing position arrays ('x', 'y', 'z').
        time_dict (Dict[str, np.ndarray]): Dictionary with detector keys mapping to time arrays.
        num_bunch_crossings (int, optional): Number of bunch crossings considered. Default is 1.
        show_plots (bool, optional): Whether to display plots. Default is True.
        save_plots (bool, optional): Whether to save plots. Default is False.
        det_mod (str, optional): Detector module string for naming conventions in plots.
        scenario (str, optional): Scenario string for naming conventions in plots.
    """

    # Define the limits in millimeters for specific sub-detector keys
    limits = {"vb": 60, "ve": 105}  # Limit in mm for 'vb'  # Limit in mm for 've'

    scale_factor = scale_sr_hits(1, scenario, background)

    det = detector_model_configurations[det_mod]
    if det.is_accelerator_fccee():
        sub_det_cols = det.get_sub_detector_collection_info()
        for sub_det_key, sub_det_name in sub_det_cols.items():
            plt.close("all")
            if det_mod and scenario:
                common_save_path = save_dir / (f"{sub_det_name.plot_collection_prefix.replace(' ', '_')}_{det_mod}_{scenario}")
                common_title = (f"{sub_det_name.plot_collection_prefix}  {det_mod}@{scenario}")
            else:
                common_title = sub_det_name.plot_collection_prefix
                common_save_path = save_dir / common_title

            save_dir.mkdir(exist_ok=True)

            # Plot histogram of the z positions
            bp = BasePlotter(
                save_plots,
                common_save_path.with_stem(common_save_path.stem + "_z_positions"),
            )

            _, ax = bp.plot()
            ax.hist(pos_dict[sub_det_key]["z"], bins=50, weights=np.ones_like(pos_dict[sub_det_key]["z"]) * scale_factor/ num_bunch_crossings)
            ax.set_title(common_title)
            ax.set_xlabel("Z Position in mm")
            ax.set_ylabel("Avg. hits per BX")
            if show_plots:
                plt.show()
            bp.finish()

            # Plot histogram of the theta positions
            if make_theta_hist:
                add_spherical_coordinates_in_place(pos_dict[sub_det_key])

                bp = BasePlotter(
                    save_plots,
                    common_save_path.with_stem(
                        common_save_path.stem + "_theta_positions"
                    ),
                )
                _, ax = bp.plot()
                ax.hist(
                    pos_dict[sub_det_key]["theta"],
                    bins=50,
                    weights=np.ones_like(pos_dict[sub_det_key]["theta"]) * scale_factor
                    / num_bunch_crossings,
                )
                ax.set_title(common_title)
                ax.set_xlabel("Theta in rad")
                ax.set_ylabel("Avg. hits per BX")
                if show_plots:
                    plt.show()
                bp.finish()

            # Plot histogram of the times using BasePlotter
            bp = BasePlotter(
                save_plots,
                common_save_path.with_stem(common_save_path.stem + "_hit_times"),
            )
            _, ax = bp.plot()
            ax.hist(
                time_dict[sub_det_key],
                bins=30,
                weights=np.ones_like(time_dict[sub_det_key]) * scale_factor / num_bunch_crossings,
            )
            ax.set_title(common_title)
            ax.set_xlabel("Time in ns")
            ax.set_ylabel("Avg. hits per BX")
            ax.set_yscale("log")
            if show_plots:
                plt.show()
            bp.finish()

            # Determine the limits for 2D histograms based on sub_det_key
            limit_value = limits.get(sub_det_key, None)

            # Plot 2D histogram of the x and y positions using BasePlotter
            bp = BasePlotter(
                save_plots,
                common_save_path.with_stem(common_save_path.stem + "_xy_hist"),
            )
            fig, ax = bp.plot()

            # Compute bin edges to calculate bin area
            x_bins = np.linspace(-limit_value, limit_value, 51)  # 50 bins means 51 edges
            y_bins = np.linspace(-limit_value, limit_value, 51)

            # Calculate bin widths and heights
            bin_width = np.diff(x_bins)
            bin_height = np.diff(y_bins)

            # Create a 2D histogram and get the value counts
            h, _, _ = np.histogram2d(
                pos_dict[sub_det_key]["x"],
                pos_dict[sub_det_key]["y"],
                bins=[x_bins, y_bins],
                weights=np.ones_like(pos_dict[sub_det_key]["x"]) * scale_factor / num_bunch_crossings,
            )

            # Calculate bin area for normalization (area = width * height)
            bin_area = np.outer(bin_height, bin_width)

            # Normalize the histogram to count per square millimeter
            h_normalized = h / bin_area

            # Plotting the 2D histogram
            h_image = ax.imshow(
                h_normalized.T,
                origin="lower",
                extent=[-limit_value, limit_value, -limit_value, limit_value],
                cmap="viridis",
                aspect="auto",
            )

            ax.set_title(common_title)
            ax.set_xlabel("X Position in mm")
            ax.set_ylabel("Y Position in mm")
            fig.colorbar(h_image, ax=ax, label=r"Avg. hits per BX and $\text{mm}^2$")

            if show_plots:
                plt.show()
            bp.finish()
