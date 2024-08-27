import cv2
import os
import numpy as np

# палитра из N цветов, без чёрного, белого, чисто красного, зеленого и синего
PALLETE = [
    [128, 0, 0], [0, 128, 0], [0, 0, 128], 
    [128, 128, 0], [0, 128, 128], [128, 0, 128], 
    [64, 0, 0], [0, 64, 0], [0, 0, 64],
    [64, 64, 0], [0, 64, 64], [64, 0, 64], 
    [128, 64, 0], [64, 128, 0], [0, 64, 128],
    [128, 0, 64], [64, 0, 128], [0, 128, 64]
]

HEIGHT, WIDTH = 720, 1280

class VideoLabeller:
    def __init__(self, video_path:str, event_classes:dict, output_dir:str, frames_skip:int=1):
        """ Initializes a new instance of VideoLabeller with the given parameters.
        
        Args:
            video_path (str): Path to the video file or directory containing video files.
            event_classes (dict): Dictionary representing the event classes.
            output_dir (str): Path to the output directory, where annotations are saved.
                If not provided, annotations are saved in the same directory as the video being annotated.
            frames_skip (int): Number of frames to skip during playback. Defaults to 1.
        """
        self.video_path = video_path
        self.event_classes = event_classes
        self.output_dir = output_dir
        self.annotations = self.read_annotation(video_path, output_dir, event_classes)
        self.current_start_frame = None
        self.current_class_id = None
        self.curret_class_id = None
        self.frame_number = 0
        self.playing = False
        self.cap = None
        self.total_frames = 0
        self.video_name = os.path.splitext(os.path.basename(video_path))[0]
        self.frames_skip = frames_skip
        self.cap = cv2.VideoCapture(self.video_path)
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width > WIDTH or height > HEIGHT:
            self.frame_scale = min(WIDTH / width, HEIGHT / height)
        else:
            self.frame_scale = 1
        self.resized_width = int(width * self.frame_scale)
        self.resized_height = int(height * self.frame_scale)
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_number = 0
        self.playing = False
        

    def run(self):
        """ Runs the video labeller, allowing the user to annotate video frames.
        
        The function continuously displays the video frames, and allows the user to navigate
        through the video using various keys. The user can select an event class and mark the 
        start and end frames of events. The annotations are saved in the specified directory.
        The user can also delete annotations and cancel the annotation process.
        """
        cv2.namedWindow(self.video_name)
        cv2.createTrackbar('Frame', self.video_name, 0, self.total_frames - 1, self.on_trackbar)
        # control position of trackbar on window
        cv2.setWindowProperty(self.video_name, cv2.WND_PROP_TOPMOST, 1)

        while self.cap.isOpened():
            if self.playing:
                self.frame_number += self.frames_skip
                if self.frame_number >= self.total_frames:
                    self.frame_number = self.total_frames - 1
                    self.playing = False

            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # frame = self.resize_frame(frame)
            cv2.imshow(self.video_name, self.draw_frame(frame))

            key = cv2.waitKey(1 if self.playing else 0) & 0xFF
            # print(f"Key {key} pressed")
            
            if key == ord(' '):  # Пробел - запуск/остановка воспроизведения
                self.playing = not self.playing

            elif key == ord('a') or key == 81:  # Левая стрелка - перемещение на кадр назад
                self.change_frame_by_step(-1)

            elif key == ord('d') or key == 83:  # Правая стрелка - перемещение на кадр вперёд
                self.change_frame_by_step(1)

            elif key == ord('w') or key == 82:  # Cтрелка вверх - перемещение на 10 кадров назад
                self.change_frame_by_step(-10)

            elif key == ord('s') or key == 84:  # Стрелка вниз - перемещение на 10 кадр вперёд
                self.change_frame_by_step(10)

            elif key == ord('q'):  # Перемещение на 30 кадров назад
                self.change_frame_by_step(-30)

            elif key == ord('e'):  # Перемещение на 30 кадр вперёд
                self.change_frame_by_step(30)
                
            elif key == ord('\r'):  # Enter - ввод класса события
                # запрос ввода
                if self.current_class_id is None:
                    class_str = ''
                    self.draw_msg(frame, "Enter class id: ")
                    while True:
                        key = cv2.waitKey(0) & 0xFF
                        if key == ord('\r') or key == 13: 
                            self.select_event_class(class_str)
                            break
                        else:    
                            class_str += chr(key) if key != ord(' ') else ''
                        self.draw_msg(frame, f"Enter class id: {class_str}")
                else:
                    self.select_event_class(self.current_class_id)
                    
            elif key in [ord(c) for c in self.event_classes.keys() if len(c) == 1]:  # Выбор класса события кнопкой с клавиатуры
                self.select_event_class(chr(key))

            elif key == ord('\b'):  # Backspace - удаление разметки, внутри которой находится текущий кадр
                for annotation in self.annotations:
                    if annotation['start_frame'] <= self.frame_number <= annotation['end_frame']:
                        self.draw_msg(frame, 
                                      [f"Delete annotation {annotation['class']}?", 
                                       f"From {annotation['start_frame']} to {annotation['end_frame']}",
                                       "'Enter' to confirm"]
                            )
                        while True:
                            if cv2.waitKey(0) & 0xFF == ord('\r'):
                                self.annotations.remove(annotation)
                            break
                        break
            
            elif key == 27:  # Escape - отмена разметки
                if self.current_class_id is not None:
                    self.current_class_id = None
                    self.current_start_frame = None
                else:
                    self.draw_msg(frame, "Cancel annotation without saving?\n'Enter' to confirm")
                    if cv2.waitKey(0) & 0xFF == ord('\r'):
                        break
                    
            elif key == ord('\\'):  # End - завершение разметки 
                self.draw_msg(frame, "Finish annotation?\n'Enter' to confirm") 
                if cv2.waitKey(0) & 0xFF == ord('\r'):
                    self.save_annotations()
                    break

            cv2.setTrackbarPos('Frame', self.video_name, self.frame_number)

        self.cap.release()
        cv2.destroyAllWindows()

    def select_event_class(self, event_class_id):
        """ Selects the event class.

        Args:
            event_class_id (str): The id of the event class to be selected.

        If the selected event class is in the list of event classes, its start frame is marked if 
        none exists, or the event is marked as finished and its start frame is cleared if it exists.
        The event class is added to the annotations list. If the selected event class is not in the list
        of event classes, a message is printed indicating that the class is unknown.
        """
        if event_class_id in self.event_classes.keys():
            self.current_class_id = event_class_id
            if self.current_start_frame is None:
                self.current_start_frame = self.frame_number
                print(f"Start of event '{self.event_classes[self.current_class_id]}' marked at frame {self.current_start_frame}")
            else:
                self.annotations.append({
                    'class': self.event_classes[self.current_class_id],
                    'start_frame': self.current_start_frame,
                    'end_frame': self.frame_number
                })
                print(f"End of event '{self.event_classes[self.current_class_id]}' marked at frame {self.frame_number}")
                self.current_start_frame = None
                self.current_class_id = None
        else:
            print(f"Unknown class {event_class_id}")

    def draw_frame(self, frame):
        """ Draws the frame with event labels and annotations.
        
        Args:
            frame (numpy.ndarray): The frame to be drawn.
            
        Returns:
            numpy.ndarray: The frame with event labels and annotations.
            
        Resizes the frame to specified dimensions. If a class is being labeled, draws a rectangle with
        label. For each annotation, if current frame is within annotation range, draws a rectangle with
        corresponding color. Draws current frame number at bottom of frame. Concatenates progress image
        with frame to display annotation timeline.
        """
        if frame.shape[0] != self.resized_height or frame.shape[1] != self.resized_width:
            frame = cv2.resize(frame, (self.resized_width, self.resized_height))
        
        if self.current_class_id is not None:
            cv2.rectangle(frame, (10, 10), (frame.shape[1] - 10, 60), (128, 128, 128), -1)
            cv2.putText(frame, f'Labelling {self.event_classes[self.current_class_id]}', (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
        for annotation in self.annotations:
            if annotation['start_frame'] <= self.frame_number <= annotation['end_frame']:
                ind = list(self.event_classes.values()).index(annotation['class'])
                cv2.rectangle(frame, (10, 10), (frame.shape[1] - 10, 60), PALLETE[ind], -1)
                cv2.putText(frame, annotation['class'], (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"{self.frame_number}", (10, frame.shape[0] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        progress_img = self.create_progress_image()
        # concatenate vertically
        return np.concatenate((frame, progress_img), axis=0)

    def create_progress_image(self, height=20):
        """Creates a progress image to display the timeline of the annotations.
        
        Args:
            height (int): The height of the progress image. Defaults to 20.
        
        Returns:
            numpy.ndarray: The progress image.
            
        Progress image is created with specified height and same width as resized video frame. 
        Annotation rectangles are drawn with colors from PALLETE, and a red line shows current frame.
        """
        progress_img = np.zeros((height, self.resized_width, 3), dtype=np.uint8)
        for annotation in self.annotations:
            start_pos = int((annotation['start_frame'] / self.total_frames) * progress_img.shape[1])
            end_pos = int((annotation['end_frame'] / self.total_frames) * progress_img.shape[1])
            # get index of class from dict event_classes
            ind = list(self.event_classes.values()).index(annotation['class'])
            cv2.rectangle(progress_img, (start_pos, 0), (end_pos, progress_img.shape[0]), PALLETE[ind], -1)
        cv2.line(progress_img, 
                 (int((self.frame_number / self.total_frames) * progress_img.shape[1]), 0),
                 (int((self.frame_number / self.total_frames) * progress_img.shape[1]), progress_img.shape[0]), (0, 0, 255), 2)
        return progress_img

    def on_trackbar(self, position):
        """ Handles the event when the trackbar value changes.
        
        Args:
            position (int): The new value of the trackbar.
            
        Updates frame number and shows the corresponding frame.
        """
        self.frame_number = position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
        ret, frame = self.cap.read()
        if ret:
            cv2.imshow(self.video_name, self.draw_frame(frame))

    def save_annotations(self):
        """Saves the annotations to a file.
        
        Each line of the file corresponds to an annotation, with the format:
        `<event_class> <start_frame> <end_frame>`.
        If the end frame is before the start frame, they are swapped.
        The file is saved in the specified directory if provided, otherwise it is saved in the 
        same directory as the video file, with the same name as the video file but with the extension .txt.
        The file is overwritten if it already exists.
        """
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, f"{self.video_name}.txt")
        else:
            output_file = os.path.join(os.path.dirname(self.video_path), f"{self.video_name}.txt")
        with open(output_file, 'w') as f:
            for annotation in self.annotations:
                c, s, e = annotation['class'], annotation['start_frame'], annotation['end_frame']
                if e < s:
                    e, s = s, e
                f.write(f"{c} {s} {e}\n")
        print(f"Annotations saved to {output_file}")

    def change_frame_by_step(self, step):
        """ Changes the frame number by a given step value.
        
        Args:
            step (int): The value to change the frame number by.
        """
        if step < 0:
            self.frame_number = max(self.frame_number + step, 0)
            self.playing = False
        elif step > 0:
            self.frame_number = min(self.frame_number + step, self.total_frames - step)
            self.playing = False
            
    def draw_msg(self, frame, msg):
        """ Draws a message on the frame with a black background.
        
        Args:
            frame (numpy.ndarray): The frame to draw the message on.
            msg (str or list): The message to draw. If a string, it is split into lines.
        """
        if type(msg) == str:
            msg = msg.split('\n')
        cv2.rectangle(frame, (10, 70), (frame.shape[1] - 10, 80+len(msg)*30), (0, 0, 0), -1)
        for i, m in enumerate(msg):
            cv2.putText(frame, m, (10, 100+i*30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow(self.video_name, self.draw_frame(frame))

    def read_annotation(self, video_path, output_dir, event_classes):
        """ Reads annotations from a file and checks if they correspond to the current video event classes.
        
        Args:
            video_path (str): Path to the video file.
            output_dir (str): Path to the directory where the annotations are saved.
            event_classes (dict): Dictionary representing the event classes.
            
        Returns:
            list or None: A list of annotations if they correspond to the current video event classes, 
            None otherwise.
        """
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        if output_dir:
            old_annotation_path = os.path.join(output_dir, f"{video_name}.txt")
        else:
            old_annotation_path = os.path.join(os.path.dirname(video_path), f"{video_name}.txt")

        if os.path.isfile(old_annotation_path):
            print(f'Annotation for {video_name} exists!')
            
            with open(old_annotation_path, 'r') as old_f:
                lines = old_f.readlines()
            
            annotations = []
            unique_labels = []
            for line in lines:
                annotation = [x.strip() for x in line.split(' ')]
                annotations.append({
                    'class': annotation[0],
                    'start_frame': int(annotation[1]),
                    'end_frame': int(annotation[2])
                })

                unique_labels.append(annotation[0])
            
            event_classes = list(event_classes.values())
            
            if not list(set(unique_labels).difference(event_classes)):
                return annotations           
            else:
                print('Annotations in config doesn\'t correspond to previously annotated file')
                return []
        else:
            return []

def is_video_file(path):
    return path.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm'))


def main(video_path, event_classes, output_dir, frames_skip=1):
    if is_video_file(video_path):
        print(f"Processing {video_path}...")
        labeller = VideoLabeller(video_path, event_classes, output_dir, frames_skip)
        labeller.run()
    else:
        video_files = [f for f in os.listdir(video_path) if is_video_file(f)]
        for video_file in video_files:
            video_file_path = os.path.join(video_path, video_file)
            print(f"Processing {video_file}...")
            labeller = VideoLabeller(video_file_path, event_classes, 
                                     output_dir, frames_skip)
            labeller.run()


if __name__ == "__main__":
    import yaml
    import argparse

    parser = argparse.ArgumentParser(description="Video Event Labelling Tool")
    parser.add_argument("--video_path", "-v", help="Path to the specific video or the directory containing video files")
    parser.add_argument("--class_cfg", "-c", help="Path to the YAML config file with class definitions")
    parser.add_argument("--output_dir", "-o", help="Path to the output directory", default="")
    parser.add_argument("--frames_skip", "-s", help="Number of frames to skip during playback", default=1, type=int)
    args = parser.parse_args()

    with open(args.class_cfg) as f:
        event_classes = yaml.safe_load(f)

    main(args.video_path, event_classes, args.output_dir, args.frames_skip)
