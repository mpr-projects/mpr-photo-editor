#include <QApplication>
#include <QPushButton>
#include <QTimer>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    // Explicitly set the application name. This helps window managers (especially
    // on Wayland) correctly identify the application, preventing the window title
    // from defaulting to the executable name (e.g., "AppRun.wrapped").
    app.setApplicationName("PhotoEditor");
    app.setApplicationDisplayName("MPR Photo Editor");

    // Check for a smoke test argument to allow for non-interactive testing.
    if (app.arguments().contains("--smoke-test")) {
        // If the flag is present, quit the application after a short delay.
        // This is enough time for it to initialize and reveal any startup errors.
        QTimer::singleShot(500, &app, &QApplication::quit);
    }

    QPushButton button("Hello from C++ GUI!");
    button.resize(200, 100);
    button.show();

    return app.exec();
}
