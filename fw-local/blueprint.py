#Formatery do pól ze specjalnymi właściwościami
def __list(x):
  #Formater konwertujący listę do rozdzielanego przecinkami stringa
  return ', '.join(x)
def __duration(x):
  #Formater wypisujący czas trwania w formie (h:m)
  v = int(x)
  h = v // 60
  m = v % 60
  return '{0!s}h {1!s}m'.format(h,m)
def __fwRating(x):
  #Formater zaokrąglający ocenę społeczności
  return str(round(float(x),1))
def __rating(x):
  #Formater dodający wizualne gwiazdki do oceny użytkownika
  v = int(x)
  if v == 0: return '-'
  return x + ' ' + ''.join('★' for i in range(v))
def __fav(x):
  #Formater konwertujący '1' odpowiadające za ulubione w serduszko
  if x=='1': return '♥'
  else: return ''
def __comment(x):
  #Formater usuwający '\"' z komentarzy i zastępujący zwykłym '"'
  return x.replace('\\\"', '"')

#Blueprint przechowuje szczegóły parsowania i prezentacji poszczególnych pól
Blueprint = dict()

Blueprint['title'] = {
  'presentation': {'name':'Tytuł', 'width':200, 'format':None},
  'html_parsing': {'tag':'h3', 'class':'filmPreview__title', 'text':True, 'array':False} }
Blueprint['year'] = {
  'presentation': {'name':'Rok', 'width':35, 'format':None},
  'html_parsing': {'tag':'span', 'class':'filmPreview__year', 'text':True, 'array':False} }
Blueprint['link'] = {
  'presentation': None,
  'html_parsing': {'tag':'a', 'class':'filmPreview__link', 'text':False, 'attr':'href'} }
Blueprint['imglink'] = {
  'presentation': None,
  'html_parsing': {'tag':'img', 'class':'filmPoster__image', 'text':False, 'attr':'data-src'} }
Blueprint['otitle'] = {
  'presentation': {'name':'Tytuł oryginalny', 'width':200, 'format':None},
  'html_parsing': {'tag':'div', 'class':'filmPreview__originalTitle', 'text':True, 'array':False} }
Blueprint['duration'] = {
  'presentation': {'name':'Długość', 'width':50, 'format':__duration},
  'html_parsing': {'tag':'div', 'class':'filmPreview__filmTime', 'text':False, 'attr':'data-duration'} }
Blueprint['fwRating'] = {
  'presentation': {'name':'Ocena FW', 'width': 65, 'format':__fwRating},
  'html_parsing': {'tag':'div', 'class':'filmPreview__rateBox', 'text':False, 'attr':'data-rate'} }
Blueprint['plot'] = {
  'presentation': None,
  'html_parsing': {'tag':'div', 'class':'filmPreview__description', 'text':True, 'array':False} }
Blueprint['genres'] = {
  'presentation': {'name':'Gatunek', 'width':175, 'format':__list},
  'html_parsing': {'tag':'div', 'class':'filmPreview__info--genres', 'text':True, 'array':True} }
Blueprint['countries'] = {
  'presentation': {'name':'Kraj produkcji', 'width':150, 'format':__list},
  'html_parsing': {'tag':'div', 'class':'filmPreview__info--countries', 'text':True, 'array':True} }
Blueprint['directors'] = {
  'presentation': {'name':'Reżyseria', 'width':150, 'format':__list},
  'html_parsing': {'tag':'div', 'class':'filmPreview__info--directors', 'text':True, 'array':True} }
Blueprint['cast'] = {
  'presentation': {'name':'Obsada', 'width':200, 'format':__list},
  'html_parsing': {'tag':'div', 'class':'filmPreview__info--cast', 'text':True, 'array':True} }
#Informacje o ocenie są parsowane w inny sposób, stąd 'html_parsing': None
Blueprint['rating'] = {
  'presentation': {'name':'Ocena', 'width':145, 'format':__rating},
  'html_parsing': None }
Blueprint['favourite'] = {
  'presentation': {'name':'Ulubione', 'width':50, 'format':__fav},
  'html_parsing': None }
Blueprint['timeSeen'] = {
  'presentation': {'name':'Data obejrzenia', 'width':100, 'format':None},
  'html_parsing': None }
Blueprint['comment'] = {
  'presentation': {'name':'Komentarz', 'width':1000, 'format':__comment},
  'html_parsing': None }
