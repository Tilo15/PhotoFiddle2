import os
import random
import threading
from gi.repository import GLib
import cv2
import subprocess
from Export.exiftool import ExifTool

class ExportDialog:

    def __init__(self, root, builder, w, h, get_image_call, done_call, path):
        self.exif = ExifTool()
        self.path = path
        self.builder = builder
        self.root = root
        # What gets called to get the image object at process time
        self.get_image_call = get_image_call
        self.done_call = done_call
        self.width = w
        self.height = h
        self.image = None

        UI_FILE = "ui/Export.glade"
        self.builder.add_from_file(UI_FILE)

        self.ui = {}

        components = [
            "window",
            "headerbar",
            "file",
            "save_button",
            "cancel_button",
            "preset",
            "format",
            "pngcrush",
            "width",
            "height",
            "quality",
            "width_spin",
            "height_spin",
            "quality_spin",
            "metadata",
            "description",
            "artist",
            "copyright"
        ]

        for component in components:
            self.ui[component] = self.builder.get_object("Export_%s" % (component))

        # Setup Export Dialog
        self.ui["window"].set_transient_for(self.root)
        self.ui["window"].set_titlebar(self.ui["headerbar"])

        self.ui["width"].set_upper(w)
        self.ui["width"].set_value(w)
        self.ui["height"].set_upper(h)
        self.ui["height"].set_value(h)

        self.ui["file"].set_filename(".".join(path.split(".")[:-1]) + "_PF")
        self.ui["file"].set_current_name(".".join(path.split("/")[-1:][0].split(".")[:-1]) + "_PF")

        # Connect siginals
        self.ui["preset"].connect("changed", self.on_preset_changed)
        self.ui["format"].connect("changed", self.on_format_changed)
        self.ui["width_spin"].connect("changed", self.on_width_changed)
        self.ui["height_spin"].connect("changed", self.on_height_changed)
        self.ui["save_button"].connect("clicked", self.on_save_clicked)
        self.ui["cancel_button"].connect("clicked", self.on_cancel_clicked)


        # Get EXIF data for this image ready
        self.exif.start()  
        data = self.exif.get_metadata(self.path)

        # Preload editable fields
        self.ui["description"].set_text(self.safe_exif_get(data, "EXIF:ImageDescription"))
        self.ui["artist"].set_text(self.safe_exif_get(data, "EXIF:Artist"))
        self.ui["copyright"].set_text(self.safe_exif_get(data, "EXIF:Copyright"))
        
        print(self.safe_exif_get(data, "Flash"))


        self.ui["window"].show_all()


    def safe_exif_get(self, data, key):
        out = ""
        if(key in data):
            out = data[key]
        return out


    def on_preset_changed(self, sender):
        if(sender.get_active() == 0):
            self.ui["width_spin"].set_sensitive(True)
            self.ui["height_spin"].set_sensitive(True)
            self.ui["format"].set_sensitive(True)
            self.ui["pngcrush"].set_sensitive(self.ui["format"].get_active() == 0)
            self.ui["quality_spin"].set_sensitive(self.ui["format"].get_active() == 1)

        else:
            if(sender.get_active() == 1):
                self.ui["width"].set_value(2048)
                self.ui["format"].set_active(1)
                self.ui["quality"].set_value(85)

            elif(sender.get_active() == 2):
                self.ui["width"].set_value(self.width)
                self.ui["format"].set_active(0)
                self.ui["pngcrush"].set_active(True)

            elif(sender.get_active() == 3):
                self.ui["width"].set_value(1920)
                self.ui["format"].set_active(1)
                self.ui["quality"].set_value(67)

            elif(sender.get_active() == 4):
                self.ui["width"].set_value(self.width)
                self.ui["format"].set_active(2)

            self.ui["width_spin"].set_sensitive(False)
            self.ui["height_spin"].set_sensitive(False)
            self.ui["format"].set_sensitive(False)
            self.ui["pngcrush"].set_sensitive(False)
            self.ui["quality_spin"].set_sensitive(False)

    def on_format_changed(self, sender):
        self.ui["pngcrush"].set_sensitive(sender.get_active() == 0)
        self.ui["quality_spin"].set_sensitive(sender.get_active() == 1)
        self.ui["pngcrush"].set_active(False)

    def on_width_changed(self, sender):
        w = sender.get_value()
        r = w/self.width
        self.ui["height_spin"].set_value(r*self.height)

    def on_height_changed(self, sender):
        h = sender.get_value()
        r = h/self.height
        self.ui["width_spin"].set_value(r*self.width)

    def on_cancel_clicked(self, sender):
        self.exif.terminate()
        self.ui["window"].close()

    def on_save_clicked(self, sender):
        self.ui["window"].close()
        format = self.ui["format"].get_active()
        quality = self.ui["quality"].get_value()
        width = self.ui["width"].get_value()
        height = self.ui["height"].get_value()
        path = self.ui["file"].get_filename()
        pngcrush = self.ui["pngcrush"].get_active()
        # Metadata
        metadata_scheme = self.ui["metadata"].get_active()
        description = self.ui["description"].get_text()
        artist = self.ui["artist"].get_text()
        copyright_info = self.ui["copyright"].get_text()
        
        threading.Thread(target=self.do_export, args=(format, quality, width,
                                                      height, path, pngcrush,
                                                      metadata_scheme,
                                                      description, artist,
                                                      copyright_info)).start()

    def do_export(self, format, quality, width, height, path, pngcrush, metadata_scheme, description, artist, copyright_info):
        self.image = self.get_image_call(width, height)
        newPath = path
        if(format == 0) and (not path.endswith(".png")):
            newPath += ".png"
        if(format == 1) and (not path.endswith(".jpg")) and (not path.endswith(".jpeg")):
            newPath += ".jpg"
        if(format == 2) and (not path.endswith(".tif")) and (not path.endswith(".tiff")):
            newPath += ".tiff"

        if(format == 1):
            # Convert to 8 Bit
            bpp = int(str(self.image.dtype).replace("uint", ""))
            im = (self.image/float(2**bpp))*255
            cv2.imwrite(newPath, im, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])

        elif(format == 0) and pngcrush:
            tempPath = "/tmp/pngcrush-%i.png" % random.randrange(1000000,9999999)
            cv2.imwrite(tempPath, self.image)
            subprocess.call(["pngcrush", "-rem gAMA", "-rem cHRM", "-rem iCCP", "-rem sRGB" , "-m 0", "-l 9", "-fix", "-v", "-v", tempPath, newPath])
            os.unlink(tempPath)

        else:
            cv2.imwrite(newPath, self.image)

        # Write metadata
        # If the scheme is Include Original Metadata
        if(metadata_scheme == 0):
            # Copy metadata from original file
            self.exif.execute(b"-TagsFromFile", self.path.encode("utf-8"), b"-all:all", newPath.encode("utf-8"), b"-overwrite_original")

        # Scheme 1 (Ignore Original Metadata) does not copy any data so is skipped here

        # If the scheme is Strip GPS Information
        if(metadata_scheme == 2):
            # Copy all metadata not pertaining to GPS information
            self.exif.execute(b"-tagsFromFile", self.path.encode("utf-8"), b"-all:all", b"-gps:all=", b"-xmp:geotag=", newPath.encode("utf-8"), b"-overwrite_original")

        # Write dialog editable metadata and application metadata to file
        self.exif.execute(self.fmt_exif_set(description, b"ImageDescription"),
                            self.fmt_exif_set(artist, b"Artist"),
                            self.fmt_exif_set(copyright_info, b"Copyright"),
                            self.fmt_exif_set("PhotoFiddle2", b"Software"),
                            newPath.encode("utf-8"), b"-overwrite_original")

        # Clean up
        self.exif.terminate()

        GLib.idle_add(self.done_call, newPath)


    def fmt_exif_set(self, data, key):
        return b"-%s=%s" % (key, data.encode("utf-8"))









