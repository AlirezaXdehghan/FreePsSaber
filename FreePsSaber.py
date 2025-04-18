import argparse
import os
import soundfile as sf
import subprocess
import json
import tempfile
import shutil
import gzip

def export_beat_data(ogg_file_path, output_json, bpm):
    try:
        # Read the OGG file
        audio_data, sample_rate = sf.read(ogg_file_path)
        num_samples = len(audio_data)
        
        if sample_rate != 44100:
            print("!!! You're using a song with a sample rate above/below 44100!!!")
        # Calculate duration from samples and sample rate
        duration = num_samples / sample_rate

        # Calculate end beat.
        end_beat = duration * (bpm / 60)

        # Construct the result dictionary
        result = {
            "_version": "2.0.0",
            "_songSampleCount": num_samples,
            "_songFrequency": sample_rate,
            "_regions": [
                {
                    "_startSampleIndex": 0,
                    "_endSampleIndex": num_samples - 1,
                    "_startBeat": 0,
                    "_endBeat": end_beat
                }
            ]
        }
        with open(output_json, "w") as f:
            json.dump(result, f, indent=4)
        print(f"📦 BMPinfo exported to: {output_json}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def get_ogg_duration(ogg_path):
    """Return duration in seconds using ffprobe."""
    # Read the OGG file
    audio_data, sample_rate = sf.read(ogg_path)
    num_samples = len(audio_data)

    # Calculate duration from samples and sample rate
    duration = num_samples / sample_rate
    return duration

def run_fsbank_direct(ogg_path, output_path):
    """Run fsbankcl without fsproj using direct CLI arguments."""
    fsbank_exe = shutil.which("fsbankcl")
    if not fsbank_exe:
        raise FileNotFoundError("❌ fsbankcl.exe not found! Add it to PATH or place it next to this script.")

    result = subprocess.run(
        [
            fsbank_exe,
            "-i", ogg_path,
            "-o", output_path,
            "-f", "ogg",  # OGG Vorbis format
            "-platform", "windows"
        ],
        capture_output=True,
        text=True
    )

    print("=== FSBank STDOUT ===")
    print(result.stdout)
    print("=== FSBank STDERR ===")
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError("❌ fsbankcl failed to create the FSB file. Check the logs above.")
    print(f"🎵 New .resources file created at: {output_path}")

def export_uabea_patch_json(fsb_path, duration, output_json):
    """Output a patch JSON for UABEA to import."""
    size = os.path.getsize(fsb_path)
    metadata_patch = {
        "path": "AudioClip Base",
        "fields": {
            "m_Size": size,
            "m_Length": duration
        }
    }

    with open(output_json, "w") as f:
        json.dump(metadata_patch, f, indent=4)
    print(f"📦 UABEA patch JSON exported to: {output_json}")
    
def gzip_dat_files(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".dat"):
            dat_file_path = os.path.join(folder_path, filename)
            gz_file_path = os.path.join(folder_path, "gz" + filename + ".txt")

            try:
                with open(dat_file_path, 'rb') as dat_file:
                    with gzip.open(gz_file_path, 'wb') as gz_file:
                        dat_content = dat_file.read()
                        gz_file.write(dat_content)
                print(f"Successfully compressed: '{dat_file_path}' to '{gz_file_path}'")
            except Exception as e:
                print(f"Error processing '{dat_file_path}': {e}")

def main():
    parser = argparse.ArgumentParser(description="Rebuild Unity .resources file with new FSB5 audio.")
    parser.add_argument("ogg_file", help="New .ogg audio file path")
    parser.add_argument("bpm", help="bpm of the song")
    parser.add_argument("output_resource", help="New .resources file output path")
    parser.add_argument("output_json", help="UABEA-compatible JSON metadata output")
    parser.add_argument("output_bpm", help="UABEA-compatible JSON BPMInfo output")
    parser.add_argument("beatmap_folder", help="beatmap folder directory with the beatmaps")
    args = parser.parse_args()

    ogg_file = os.path.abspath(args.ogg_file)
    output_resource = os.path.abspath(args.output_resource)
    output_json = os.path.abspath(args.output_json)
    output_bpm = args.output_bpm
    beatmap_folder = os.path.abspath(args.beatmap_folder)

    duration = get_ogg_duration(ogg_file)
    run_fsbank_direct(ogg_file, output_resource)
    export_uabea_patch_json(output_resource, duration, output_json)
    export_beat_data(ogg_file, output_bpm)
    gzip_dat_files(beatmap_folder)
    

    print(f"All files were created successfully!")




if __name__ == "__main__":
    main()
