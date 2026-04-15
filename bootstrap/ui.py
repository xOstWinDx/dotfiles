"""UI layer with Rich support and graceful fallback to plain CLI."""

import sys
from typing import Any, Optional

# Try to import Rich, with graceful fallback
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm, PromptType
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class UIBackend:
    """UI backend - Rich if available, plain text fallback otherwise."""
    
    def __init__(self):
        self.rich = RICH_AVAILABLE
        self._console: Optional[Any] = None
        
        if self.rich:
            self._console = Console()
    
    @property
    def console(self) -> Any:
        if not self.rich:
            raise RuntimeError("Rich is not available")
        return self._console
    
    def is_rich_available(self) -> bool:
        """Check if Rich is available."""
        return self.rich
    
    def print(self, *args, **kwargs):
        """Print with optional Rich formatting."""
        if self.rich:
            rprint(*args, **kwargs)
        else:
            # Plain text fallback
            print(*args)
    
    def print_header(self, text: str):
        """Print a section header."""
        if self.rich:
            rprint(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
            rprint(f"[bold cyan]  {text}[/bold cyan]")
            rprint(f"[bold cyan]{'=' * 60}[/bold cyan]")
        else:
            print(f"\n{'=' * 60}")
            print(f"  {text}")
            print(f"{'=' * 60}")
    
    def print_success(self, text: str):
        """Print success message."""
        if self.rich:
            rprint(f"[green]✓[/green] {text}")
        else:
            print(f"[OK] {text}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        if self.rich:
            rprint(f"[yellow]⚠[/yellow] {text}")
        else:
            print(f"[WARN] {text}")
    
    def print_error(self, text: str):
        """Print error message."""
        if self.rich:
            rprint(f"[red]✗[/red] {text}")
        else:
            print(f"[ERROR] {text}")
    
    def print_info(self, text: str):
        """Print info message."""
        if self.rich:
            rprint(f"[blue]ℹ[/blue] {text}")
        else:
            print(f"[INFO] {text}")
    
    def print_dry_run(self, text: str):
        """Print dry run message."""
        if self.rich:
            rprint(f"[dim]{text}[/dim]")
        else:
            print(f"[DRY RUN] {text}")
    
    def create_table(self, title: str = "") -> Any:
        """Create a table (Rich Table or placeholder)."""
        if self.rich:
            table = Table(title=title, show_header=True, header_style="bold cyan")
            return table
        else:
            # Return a simple dict-based table for plain mode
            return {"title": title, "rows": [], "headers": []}
    
    def table_add_column(self, table: Any, title: str, style: str = ""):
        """Add a column to a table."""
        if self.rich:
            table.add_column(title, style=style)
        else:
            table["headers"].append(title)
    
    def table_add_row(self, table: Any, *columns: str):
        """Add a row to a table."""
        if self.rich:
            table.add_row(*columns)
        else:
            table["rows"].append(list(columns))
    
    def print_table(self, table: Any):
        """Print a table."""
        if self.rich:
            self.console.print(table)
        else:
            # Simple plain text table
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if table.get("title"):
                print(f"\n{table['title']}")
            print("  " + " | ".join(str(h) for h in headers))
            print("  " + "-" * (len(" | ".join(str(h) for h in headers))))
            for row in rows:
                print("  " + " | ".join(str(c) for c in row))
    
    def create_progress(self) -> Any:
        """Create a progress bar."""
        if self.rich:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            )
        else:
            # Return a simple progress placeholder
            return SimpleProgress()
    
    def prompt_yes_no(self, question: str, default: bool = False) -> bool:
        """Prompt user with yes/no question."""
        if self.rich:
            return Confirm.ask(question, default=default)
        else:
            suffix = " [Y/n]" if default else " [y/N]"
            while True:
                response = input(f"{question}{suffix}: ").strip().lower()
                if not response:
                    return default
                if response in ("y", "yes"):
                    return True
                if response in ("n", "no"):
                    return False
                print("Please answer 'y' or 'n'")
    
    def prompt_choice(self, question: str, options: list[str], default: Optional[int] = None) -> Optional[int]:
        """Prompt user to choose from a list of options."""
        if self.rich:
            choice = Prompt.ask(
                question,
                choices=[str(i) for i in range(len(options))],
                default=str(default) if default is not None else None,
            )
            return int(choice)
        else:
            print(f"\n{question}")
            for i, opt in enumerate(options):
                print(f"  {i}. {opt}")
            
            if default is not None:
                prompt = f"Select (default {default}): "
            else:
                prompt = "Select: "
            
            while True:
                response = input(prompt).strip()
                if not response and default is not None:
                    return default
                try:
                    idx = int(response)
                    if 0 <= idx < len(options):
                        return idx
                except ValueError:
                    pass
                print(f"Please enter a number between 0 and {len(options) - 1}")
    
    def prompt_text(self, question: str, default: str = "", password: bool = False) -> str:
        """Prompt user for text input."""
        if self.rich and not password:
            return Prompt.ask(question, default=default)
        else:
            if default:
                prompt = f"{question} [{default}]: "
            else:
                prompt = f"{question}: "
            
            response = input(prompt).strip()
            return response if response else default


class SimpleProgress:
    """Simple progress fallback for non-Rich environments."""
    
    def __init__(self):
        self.tasks = {}
        self.current = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def add_task(self, description: str, total: int = 100) -> int:
        task_id = self.current
        self.tasks[task_id] = {"description": description, "total": total, "current": 0}
        self.current += 1
        return task_id
    
    def update(self, task_id: int, advance: int = 1, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id]["current"] += advance
            total = self.tasks[task_id]["total"]
            current = self.tasks[task_id]["current"]
            desc = kwargs.get("description", self.tasks[task_id]["description"])
            pct = min(100, int(current / total * 100))
            print(f"\r{desc}: {pct}%", end="", flush=True)
            if current >= total:
                print()  # Newline on completion
    
    def start(self):
        pass
    
    def stop(self):
        print()  # Final newline


# Global UI instance
_ui: Optional[UIBackend] = None


def get_ui() -> UIBackend:
    """Get the global UI backend instance."""
    global _ui
    if _ui is None:
        _ui = UIBackend()
    return _ui


def is_rich_available() -> bool:
    """Check if Rich is available."""
    return RICH_AVAILABLE


def detect_ui_capabilities() -> dict:
    """Detect UI capabilities of the current environment."""
    ui = get_ui()
    
    capabilities = {
        "rich_available": ui.is_rich_available(),
        "is_interactive": sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False,
        "supports_colors": False,
    }
    
    if ui.is_rich_available():
        capabilities["supports_colors"] = True
        capabilities["supports_tables"] = True
        capabilities["supports_progress"] = True
        capabilities["ui_level"] = "rich"
    else:
        capabilities["supports_colors"] = True  # ANSI codes always available in terminals
        capabilities["supports_tables"] = False
        capabilities["supports_progress"] = False
        capabilities["ui_level"] = "plain"
    
    return capabilities
