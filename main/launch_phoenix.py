
import sys
import time

import phoenix as px

try:
    # Launch Phoenix with pharmaceutical project settings
    session = px.launch_app(
        host="localhost",
        port=6006,
        # Set project name for pharmaceutical compliance
        # project_name="pharmaceutical_test_generation",
    )

    print(f"Phoenix launched successfully at: {session.url}")
    print("Phoenix is now ready for pharmaceutical workflow tracing")
    print("Press Ctrl+C to stop Phoenix")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPhoenix shutdown requested")
        sys.exit(0)

except Exception as e:
    print(f"Failed to launch Phoenix: {e}")
    sys.exit(1)
