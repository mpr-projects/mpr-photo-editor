from dearpygui import dearpygui
from mpr_photo_editor.backend import invert_image

image_data = [128] * (100 * 100)  # Dummy grayscale image

def process_callback():
    global image_data
    result = invert_image(image_data, 100, 100)
    print("Image processed. First 10 pixels:", result[:10])

def launch_gui():
    dearpygui.create_context()

    with dearpygui.window(label="MPR Photo Editor"):
        dearpygui.add_button(label="Invert Image", callback=process_callback)

    dearpygui.create_viewport(title='MPR Photo Editor', width=800, height=600)
    dearpygui.setup_dearpygui()
    dearpygui.show_viewport()
    dearpygui.start_dearpygui()
    dearpygui.destroy_context()

def main():
    launch_gui()

if __name__ == "__main__":
    main()
