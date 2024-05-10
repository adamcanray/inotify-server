import pyinotify
import config
import os
import time
import dicom_handler

class EventHandler(pyinotify.ProcessEvent):
  def __init__(self):
    super().__init__()
    self.last_close_write_time = {}

  def process_IN_DELETE(self, event):
    dicom_handler.dicom_deleted(event.pathname)

  def process_IN_CLOSE_WRITE(self, event):
    current_time = time.time()
    file_path = event.pathname

    if file_path in self.last_close_write_time:
      last_time = self.last_close_write_time[file_path]
      if current_time - last_time < 1:
        return

    dicom_handler.dicom_written(event.pathname)
    self.last_close_write_time[file_path] = current_time

def main():
  try:
    wm = pyinotify.WatchManager()
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    path = os.environ.get('shared-directory', '')

    if len(path) == 0:
      raise ValueError("Path not found")

    mask = pyinotify.IN_DELETE | pyinotify.IN_CLOSE_WRITE
    wdd = wm.add_watch(path, mask)

    print("Monitoring directory:", path)

    notifier.loop()
  except ValueError as e:
    print("Error:", e)

if __name__ == "__main__":
    main()