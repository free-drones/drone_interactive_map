import cv2 as cv
import numpy as np

from PIL import Image, ImageOps
# Image lab!

# ====================== TEST TEST

def create_mask(img1,img2,version):

    height_img1 = img1.shape[0]
    height_img2 = img2.shape[0]
    width_img1 = img1.shape[1]
    width_img2 = img2.shape[1]

    height_panorama = height_img1 + height_img2
    width_panorama = width_img1 + width_img2

    offset = 50//2
    barrier = img1.shape[1] - offset

    mask = np.zeros((height_panorama, width_panorama))
    if version == 'left_image':
        mask[:, barrier - offset:barrier + offset ] = np.tile(np.linspace(1, 0, 2 * offset ).T, (height_panorama, 1))
        mask[:, :barrier - offset] = 1
    else:
        mask[:, barrier - offset :barrier + offset ] = np.tile(np.linspace(0, 1, 2 * offset ).T, (height_panorama, 1))
        mask[:, barrier + offset:] = 1

    return cv.merge([mask, mask, mask])

def blending(H,img1,img2):

    height_img1 = img1.shape[0]
    height_img2 = img2.shape[0]
    width_img1 = img1.shape[1]
    width_img2 = img2.shape[1]
    height_panorama = height_img1 + height_img2
    width_panorama = width_img1 + width_img2

    panorama1 = np.zeros((height_panorama, width_panorama, 3))
    mask1 = create_mask(img1, img2, version='left_image')
    panorama1[0:img1.shape[0], 0:img1.shape[1], :] = img1
    panorama1 *= mask1

    mask2 = create_mask(img1,img2,version='right_image')
    panorama2 = cv.warpPerspective(img2, H, (width_panorama, height_panorama))*mask2
    result=panorama1+panorama2

    rows, cols = np.where(result[:, :, 0] != 0)
    min_row, max_row = min(rows), max(rows) + 1
    min_col, max_col = min(cols), max(cols) + 1

    final_result = result[min_row:max_row, min_col:max_col, :]

    return final_result

# ==============================


def cv2_img_to_PIL(cv2_image):
	color_converted = cv.cvtColor(cv2_image, cv.COLOR_BGR2RGB)
	return Image.fromarray(color_converted)

def PIL_to_cv2_img(PIL_image):
	numpy_image = np.array(PIL_image)  
	return cv.cvtColor(numpy_image, cv.COLOR_RGB2BGR)


def scale_img(img, factor):
	return cv.resize(img, (0,0), fx=factor, fy=factor) 


def split_image_from_overlap(img, overlap_factor):
	""" 
	Split the given image into two new images which overlap in the center by the overlap factor.
	For example, with an overlap factor of 0.2, the new images will overlap by 20%.
	"""
	assert 0 <= overlap_factor <= 1

	img = cv2_img_to_PIL(img)

	# Center position (x,y) of the input image
	im_center = tuple(coord * 0.5 for coord in img.size) 

	# Size (w,h) of the resulting overlap
	overlap_size = (img.width * overlap_factor,
					img.height * overlap_factor)

	# New image size (w,h) of the new images.
	new_img_size = tuple(im_center[i] + overlap_size[i]/2 for i in range(2))

	# IMAGE ONE - Cropped from top left
	im_1 = img.crop((0, 0, new_img_size[0], new_img_size[1])) # Left, top, right, bottom

	# IMAGE TWO - Cropped from bottom right
	im_2_pos = (img.width - new_img_size[0], img.height - new_img_size[1])
	im_2 = img.crop((im_2_pos[0], 	# Left
					im_2_pos[1],	# Top
					img.width, 		# Right
					img.height))	# Bottom

	im_1 = PIL_to_cv2_img(im_1)
	im_2 = PIL_to_cv2_img(im_2)

	return im_1, im_2, im_2_pos


def merged_images(bottom_img, top_img, top_img_pos):
	""" 
		Return the composite of bottom_img and top_img. The top image is pasted on top of 
		the bottom image with the given offset position.
		bottom_img and top_img are expected to be cv2 images, and are temporarily converted
		to PIL images for certain image operations.
	"""
	bottom_img = cv2_img_to_PIL(bottom_img)
	top_img = cv2_img_to_PIL(top_img)

	left_expansion = int(-min(0, top_img_pos[0])) # Left direction
	top_expansion = int(-min(0, top_img_pos[1]))  # Up direction

	right_expansion = int(max(0, (top_img.width + top_img_pos[0]) - bottom_img.width))    # Right direction
	bottom_expansion = int(max(0, (top_img.height + top_img_pos[1]) - bottom_img.height)) # Down direction

	# Expand the size of bottom_img
	new_image = ImageOps.expand(bottom_img, (left_expansion, top_expansion, right_expansion, bottom_expansion), fill='black')

	# Paste top_img on top of bottom_img
	new_image.paste(top_img, (int(top_img_pos[0]), int(top_img_pos[1])))

	new_image = PIL_to_cv2_img(new_image)

	return new_image


def sobel_grad(image):
	## TODO : Set kernel size through JSON!
	gx = cv.Sobel(image, ddepth=cv.CV_32F, dx=1, dy=0, ksize=3)
	gy = cv.Sobel(image, ddepth=cv.CV_32F, dx=0, dy=1, ksize=3)
	return np.sqrt(gx**2 + gy**2)


def fft_psd_norm(image):
	"""
		Return the normalized FFT power spectrum distribution.
	"""
	grayscale_img = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

	f = np.fft.fft2(grayscale_img) # Compute 2D FFT
	fshift = np.fft.fftshift(f)

	psd = np.abs(fshift)**2 # Calculate the power spectrum
	psd_norm = psd / np.sum(psd)

	return psd_norm


def psd_entropy(psd):
	""" 
		Return the texture detail level with respect to the entropy of the fft power spectrum of an image.
	"""
	entropy = -np.sum(psd[psd > 0] * np.log2(psd[psd > 0]))

	return entropy


def texture_detail(img):
	"""
		Return the approximated texture detail in an image using various metrics.
	"""
	psd = fft_psd_norm(img)
	entropy = psd_entropy(psd)

	grad = sobel_grad(img)

	mean_grad = np.mean(grad)
	std_grad = np.std(grad)
	var_grad = np.var(grad) 

	return {"entropy": entropy, "mean_grad": mean_grad, "std_grad": std_grad, "var_grad": var_grad}


def main():
	img = Image.open("input/fire_2b.JPG")
	#img = Image.open("input/black.jpg")

	img = PIL_to_cv2_img(img)

	print(texture_detail(img).values())

	im_1, im_2, im_2_pos = split_image_from_overlap(img, 0.25)

	merged = merged_images(im_1, im_2, im_2_pos)

	cv.imshow("Image 1", merged)
	cv.waitKey(0)
	cv.destroyAllWindows()
	

if __name__ == '__main__':
	main()