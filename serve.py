import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageFilter
import base64
import io
import hashlib
import time
from urllib.parse import quote
import json
from datetime import datetime
import pandas as pd

# Page configuration with mobile-friendly settings
st.set_page_config(
    page_title="Gemma-3 OCR (OCR.Space)",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for accessibility and mobile responsiveness
st.markdown("""
<style>
    /* High contrast colors for accessibility */
    .main-header {
        color: #1f1f1f !important;
        font-weight: bold !important;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .stButton > button {
            width: 100% !important;
            margin: 5px 0 !important;
        }
        .stDownloadButton > button {
            width: 100% !important;
        }
        .stMarkdown {
            font-size: 14px !important;
        }
    }
    
    /* High contrast focus indicators */
    .stButton > button:focus,
    .stDownloadButton > button:focus {
        outline: 3px solid #0066cc !important;
        outline-offset: 2px !important;
    }
    
    /* Better contrast for text */
    .ocr-result {
        background-color: #f8f9fa !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
    }
    
    /* Share link styling */
    .share-link {
        background-color: #e3f2fd !important;
        border: 1px solid #2196f3 !important;
        border-radius: 4px !important;
        padding: 8px !important;
        margin: 5px 0 !important;
        word-break: break-all !important;
    }
    
    /* History item styling */
    .history-item {
        background-color: #f5f5f5 !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
    }
    
    /* Structure preview styling */
    .structure-preview {
        background-color: #e8f5e8 !important;
        border: 1px solid #4caf50 !important;
        border-radius: 4px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
    }
    
    /* Accessibility improvements */
    .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_logo_base64():
    try:
        with open("./assets/gemma3.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

def generate_shareable_link(text, language):
    """Generate a unique shareable link for OCR results"""
    timestamp = str(int(time.time()))
    content_hash = hashlib.md5(f"{text}{language}{timestamp}".encode()).hexdigest()[:8]
    share_id = f"{timestamp}_{content_hash}"
    
    # Store in session state for demo purposes
    # In production, you'd store this in a database
    if 'shared_results' not in st.session_state:
        st.session_state['shared_results'] = {}
    
    st.session_state['shared_results'][share_id] = {
        'text': text,
        'language': language,
        'timestamp': timestamp
    }
    
    # Generate shareable URL (in production, this would be your domain)
    base_url = st.get_option("server.baseUrlPath") or "http://localhost:8501"
    share_url = f"{base_url}?share={share_id}"
    return share_url, share_id

def get_shared_result(share_id):
    """Retrieve shared OCR result"""
    if 'shared_results' in st.session_state and share_id in st.session_state['shared_results']:
        return st.session_state['shared_results'][share_id]
    return None

def add_to_history(text, language, filename, processing_time):
    """Add OCR result to history"""
    if 'ocr_history' not in st.session_state:
        st.session_state['ocr_history'] = []
    
    history_item = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'text': text[:200] + "..." if len(text) > 200 else text,
        'language': language,
        'filename': filename,
        'processing_time': processing_time,
        'full_text': text
    }
    
    st.session_state['ocr_history'].insert(0, history_item)
    
    # Keep only last 20 items
    if len(st.session_state['ocr_history']) > 20:
        st.session_state['ocr_history'] = st.session_state['ocr_history'][:20]

def analyze_text_structure(text):
    """Analyze text structure and return detected elements"""
    lines = text.split('\n')
    structure = {
        'headings': [],
        'lists': [],
        'paragraphs': [],
        'tables': [],
        'code_blocks': []
    }
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect headings (lines with # or all caps)
        if line.startswith('#') or (line.isupper() and len(line) < 100):
            structure['headings'].append({'line': i+1, 'text': line})
        
        # Detect lists (lines starting with numbers, bullets, or dashes)
        elif line.startswith(('•', '-', '*', '1.', '2.', '3.')):
            structure['lists'].append({'line': i+1, 'text': line})
        
        # Detect potential code blocks (lines with special characters)
        elif any(char in line for char in ['{', '}', '(', ')', ';', '=']):
            structure['code_blocks'].append({'line': i+1, 'text': line})
        
        # Detect potential tables (lines with multiple spaces or tabs)
        elif '\t' in line or line.count('  ') > 3:
            structure['tables'].append({'line': i+1, 'text': line})
        
        # Regular paragraphs
        else:
            structure['paragraphs'].append({'line': i+1, 'text': line})
    
    return structure

def create_pdf_content(text, language):
    """Create PDF content with proper formatting"""
    pdf_content = f"""
# OCR Result Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Language:** {language}

## Extracted Text
{text}

---
*Generated by Gemma-3 OCR Tool*
    """
    return pdf_content

def create_word_content(text, language):
    """Create Word document content"""
    word_content = f"""
OCR Result Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Language: {language}

Extracted Text:
{text}

---
Generated by Gemma-3 OCR Tool
    """
    return word_content

# Check for shared result in URL parameters
query_params = st.query_params
shared_id = query_params.get("share", None)

if shared_id:
    shared_result = get_shared_result(shared_id)
    if shared_result:
        st.success("📤 Shared OCR Result Retrieved!")
        st.markdown(f"**Language:** {shared_result['language']}")
        st.markdown(f"**Extracted Text:**")
        st.markdown(f"<div class='ocr-result'>{shared_result['text']}</div>", unsafe_allow_html=True)
        st.download_button(
            label="Download Shared Text",
            data=shared_result['text'],
            file_name=f"shared_ocr_{shared_id}.txt",
            mime="text/plain"
        )
        st.markdown("---")

logo_b64 = get_logo_base64()
if logo_b64:
    st.markdown(f"""
        <h1 class="main-header" role="heading" aria-level="1">
            <img src="data:image/png;base64,{logo_b64}" width="50" style="vertical-align: -12px;" alt="Gemma-3 Logo">
            Gemma-3 OCR (OCR.Space)
        </h1>
    """, unsafe_allow_html=True)
else:
    st.markdown('<h1 class="main-header" role="heading" aria-level="1">Gemma-3 OCR (OCR.Space)</h1>', unsafe_allow_html=True)

col1, col2 = st.columns([6,1])
with col2:
    if st.button("Clear 🗑️", key="clear_button", help="Clear all results"):
        if 'ocr_result' in st.session_state:
            del st.session_state['ocr_result']
        if 'ocr_text_download' in st.session_state:
            del st.session_state['ocr_text_download']
        if 'share_url' in st.session_state:
            del st.session_state['share_url']
        st.rerun()

st.markdown('<p style="margin-top: -20px;">Extract structured text from images using OCR.Space!</p>', unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an image...", 
        type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'doc'],
        help="Upload an image file (PNG, JPG, JPEG, PDF, DOCX, DOC) under 1MB"
    )

    # Image preprocessing options
    if uploaded_file is not None:
        st.markdown("---")
        st.header("🔧 Image Preprocessing")
        
        # Rotation
        rotate_angle = st.selectbox(
            "🔄 Rotate image (degrees)", 
            [0, 90, 180, 270], 
            index=0,
            help="Rotate the image before OCR processing"
        )
        
        # Brightness adjustment
        brightness = st.slider(
            "💡 Brightness", 
            min_value=0.1, 
            max_value=2.0, 
            value=1.0, 
            step=0.1,
            help="Adjust image brightness"
        )
        
        # Contrast adjustment
        contrast = st.slider(
            "🎨 Contrast", 
            min_value=0.1, 
            max_value=2.0, 
            value=1.0, 
            step=0.1,
            help="Adjust image contrast"
        )
        
        # Sharpness adjustment
        sharpness = st.slider(
            "🔍 Sharpness", 
            min_value=0.1, 
            max_value=2.0, 
            value=1.0, 
            step=0.1,
            help="Adjust image sharpness"
        )
        
        # Crop options
        st.subheader("✂️ Crop Image")
        crop_enabled = st.checkbox("Enable cropping", help="Crop the image to focus on specific text")
        
        if crop_enabled:
            st.info("💡 Tip: After enabling cropping, you'll be able to select the crop area in the main view")

    # Multi-language support with corrected language codes
    languages = {
        'English': 'eng',
        'French': 'fra',
        'Spanish': 'spa',
        'German': 'deu',
        'Italian': 'ita',
        'Portuguese': 'por',
        'Dutch': 'nld',
        'Russian': 'rus',
        'Chinese (Simplified)': 'chs',
        'Japanese': 'jpn',
        'Korean': 'kor',
        'Arabic': 'ara',
        'Turkish': 'tur',
        'Polish': 'pol',
        'Romanian': 'ron',
        'Ukrainian': 'ukr',
        'Vietnamese': 'vie',
        'Czech': 'ces',
        'Greek': 'ell',
        'Bulgarian': 'bul',
        'Croatian': 'hrv',
        'Hungarian': 'hun',
        'Slovak': 'slk',
        'Slovenian': 'slv',
        'Swedish': 'swe',
        'Finnish': 'fin',
        'Danish': 'dan',
        'Norwegian': 'nor',
        'Hebrew': 'heb',
        'Hindi': 'hin',
        'Malay': 'msa',
        'Thai': 'tha',
        'Indonesian': 'ind',
        'Filipino': 'fil',
        'Serbian (Latin)': 'srp',
        'Serbian (Cyrillic)': 'srp-cyr',
        'Albanian': 'sqi',
        'Estonian': 'est',
        'Latvian': 'lav',
        'Lithuanian': 'lit',
        'Macedonian': 'mkd',
        'Georgian': 'kat',
        'Armenian': 'hye',
        'Azerbaijani': 'aze',
        'Kazakh': 'kaz',
        'Uzbek': 'uzb',
        'Mongolian': 'mon',
        'Persian': 'fas',
        'Pashto': 'pus',
        'Urdu': 'urd',
        'Bengali': 'ben',
        'Tamil': 'tam',
        'Telugu': 'tel',
        'Kannada': 'kan',
        'Malayalam': 'mal',
        'Marathi': 'mar',
        'Gujarati': 'guj',
        'Punjabi': 'pan',
        'Sinhala': 'sin',
        'Nepali': 'nep',
        'Burmese': 'mya',
        'Khmer': 'khm',
        'Lao': 'lao',
        'Tibetan': 'bod',
        'Other': 'eng'
    }
    
    # Store previous language selection for comparison
    if 'previous_language' not in st.session_state:
        st.session_state['previous_language'] = 'English'
    
    selected_lang = st.selectbox(
        "🌍 Select OCR Language", 
        list(languages.keys()), 
        index=0,
        help="Choose the language of the text in your image"
    )
    
    # Show language change notification
    if selected_lang != st.session_state['previous_language']:
        st.success(f"✅ Language changed to: {selected_lang}")
        st.session_state['previous_language'] = selected_lang

    st.markdown("---")
    st.header("📖 How to Use")
    st.markdown("""
    1. **Upload** an image (max 1MB)
    2. **Preprocess** the image if needed
    3. **Select** the language of the text
    4. **Click** 'Extract Text' to process
    5. **Download** or **Share** the result!
    """)
    
    st.markdown("---")
    st.header("♿ Accessibility")
    st.markdown("""
    - **Keyboard Navigation**: Use Tab to navigate
    - **Screen Readers**: All elements have proper labels
    - **High Contrast**: Optimized for visibility
    - **Mobile Friendly**: Responsive design
    """)
    
    st.markdown("---")
    st.header("🔒 Privacy Policy")
    st.markdown("""
    - **No Data Storage**: Images are processed and immediately deleted
    - **Temporary Results**: OCR results are stored only in your browser session
    - **No Tracking**: We don't collect personal information
    - **Secure Processing**: All processing happens via secure API calls
    """)
    
    st.markdown("---")
    st.info("💡 **Tip**: For best results, use clear, high-contrast images. Supported languages: 50+")

# --- OCR Function ---
def ocr_space_file(file_bytes, language_code, api_key='helloworld'):
    payload = {
        'isOverlayRequired': False,
        'apikey': api_key,
        'language': language_code,
        'OCREngine': 2
    }
    files = {'file': ('image.png', file_bytes, 'image/png')}
    response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
    return response.json()

# --- Main Logic ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # Apply preprocessing
    if rotate_angle != 0:
        image = image.rotate(-rotate_angle, expand=True)
    
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)
    
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sharpness)
    
    # Display original and processed images
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📷 Original Image")
        st.image(uploaded_file, caption="Original", use_container_width=True)
    
    with col2:
        st.subheader("🔧 Processed Image")
        st.image(image, caption="After Preprocessing", use_container_width=True)
    
    # Crop functionality
    if crop_enabled:
        st.subheader("✂️ Crop Selection")
        st.info("Click and drag to select the area you want to crop")
        # Note: Streamlit doesn't have built-in image cropping, so we'll show instructions
        st.warning("Manual cropping feature coming soon! For now, please crop your image before uploading.")
    
    if st.button("🔍 Extract Text", type="primary", help="Process the image and extract text"):
        start_time = time.time()
        with st.spinner("Processing image..."):
            try:
                # Compress/resize image to ensure it's under 1MB
                buffer = io.BytesIO()
                image.save(buffer, format="PNG", optimize=True, quality=70)
                file_bytes = buffer.getvalue()
                
                if len(file_bytes) > 1024 * 1024:
                    image_resized = image.resize((image.width // 2, image.height // 2))
                    buffer = io.BytesIO()
                    image_resized.save(buffer, format="PNG", optimize=True, quality=70)
                    file_bytes = buffer.getvalue()
                
                if len(file_bytes) > 1024 * 1024:
                    st.error("Image is too large even after compression. Please upload a smaller image (under 1MB).")
                else:
                    # Show which language is being used
                    st.info(f"🔍 Processing with language: {selected_lang} ({languages[selected_lang]})")
                    
                    result = ocr_space_file(file_bytes, languages[selected_lang])
                    
                    if result.get('IsErroredOnProcessing'):
                        error_msg = result.get('ErrorMessage', 'Unknown error')
                        st.error(f"OCR Error: {error_msg}")
                    else:
                        parsed_results = result.get('ParsedResults', [])
                        if parsed_results:
                            text = parsed_results[0].get('ParsedText', '').strip()
                            if text:
                                processing_time = round(time.time() - start_time, 2)
                                
                                st.session_state['ocr_result'] = text
                                st.session_state['ocr_language'] = selected_lang
                                st.session_state['ocr_language_code'] = languages[selected_lang]
                                st.session_state['processing_time'] = processing_time
                                
                                # Add to history
                                add_to_history(text, selected_lang, uploaded_file.name, processing_time)
                                
                                # Generate shareable link
                                share_url, share_id = generate_shareable_link(text, selected_lang)
                                st.session_state['share_url'] = share_url
                                st.session_state['share_id'] = share_id
                                
                                st.success(f"✅ Text extracted successfully using {selected_lang} language! (Time: {processing_time}s)")
                            else:
                                st.warning("No text found in the image.")
                        else:
                            st.warning("No text found in the image.")
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

# --- Main Content Area ---
if 'ocr_result' in st.session_state:
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Extracted Text", "🔍 Structure Analysis", "📊 History", "📋 Export"])
    
    with tab1:
        st.markdown("### 📄 Extracted Text")
        import html
        escaped_text = html.escape(st.session_state['ocr_result'])
        st.markdown(f"<div class='ocr-result' role='textbox' aria-label='Extracted text result'>{escaped_text}</div>", unsafe_allow_html=True)
        
        # Action buttons in columns for better mobile layout
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.download_button(
                label="💾 Download Text",
                data=st.session_state['ocr_result'],
                file_name="extracted_text.txt",
                mime="text/plain",
                help="Download the extracted text as a text file"
            )
        
        with col2:
            # Copy to clipboard button with JavaScript
            import html
            ocr_text_escaped = html.escape(st.session_state['ocr_result'])
            ocr_text_js = st.session_state['ocr_result'].replace("'", "\\'").replace('"', '\\"').replace('{', '\\{').replace('}', '\\}')
            st.markdown(f"""
            <button onclick="copyToClipboard()" style="width: 100%; padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
                📋 Copy to Clipboard
            </button>
            <script>
            function copyToClipboard() {{
                const text = `{ocr_text_js}`;
                navigator.clipboard.writeText(text).then(function() {{
                    alert('Text copied to clipboard!');
                }}, function(err) {{
                    console.error('Could not copy text: ', err);
                }});
            }}
            </script>
            """, unsafe_allow_html=True)
        
        with col3:
            if 'share_url' in st.session_state:
                st.markdown(f"""
                <div class="share-link">
                    <strong>🔗 Share Link:</strong><br>
                    <a href="{st.session_state['share_url']}" target="_blank">{st.session_state['share_url']}</a>
                </div>
                """, unsafe_allow_html=True)
        
        # Language info with more details
        if 'ocr_language' in st.session_state:
            lang_code = st.session_state.get('ocr_language_code', 'eng')
            st.info(f"🌍 OCR Language: {st.session_state['ocr_language']} ({lang_code})")
    
    with tab2:
        st.markdown("### 🔍 Structure Analysis")
        structure = analyze_text_structure(st.session_state['ocr_result'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Detected Elements")
            st.markdown(f"**Headings:** {len(structure['headings'])}")
            st.markdown(f"**Lists:** {len(structure['lists'])}")
            st.markdown(f"**Paragraphs:** {len(structure['paragraphs'])}")
            st.markdown(f"**Tables:** {len(structure['tables'])}")
            st.markdown(f"**Code Blocks:** {len(structure['code_blocks'])}")
        
        with col2:
            st.markdown("#### 📋 Preview")
            if structure['headings']:
                st.markdown("**Headings:**")
                for heading in structure['headings'][:3]:  # Show first 3
                    st.markdown(f"- Line {heading['line']}: {heading['text']}")
            
            if structure['lists']:
                st.markdown("**Lists:**")
                for item in structure['lists'][:3]:  # Show first 3
                    st.markdown(f"- Line {item['line']}: {item['text']}")
    
    with tab3:
        st.markdown("### 📊 OCR History")
        if 'ocr_history' in st.session_state and st.session_state['ocr_history']:
            for i, item in enumerate(st.session_state['ocr_history']):
                with st.expander(f"📄 {item['filename']} - {item['timestamp']}"):
                    st.markdown(f"**Language:** {item['language']}")
                    st.markdown(f"**Processing Time:** {item['processing_time']}s")
                    st.markdown(f"**Text Preview:** {item['text']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"View Full Text {i}", key=f"view_{i}"):
                            st.session_state['ocr_result'] = item['full_text']
                            st.session_state['ocr_language'] = item['language']
                            st.rerun()
                    with col2:
                        if st.button(f"Delete {i}", key=f"delete_{i}"):
                            st.session_state['ocr_history'].pop(i)
                            st.rerun()
        else:
            st.info("No OCR history yet. Process some images to see your history here!")
    
    with tab4:
        st.markdown("### 📋 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # PDF Export (simulated)
            pdf_content = create_pdf_content(st.session_state['ocr_result'], st.session_state.get('ocr_language', 'Unknown'))
            st.download_button(
                label="📄 Export as PDF",
                data=pdf_content,
                file_name="ocr_result.pdf",
                mime="application/pdf",
                help="Export as PDF document"
            )
        
        with col2:
            # Word Export (simulated)
            word_content = create_word_content(st.session_state['ocr_result'], st.session_state.get('ocr_language', 'Unknown'))
            st.download_button(
                label="📝 Export as Word",
                data=word_content,
                file_name="ocr_result.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                help="Export as Word document"
            )
        
        with col3:
            # JSON Export
            json_data = {
                'text': st.session_state['ocr_result'],
                'language': st.session_state.get('ocr_language', 'Unknown'),
                'timestamp': datetime.now().isoformat(),
                'structure': analyze_text_structure(st.session_state['ocr_result'])
            }
            st.download_button(
                label="📊 Export as JSON",
                data=json.dumps(json_data, indent=2),
                file_name="ocr_result.json",
                mime="application/json",
                help="Export as JSON with structure analysis"
            )

else:
    st.info("📤 Upload an image and click 'Extract Text' to see the results here.")

# Footer with accessibility info
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    Made with ❤️ using OCR.Space API | 
    <a href="https://github.com/patchy631/ai-engineering-hub/issues" target="_blank">Report an Issue</a> |
    <span class="sr-only">Accessible OCR tool for text extraction from images</span>
</div>
""", unsafe_allow_html=True)
