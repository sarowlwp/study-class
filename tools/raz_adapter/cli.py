"""Command-line interface for RAZ Resource Adapter."""

from pathlib import Path

import click
from tqdm import tqdm

from .scanner import ResourceScanner
from .matcher import ResourceMatcher
from .generator import BookGenerator
from .transcriber import WhisperTranscriber
from . import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """RAZ Resource Adapter - Convert resources to book.json format."""
    pass


@cli.command()
@click.option(
    "--level",
    required=True,
    help="Reading level to process (e.g., e, f, g)",
)
@click.option(
    "--resourcer-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("raz-resourcer"),
    help="Path to raz-resourcer directory",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("data/raz"),
    help="Output directory for generated books",
)
@click.option(
    "--model",
    default="small",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    help="Whisper model size",
)
@click.option(
    "--device",
    default="cpu",
    type=click.Choice(["cpu", "cuda"]),
    help="Device for transcription",
)
@click.option(
    "--skip-existing",
    is_flag=True,
    help="Skip books that already have book.json",
)
@click.option(
    "--on-duplicate",
    default="skip",
    type=click.Choice(["skip", "replace", "error"]),
    help="How to handle duplicate book names",
)
def process_level(
    level: str,
    resourcer_dir: Path,
    output_dir: Path,
    model: str,
    device: str,
    skip_existing: bool,
    on_duplicate: str,
):
    """Process all books for a reading level."""
    click.echo(f"Processing level {level.upper()}...")

    # Initialize scanner and find resources
    scanner = ResourceScanner(resourcer_dir)
    resources = scanner.scan_level(level)
    click.echo(f"Found {len(resources)} resources")

    # Match resources into books
    matcher = ResourceMatcher(resources)
    matched_books = matcher.match_books()
    click.echo(f"Matched {len(matched_books)} books")

    stats = matcher.get_match_stats()
    click.echo(f"  - With video: {stats['with_video']}")
    click.echo(f"  - Without video: {stats['without_video']}")

    if not matched_books:
        click.echo("No books to process")
        return

    # Initialize transcriber
    transcriber = WhisperTranscriber(model_size=model, device=device)

    # Initialize generator
    generator = BookGenerator(
        output_dir=output_dir,
        transcriber=transcriber,
        confidence_threshold=0.8
    )

    # Generate books with progress bar
    generated = []
    errors = []

    with tqdm(matched_books, desc="Generating books") as pbar:
        for book in pbar:
            pbar.set_postfix({"book": book.title[:20]})
            try:
                result = generator.generate(book, skip_existing=skip_existing)
                if result:
                    generated.append(book.title)
            except Exception as e:
                errors.append((book.title, str(e)))

    click.echo(f"\nGenerated {len(generated)} books")

    if errors:
        click.echo(f"Errors: {len(errors)}")
        for title, error in errors:
            click.echo(f"  - {title}: {error}")


@cli.command()
@click.option(
    "--audio",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to audio file",
)
@click.option(
    "--pdf",
    type=click.Path(exists=True, path_type=Path),
    help="Path to PDF file",
)
@click.option(
    "--video",
    type=click.Path(exists=True, path_type=Path),
    help="Path to video file",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory",
)
@click.option(
    "--title",
    required=True,
    help="Book title",
)
@click.option(
    "--level",
    required=True,
    help="Reading level",
)
@click.option(
    "--model",
    default="small",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    help="Whisper model size",
)
def process_single(
    audio: Path,
    pdf: Path,
    video: Path,
    output: Path,
    title: str,
    level: str,
    model: str,
):
    """Process a single book."""
    from .normalizer import to_kebab_case
    from .matcher import MatchedBook

    click.echo(f"Processing single book: {title}")

    # Create matched book
    book_id = to_kebab_case(title)
    matched = MatchedBook(
        normalized_name=title.lower(),
        title=title,
        book_id=book_id,
        level=level,
        pdf=pdf,
        audio=audio,
        video=video
    )

    # Initialize and run
    transcriber = WhisperTranscriber(model_size=model)
    generator = BookGenerator(
        output_dir=output.parent,
        transcriber=transcriber
    )

    result = generator.generate(matched)

    if result:
        click.echo(f"Generated: {result}")
    else:
        click.echo("Failed to generate book")


if __name__ == "__main__":
    cli()
