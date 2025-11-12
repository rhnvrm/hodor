"""Test fixtures and mocks for Hodor tests."""

import sys
import types
from unittest.mock import MagicMock


def _install_openhands_stub():
    """Provide lightweight stubs for OpenHands SDK modules so tests don't need real deps."""

    if "openhands" in sys.modules:
        return

    # Create mock modules
    openhands_module = types.ModuleType("openhands")
    sdk_module = types.ModuleType("openhands.sdk")
    conversation_module = types.ModuleType("openhands.sdk.conversation")
    tools_module = types.ModuleType("openhands.tools")
    tools_preset_module = types.ModuleType("openhands.tools.preset")
    tools_default_module = types.ModuleType("openhands.tools.preset.default")

    # Mock LLM class
    class MockLLM:
        def __init__(self, **kwargs):
            self.config = kwargs

    # Mock Agent class
    class MockAgent:
        def __init__(self, llm, cli_mode=True):
            self.llm = llm
            self.cli_mode = cli_mode

    # Mock Conversation class
    class MockConversation:
        def __init__(self, agent, workspace):
            self.agent = agent
            self.workspace = workspace
            self.state = MagicMock()
            self.state.events = []

        def send_message(self, message):
            pass

        def run(self):
            pass

    # Mock get_agent_final_response function
    def mock_get_agent_final_response(events):
        return "### Mock Review\n\nThis is a test review output from the mocked OpenHands agent."

    # Mock get_default_agent function
    def mock_get_default_agent(llm, cli_mode=True):
        return MockAgent(llm=llm, cli_mode=cli_mode)

    # Mock get_logger function
    def mock_get_logger(name):
        import logging

        return logging.getLogger(name)

    # Assign mocks to modules
    sdk_module.LLM = MockLLM
    sdk_module.Conversation = MockConversation
    sdk_module.get_logger = mock_get_logger

    conversation_module.get_agent_final_response = mock_get_agent_final_response

    tools_default_module.get_default_agent = mock_get_default_agent

    # Register modules
    sys.modules["openhands"] = openhands_module
    sys.modules["openhands.sdk"] = sdk_module
    sys.modules["openhands.sdk.conversation"] = conversation_module
    sys.modules["openhands.tools"] = tools_module
    sys.modules["openhands.tools.preset"] = tools_preset_module
    sys.modules["openhands.tools.preset.default"] = tools_default_module


# Install stubs before any hodor imports
_install_openhands_stub()
