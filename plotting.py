from PIL import Image, ImageTk
import matplotlib.pyplot as plt

def drawHistogram(histogram):
  fig = plt.figure(figsize=(6,3))
  plt.bar(range(11), histogram, width=.5, zorder=1.0)
  plt.grid(True, which='major', axis='y')
  fig.axes[0].set_xticks(range(11))
  fig.axes[0].set_xticklabels(['brak'] + [str(i) for i in range(1,11,1)])

  fig.canvas.draw()
  w,h = fig.canvas.get_width_height()
  img = Image.frombytes("RGB", (w,h), fig.canvas.tostring_rgb())
  im = ImageTk.PhotoImage('RGB', img.size)
  im.paste(img)

  return im
