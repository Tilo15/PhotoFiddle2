import cv2
import numpy
import math

class Histogram:
    @staticmethod
    def draw_hist(image, path):
        bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
        img = ((image/2**bpp)*255).astype('uint8')

        hist = numpy.zeros(shape=(128, 330, 3))

        color = ('b', 'g', 'r')
        for i, col in enumerate(color):
            colhist = numpy.zeros(shape=(128, 510, 3))
            histr = cv2.calcHist([img], [i], None, [256], [0, 255])
            hi = max(histr)
            for i2, hval in enumerate(histr):
                value = hval
                if(i2 != 0 and i2 != 255):
                    value = (hval + histr[i2-1] + histr[i2+1]) / 3.0

                x = i2*2
                height = int((-(value/hi)+1) * 128)
                cv2.line(colhist, (x, height), (x, 128), (255,255,255), 2)
            
            hist[0:, 0:, i] = cv2.resize(colhist, (330, 128), interpolation=cv2.INTER_LANCZOS4)[0:, 0:, i]

        cv2.imwrite(path, hist)


# # Oi! TODO look at his
# # Port it to something we can use eh


# void
# gth_histogram_calculate_for_image (GthHistogram    *self,
# 				   cairo_surface_t *image)
# {
# 	int    **values;
# 	int     *values_max;
# 	int      width, height, has_alpha;
# 	int      rowstride;
# 	guchar  *line, *pixel;
# 	int      i, j, value, temp;
# 	guchar   red, green, blue, alpha;

# 	g_return_if_fail (GTH_IS_HISTOGRAM (self));

# 	values = self->priv->values;
# 	values_max = self->priv->values_max;

# 	if (image == NULL) {
# 		self->priv->n_channels = 0;
# 		histogram_reset_values (self);
# 		gth_histogram_changed (self);
# 		return;
# 	}

# 	has_alpha  = _cairo_image_surface_get_has_alpha (image);
# 	rowstride  = cairo_image_surface_get_stride (image);
# 	line       = _cairo_image_surface_flush_and_get_data (image);
# 	width      = cairo_image_surface_get_width (image);
# 	height     = cairo_image_surface_get_height (image);

# 	self->priv->n_pixels = width * height;
# 	self->priv->n_channels = (has_alpha ? 4 : 3) + 1;
# 	histogram_reset_values (self);

# 	for (i = 0; i < height; i++) {
# 		pixel = line;

# 		for (j = 0; j < width; j++) {
# 			CAIRO_GET_RGBA (pixel, red, green, blue, alpha);

# 			/* count values for each RGB channel */

# 			values[GTH_HISTOGRAM_CHANNEL_RED][red] += 1;
# 			values[GTH_HISTOGRAM_CHANNEL_GREEN][green] += 1;
# 			values[GTH_HISTOGRAM_CHANNEL_BLUE][blue] += 1;
# 			if (has_alpha)
# 				values[GTH_HISTOGRAM_CHANNEL_ALPHA][alpha] += 1;

# 			/* count value for Value channel */

# 			value = MAX (MAX (red, green), blue);
# 			values[GTH_HISTOGRAM_CHANNEL_VALUE][value] += 1;

# 			/* min and max pixel values */

# 			self->priv->min_value[GTH_HISTOGRAM_CHANNEL_VALUE] = MIN (self->priv->min_value[GTH_HISTOGRAM_CHANNEL_VALUE], value);
# 			self->priv->min_value[GTH_HISTOGRAM_CHANNEL_RED] = MIN (self->priv->min_value[GTH_HISTOGRAM_CHANNEL_RED], red);
# 			self->priv->min_value[GTH_HISTOGRAM_CHANNEL_GREEN] = MIN (self->priv->min_value[GTH_HISTOGRAM_CHANNEL_GREEN], green);
# 			self->priv->min_value[GTH_HISTOGRAM_CHANNEL_BLUE] = MIN (self->priv->min_value[GTH_HISTOGRAM_CHANNEL_BLUE], blue);
# 			if (has_alpha)
# 				self->priv->min_value[GTH_HISTOGRAM_CHANNEL_ALPHA] = MIN (self->priv->min_value[GTH_HISTOGRAM_CHANNEL_ALPHA], alpha);

# 			self->priv->max_value[GTH_HISTOGRAM_CHANNEL_VALUE] = MAX (self->priv->max_value[GTH_HISTOGRAM_CHANNEL_VALUE], value);
# 			self->priv->max_value[GTH_HISTOGRAM_CHANNEL_RED] = MAX (self->priv->max_value[GTH_HISTOGRAM_CHANNEL_RED], red);
# 			self->priv->max_value[GTH_HISTOGRAM_CHANNEL_GREEN] = MAX (self->priv->max_value[GTH_HISTOGRAM_CHANNEL_GREEN], green);
# 			self->priv->max_value[GTH_HISTOGRAM_CHANNEL_BLUE] = MAX (self->priv->max_value[GTH_HISTOGRAM_CHANNEL_BLUE], blue);
# 			if (has_alpha)
# 				self->priv->max_value[GTH_HISTOGRAM_CHANNEL_ALPHA] = MAX (self->priv->max_value[GTH_HISTOGRAM_CHANNEL_ALPHA], alpha);

# 			/* track min and max value for each channel */

# 			values_max[GTH_HISTOGRAM_CHANNEL_VALUE] = MAX (values_max[GTH_HISTOGRAM_CHANNEL_VALUE], values[GTH_HISTOGRAM_CHANNEL_VALUE][value]);
# 			values_max[GTH_HISTOGRAM_CHANNEL_RED] = MAX (values_max[GTH_HISTOGRAM_CHANNEL_RED], values[GTH_HISTOGRAM_CHANNEL_RED][red]);
# 			values_max[GTH_HISTOGRAM_CHANNEL_GREEN] = MAX (values_max[GTH_HISTOGRAM_CHANNEL_GREEN], values[GTH_HISTOGRAM_CHANNEL_GREEN][green]);
# 			values_max[GTH_HISTOGRAM_CHANNEL_BLUE] = MAX (values_max[GTH_HISTOGRAM_CHANNEL_BLUE], values[GTH_HISTOGRAM_CHANNEL_BLUE][blue]);
# 			if (has_alpha)
# 				values_max[GTH_HISTOGRAM_CHANNEL_ALPHA] = MAX (values_max[GTH_HISTOGRAM_CHANNEL_ALPHA], values[GTH_HISTOGRAM_CHANNEL_ALPHA][alpha]);

# 			pixel += 4;
# 		}

# 		line += rowstride;
# 	}

# 	gth_histogram_changed (self);
# }
