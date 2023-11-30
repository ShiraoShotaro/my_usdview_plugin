import os

root = "P:\\output"
for file in os.listdir(root):
    new_file = file.replace("tt_turntable_camera_0", "tt_turntable_camera")
    os.rename(os.path.join(root, file), os.path.join(root, new_file))
