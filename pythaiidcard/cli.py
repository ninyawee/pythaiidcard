"""Command-line interface for Thai ID Card reader."""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typing_extensions import Annotated

from .exceptions import ThaiIDCardException
from .reader import ThaiIDCardReader, read_thai_id_card
from .utils import format_cid

app = typer.Typer(
    name="pythaiidcard",
    help="Thai National ID Card Reader - Read data from Thai ID cards using smart card readers",
    add_completion=False,
)
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def setup_logging(verbose: bool) -> None:
    """Setup logging based on verbosity."""
    if verbose:
        logging.getLogger("pythaiidcard").setLevel(logging.DEBUG)


@app.command("list-readers")
def list_readers(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
) -> None:
    """List all available smart card readers."""
    setup_logging(verbose)
    
    try:
        readers = ThaiIDCardReader.list_readers()
        
        if not readers:
            console.print("[red]No smart card readers found.[/red]")
            console.print("Please connect a smart card reader and try again.")
            raise typer.Exit(1)
        
        # Create table
        table = Table(title="Available Smart Card Readers", show_header=True)
        table.add_column("Index", style="cyan", width=6)
        table.add_column("Reader Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("ATR", style="dim")
        
        for reader in readers:
            status = "[green]Card Present[/green]" if reader.connected else "[dim]No Card[/dim]"
            atr = reader.atr if reader.atr else "-"
            table.add_row(
                str(reader.index),
                reader.name,
                status,
                atr
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing readers: {e}[/red]")
        raise typer.Exit(1)


@app.command("read")
def read_card(
    reader: Annotated[Optional[int], typer.Option("--reader", "-r", help="Reader index to use")] = None,
    format: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "text",
    save_photo: Annotated[Optional[Path], typer.Option("--save-photo", help="Path to save photo")] = None,
    no_photo: Annotated[bool, typer.Option("--no-photo", help="Skip reading photo data")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
) -> None:
    """Read data from a Thai National ID card."""
    setup_logging(verbose)
    
    if format not in ["text", "json"]:
        console.print(f"[red]Invalid format: {format}. Use 'text' or 'json'.[/red]")
        raise typer.Exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # Connect to card
            progress.add_task("Connecting to card reader...", total=None)
            card_reader = ThaiIDCardReader(reader_index=reader)
            card_reader.connect()
            
            # Read card data
            include_photo = not no_photo
            
            if include_photo:
                task = progress.add_task("Reading card data and photo...", total=20)
                
                def photo_progress(current: int, total: int):
                    progress.update(task, completed=current, description=f"Reading photo ({current}/{total})...")
                
                card = card_reader.read_card(include_photo=True, photo_progress_callback=photo_progress)
            else:
                progress.add_task("Reading card data...", total=None)
                card = card_reader.read_card(include_photo=False)
            
            card_reader.disconnect()
        
        # Handle photo saving
        if save_photo and card.photo:
            photo_path = card.save_photo(save_photo)
            console.print(f"[green]Photo saved to: {photo_path}[/green]")
        elif include_photo and card.photo and not save_photo:
            # Save with default name if photo was read
            photo_path = card.save_photo()
            console.print(f"[green]Photo saved to: {photo_path}[/green]")
        
        # Output results
        if format == "json":
            # Convert to dict and handle dates
            data = card.model_dump(exclude={"photo"})
            print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        else:
            # Text output with rich formatting
            table = Table(title=f"Thai National ID Card", show_header=False, box=None)
            table.add_column("Field", style="cyan", width=20)
            table.add_column("Value", style="white")
            
            # Add rows with formatted data
            table.add_row("CID", format_cid(card.cid))
            table.add_row("Thai Name", card.thai_fullname)
            table.add_row("English Name", card.english_fullname)
            table.add_row("Date of Birth", f"{card.date_of_birth.strftime('%Y-%m-%d')} (Age: {card.age})")
            table.add_row("Gender", card.gender_text)
            table.add_row("Address", card.address)
            table.add_row("Card Issuer", card.card_issuer)
            table.add_row("Issue Date", card.issue_date.strftime('%Y-%m-%d'))
            
            # Highlight expiry status
            expiry_text = card.expire_date.strftime('%Y-%m-%d')
            if card.is_expired:
                expiry_text = f"[red]{expiry_text} (EXPIRED)[/red]"
            else:
                days = card.days_until_expiry
                if days < 30:
                    expiry_text = f"[yellow]{expiry_text} (Expires in {days} days)[/yellow]"
                else:
                    expiry_text = f"{expiry_text} (Valid for {days} days)"
            
            table.add_row("Expire Date", expiry_text)
            
            if card.photo:
                table.add_row("Photo", f"[green]✓[/green] {len(card.photo):,} bytes")
            
            console.print(table)
        
    except ThaiIDCardException as e:
        console.print(f"[red]Card Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command("watch")
def watch_cards(
    reader: Annotated[Optional[int], typer.Option("--reader", "-r", help="Reader index to use")] = None,
    interval: Annotated[int, typer.Option("--interval", "-i", help="Check interval in seconds")] = 2,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
) -> None:
    """Continuously watch for card insertions and read them."""
    setup_logging(verbose)
    
    import time
    
    console.print("[cyan]Watching for Thai ID cards... Press Ctrl+C to stop.[/cyan]")
    
    last_cid = None
    card_reader = ThaiIDCardReader(reader_index=reader)
    
    try:
        while True:
            try:
                card_reader.connect()
                card = card_reader.read_card(include_photo=False)
                
                # Only show if it's a different card
                if card.cid != last_cid:
                    console.print(f"\n[green]Card detected![/green]")
                    console.print(f"CID: {format_cid(card.cid)}")
                    console.print(f"Name: {card.english_fullname}")
                    console.print(f"Thai Name: {card.thai_fullname}")
                    last_cid = card.cid
                
                card_reader.disconnect()
                
            except ThaiIDCardException:
                # No card or error reading
                if last_cid:
                    console.print("[yellow]Card removed[/yellow]")
                    last_cid = None
            except Exception as e:
                if verbose:
                    console.print(f"[dim]Error: {e}[/dim]")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching.[/yellow]")
        try:
            card_reader.disconnect()
        except:
            pass


@app.command("validate")
def validate_cid(
    cid: Annotated[str, typer.Argument(help="13-digit citizen ID to validate")],
) -> None:
    """Validate a Thai citizen ID number."""
    from .utils import validate_cid as validate_cid_func
    
    # Remove any dashes or spaces
    cid = cid.replace("-", "").replace(" ", "")
    
    if validate_cid_func(cid):
        console.print(f"[green]✓ Valid CID: {format_cid(cid)}[/green]")
    else:
        console.print(f"[red]✗ Invalid CID: {cid}[/red]")
        raise typer.Exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()