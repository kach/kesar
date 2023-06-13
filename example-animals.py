from kesar import *

@kesar
def experiment():
  data = {}
  animals = ['cat', 'dog', 'beaver']

  for animal in animals:
    response = yield text_input_('rating',
      f'Do you have a pet {animal}? (y/n)')
    data[animal] = response['rating']
  return data  # to be logged