# start_apps.py - Launch both applications

import subprocess
import sys
import time
import webbrowser
from threading import Thread


def start_dashboard_app():
    """Start the dashboard application"""
    try:
        print("🚀 Starting Dashboard Application...")
        subprocess.run([sys.executable, "dashboard_app.py"], check=True)
    except KeyboardInterrupt:
        print("📊 Dashboard application stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")


def start_map_app():
    """Start the map application"""
    try:
        print("🚀 Starting Map Application...")
        subprocess.run([sys.executable, "map_app.py"], check=True)
    except KeyboardInterrupt:
        print("🗺️ Map application stopped")
    except Exception as e:
        print(f"❌ Error starting map: {e}")


def open_browsers():
    """Open both applications in browser after delay"""
    time.sleep(3)  # Wait for servers to start

    try:
        print("🌐 Opening Dashboard in browser...")
        webbrowser.open("http://127.0.0.1:8050")

        time.sleep(1)

        print("🌐 Opening Map in browser...")
        webbrowser.open("http://127.0.0.1:5002")

    except Exception as e:
        print(f"❌ Error opening browsers: {e}")


def main():
    """Main function to start both applications"""
    print("=" * 70)
    print("🚀 PROBENPLANUNG - DUAL APPLICATION LAUNCHER")
    print("=" * 70)
    print()
    print("📊 Dashboard Application: http://127.0.0.1:8050")
    print("🗺️ Map Application:       http://127.0.0.1:5002")
    print()
    print("Both applications will start in separate processes...")
    print("Press Ctrl+C to stop both applications")
    print("=" * 70)

    try:
        # Start browser opening in background
        browser_thread = Thread(target=open_browsers, daemon=True)
        browser_thread.start()

        # Start both applications
        dashboard_thread = Thread(target=start_dashboard_app, daemon=True)
        map_thread = Thread(target=start_map_app, daemon=True)

        dashboard_thread.start()
        time.sleep(2)  # Stagger startup
        map_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping all applications...")
        print("✅ Applications stopped successfully")


if __name__ == "__main__":
    main()