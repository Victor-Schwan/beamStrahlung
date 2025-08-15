import os
import glob
import pyhepmc

def convert_hepevt_to_hepmc(hepevt_path, hepmc_path):
    writer = pyhepmc.WriterAscii(hepmc_path)
    event = pyhepmc.GenEvent()

    with open(hepevt_path) as f:
        lines = f.readlines()

    for line in lines:
        if line.strip() == "":
            continue
        parts = line.strip().split()
        if len(parts) < 10:
            continue

        pid = int(parts[0])
        status = int(parts[1])
        px = float(parts[6])
        py = float(parts[7])
        pz = float(parts[8])
        e = float(parts[9])
        m = float(parts[10]) if len(parts) > 10 else 0.0

        particle = pyhepmc.GenParticle((px, py, pz, e), pid, status)
        event.add_particle(particle)

    writer.write_event(event)
    writer.close()
    print(f"Converted: {hepevt_path} -> {hepmc_path}")

def convert_all_in_directory(top_level_dir):
    # Loop over each folder inside the top-level directory
    for folder_name in os.listdir(top_level_dir):
        folder_path = os.path.join(top_level_dir, folder_name)
        if os.path.isdir(folder_path):
            hepevt_files = glob.glob(os.path.join(folder_path, "*.hepevt"))
            if not hepevt_files:
                continue  # Skip if no .hepevt files

            for hepevt_file in hepevt_files:
                base = os.path.basename(hepevt_file)
                filename_wo_ext = os.path.splitext(base)[0]
                hepmc_path = os.path.join(folder_path, filename_wo_ext + ".hepmc")
                convert_hepevt_to_hepmc(hepevt_file, hepmc_path)

convert_all_in_directory('/data/dust/user/keyworth/promotion/data/split_up_SR_files')