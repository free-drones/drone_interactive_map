import cv2 as cv
import time
import json

import im_lab

import matplotlib.pyplot as plt
import numpy as np

from tqdm import tqdm
from functools import wraps
from enum import Enum

# ============= Options ============= 

class ExtractOptions(Enum):
	ORB = 1
	SIFT = 2
	D2_NET = 3

class MatchOptions(Enum):
	BRUTE_FORCE = 1
	FLANN = 2

# ============= Decorators =============

def time_log(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		start_time = time.time()
		result = func(*args, **kwargs)
		elapsed_time = time.time() - start_time
		print(f"Function {func.__name__} took {elapsed_time:.4f} seconds to execute.")
		return result, elapsed_time
	return wrapper

# ====================================== 

class FeatureExtractor:
	def __init__(self, extract_option : ExtractOptions):
		self.extract_option = extract_option
		self.extractor = self.__init_extractor()

	def __init_extractor(self):
		"""
			Wrapper to init the selected extractor.
		"""
		if self.extract_option == ExtractOptions.ORB:
			return self.__orb_init()
		if self.extract_option == ExtractOptions.SIFT:
			return self.__sift_init()
		if self.extract_option == ExtractOptions.D2_NET:
			return self.__d2n_init()
		raise ValueError(f"Failed to initialize unsupported extract option: {self.extract_option}")

	def process_img(self, image_file):
		"""
			Process an image from an image file.
			Return said image.
		"""
		return cv.imread(image_file)

	@time_log
	def process(self, img):
		""" 
			Extract the features from an image file
		"""
		assert self.extractor, "Extractor is uninitialized!"

		if self.extract_option == ExtractOptions.ORB:
			return self.__orb_extract(img)
		if self.extract_option == ExtractOptions.SIFT:
			return self.__sift_extract(img)
		if self.extract_option == ExtractOptions.D2_NET:
			return self.__d2n_extract(img)
		raise ValueError(f"Failed to process unsupported extract option: {self.extract_option}")

	# ======= ORB =======
	def __orb_init(self):
		"""
			Init ORB extractor.
		"""
		if self.extract_option is not ExtractOptions.ORB:
			print(f"Warning! Initializing ORB when ExtractOption is set to {self.extract_option}")
		return cv.ORB_create(nfeatures = 20000)

	def __orb_extract(self, img):
		"""
			Find extracted keypoints and descriptors using the ORB extractor.
		"""
		keypoints, descriptors = self.extractor.detectAndCompute(img, None)
		scores = []
		return {"keypoints": keypoints, "scores": scores, "descriptors": descriptors}

	# ======= SIFT =======
	def __sift_init(self):
		"""
			Init SIFT extractor.
		"""
		if self.extract_option is not ExtractOptions.SIFT:
			print(f"Warning! Initializing SIFT when ExtractOption is set to {self.extract_option}")
		return cv.SIFT_create()

	def __sift_extract(self, img):
		"""
			Find extracted keypoints and descriptors using the SIFT extractor.
		"""
		keypoints, descriptors = self.extractor.detectAndCompute(img, None)
		scores = []
		return {"keypoints": keypoints, "scores": scores, "descriptors": descriptors}

	# ======= D2-Net =======
	def __init_d2n(self):
		# Load model etc
		if self.extract_option is not ExtractOptions.D2_NET:
			print(f"Warning! Initializing D2-net when ExtractOption is set to {self.extract_option}")
		raise NotImplementedError("D2-Net is not yet implemented")

	def __d2n_extract(self, img):
		raise NotImplementedError("D2-Net is not yet implemented")


class FeatureMatcher:
	def __init__(self, match_option : MatchOptions, extract_option : ExtractOptions, settings):
		self.match_option = match_option
		self.extract_option = extract_option
		self.settings = settings["feature_matching"]

		self.matcher = self.__init_matcher()

	def __init_matcher(self):
		"""
			Wrapper to init the selected matcher.
		"""
		if self.match_option == MatchOptions.BRUTE_FORCE:
			return self.__brute_force_init()
		if self.match_option == MatchOptions.FLANN:
			return self.__flann_init()

	def __brute_force_init(self):
		"""
			Init brute force matcher.
		"""
		norm_type = cv.NORM_L1 # L1 and L2 norms are preferable choices for SIFT and SURF
		if self.extract_option == ExtractOptions.ORB:
			norm_type = cv.NORM_HAMMING # NORM_HAMMING should be used with ORB, BRISK and BRIEF

		cross_check = self.settings["brute_force"]["enable_cross_check"]

		return cv.BFMatcher(norm_type, crossCheck=cross_check)

	def __flann_init(self):
		"""
			Init FLANN matcher.
		"""
		if self.extract_option == ExtractOptions.ORB:
			lsh_settings = self.settings["flann"]["lsh"]

			# Lsh parameters
			lsh_algorithm_idx = lsh_settings["index"]
			lsh_table_num = lsh_settings["table_number"]
			lsh_key_size = lsh_settings["key_size"]
			lsh_multi_probe_level = lsh_settings["multi_probe_level"]

			index_params = dict(
				algorithm = lsh_algorithm_idx, 
				table_number = lsh_table_num,
				key_size = lsh_key_size,
				multi_probe_level = lsh_multi_probe_level
			)
		else:
			kdtree_algorithm_idx = self.settings["flann"]["kdtree"]["index"]
			num_trees = self.settings["flann"]["kdtree"]["num_trees"]

			index_params = dict(
				algorithm = kdtree_algorithm_idx, 
				trees = num_trees
			)

		num_checks = self.settings["flann"]["num_checks"]
		search_params = dict(checks = num_checks)

		return cv.FlannBasedMatcher(index_params, search_params)
		

	@staticmethod
	def pair(im1_data, im2_data):
		return {"image1": im1_data, "image2": im2_data}

	@time_log
	def process(self, extracted_data_pair):
		"""
			Wrapper function to compute matches based on the chosen option
		"""
		assert self.matcher, "Extractor is uninitialized!"

		if self.match_option == MatchOptions.BRUTE_FORCE:
			return self.__filtered_matches(extracted_data_pair)
		if self.match_option == MatchOptions.FLANN:
			return self.__filtered_matches(extracted_data_pair)
		raise ValueError(f"Failed to process unsupported match option: {self.match_option}")

	def __filtered_matches(self, extracted_data_pair):
		"""
			Return the filtered matches, computed by the chosen matcher. If applicable (given the
			match settings), these are filtered according to Lowe's ratio test.
		"""
		des1 = extracted_data_pair["image1"]["descriptors"]
		des2 = extracted_data_pair["image2"]["descriptors"]

		# knn_k needs to be 1 with brute-force if cross_check is enabled.
		# Then the ratio test cannot be performed, so the raw matches are returned instead.  
		if self.match_option == MatchOptions.BRUTE_FORCE and self.settings["brute_force"]["enable_cross_check"]:
			print("Ignoring ratio test...")
			return self.matcher.knnMatch(des1, des2, k=1)

		knn_k = 2
		matches = self.matcher.knnMatch(des1, des2, k=knn_k)
		return self.ratio_test(matches)

	def ratio_test(self, matches, threshold=0.75):
		""" Filter matches based on their distance ratio, keeping matches within a specified threshold """
		return [m for (m,n) in matches if m.distance < threshold*n.distance]

# ====================================== 

def feature_extract_all(lines, feature_extractor):
	""" 
		Find the features (consisting of keypoints, scores, descriptors) using the specified feature extractor.
	"""
	print("Starting feature extraction...")
	extraction_results = []
	for line in tqdm(lines, total=len(lines)):
		path = line.strip()
		print(f"\n === Extracting features from image '{path}' ===")

		# Extract 
		img = feature_extractor.process_img(path)
		extracted_data, elapsed_time = feature_extractor.process(img)
		data = {
			"path": path,
			"img": img, 
			"extracted_data": extracted_data, 
			"elapsed_time": elapsed_time
		}
		extraction_results.append(data)
	return extraction_results

def feature_match_all(extraction_results, feature_matcher):
	""" 
		Feature match all the extraction results using the specified feature matcher
	"""
	print("Starting feature matching...")
	match_results = []
	for i,k in zip(extraction_results[0::2], extraction_results[1::2]):
		pair = FeatureMatcher.pair(i["extracted_data"], k["extracted_data"])
		matches, elapsed_time = feature_matcher.process(pair)

		data = {
			"matches": matches,
			"num_matches": len(matches),
			"elapsed_time": elapsed_time
		}
		match_results.append(data)
	return match_results

def stitched_image(left_extraction, right_extraction, match_data):
	""" 
		Return a panorama of the images with the extracted data "left_extraction" and "right_extraction" 
		respectively, with the match data from the two extractions.
	"""
	kp_left = left_extraction["extracted_data"]["keypoints"]
	kp_right = right_extraction["extracted_data"]["keypoints"]
	matching_kp_left = np.float32([kp_left[x.queryIdx].pt for x in match_data["matches"]]).reshape(-1, 1, 2)
	matching_kp_right = np.float32([kp_right[x.trainIdx].pt for x in match_data["matches"]]).reshape(-1, 1, 2)

	left_im = left_extraction["img"]
	right_im = right_extraction["img"]

	h, status = cv.findHomography(matching_kp_left, matching_kp_right, cv.RANSAC)
	#right_im_warped = cv.warpAffine(right_im, h, (left_im.shape[1], left_im.shape[0]), borderMode=cv.BORDER_TRANSPARENT)
	return im_lab.blending(h, right_im, left_im)

def stitch_all_images(result_data):
	"""
		Stitch all the images from the result data (containing lists of extraction results and match
		results respectively). Return the resulting list of stitched images, and the fail count.  
	"""
	extraction_results = result_data["extraction"]
	match_results = result_data["match"]

	num_fails = 0
	stitched = []

	for match_index in range(len(match_results)):
		# Indicies corresponding to feature extraction pairs, since there are
		# two extractions per match.
		extract_indices = (match_index*2, match_index*2 + 1)

		left_extraction, right_extraction = tuple(extraction_results[extract_indices[i]] for i in range(2))

		try:
			output = stitched_image(left_extraction, right_extraction, match_results[match_index])
		except:
			output = None
			path = left_extraction["path"]
			print(f"Failed to stitch image with path {path}. ")
			num_fails += 1

		if output is not None:
			output = im_lab.scale_img(output, 0.5)
			stitched.append(output)

	return stitched, num_fails


def plot_time(result_data):
	# (0, 0, 1, 1, ..) since there are two extractions per match
	image_indices = [i for i in range(len(result_data["extraction"])) ]

	extract_times = [data["elapsed_time"] for data in result_data["extraction"]]
	match_times = [data["elapsed_time"] for data in result_data["match"] for j in range(2)]
	num_matches = [data["num_matches"] for data in result_data["match"] for j in range(2)]
	total_times = [extract_times[i] + match_times[i] for i in range(len(image_indices))]

	# Create bar chart with split bars
	fig, ax = plt.subplots()
	bar_width = 0.35
	opacity = 0.8
	colors = ['b', 'g']

	# Create bar for extract time
	match_bars = ax.bar(image_indices, match_times, bar_width, alpha=opacity, color=colors[0], label='Match time')

	# Create bar for match time
	extract_bars = ax.bar(image_indices, extract_times, bar_width, bottom=match_times, alpha=opacity, color=colors[1], label='Extract Time')

	# Set labels and legend
	ax.set_xlabel('Image Index')
	ax.set_ylabel('Time (s)')
	ax.set_title('Processing Time by Image Index')
	ax.set_xticks(image_indices)

	handles, labels = plt.gca().get_legend_handles_labels()
	order = [1, 0]
	ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order]) 

	# Display total time as text above each bar
	for i, (extract_bar, match_bar) in enumerate(zip(extract_bars, match_bars)):
		num_match = num_matches[i]
		total_time = total_times[i]
		ax.text(extract_bar.get_x() + extract_bar.get_width() / 2., total_time + 0.2, num_match, ha='center', va='bottom')

	plt.tight_layout()
	plt.show()


def main():
	with open("im_matching_settings.json") as f:
		settings = json.load(f)

	# ===== OPTIONS =====
	EXTRACT_OPTION = ExtractOptions.SIFT
	MATCH_OPTION = MatchOptions.FLANN

	# ===== INIT =====
	feature_extractor = FeatureExtractor(EXTRACT_OPTION)
	feature_matcher = FeatureMatcher(MATCH_OPTION, EXTRACT_OPTION, settings)
	image_list_file = "input_images.txt"

	with open(image_list_file, 'r') as f:
		lines = f.readlines()

	# ===== EXTRACT AND MATCH =====
	extraction_results = feature_extract_all(lines, feature_extractor) # Feature extraction
	match_results = feature_match_all(extraction_results, feature_matcher) # Feature matching
	result_data = {"extraction": extraction_results, "match": match_results}

	# ===== STITCHING =====
	stitched_im_ls, num_fails = stitch_all_images(result_data)
	print(f"Successfully stitched {len(stitched_im_ls)} with {num_fails} fails.")

	for stitched_im in stitched_im_ls:
		cv.imshow("Panorama result", stitched_im/255)
		cv.waitKey(0)

	# ===== PLOT DATA =====
	plot_time(result_data)

	# Image index vs:  Extract time, Match time, Total matches


if __name__ == '__main__':
	main()



# Run benchmarks: batches

# Generate funky graphs and stuff
