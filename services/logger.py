from rich.console import Console

console = Console()


def info(message):
    console.print(f"[cyan]{message}[/cyan]")


def success(message):
    console.print(f"[green]{message}[/green]")


def warning(message):
    console.print(f"[yellow]{message}[/yellow]")


def error(message):
    console.print(f"[red]{message}[/red]")