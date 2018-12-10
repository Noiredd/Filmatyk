from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import statistics
import tkinter as tk

class StatView(object):
  STRINGS = {
    'Movie': {
      'summary': 'Wyświetlono {} z {} filmów.',
      'average': 'Średnia ocena wyświetlonych: {:.2f}',
      'missing': 'Wygląda na to, że nic tu nie ma.\nMożliwe, że nie masz ocenionych żadnych filmów?'
    }
  }

  def __init__(self, root, itemtype:str):
    self.main = tk.Frame(root)
    self.total_length = 0
    self.summary = tk.Label(self.main, text='')
    self.summary.grid(row=0, column=0, sticky=tk.NW)
    self.average = tk.Label(self.main, text='')
    self.average.grid(row=1, column=0, sticky=tk.NW)
    self.plot = tk.Label(self.main, text='', anchor=tk.CENTER)
    self.plot.grid(row=2, column=0, sticky=tk.N)
    self.figure = None
    self.image = None
    self.strings = self.STRINGS[itemtype]
  def update(self, items:list):
    item_count = len(items)
    if not item_count:
      self.noItemsNotify()
      return
    # calculate statistics
    if item_count > self.total_length:
      self.total_length = item_count # effectively: set total DB size *once*
    item_histo = [0 for i in range(11)]
    for item in items:
      rating = item.getRawProperty('rating')
      item_histo[rating] += 1
    # update summaries and graphics
    self.summary['text'] = self.strings['summary'].format(item_count, self.total_length)
    self.printMeanRating(items)
    self.drawHistogram(item_histo)
  def printMeanRating(self, items:list):
    ratings = [item.getRawProperty('rating') for item in items]
    ratings = [r for r in ratings if r > 0]
    fmt_str = self.strings['average']
    if len(ratings) == 0:
      mean = 0.0
    else:
      mean = statistics.mean(ratings)
    self.average['text'] = fmt_str.format(mean)
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
  def noItemsNotify(self):
    self.plot['text'] = self.strings['missing']

  # TK interface
  def grid(self, **grid_args):
    self.main.grid(**grid_args)
