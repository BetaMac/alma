import subprocess
import sys
import os
from pathlib import Path

def start_services():
    # Get the absolute path to the project root
    root_dir = Path(__file__).parent.absolute()
    backend_dir = root_dir / 'backend'
    frontend_dir = root_dir / 'frontend'

    # Command to run backend with specific host (using uvicorn)
    backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1"]
    
    # Command to run frontend
    frontend_cmd = ["npm", "run", "dev"]

    try:
        # Start backend
        print("Starting backend server...")
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=str(backend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        # Start frontend
        print("Starting frontend server...")
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=str(frontend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        print("\nBoth services are starting!")
        print("Frontend will be available at: http://localhost:3000")
        print("Backend will be available at: http://127.0.0.1:8000")
        print("\nPress Ctrl+C to stop both services...")

        # Wait for both processes
        backend_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        print("\nShutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Services stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_services()