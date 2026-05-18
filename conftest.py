import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "headless": True,
        "slow_mo" : 1000,
    }

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width" : 1280,
            "height": 720
        },
        "record_video_dir": "reports/videos",
        "record_video_size": {
            "width": 1280,
            "height": 720
        }
    }
