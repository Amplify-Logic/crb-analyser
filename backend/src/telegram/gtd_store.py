"""
GTD Store — Markdown-based Getting Things Done data store.

Based on David Allen's GTD methodology:
- Capture: everything into inbox
- Clarify: decide what each item means
- Organize: file into the right bucket
- Reflect: regular reviews
- Engage: choose actions by context/time/energy/priority

Seven lists: Inbox, Projects, Next Actions, Waiting For,
Calendar, Someday/Maybe, Reference
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class GTDStore:
    """Markdown-backed GTD task management."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Ensure all list files exist
        for filename in [
            "inbox.md",
            "projects.md",
            "next-actions.md",
            "waiting-for.md",
            "calendar.md",
            "someday-maybe.md",
            "ideas.md",
        ]:
            filepath = self.base_dir / filename
            if not filepath.exists():
                filepath.write_text(f"# {filename.replace('.md', '').replace('-', ' ').title()}\n\n")

        ref_dir = self.base_dir / "reference"
        ref_dir.mkdir(exist_ok=True)

    def _now_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    # =========================================================================
    # CAPTURE
    # =========================================================================

    def capture(self, text: str) -> None:
        """Add an item to the inbox for later clarification."""
        filepath = self.base_dir / "inbox.md"
        with open(filepath, "a") as f:
            f.write(f"- [ ] {text} _(captured {self._now_str()})_\n")

    def get_inbox(self) -> List[Dict[str, str]]:
        """Get all inbox items."""
        return self._parse_checklist(self.base_dir / "inbox.md")

    def clear_inbox_item(self, item_text: str) -> bool:
        """Remove an item from inbox (after clarifying/organizing it)."""
        return self._remove_item(self.base_dir / "inbox.md", item_text)

    # =========================================================================
    # NEXT ACTIONS (by context)
    # =========================================================================

    def add_next_action(self, text: str, context: str = "general") -> None:
        """Add a next action under a context (@calls, @errands, @computer, etc.)."""
        filepath = self.base_dir / "next-actions.md"
        content = filepath.read_text()

        context_header = f"## @{context}"
        if context_header not in content:
            content += f"\n{context_header}\n\n"

        # Insert after the context header
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip() == context_header:
                insert_idx = i + 1
                # Skip blank lines after header
                while insert_idx < len(lines) and lines[insert_idx].strip() == "":
                    insert_idx += 1
                break

        if insert_idx is not None:
            lines.insert(insert_idx, f"- [ ] {text} _(added {self._now_str()})_")
        else:
            lines.append(f"- [ ] {text} _(added {self._now_str()})_")

        filepath.write_text("\n".join(lines))

    def get_next_actions(self, context: Optional[str] = None) -> List[Dict[str, str]]:
        """Get next actions, optionally filtered by context."""
        filepath = self.base_dir / "next-actions.md"
        if not filepath.exists():
            return []

        content = filepath.read_text()
        if context:
            # Parse only the section under this context
            pattern = rf"## @{context}\n(.*?)(?=\n## |$)"
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                return []
            section = match.group(1)
            return self._parse_checklist_text(section)

        return self._parse_checklist(filepath)

    def complete_action(self, text: str) -> bool:
        """Mark a next action as complete."""
        filepath = self.base_dir / "next-actions.md"
        return self._check_item(filepath, text)

    # =========================================================================
    # PROJECTS
    # =========================================================================

    def add_project(self, name: str, next_action: Optional[str] = None) -> None:
        """Add a project with an optional first next action."""
        filepath = self.base_dir / "projects.md"
        with open(filepath, "a") as f:
            f.write(f"\n## {name}\n\n")
            f.write(f"_Created: {self._now_str()}_\n\n")
            if next_action:
                f.write(f"Next action: {next_action}\n")
                # Also add to next actions list
                self.add_next_action(f"[{name}] {next_action}", context="general")

    def get_projects(self) -> List[Dict[str, str]]:
        """Get all active projects."""
        filepath = self.base_dir / "projects.md"
        if not filepath.exists():
            return []

        content = filepath.read_text()
        projects = []
        for match in re.finditer(r"^## (.+)$", content, re.MULTILINE):
            projects.append({"name": match.group(1)})
        return projects

    # =========================================================================
    # WAITING FOR
    # =========================================================================

    def add_waiting_for(self, text: str, who: str) -> None:
        """Add an item to the waiting-for list."""
        filepath = self.base_dir / "waiting-for.md"
        with open(filepath, "a") as f:
            f.write(f"- [ ] {text} — waiting on: {who} _(added {self._now_str()})_\n")

    def get_waiting_for(self) -> List[Dict[str, str]]:
        """Get all waiting-for items."""
        return self._parse_checklist(self.base_dir / "waiting-for.md")

    # =========================================================================
    # SOMEDAY / MAYBE
    # =========================================================================

    def add_someday(self, text: str) -> None:
        """Add an item to someday/maybe."""
        filepath = self.base_dir / "someday-maybe.md"
        with open(filepath, "a") as f:
            f.write(f"- {text} _(added {self._now_str()})_\n")

    def get_someday(self) -> List[Dict[str, str]]:
        """Get someday/maybe items."""
        return self._parse_checklist(self.base_dir / "someday-maybe.md")

    # =========================================================================
    # IDEAS
    # =========================================================================

    def add_idea(self, text: str, tags: Optional[List[str]] = None) -> None:
        """Capture an idea."""
        filepath = self.base_dir / "ideas.md"
        tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
        with open(filepath, "a") as f:
            f.write(f"- {text} {tag_str} _(captured {self._now_str()})_\n")

    def get_ideas(self) -> List[Dict[str, str]]:
        """Get all captured ideas."""
        return self._parse_checklist(self.base_dir / "ideas.md")

    # =========================================================================
    # REVIEW
    # =========================================================================

    def get_review_summary(self) -> str:
        """Generate a review summary for reflection."""
        inbox = self.get_inbox()
        actions = self.get_next_actions()
        projects = self.get_projects()
        waiting = self.get_waiting_for()
        someday = self.get_someday()

        return (
            f"*GTD Review*\n\n"
            f"Inbox: {len(inbox)} items\n"
            f"Next Actions: {len(actions)} items\n"
            f"Projects: {len(projects)} active\n"
            f"Waiting For: {len(waiting)} items\n"
            f"Someday/Maybe: {len(someday)} items"
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _parse_checklist(self, filepath: Path) -> List[Dict[str, str]]:
        """Parse a markdown file for checklist items."""
        if not filepath.exists():
            return []
        return self._parse_checklist_text(filepath.read_text())

    def _parse_checklist_text(self, text: str) -> List[Dict[str, str]]:
        """Parse checklist items from text."""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]"):
                items.append({"text": line[6:].strip(), "done": False})
            elif line.startswith("- [x]"):
                items.append({"text": line[6:].strip(), "done": True})
            elif line.startswith("- ") and not line.startswith("- ["):
                items.append({"text": line[2:].strip(), "done": False})
        return items

    def _remove_item(self, filepath: Path, item_text: str) -> bool:
        """Remove an item containing the given text."""
        if not filepath.exists():
            return False
        content = filepath.read_text()
        lines = content.split("\n")
        new_lines = [l for l in lines if item_text not in l]
        if len(new_lines) == len(lines):
            return False
        filepath.write_text("\n".join(new_lines))
        return True

    def _check_item(self, filepath: Path, item_text: str) -> bool:
        """Mark a checklist item as done."""
        if not filepath.exists():
            return False
        content = filepath.read_text()
        if item_text not in content:
            return False
        content = content.replace(f"- [ ] {item_text}", f"- [x] {item_text}")
        filepath.write_text(content)
        return True
