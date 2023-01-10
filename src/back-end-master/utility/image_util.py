"""
This file contains various help functions that are used in the image processing.

It is assumed that all images passed to functions in this module are given as
cv2 images, i.e. numpy arrays rows and columns as first and second dimension and
(optionally) colour channels in the third dimension.

All functions operating on images returns a copy of the result, unless specified otherwise.
"""

import cv2
import numpy

"""
Colours in BGR format.
"""
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)

def pixel(b, g, r):
    """Creates a BGR pixel from colour components.

    Colour components should be given as an int in the range 0-255.
    
    Keyword arguments:
    b -- The blue component.
    g -- The green component.
    r -- The red component.
    """
    return numpy.array((b, g, r), numpy.uint8)

__windows_initialized = False
def show_comparison(img1, img2, delay=1):
    """Displays two images with a comparison between two images.

    This function is only meant for debugging. The first time the
    function is called, two empty windows are created. The user
    can resize them and should press space when satisfied. These
    windows are then reused for all subsequent calls to the function,
    and should therefore not be closed manually.

    Keyword arguments:
    img1 -- The first image to display.
    img2 -- The second image to display.
    delay -- The time in seconds to wait before proceeding. If set to
             0, the user has to press space to proceed.
    """
    global __windows_initialized

    if not __windows_initialized:
        cv2.namedWindow("Image 1", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Image 2", cv2.WINDOW_NORMAL)
        cv2.waitKey(0)
        __windows_initialized = True
    cv2.imshow("Image 1", img1)
    cv2.imshow("Image 2", img2)
    cv2.waitKey(delay*1000)

def blur(image, size=3, blur_type="median"):
    """Applies blur to an image.

    Keyword arguments:
    image -- The image to blur.
    size -- The aperture size of the blur.
    blur_type -- The type of blur to apply, given as a string. Supported blur
                 types are median, mean and gaussian.

    Returns the blurred image.

    Throws a ValueError if an unsupported blur type is requested.
    """
    if blur_type == "median":
        return cv2.medianBlur(image, size)
    elif blur_type == "mean":
        kernel = numpy.ones((size, size), numpy.float32) / size**2
        return cv2.filter2D(image, -1, kernel)
    elif blur_type == "gaussian":
        return cv2.GaussianBlur(image, (size, size), .05)
    else:
        raise ValueError("Unsupported blur type: " + blur_type)

def dilate(image, size):
    """Dilates an image.

    Keyword arguments:
    image -- The image to dilate.
    size -- The dilation aperture size.

    Returns the blurred image.
    """
    return cv2.dilate(image, numpy.ones((size, size), numpy.uint8))

def color_mask(image, color, low_diff=0, high_diff=0):
    """Creates mask denoting the presence of the specified colour in the image.

    The created mask indicates all pixels p where
    color - low_diff <= p <= color + high_diff. If the image has more than one
    colour channel, this expression must be true for all channel values. If the
    tolerances are integer values, the same tolerance is applied to all channels.

    Keyword arguments:
    image -- The image to mask.
    color -- The colour to look for.
    low_diff -- The lower tolerance.
    high_diff -- The upper tolerance.

    Returns a binary mask as described above.
    """
    low_thres = color - low_diff
    high_thres = color + high_diff
    return cv2.inRange(image, low_thres, high_thres)

def add_images(img1, img2):
    """Pastes two images of the same size.

    Let p[y, x] be the pixel value of the resulting image at coordinates (x, y),
    and similarly for img1[y, x] and img2[y, x]. Then p[y, x] = img2[y, x] iff
    |img2[y, x] > 0| else p[y, x] = img1[y, x].

    Keyword arguments:
    img1 -- The first image.
    img2 -- The second image.

    Returns the resulting image.
    """
    if len(img2.shape) > 2:
        gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        gray = img2
    (_, mask) = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
    final = numpy.zeros(img1.shape, numpy.uint8)
    final = cv2.add(final, img1, mask=numpy.bitwise_not(mask), dtype=cv2.CV_8U)
    final = cv2.add(final, img2, dtype=cv2.CV_8U)
    return final

def warp(shape, transform):
    """Warps a shape using the specified transformation.

    Keyword arguments:
    shape -- A list of 2d coordinates to warp.
    transform -- The transformation matrix.

    Returns the transformed shape.
    """
    res = []
    for x, y in shape:
        e = numpy.array([x, y, 1], numpy.float32).reshape((3))
        d = transform.dot(e)
        res.append([int(d[0]/d[2]), int(d[1]/d[2])])
    return res

def warp_contours(contours, transform):
    """Warps a cv2 contour using the specified transformation.

    Keyword arguments:
    contours -- A list of contours as returned by cv2 contour functions.
    transform -- the transform to apply.

    Returns the transformed contours list.
    """
    res = []
    for contour in contours:
        vertices = to_vertex_list(contour)
        warped = warp(vertices, transform)
        res.append(to_contour(warped))
    return res

def add_bound(image, points, color=RED):
    """Paints a minimum area bound of a set of points in an image.

    Keyword arguments:
    image -- The image to paint.
    points -- A list of coordinates to include in the bound.
    colour -- The colour used to mark the bound.

    Returns an image where the minimum area rectangular bound of the provided
    points has been marked.
    """
    rect = cv2.minAreaRect(points)
    box = cv2.boxPoints(rect)
    box = numpy.int0(box)
    image = image.copy()
    cv2.drawContours(image, [box], 0, color, 5)
    return image

def to_contour(shape):
    """Converts from a coordinate list to a cv2 contour format.

    Keyword arguments:
    shape -- A list of coordinates.

    Returns the shape given as a cv2 contour.
    """
    return numpy.array(shape).reshape((-1, 1, 2)).astype(numpy.int32)

def to_vertex_list(contour):
    """Converts a cv2 contour to a coordinate list.

    Keyword arguments:
    contour -- A cv2 contour.

    Returns the contour as a list of coordinates.
    """
    res = [[x, y] for [[x, y]] in contour]
    return res
