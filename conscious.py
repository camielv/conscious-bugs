import os
import sys
import operator
import cPickle as pickle

import numpy as np
import matplotlib.pyplot as plt
from settings import Settings 

from clarifai.client import ClarifaiApi

# TagADream: Tags dreams of children.

IMAGE_EXTENSIONS = ["jpg", "gif", "jpeg"]

class Image():

	def __init__(self, filename, filedir, tags):
		self.__filename = ""
		self.__dir = ""
		self.__tags = []
		self.__probs = []
		self.__meta = {}

		self.__filename = filename
		self.__dir = filedir
		self.__meta = tags['meta']['tag']
		self.__probs = tags['results'][0]['result']['tag']['probs']

		for tag in tags['results'][0]['result']['tag']['classes']:
			self.__tags.append(str(tag))

	def get_probs(self):
		return self.__probs

	def get_tags(self):
		return self.__tags

	def get_dir(self):
		return self.__dir

	def get_filename(self):
		return self.__filename

def main(argv):
	image_dir = "./tests/data"
	dataset = get_data(image_dir)

	frequencies = dict()

	for image in dataset:
		for tag in image.get_tags():
			if tag in frequencies:
				frequencies[tag] += 1
			else:
				frequencies[tag] = 1

	database = dict()

	for image_a in dataset:
		database[image_a.get_filename()] = dict()

		for image_b in dataset:
			if image_a.get_filename() == image_b.get_filename():
				continue

			tags_a = image_a.get_tags()
			tags_b = image_b.get_tags()

			score = 0

			for tag in tags_a:
				if tag in tags_b:
					score += 1.0/frequencies[tag]

			database[image_a.get_filename()][image_b.get_filename()] = score

	for key in database:
		sorted_db = sorted(database[key].items(), key=operator.itemgetter(1))
		print key
		print sorted_db
		print "----------"
	print frequencies

def parse_extension(filename):
	split_filename = filename.split(".")
	extension = split_filename[len(split_filename) - 1]

	return extension

def parse_path(path):
	"Parses the image path and returns the directory and the image filename"

	split_path = path.split("/")
	filename = split_path[len(split_path)- 1]
	directory = path[:len(path)-len(filename)]

	return (directory, filename)

def get_data(image_dir):
	''' Get tags from Clarifai, which are either stored locally or have to be retrieved from the server. '''

	filenames = os.listdir(image_dir)
	data = list()

	# Loop over all files in the storage directory.
	for filename in filenames:
		extension = parse_extension(filename)

		# Check if the file is an image.
		if extension in IMAGE_EXTENSIONS:
			image_filename = image_dir + "/image_" + filename + ".p"
			image_file = get_file(image_filename)

			# Check if an image file exists
			if image_file:
				image = pickle.load(image_file)
				data.append(image)
			else:
				tags_filename = image_dir + "/" + filename + ".p"
				tags_file = get_file(tags_filename)

				# Check if an tags file exists
				if tags_file:
					tags = pickle.load(tags_file)
					image = Image(filename, image_dir, tags)
					
					#save_file(image, image_filename)
					data.append(image)
				else:
					# Otherwise create both
					api_settings = Settings()
					api = ClarifaiApi(app_id=api_settings.app_id, app_secret=api_settings.app_secret)
					tags = None

					with open(image_dir + '/' + filename, 'rb') as image_file:
						tags = api.tag_images(image_file)

					save_file(tags, tags_filename)

					image = Image(filename, image_dir, tags)
					#save_file(image, image_filename)
					data.append(image)

	return data

def get_file(filename):
	try:
		return open(filename, "rb")
	except IOError:
		return False

def save_file(content, filename):
	pickle.dump(content, open(filename, "wb" ))

if __name__ == '__main__':
	main(sys.argv)
