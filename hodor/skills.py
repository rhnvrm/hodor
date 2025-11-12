"""Skill discovery and loading for repository-specific review guidelines.

This module implements the skills system documented in README.md and SKILLS.md,
enabling users to customize PR reviews with project-specific guidelines.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def discover_skills(workspace: Path) -> list[dict]:
    """Discover and load skills from workspace.

    Searches for skills in priority order:
    1. .cursorrules - Simple, single-file project guidelines
    2. agents.md or agent.md - Alternative single-file location
    3. .hodor/skills/*.md - Modular skills organized by topic

    All discovered files are loaded as "repository skills" (always active).

    Args:
        workspace: Path to the repository workspace

    Returns:
        List of skill dictionaries with 'name', 'content', and 'trigger' keys.
        Empty list if no skills found.

    Example:
        >>> workspace = Path("/tmp/my-repo")
        >>> skills = discover_skills(workspace)
        >>> print(f"Loaded {len(skills)} skill(s)")
    """
    skills = []

    # 1. Check .cursorrules (priority 1 - most common)
    cursorrules = workspace / ".cursorrules"
    if cursorrules.exists() and cursorrules.is_file():
        try:
            content = cursorrules.read_text(encoding="utf-8")
            skills.append({"name": ".cursorrules", "content": content, "trigger": None})
            logger.info("Found skill: .cursorrules")
        except Exception as e:
            logger.warning(f"Failed to read .cursorrules: {e}")

    # 2. Check agents.md / agent.md (priority 2 - alternative location)
    for filename in ["agents.md", "agent.md", "AGENTS.md"]:
        agents_file = workspace / filename
        if agents_file.exists() and agents_file.is_file():
            try:
                content = agents_file.read_text(encoding="utf-8")
                skills.append({"name": filename, "content": content, "trigger": None})
                logger.info(f"Found skill: {filename}")
                break  # Only load first match to avoid duplicates
            except Exception as e:
                logger.warning(f"Failed to read {filename}: {e}")

    # 3. Check .hodor/skills/*.md (priority 3 - modular organization)
    skills_dir = workspace / ".hodor" / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        skill_files = sorted(skills_dir.glob("*.md"))
        for skill_file in skill_files:
            try:
                content = skill_file.read_text(encoding="utf-8")
                skill_name = f".hodor/skills/{skill_file.name}"
                skills.append({"name": skill_name, "content": content, "trigger": None})
                logger.info(f"Found skill: {skill_name}")
            except Exception as e:
                logger.warning(f"Failed to read {skill_file}: {e}")

    # Log summary
    if skills:
        logger.info(f"Loaded {len(skills)} skill(s) from workspace")
    else:
        logger.debug("No skills found in workspace (checked .cursorrules, agents.md, .hodor/skills/)")

    return skills
