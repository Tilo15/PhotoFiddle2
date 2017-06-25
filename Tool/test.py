import Tool

class Test_Tool(Tool.Tool):
    def on_init(self):
        self.id = "TestTool"
        self.name = "Test Tool"
        self.icon_path = "ui/testtool.png"
        self.properties = [
            Tool.Property("header", "Test Tool", "Header", None, has_toggle=False, has_button=True, button_callback=None, button_label="Auto Contrast"),
            Tool.Property("value", "Value", "Slider", 50, max=100, min=0),
            Tool.Property("header", "Test Tool 2", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("value", "Value2", "Spin", 50, max=100, min=0),
            Tool.Property("header", "Test Tool 2", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("value", "Value3", "Toggle", True),
            Tool.Property("value", "Long Label", "Combo", 0, options=["Option1", "Option2", "Option3"])
        ]
