"""Everything the website looks like: the page shell, shared components and one module per page (pages/).
website.py collects the data and runs the build; it never writes HTML itself."""
from .site import Site  # noqa: F401
