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

HEIGHT, WIDTH = 720, 12870

class VideoLabeller:
    def __init__(self, video_path:str, event_classes:dict, output_dir:str, frames_skip:int=1):
        self.video_path = video_path
        self.event_classes = event_classes
        self.output_dir = output_dir
        # self.annotations = []
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

    def run(self):
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_number = 0
        self.playing = False

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
            
            frame = self.resize_frame(frame)
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
        # self.current_class_id = self.event_classes[event_class_id]
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
        progress_img = np.zeros((height, min(WIDTH, int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))), 3), dtype=np.uint8)
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
        self.frame_number = position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
        ret, frame = self.cap.read()
        if ret:
            frame = self.resize_frame(frame)
            cv2.imshow(self.video_name, self.draw_frame(frame))

    def resize_frame(self, frame):
          # limit displayed frame size to 1280x720
        height, width, _ = frame.shape
        if width > WIDTH or height > HEIGHT:
            scale = min(WIDTH / width, HEIGHT / height)
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
            
        return frame
    
    def save_annotations(self):
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
        if step < 0:
            self.frame_number = max(self.frame_number + step, 0)
            self.playing = False
        elif step > 0:
            self.frame_number = min(self.frame_number + step, self.total_frames - step)
            self.playing = False
            
    def draw_msg(self, frame, msg):
        if type(msg) == str:
            msg = msg.split('\n')
        cv2.rectangle(frame, (10, 70), (frame.shape[1] - 10, 80+len(msg)*30), (0, 0, 0), -1)
        for i, m in enumerate(msg):
            cv2.putText(frame, m, (10, 100+i*30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow(self.video_name, self.draw_frame(frame))

    def read_annotation(self, video_path, output_dir, event_classes):
        video_name = os.path.basename(video_path).split(".")[0]

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
