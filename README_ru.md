# VideoTimelineAnnotator

Разметчик для задачи сегментации видео временной шкалы.

### Описание параметров скрипта

* `-v` или `--video_path`: путь к видеофайлу или директории с видеофайлами, *обязательный аргумент*.
* `-c` или `--class_cfg`: путь к YAML-файлу с классами событий, *обязательный аргумент*.
* `-o` или `--output_dir`: путь к директории для вывода аннотаций, если не передан, то сохраняются в той же директории, в которой находится размечаемое видео
* `-s` или `--frames_skip`: количество кадров для пропуска во время воспроизведения, если не передан, используется значение по умолчанию: 1

### Примеры запуска

```bash
python labeller.py -v data -c classes.yml
```
В этом примере скрипт будет запущен со всеми видеофайлами в директори `data`, классами событий из файла `classes.yml`, аннотации будут сохранены в директории исходными видео, пропуском 10 кадров во время воспроизведения.

```bash
python labeller.py -v video.mp4 -c configs/classes.yml -o annotations -s 10
```

В этом примере скрипт будет запущен с видеофайлом `video.mp4`, классами событий из файла `configs/classes.yml`, и аннотации будут сохранены в директории `annotations` с пропуском 10 кадров во время воспроизведения.

**Инструкция по использованию**

1. Запустите скрипт `labeller.py` с необходимыми параметрами.
2. Появится окно видео с временной шкалой. Возможен запуск на отдельном видео или папке с видео. Во втором случае скрипт обработает кажое видео последовательно
3. Для навигации по видео используются клавиши:
	* `Space` (Пробел): запуск/остановка воспроизведения
	* `a` или `←` Левая стрелка: перемещение на кадр назад
	* `d` или `→` Правая стрелка: перемещение на кадр вперёд
	* `w` или `↑` Стрелка вверх: перемещение на 10 кадров назад
	* `s` или `↓` Стрелка вниз: перемещение на 10 кадров вперёд
4. Разметка кадров начала и окончания возможна в любом порядке (допустима как последовательность [начало, конец], так и [конец, начало]). Аннотация события возможна двумя способами:
    * С использованием текстового ввода id события
        1. Зафиксировать видео на кадре с началом/окончанием события
        2. Нажать `Enter`
        3. Ввести id события
        4. Подтвердить ввод повторным нажатием `Enter`
        5. Зафиксировать видео на кадре с окончанием/началом события (вторая метка)
        6. Снова нажать `Enter`
    * С использованием ввода id класса нажатием клавиши клавиатуры, соответсвующей этому id (работает с односимвольными id)
        1. Остановить видео на кадре с началом/окончанием события
        2. Нажать клавишу, соответствующую id события
        3. Зафиксировать видео на кадре с окончанием/началом события (вторая метка)
        4. Нажать `Enter`
5. Для завершения разметки и сохранения аннотаций необходимо нажать клавишу `\`. Аннотации будут сохранены в файле в директории, указанной в параметре `-o`.
6. Для отмены разметки видео нажать `Esc`

**Системные требования**

- python версии не ниже 3.8
- библиотеки *opencv* и *yaml* для него

Библиотеки можно установить командой
```bash 
pip install opencv-python pyyaml
``` 
