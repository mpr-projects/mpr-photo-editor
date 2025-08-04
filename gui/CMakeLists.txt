# Enable automatic handling of Qt's Meta-Object Compiler (MOC),
# User Interface Compiler (UIC), and Resource Compiler (RCC).
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Define the executable for our C++ GUI.
# On Apple platforms, MACOSX_BUNDLE creates a .app bundle.
add_executable(PhotoEditor MACOSX_BUNDLE
    src/main.cpp
    ${MPO_CORE_LOGIC_SOURCES} # Add core logic sources directly
)

# The GUI needs access to the core logic and LibRaw headers.
target_include_directories(PhotoEditor PRIVATE
    ${MPO_CORE_LOGIC_INCLUDE_DIRS}
    ${PC_LIBRAW_INCLUDE_DIRS}
)

# Link the executable against the Qt6 Widgets library.
target_link_libraries(PhotoEditor PRIVATE
    Qt6::Widgets
    ${PC_LIBRAW_LINK_LIBRARIES} # Link against LibRaw directly
)

# Copy application resources to the build directory so linuxdeployqt can find them.
if(UNIX AND NOT APPLE)
    file(COPY
        "${CMAKE_CURRENT_SOURCE_DIR}/resources/PhotoEditor.desktop"
        "${CMAKE_CURRENT_SOURCE_DIR}/resources/PhotoEditor.png"
        DESTINATION "${CMAKE_CURRENT_BINARY_DIR}"
    )
endif()
