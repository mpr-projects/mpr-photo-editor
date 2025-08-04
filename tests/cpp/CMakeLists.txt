# Add a test that runs the C++ GUI in a special "smoke test" mode.
# This test will launch the GUI, let it run for a moment, and then the GUI
# will close itself. This verifies that the application can start, find its
# dependencies (like Qt and LibRaw), and initialize without crashing.
add_test(
    NAME GuiSmokeTest
    COMMAND $<TARGET_FILE:PhotoEditor> --smoke-test
    WORKING_DIRECTORY $<TARGET_FILE_DIR:PhotoEditor>
)

# Set a timeout as a safety measure, in case the application hangs.
set_tests_properties(GuiSmokeTest PROPERTIES TIMEOUT 10)
