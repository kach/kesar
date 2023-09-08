from kesar import *

@kesar
def experiment():
  data = {}
  animals = ['cat', 'dog', 'beaver']

  for animal in animals:
    response = yield div_()(
      text_input_('rating', f'Do you have a pet {animal}? (y/n)'),
      submit_()
    )
    data[animal] = response['rating']
  return data  # to be logged