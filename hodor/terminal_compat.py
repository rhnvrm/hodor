"""Terminal compatibility utilities for OpenHands SDK.

This module provides compatibility patches for OpenHands SDK terminal implementations
to work correctly on systems where bash is not located at /bin/bash (e.g., NixOS).

TODO: Remove this module once OpenHands SDK supports configurable bash paths.
      Tracking issue: https://github.com/OpenHands/agent-sdk/issues/TBD
"""

import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def patch_subprocess_terminal_for_nixos() -> bool:
    """Patch SubprocessTerminal to use discovered bash path instead of hardcoded /bin/bash.

    This is a temporary workaround for systems like NixOS where bash is not at /bin/bash.
    The patch will only be applied if:
    1. Bash is not found at /bin/bash
    2. Bash is found elsewhere via shutil.which()

    Returns:
        bool: True if patch was applied, False if not needed or failed

    Note:
        This function monkey-patches openhands.tools.terminal.terminal.subprocess_terminal.
        It should be called before creating any Conversation instances.

    Example:
        >>> from hodor.terminal_compat import patch_subprocess_terminal_for_nixos
        >>> patch_subprocess_terminal_for_nixos()  # Apply patch if needed
        >>> conversation = Conversation(agent=agent, workspace=workspace)  # Now works on NixOS
    """
    # Check if patch is needed
    if Path("/bin/bash").exists():
        logger.debug("Bash found at /bin/bash, no patching needed")
        return False

    bash_path = shutil.which("bash")
    if not bash_path:
        logger.warning("Bash not found in PATH, cannot apply compatibility patch")
        return False

    logger.info(f"Applying NixOS compatibility patch: bash at {bash_path}")

    try:
        from openhands.tools.terminal.terminal import subprocess_terminal

        # Store original for potential restoration
        original_initialize = subprocess_terminal.SubprocessTerminal.initialize

        def patched_initialize(self: Any) -> None:
            """Patched initialize() that uses dynamically discovered bash path.

            This implementation mirrors the original SubprocessTerminal.initialize()
            but uses the discovered bash_path instead of hardcoded /bin/bash.
            """
            if self._initialized:
                return

            import pty

            # Inherit environment variables from the parent process
            env = os.environ.copy()
            env["PS1"] = self.PS1
            env["PS2"] = ""
            env["TERM"] = "xterm-256color"

            # Use dynamically detected bash path instead of hardcoded /bin/bash
            bash_cmd = [bash_path, "-i"]

            # Create a PTY; give the slave to the child, keep the master
            master_fd, slave_fd = pty.openpty()

            logger.debug("Initializing PTY terminal with: %s", " ".join(bash_cmd))

            try:
                # Spawn bash process
                self.process = subprocess.Popen(
                    bash_cmd,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=self.work_dir,
                    env=env,
                    text=False,  # bytes I/O
                    bufsize=0,
                    close_fds=True,
                )

                # Store PTY master file descriptor
                self._pty_master_fd = master_fd
                os.close(slave_fd)

                # Start reader thread to consume output
                self.reader_thread = threading.Thread(
                    target=self._read_output_loop, daemon=True, name="PTYReader"
                )
                self.reader_thread.start()

                # Wait for bash to be ready
                self._wait_for_prompt_or_sentinel()
                self._initialized = True

            except Exception as e:
                # Cleanup on error
                os.close(master_fd)
                if self._pty_master_fd is not None:
                    try:
                        os.close(self._pty_master_fd)
                    except OSError:
                        pass
                if self.process:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                raise RuntimeError(f"Failed to initialize PTY terminal: {e}") from e

        # Apply the patch
        subprocess_terminal.SubprocessTerminal.initialize = patched_initialize

        # Store reference to original for potential restoration
        if not hasattr(subprocess_terminal, "_original_initialize"):
            subprocess_terminal._original_initialize = original_initialize

        logger.info(f"Successfully patched SubprocessTerminal (bash: {bash_path})")
        return True

    except Exception as e:
        logger.error(f"Failed to apply terminal compatibility patch: {e}")
        logger.warning("May encounter '/bin/bash not found' errors on NixOS")
        return False


def restore_subprocess_terminal() -> bool:
    """Restore SubprocessTerminal to its original implementation.

    This function reverses the patch applied by patch_subprocess_terminal_for_nixos().
    Useful for testing or if the patch causes issues.

    Returns:
        bool: True if successfully restored, False otherwise
    """
    try:
        from openhands.tools.terminal.terminal import subprocess_terminal

        if hasattr(subprocess_terminal, "_original_initialize"):
            subprocess_terminal.SubprocessTerminal.initialize = subprocess_terminal._original_initialize
            delattr(subprocess_terminal, "_original_initialize")
            logger.info("Restored original SubprocessTerminal implementation")
            return True
        else:
            logger.debug("No patch to restore (terminal not patched)")
            return False

    except Exception as e:
        logger.error(f"Failed to restore terminal: {e}")
        return False
