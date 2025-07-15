# Gemma-3 OCR (OCR.Space)

Gemma-3 OCR is a web application that allows you to extract structured text from images and documents using Optical Character Recognition (OCR) powered by the OCR.Space API. The app is designed to be accessible, mobile-friendly, and easy to use.

## Features
- **Extract text from images and documents** (PNG, JPG, JPEG, PDF, DOCX, DOC)
- **Multi-language support** (50+ languages)
- **Image preprocessing**: Rotate, adjust brightness, contrast, and sharpness
- **Text structure analysis**: Detects headings, lists, tables, code blocks, and paragraphs
- **Download results** as Text, PDF, Word, or JSON
- **Share results** with a unique link
- **History**: Keeps a session-based history of your extractions
- **Accessibility**: High-contrast, keyboard navigation, screen reader support
- **Mobile-friendly**: Responsive design for all devices
- **Privacy**: No permanent data storage; all processing is temporary and secure

## Installation

1. **Clone the repository** (or download the files):
   ```bash
   git clone <repo-url>
   cd ai_engineering
   ```

2. **Install dependencies**:
   ```bash
   pip install streamlit requests pillow pandas
   ```

## Usage

1. **Run the app**:
   ```bash
   streamlit run serve.py
   ```

2. **Open your browser** to [http://localhost:8501](http://localhost:8501) (it should open automatically).

3. **How to use:**
   - Upload an image or document (max 1MB)
   - (Optionally) adjust image settings (rotate, brightness, contrast, sharpness)
   - Select the language of the text
   - Click **Extract Text**
   - View, download, or share the extracted text

## Privacy & Accessibility
- **No Data Storage**: Images and results are processed in-memory and not stored permanently.
- **Session-based History**: Your extraction history is only available in your browser session.
- **Accessibility**: Designed for keyboard navigation, screen readers, and high-contrast viewing.

## License
MIT License (or specify your license here)

## Issues & Feedback
For issues or suggestions, please [open an issue](https://github.com/patchy631/ai-engineering-hub/issues). 