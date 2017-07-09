#!/usr/bin/python3
from gi import require_version

import FocusStack
import HDR
import LightStack

require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gio
import sys
import PF2


# MENU UI FILE
MENU_FILE = "ui/menu.ui"
# UI FILE
UI_FILE = "ui/PhotoFiddle.glade"

Gtk.Settings.get_default().set_property("gtk_application_prefer_dark_theme", True)


class App(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id="com.pcthingz.photofiddle",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.connect("activate", self.activateCb)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)

        # TODO: Menu

        self.builder.add_from_file(MENU_FILE)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.quit)
        self.add_action(action)

        self.set_app_menu(self.builder.get_object("app-menu"))

    def activateCb(self, app):

        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object('window')
        self.window.set_wmclass("PhotoFiddle", "PhotoFiddle")
        self.window.set_titlebar(self.builder.get_object('header_bar'))
        app.add_window(self.window)

        self.stack = self.builder.get_object('stack')
        self.stack.add_titled(self.builder.get_object('initial_box'), "init", "PhotoFiddle")

        self.header_stack = self.builder.get_object('header_stack')
        self.no_header = self.builder.get_object('initial_header')
        self.header_stack.add_titled(self.no_header, "noh", "No Header")

        spinner = self.builder.get_object('spinner')

        # Initialse Activities
        args = (self.stack, self.header_stack, self.builder, self.window, self.show_message, self.hide_message,
                self.update_message_progress, spinner.start, spinner.stop, self.switch_activity_id)

        self.activities = [PF2.PF2(*args), FocusStack.FocusStack(*args), HDR.HDR(*args), LightStack.LightStack(*args)]

        self.header_stack.set_visible_child_name("noh")

        self.window.show_all()
        self.window.maximize()

        self.add_activities()

    activity_map = {}

    def add_activities(self):
        activity_list = self.builder.get_object('activity_list')
        for activity in self.activities:
            # Add activities to the man menu
            item = Gtk.VBox()
            item.set_margin_left(18)
            item.set_margin_right(18)
            item.set_margin_top(6)
            item.set_margin_bottom(6)

            title = Gtk.Label()
            title.set_markup("<b>%s</b>" % activity.name)
            title.set_halign(Gtk.Align.START)
            item.add(title)
            subtitle = Gtk.Label()
            subtitle.set_markup("<i>%s</i>" % activity.subtitle)
            subtitle.set_halign(Gtk.Align.START)
            item.add(subtitle)

            item.show()
            title.show()
            subtitle.show()
            activity_list.add(item)
            self.activity_map[item.get_parent()] = activity

    current_activity = None

    def activity_selected(self, sender, row):
        activity = self.activity_map[row]
        self.switch_activity(activity)

    def switch_activity(self, activity, path=None):
        self.current_activity = activity
        self.stack.set_visible_child(activity.widget)
        if(activity.header_widget != None):
            self.header_stack.set_visible_child(activity.header_widget)

        back = self.builder.get_object("back_button")
        back.set_sensitive(True)

        menu = self.builder.get_object("menu_button")
        menu.set_popover(activity.menu_popover)

        activity.on_open(path)


    def go_back(self, sender):
        if(self.current_activity.on_exit()):
            self.hide_message()
            back = self.builder.get_object("back_button")
            back.set_sensitive(False)

            menu = self.builder.get_object("menu_button")
            menu.set_popover(None)

            self.header_stack.set_visible_child(self.no_header)
            self.stack.set_visible_child_name("init")

    def quit(self, sender, item):
        self.window.close()

    def on_about(self, sender, item):
        self.builder.get_object('about_dialog').run()
        self.builder.get_object('about_dialog').hide()

    def show_message(self, title, subtitle, ongoing=False, progressive=False):
        self.builder.get_object('info_title').set_text(title)
        self.builder.get_object('info_subtitle').set_text(subtitle)
        if(ongoing):
            self.builder.get_object('info_spinner').start()
        else:
            self.builder.get_object('info_spinner').stop()
        self.builder.get_object('info_progress').set_visible(progressive)
        self.builder.get_object('info_reveal').set_reveal_child(True)
        self.builder.get_object('info_bar').set_show_close_button(not ongoing)

    def hide_message(self):
        self.builder.get_object('info_reveal').set_reveal_child(False)

    def update_message_progress(self, step, steps):
        self.builder.get_object('info_progress').set_fraction(float(step)/float(steps))

    def on_message_close(self, sender, arg):
        self.hide_message()

    def switch_activity_id(self, activity_id, file=None):
        self.current_activity.on_exit()
        for activity in self.activities:
            if(activity.id == activity_id):
                self.switch_activity(activity, file)
                return True

        return False




## MAIN ##
if __name__ == '__main__':
     app = App()
     app.run(sys.argv)