"""
PDF Processing Constants

Centralized constants for PDF extraction, parsing, and processing.
Eliminates magic numbers and makes configuration more maintainable.
"""

# ============================================================================
# DPI (Dots Per Inch) Constants
# ============================================================================

# PDF standard DPI (PostScript points per inch)
# PDFs use 72 points per inch as the base unit
PDF_STANDARD_DPI = 72

# Default DPI for image rendering and OCR processing
# Higher DPI = better quality but slower processing
DEFAULT_PROCESSING_DPI = 200


# ============================================================================
# Coordinate Thresholds
# ============================================================================

# Default tolerance for word extraction (pdfplumber)
# Horizontal tolerance for grouping characters into words
DEFAULT_X_TOLERANCE = 3

# Vertical tolerance for grouping characters into words
DEFAULT_Y_TOLERANCE = 3

# Y-coordinate threshold for grouping lines
# Lines within this pixel distance are considered the same line
DEFAULT_LINE_Y_THRESHOLD = 10

# X-coordinate threshold for merging adjacent text
# Text within this pixel distance horizontally is merged
DEFAULT_WORD_X_THRESHOLD = 50

# Y-coordinate threshold for paragraph grouping
# Lines within this distance are grouped into same paragraph
DEFAULT_PARAGRAPH_Y_THRESHOLD = 25

# Tolerance for character-to-word coordinate matching
# Used when mapping individual characters to words for color extraction
CHAR_WORD_MATCH_TOLERANCE = 2


# ============================================================================
# Page Number Constants
# ============================================================================

# First page number (PDFs are 1-indexed)
PDF_FIRST_PAGE = 1

# Default last page of table of contents
DEFAULT_TOC_END_PAGE = 7

# Default first page of main content
DEFAULT_CONTENT_START_PAGE = 8


# ============================================================================
# Color Constants
# ============================================================================

# Maximum RGB color value (8-bit color)
RGB_MAX_VALUE = 255


# ============================================================================
# Sampling Limits
# ============================================================================

# Number of sample texts to extract for template matching
TEMPLATE_MATCH_SAMPLE_SIZE = 50

# Maximum number of answers in speech grammar list
# Browser compatibility limit
SPEECH_GRAMMAR_MAX_ANSWERS = 100

# Number of texts to show in debug output (TOC pages)
DEBUG_TOC_TEXT_LIMIT = 30

# Number of texts to show in debug output (content pages)
DEBUG_CONTENT_TEXT_LIMIT = 20

# Number of top texts to check for lecture titles
LECTURE_TITLE_CHECK_LIMIT = 50


# ============================================================================
# Progress Reporting
# ============================================================================

# Interval for progress logging (percentage)
# Log every 10% of completion
PROGRESS_LOG_INTERVAL_PERCENT = 10

# Page interval for periodic status logging
# Log every N pages during processing
PAGE_LOG_INTERVAL = 10


# ============================================================================
# Character Width Estimation
# ============================================================================

# Approximate pixel width per character
# Used for estimating text bounding boxes
APPROX_CHAR_WIDTH_PIXELS = 10


# ============================================================================
# Template Matching
# ============================================================================

# Number of pages to sample for template matching
TEMPLATE_MATCH_PAGE_SAMPLE = 5

# Default confidence threshold for template matching (0.0 - 1.0)
DEFAULT_TEMPLATE_CONFIDENCE_THRESHOLD = 0.85


# ============================================================================
# Pattern Constants
# ============================================================================

# Maximum lecture number to consider valid
# Prevents false positives from large numbers
MAX_VALID_LECTURE_NUMBER = 200

# Length threshold for non-lecture lines
# Lines longer than this are likely not headers
NON_LECTURE_LINE_MAX_LENGTH = 50

# Maximum length for concept title recognition
MAX_CONCEPT_TITLE_LENGTH = 20

# Minimum length for Korean text patterns
MIN_KOREAN_TEXT_LENGTH = 2

# Maximum word count for concept titles
MAX_CONCEPT_TITLE_WORDS = 3

# Minimum confidence for OCR results (0.0 - 1.0)
MIN_OCR_CONFIDENCE = 0.0

# Default confidence when not available
DEFAULT_CONFIDENCE = 0.8


# ============================================================================
# Debug Pages
# ============================================================================

# Page numbers to show detailed debug output
DEBUG_TOC_PAGES = [4, 5, 6]
DEBUG_CONTENT_PAGES = [8, 9, 10]
