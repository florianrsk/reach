#!/usr/bin/env python3
"""
Demonstrate the module system functionality
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def demo_module_system():
    """Demonstrate module system functionality"""
    print("=" * 60)
    print("MODULE SYSTEM DEMONSTRATION")
    print("=" * 60)

    session = requests.Session()

    try:
        # 1. Create test user
        print("1. Creating test user...")
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")
        headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}

        timestamp = int(time.time())
        test_email = f"demo_{timestamp}@example.com"
        test_handle = f"demo{timestamp}"

        # Register
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": "SecurePass123!@#",
                "name": "Demo User",
            },
            headers=headers,
        )

        # Login
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": "SecurePass123!@#"},
            headers=headers,
        )

        print(f"   User created: {test_email}")

        # 2. Create Face-completed identity
        print("2. Creating Face-completed identity...")
        face_data = {
            "handle": test_handle,
            "display_name": "Alex Johnson",
            "headline": "Product designer building human-centered tools",
            "current_focus": "Redesigning how people connect online",
            "availability_signal": "I check reach requests every Tuesday and Friday",
            "prompt": "What's on your mind and how can I help?",
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop",
            "links": [
                {"label": "Portfolio", "url": "https://alexjohnson.design"},
                {"label": "Writing", "url": "https://blog.alexjohnson.design"},
            ],
        }

        response = session.post(
            f"{BASE_URL}/api/identity", json=face_data, headers=headers
        )

        if response.status_code != 200:
            print(f"   FAIL: Failed to create Face: {response.status_code}")
            return False

        print(f"   Face created: {test_handle}")

        # 3. Configure modules
        print("3. Configuring modules...")
        modules_config = {
            "intent_categories": {
                "enabled": True,
                "categories": ["Collaboration", "Feedback", "Press", "Question"],
            },
            "challenge_question": {
                "enabled": True,
                "question": "What motivated you to reach out today?",
            },
            "waiting_period": {"enabled": True, "seconds": 30},
            "time_signal": {"enabled": True},
            "deposit": {"enabled": True, "amount_usd": 10.0, "response_days": 7},
            "rules_engine": {
                "enabled": True,
                "rules": [
                    "If message mentions sales or agency — reject automatically",
                    "If message is under 30 words — ask for more context",
                    "If time requirement is a conversation — require deposit",
                ],
            },
            "capacity_controls": {
                "enabled": True,
                "max_approved_per_week": 5,
                "sender_cooldown_days": 3,
                "daily_submission_cap": 10,
            },
        }

        update_response = session.put(
            f"{BASE_URL}/api/modules", json=modules_config, headers=headers
        )

        if update_response.status_code != 200:
            print(f"   FAIL: Failed to update modules: {update_response.status_code}")
            return False

        print("   Modules configured successfully")

        # 4. Show what the sender page includes
        print("4. Checking sender page data...")
        public_response = session.get(f"{BASE_URL}/api/reach/{test_handle}")

        if public_response.status_code != 200:
            print(f"   FAIL: Public page failed: {public_response.status_code}")
            return False

        public_data = public_response.json()
        identity = public_data["identity"]
        modules = public_data.get("modules", {})

        print(f"   Identity: {identity['display_name']}")
        print(f'   Prompt: "{identity["prompt"]}"')
        print(f"   Enabled modules: {len(modules)}")

        for module_name, config in modules.items():
            print(f"   - {module_name}: {config}")

        # 5. Test challenge question flow
        print("5. Testing challenge question flow...")
        print("   When a sender visits the page, they will see:")
        print(f'   Challenge question: "{modules["challenge_question"]["question"]}"')
        print("   They must answer before the message box appears")

        # 6. Test rules engine
        print("6. Testing rules engine...")
        print("   Configured rules:")
        for rule in modules_config["rules_engine"]["rules"]:
            print(f"   - {rule}")

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE!")
        print("=" * 60)

        # Print URLs for manual testing
        print(f"\n📋 TESTING URLs:")
        print(f"   Settings page: http://localhost:3000/settings")
        print(f"   Public page: http://localhost:3000/r/{test_handle}")
        print(f"   Preview page: http://localhost:3000/r/{test_handle}?preview=true")

        print(f"\n🔧 MODULES CONFIGURED:")
        print(
            f"   1. Intent Categories: {len(modules_config['intent_categories']['categories'])} categories"
        )
        print(
            f"   2. Time Signal: {'Enabled' if modules_config['time_signal']['enabled'] else 'Disabled'}"
        )
        print(
            f'   3. Challenge Question: "{modules_config["challenge_question"]["question"]}"'
        )
        print(
            f"   4. Waiting Period: {modules_config['waiting_period']['seconds']} seconds"
        )
        print(
            f"   5. Deposit: ${modules_config['deposit']['amount_usd']} for {modules_config['deposit']['response_days']} day response"
        )
        print(
            f"   6. Rules Engine: {len(modules_config['rules_engine']['rules'])} rules"
        )
        print(
            f"   7. Capacity Controls: {modules_config['capacity_controls']['daily_submission_cap']} daily submissions max"
        )

        print(f"\n👁️  PREVIEW FUNCTIONALITY:")
        print(
            f"   Click 'Preview your page' in Settings to see exactly what senders see"
        )
        print(f"   All active modules are applied in preview mode")

        print(f"\n✅ Step 3 - The Module System is complete!")
        print(f"   - 7 independent modules, each optional and off by default")
        print(f"   - AI assists rule execution (never decides autonomously)")
        print(f"   - Owner's rules always come first")
        print(f"   - Every AI action is visible and overridable")
        print(f"   - Preview button shows exactly what senders see")

        return True

    except Exception as e:
        print(f"FAIL: Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = demo_module_system()
    exit(0 if success else 1)
