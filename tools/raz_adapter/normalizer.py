"""Book name normalization for matching across resource types."""

import re


def normalize_name(name: str) -> str:
    """
    Normalize book name for matching.

    Args:
        name: Raw filename like "01 arctic animals.mp3" or
              "E-01Arctic Animals.mp4"

    Returns:
        Normalized lowercase string like "arcticanimals"

    Examples:
        >>> normalize_name("01 arctic animals.mp3")
        'arcticanimals'
        >>> normalize_name("E-01Arctic Animals.mp4")
        'arcticanimals'
        >>> normalize_name("04places plants and animals live.mp3")
        'placesplantsandanimalslive'
    """
    # Remove file extension
    name = re.sub(r"\.[^.]+$", "", name)

    # Remove Chinese suffixes like "-公众号-Lily的育儿百宝箱(...)"
    name = re.sub(r"-(公众号|微信).*$", "", name)

    # Remove leading numbers and separators: "01 ", "E-01", "E-02", "E-01Arctic"
    name = re.sub(r"^[A-Z]?-?\d+[\s\-]*", "", name)

    # Remove non-alphanumeric (except spaces for now)
    name = re.sub(r"[^\w\s]", "", name)

    # Replace underscores with spaces (W level audio uses _ as separator)
    name = name.replace("_", " ")

    # Normalize to lowercase
    name = name.lower()

    # Remove leading digits that might remain
    name = re.sub(r"^\d+", "", name)

    # Remove "book X " prefix (e.g., "Book 5 Let a Smiley Face..." -> "Let a Smiley Face...")
    name = re.sub(r"^book\s+\d+\s+", "", name)

    # Replace "&" with "and" for matching (PDF uses "&", audio uses "and")
    name = name.replace("&", "and")

    # Compress whitespace
    name = re.sub(r"\s+", "", name)

    return name


def to_kebab_case(title: str) -> str:
    """
    Convert title to kebab-case for IDs.

    Args:
        title: Book title like "Arctic Animals"

    Returns:
        kebab-case string like "arctic-animals"
    """
    # Remove non-alphanumeric except spaces
    name = re.sub(r"[^\w\s]", "", title)
    # Normalize spaces and convert to lowercase
    name = re.sub(r"\s+", "-", name.strip()).lower()
    # Remove leading/trailing dashes
    name = name.strip("-")
    return name


def to_title_case(name: str) -> str:
    """
    Convert normalized name to title case for display.

    Args:
        name: String like "arctic animals"

    Returns:
        Title case string like "Arctic Animals"
    """
    # Convert dashes to spaces first
    name = name.replace("-", " ")
    # First normalize to remove any remaining artifacts
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name.strip())
    return name.title()
