'''
require:
	python
	OpenImageIO
'''

__author__ = 'Lex Darlog (DRL)'


import OpenImageIO.OpenImageIO as oiio
import warnings as wrn

rgba_tuple = ('R', 'G', 'B', 'A')


def apply_gamma(img, gamma=1.0):
	assert isinstance(img, oiio.ImageBuf)
	if gamma == 1.0:
		return img
	if gamma <= 0.0:
		wrn.warn('\nProvided negative gamma value.', RuntimeWarning, stacklevel=2)
		return img

	dest = oiio.ImageBuf(img.spec())
	oiio.ImageBufAlgo.pow(dest, img, 1.0/gamma)
	return dest

def luminance(img):
	'''
	Converts colorful RGB image to a grayscale one.
	:param src: source image, represented as oiio.ImageBuf
	:return:
	'''
	assert isinstance(img, oiio.ImageBuf)
	roi = img.roi
	assert isinstance(roi, oiio.ROI)
	dest = oiio.ImageBuf(img.spec())
	dest.copy_metadata(img)
	dest.roi = roi
	roi.chbegin = 0
	roi.chend = 3
	oiio.ImageBufAlgo.channel_sum(dest, img, (.2126, .7152, .0722), roi)
	return dest

def read_image(image_path, num_channels=3):
	import os.path as path
	if not(path.exists(image_path) and path.isfile(image_path)):
		raise Exception('There is no file at the given path.')


	assert isinstance(image_path, basestring)
	img = oiio.ImageBuf(image_path)
	spec = img.spec()

	assert isinstance(spec, oiio.ImageSpec)
	if spec.nchannels != num_channels:
		last_channel = max(1, min(4, num_channels))
		read_channels = rgba_tuple[:last_channel]
		dest = oiio.ImageBuf(spec)
		oiio.ImageBufAlgo.channels(dest, img, read_channels)
		img = dest
	return img



def post_bake(src_tex_path, src_in_sRGB=False, make_grayscale=False, intensity=1.0, post_gamma=1.0):
	import os.path as path
	# intensity=2.0
	# src_tex_path = r'e:\1-Projects\5-ShaderFX\sources\Trash\Trash.exr'
	# src_tex_path = r'e:\1-Projects\5-ShaderFX\sources\Trash\Trash-rgb.png'
	assert isinstance(src_tex_path, str)
	tex_path = src_tex_path.replace('\\', '/')
	img = read_image(tex_path)
	spec = img.spec()
	assert isinstance(spec, oiio.ImageSpec)

	if src_in_sRGB:
		oiio.ImageBufAlgo.colorconvert(img, img, 'sRGB', 'linear')
	if make_grayscale:
		img = luminance(img)
	if intensity != 1.0:
		dest = oiio.ImageBuf(img.spec())
		oiio.ImageBufAlgo.mul(dest, img, intensity)
		img = dest
	img = apply_gamma(img, post_gamma)

	png_path = path.splitext(tex_path)[0] + '.png'
	#img = apply_gamma(img, 2.2)
	#spec.get_string_attribute("oiio:ColorSpace")
	out = oiio.ImageBuf(oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8))
	out.spec().attribute("oiio:ColorSpace", 'sRGB')
	#oiio.ImageBufAlgo.pow(out, img, .4545)
	oiio.ImageBufAlgo.colorconvert(out, img, 'linear', 'sRGB')

	#oiio.ImageBufAlgo.channels(out, img, rgba_tuple[:3])
	out.write(png_path)