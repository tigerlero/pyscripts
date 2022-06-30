from moviepy.editor import VideoFileClip, ImageClip

clip = VideoFileClip("static/media/videos/Anime 404.mp4").subclip(1,2)
image = clip.save_frame("frame.jpeg")
print(clip)
print(image)