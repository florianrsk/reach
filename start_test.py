#!/usr/bin/env python3
"""
Start Phase 1 testing - launches backend and runs validation tests
"""

import sys
import os
import subprocess
import time
import requests
import json


def check_mongodb():
    """Check if MongoDB is running"""
    print("Checking MongoDB connection...")
    try:
        import pymongo

        client = pymongo.MongoClient(
            "mongodb://localhost:27017", serverSelectionTimeoutMS=3000
        )
        client.server_info()
        print("SUCCESS: MongoDB is running and accessible")
        return True
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        print("\nTo start MongoDB:")
        print("1. Using Docker (recommended):")
        print("   docker run -d -p 27017:27017 --name mongodb mongo:latest")
        print("\n2. Install MongoDB locally:")
        print("   Download from https://www.mongodb.com/try/download/community")
        print("   Start MongoDB service")
        return False


def start_backend():
    """Start the backend server"""
    print("\nStarting backend server...")

    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")

    # Start server in background
    try:
        # On Windows, we need to use start
        import platform

        if platform.system() == "Windows":
            proc = subprocess.Popen(
                ["python", "server.py"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        else:
            proc = subprocess.Popen(
                ["python", "server.py"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        # Give server time to start
        print("Waiting for server to start...")
        time.sleep(5)

        # Check if server is responding
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print(f"SUCCESS: Backend server is running at http://localhost:8000")
                print(f"   Health status: {response.json().get('status', 'unknown')}")
                return proc
            else:
                print(f"ERROR: Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Server not responding: {e}")

        return None
    except Exception as e:
        print(f"ERROR: Failed to start backend: {e}")
        return None


def run_validation_tests():
    """Run Phase 1 validation tests"""
    print("\nRunning Phase 1 validation tests...")

    try:
        # Run the validation test script
        test_script = os.path.join(os.path.dirname(__file__), "test_phase1_local.py")
        result = subprocess.run(
            [sys.executable, test_script], capture_output=True, text=True, timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("Phase 1: Security & Stability Foundation - Testing")
    print("=" * 60)

    # Step 1: Check MongoDB
    if not check_mongodb():
        return 1

    # Step 2: Start backend
    backend_proc = start_backend()
    if not backend_proc:
        return 1

    # Step 3: Run tests
    success = run_validation_tests()

    # Step 4: Cleanup
    print("\nCleaning up...")
    if backend_proc:
        backend_proc.terminate()
        backend_proc.wait(timeout=5)

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Phase 1 testing completed successfully!")
        print("\n📊 Next steps:")
        print("1. Review test results in 'phase1_test_results.json'")
        print("2. Check backend logs for structured logging")
        print("3. Test the frontend at http://localhost:3000")
        print("4. Proceed to Phase 2: Performance & Scalability")
    else:
        print("ERROR: Phase 1 testing failed")
        print("\n🔧 Troubleshooting:")
        print("1. Check MongoDB is running: mongosh --eval 'db.adminCommand(\"ping\")'")
        print("2. Check server logs for errors")
        print("3. Verify .env file configuration")
        print("4. Run manual tests with curl")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
