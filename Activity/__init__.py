
class Activity:

    def __init__(self, stack, header_stack, builder, root, show_message, hide_message, update_message_progress, start_work, stop_work, switch_activity):
        self.widget = None
        self.stack = stack
        self.header_widget = None
        self.header_stack = header_stack
        self.menu_popover = None
        self.id = ""
        self.name = ""
        self.subtitle = ""
        self.builder = builder
        self.root = root
        self.show_message = show_message
        self.hide_message = hide_message
        self.update_message_progress = update_message_progress
        self.start_work = start_work
        self.stop_work = stop_work
        self.switch_activity = switch_activity

        self.on_init()

    def on_init(self):
        raise NotImplemented()

    def on_exit(self):
        return True

    def on_open(self, path):
        raise NotImplemented()
