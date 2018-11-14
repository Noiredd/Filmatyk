from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import tkinter as tk

class StatView(object):
  STRINGS = {
    'Movie': {
      'summary': 'Wyświetlono {} z {} filmów.'
    }
  }

  def __init__(self, root, itemtype:str):
    self.main = tk.Frame(root)
    self.total_length = 0
    self.summary = tk.Label(self.main, text='')
    self.summary.grid(row=0, column=0, sticky=tk.NW)
    self.plot = tk.Label(self.main, text='')
    self.plot.grid(row=1, column=0, sticky=tk.N)
    self.figure = None
    self.image = None
    self.strings = self.STRINGS[itemtype]
  def update(self, items:list):
    # calculate statistics
    item_count = len(items)
    if item_count > self.total_length:
      self.total_length = item_count # effectively: set total DB size *once*
    item_histo = [0 for i in range(11)]
    for item in items:
      rating = item.getRawProperty('rating')
      item_histo[rating] += 1
    # update summary string and graphics
    self.summary['text'] = self.strings['summary'].format(item_count, self.total_length)
    self.drawHistogram(item_histo)
  def drawHistogram(self, values):
    # draw
    if self.figure is None:
      self.figure = plt.figure(figsize=(6,3))
    plt.clf()
    plt.bar(range(11), values, width=0.5, zorder=1.0)
    plt.grid(True, which='major', axis='y')
    self.figure.axes[0].set_xticks(range(11))
    self.figure.axes[0].set_xticklabels(['brak'] + [str(i) for i in range(1,11,1)])
    # prepare for display
    self.figure.canvas.draw()
    w,h = self.figure.canvas.get_width_height()
    idata = Image.frombytes('RGB', (w,h), self.figure.canvas.tostring_rgb())
    self.image = ImageTk.PhotoImage('RGB', idata.size)
    self.image.paste(idata)
    # assign to label
    self.plot.configure(image=self.image)

  # TK interface
  def grid(self, **grid_args):
    self.main.grid(**grid_args)
