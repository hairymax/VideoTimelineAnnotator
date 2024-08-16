# VideoTimelineAnnotator

A tool for video timeline segmentation and annotation.

### Script Parameters Description

* `-v` or `--video_path`: path to the video file or directory containing video files, *required argument*.
* `-c` or `--class_cfg`: path to the YAML file with event classes, *required argument*.
* `-o` or `--output_dir`: path to the directory for saving annotations; if not provided, annotations are saved in the same directory as the video being annotated.
* `-s` or `--frames_skip`: number of frames to skip during playback; if not provided, the default value of 1 is used.

### Example Usage

```bash
python labeller.py -v data -c classes.yml
```
In this example, the script will process all video files in the `data` directory, use event classes from `classes.yml`, and save annotations in the same directory as the source videos, skipping 10 frames during playback.

```bash
python labeller.py -v video.mp4 -c configs/classes.yml -o annotations -s 10
```

In this example, the script will run with the `video.mp4` file, use event classes from `configs/classes.yml`, and save annotations in the `annotations` directory, skipping 10 frames during playback.

**Usage Instructions**

1. Run the `labeller.py` script with the required parameters.
2. A video window with a timeline will appear. The script can be run on a single video or a directory of videos. In the latter case, the script will process each video sequentially.
3. Use the following keys to navigate the video:
   * `Space`: start/stop playback
   * `a` or `←` Left Arrow: move one frame backward
   * `d` or `→` Right Arrow: move one frame forward
   * `w` or `↑` Up Arrow: move 10 frames backward
   * `s` or `↓` Down Arrow: move 10 frames forward
4. Marking the start and end frames can be done in any order (e.g., [start, end] or [end, start]). Events can be annotated in two ways:
    * Using text input for event id:
        1. Pause the video at the start/end frame of the event.
        2. Press `Enter`.
        3. Enter the event id.
        4. Confirm by pressing `Enter` again.
        5. Pause the video at the end/start frame of the event (the second marker).
        6. Press `Enter` again.
    * Using keyboard input for event class id (works with single-character ids):
        1. Pause the video at the start/end frame of the event.
        2. Press the key corresponding to the event id.
        3. Pause the video at the end/start frame of the event (the second marker).
        4. Press `Enter`.
5. To finish annotation and save the annotations, press the `\` key. Annotations will be saved in the file within the directory specified by the `-o` parameter.
6. To cancel the video annotation, press `Esc`.

**System Requirements**

- Python version 3.8 or higher
- Libraries *opencv* and *yaml* for Python

You can install the required libraries using:
```bash
pip install opencv-python pyyaml
```