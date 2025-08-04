# Enable automatic handling of Qt's Meta-Object Compiler (MOC),
# User Interface Compiler (UIC), and Resource Compiler (RCC).
# This is the modern way to handle Qt's build requirements in CMake.
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Define the executable for our C++ GUI.
# On Apple platforms, MACOSX_BUNDLE creates a .app bundle.
add_executable(mpr_photo_editor_gui MACOSX_BUNDLE
    src/main.cpp
)

# Link the executable against the Qt6 Widgets library.
target_link_libraries(mpr_photo_editor_gui PRIVATE Qt6::Widgets)