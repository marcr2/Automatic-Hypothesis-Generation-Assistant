# AI Research Processor

**AI-Powered Scientific Hypothesis Generator for Biomedical Research**

A comprehensive research tool with an intuitive graphical interface that scrapes scientific literature, generates embeddings, and uses AI to generate novel research hypotheses for any biomedical research topic. This system accelerates scientific discovery by analyzing vast amounts of research data and proposing testable hypotheses.

## 🚀 Quick Start

## We now have a website!
You can find AHGA at www.https://ahga.it.com

#However if you prefer local usage, we also have a local installation option:

### **Windows Users (Recommended)**
```bash
# 1. First time setup (run once)
install.bat

# 2. Launch GUI (run anytime)
python src/interfaces/gui_main.py
```

### **Manual Installation**
```bash
# Create a virtual environment
python -m venv .venv

# Install dependencies
pip install -r requirements.txt

# Launch GUI
python src/interfaces/gui_main.py
```

## 📁 Project Structure

The codebase is now organized into logical modules for better maintainability:

```
AHG-UBR5/
├── src/                          # Main source code
│   ├── core/                     # Core functionality
│   │   ├── chromadb_manager.py   # Vector database management
│   │   ├── processing_config.py  # Configuration settings
│   │   └── network_fix.py        # Network connectivity fixes
│   ├── scrapers/                 # Data scraping modules
│   │   ├── pubmed_scraper_json.py
│   │   ├── process_xrvix_dumps_json.py
│   │   ├── semantic_scholar_scraper.py
│   │   └── xrvix_downloader.py
│   ├── ai/                       # AI and hypothesis generation
│   │   ├── enhanced_rag_with_chromadb.py
│   │   ├── hypothesis_tools.py
│   │   └── optimized_prompts.py
│   ├── utils/                    # Utility modules
│   │   └── citation_mapping_utils.py # Citation analysis tools
│   └── interfaces/               # User interfaces
│       ├── main.py               # Terminal interface
│       └── gui_main.py           # GUI interface
├── scripts/                      # Command-line tools
│   └── analyze_citations.py     # Citation analysis script
├── config/                       # Configuration files
│   ├── keys.json                 # API keys
│   ├── search_keywords_config.json
│   └── critique_config.json
├── install.bat                   # Installation script
├── run.bat                       # GUI launcher script
└── run_on_terminal.bat           # Terminal launcher script
├── data/                         # Data directories
├── docs/                         # Documentation
└── hypothesis_export/            # Export files
```

## 🖥️ GUI Interface

The system now features a modern **Tkinter-based graphical interface** with tabbed organization:

### **Main Tabs**
- **📚 Paper Scraping & Processing** - Collect data from multiple sources
- **🗄️ Vector Database Management** - Manage ChromaDB storage
- **⚙️ Settings & Config** - System status and configuration
- **🧠 Hypothesis Generation** - AI-powered hypothesis creation
- **📖 Tutorial** - Comprehensive data pipeline guide

### **Key Features**
- **Scrollable Interface** - All tabs support scrolling for better navigation
- **Resizable Text Windows** - Click and drag to resize output areas
- **Real-time Progress** - Live updates and status indicators
- **Threading Support** - GUI remains responsive during long operations
- **Error Handling** - User-friendly error messages and suggestions

## 📚 Complete Installation Tutorial

### **Step 1: Prerequisites**

Before installing, ensure you have:

- **Python 3.13+** installed on your system
- **Internet connection** for downloading dependencies and data
- **Google AI API key** (optional but recommended for full functionality)
- **At least 2GB free disk space** for data storage

#### **Installing Python (if needed)**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.13 or newer
3. **IMPORTANT**: During installation, check "Add Python to PATH"
4. Complete the installation

### **Step 2: Download the Software**

1. **Clone or download** this repository to your computer
2. **Navigate** to the AI Research Processor folder in your file explorer
3. **Open Command Prompt** or PowerShell in this folder

### **Step 3: Installation (Windows - Easy Method)**

#### **Option A: Automatic Installation (Recommended)**
```bash
# Double-click install.bat or run from command prompt:
install.bat
```

**What the installer does:**
- ✅ Checks Python installation
- ✅ Creates virtual environment (`.venv`)
- ✅ Installs all required packages
- ✅ Creates data directory structure
- ✅ Checks API configuration
- ✅ Provides setup guidance

#### **Option B: Manual Installation**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir data
mkdir data\embeddings
mkdir data\embeddings\xrvix_embeddings
mkdir data\embeddings\xrvix_embeddings\biorxiv
mkdir data\embeddings\xrvix_embeddings\medrxiv
mkdir data\embeddings\xrvix_embeddings\pubmed
mkdir data\embeddings\xrvix_embeddings\semantic_scholar
mkdir data\logs
mkdir data\scraped_data
mkdir data\vector_db
mkdir data\backups
```

### **Step 4: API Configuration**

A google API and gemini API key is **required**, and an NCBI API key is *reccommended* if you want to scrape from pubmed.

1. **Get API Key**: Visit [Google AI Studio](https://aistudio.google.com/)
2. **Create keys.json**: In the AI Research Processor folder, create a file called `keys.json`:
```json
{
  "ncbi_api_key": "your_api_key_here",
  "GOOGLE_API_KEY": "your_api_key_here",
  "GEMINI_API_KEY": "your_api_key_here"
}
```

### **Step 5: Running the Software**

run 
```bash
run.bat
```
#### **Legacy Command Line Interface**
run 
```bash
run_on_terminal.bat
```

### **Step 6: First-Time Usage with GUI**

When you first run the GUI:

1. **Start with Tutorial Tab** - Read the comprehensive data pipeline guide
2. **Check System Status** - Go to Settings → Data Status
3. **Collect Data** - Use Paper Scraping → Full Scraper (start with option 1)- **Note that this can take a while, up to many hours- but it only needs to be done once.**
4. **Configure Keywords** - Enter your research interests or use defaults
5. **Load Data** - Go to Vector Database → Load Embeddings
6. **Generate Hypotheses** - Use Hypothesis Generation → Generate Hypothesess

## 📋 GUI Interface Guide

### **📚 Paper Scraping & Processing Tab**

**Full Scraper Subtab**
- Scrapes all sources (PubMed, preprints, Semantic Scholar)
- Customizable keywords for both PubMed and Semantic Scholar
- Configurable PubMed result limits
- Automatic preprint dump downloading

**Journal Articles Only Subtab**
- Focuses on peer-reviewed literature
- PubMed + Semantic Scholar scraping
- Unified keyword configuration

**Preprints Only Subtab**
- Processes Biorxiv and Medrxiv dumps
- Automatic dump downloading if needed
- Status checking for available dumps

**Generate Embeddings Subtab**
- Embedding generation status
- Information about automatic embedding creation

### **🗄️ Vector Database Management Tab**

**Load Embeddings Subtab**
- Loads processed data into ChromaDB
- Real-time progress monitoring
- Automatic data source detection
- Reload confirmation for existing data

**Show ChromaDB Data Subtab**
- Database statistics and document counts
- Source breakdown analysis
- Collection information
- Refresh functionality

**Clear ChromaDB Data Subtab**
- Safe data clearing with confirmation
- Warning messages for destructive operations
- Status updates during clearing

### **⚙️ Settings & Config Tab**

**Data Status Subtab**
- Overview of all data sources
- File size and document count information
- ChromaDB status checking
- Recommendations for next steps

**Configurations Subtab**
- Current system settings display
- Processing configuration information
- Database settings overview

### **🧠 Hypothesis Generation Tab**

**Generate Hypotheses Subtab**
- Prerequisites checking
- ChromaDB data validation
- Enhanced RAG system launch
- Status monitoring

**Test Run Subtab**
- Customizable test queries for any research topic
- Prerequisites validation
- Quick demonstration mode

### **📖 Tutorial Tab**

**Comprehensive Guide Including:**
- Data pipeline overview (4 stages)
- Detailed stage explanations
- Recommended workflow
- Configuration tips
- Troubleshooting guide
- Advanced features
- Getting help resources

### **📊 Citation Analysis Tab**

**Citation Analysis Tools:**
- Analyze citation patterns across hypotheses
- Export citation data to CSV for further analysis
- Track citation cache keys for easy mapping
- Generate comprehensive citation reports

**Command Line Usage:**
```bash
# Analyze latest hypothesis export
python scripts/analyze_citations.py

# Analyze specific export
python scripts/analyze_citations.py hypothesis_export/Hypothesis_Export_09202025-2043
```

**Programmatic Usage:**
```python
from src.utils.citation_mapping_utils import CitationMappingUtils

# Load citation data
utils = CitationMappingUtils("hypothesis_export/Hypothesis_Export_09202025-2043")

# Get citations for hypothesis #5
citations = utils.get_hypothesis_citations(5)

# Create summary table
summary_df = utils.create_citation_summary_table()

# Export to CSV
utils.export_citation_mapping_to_csv()
```

## 🏗️ System Architecture

### Core Components

- **`gui_main.py`** - Main GUI interface with tabbed organization
- **`main.py`** - Legacy command line interface
- **`enhanced_rag_with_chromadb.py`** - Advanced RAG system with hypothesis generation
- **`chromadb_manager.py`** - Vector database management
- **`pubmed_scraper_json.py`** - PubMed literature scraping
- **`process_xrvix_dumps_json.py`** - Preprint processing (Biorxiv, Medrxiv)
- **`semantic_scholar_scraper.py`** - Semantic Scholar API scraping
- **`hypothesis_tools.py`** - AI hypothesis generation tools
- **`citation_mapping_utils.py`** - Citation analysis and mapping utilities

### Data Sources

1. **PubMed** - Peer-reviewed journal articles
2. **Biorxiv** - Biology preprint server
3. **Medrxiv** - Medicine preprint server  
4. **Semantic Scholar API** - Comprehensive academic literature search

## 📁 Data Structure

```
data/
├── backups/                    # Backup files
│   └── embeddings_backup.zip   # Embeddings backup
├── embeddings/                 # Generated embeddings
│   └── xrvix_embeddings/      # Main embeddings directory
│       ├── biorxiv/           # Biorxiv preprint embeddings
│       ├── medrxiv/           # Medrxiv preprint embeddings
│       ├── pubmed/            # PubMed journal article embeddings
│       └── semantic_scholar/   # Semantic Scholar API scraped embeddings
├── logs/                      # Log files
│   ├── paper_processing.log   # Paper processing logs
│   └── semantic_scholar_scraping.log # Semantic Scholar API scraping logs
├── scraped_data/              # Raw scraped data
│   └── paperscraper_dumps/    # Paperscraper dump files
└── vector_db/                 # Vector database storage
    └── chroma_db/            # ChromaDB persistent storage
```

## 🛠️ Configuration

### Processing Configuration
- **Batch Sizes** - Configurable processing batch sizes
- **Rate Limiting** - API rate limit management
- **Parallel Processing** - Multi-threaded data processing
- **Memory Management** - Efficient memory usage

### API Configuration
- **Google AI Studio** - Gemini model configuration
- **Semantic Scholar** - API key and rate limiting
- **PubMed** - E-utilities API configuration

## 📈 Performance

### Optimization Features
- **Memory Profiling** - Efficient memory usage
- **Progress Monitoring** - Real-time performance tracking
- **Error Recovery** - Automatic retry and recovery mechanisms

### Scalability
- **Batch Processing** - Handles large datasets efficiently
- **Persistent Storage** - ChromaDB for fast data retrieval
- **Modular Design** - Easy to extend and modify
- **API Integration** - Seamless integration with external APIs

## 🐛 Troubleshooting

### Common Issues

1. **"No ChromaDB collections found"**
   - Solution: Run "Load Embeddings" first to populate the database

2. **"No preprint dumps found"**
   - Solution: The system will automatically download dumps when needed
   - Ensure you have internet connection

3. **"Keywords not saved"**
   - Solution: Check file permissions in the project directory
   - Try running as administrator if needed

4. **"Import errors"**
   - Solution: Install missing dependencies: `pip install pandas paperscraper chromadb`
   - Check Python version compatibility

5. **"Long processing times"**
   - Solution: This is normal for large datasets
   - Use smaller PubMed limits for faster initial runs
   - Monitor progress in output areas

### Log Files
- Check `data/logs/` for detailed error information
- Monitor processing status in real-time through GUI output areas

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to functions
- Include type hints where appropriate
- Write comprehensive tests

## 📄 License

See the LICENSE file for details.

## 🙏 Acknowledgments

- **Google AI Studio** - Gemini model access
- **Semantic Scholar** - Research paper API
- **ChromaDB** - Vector database technology
- **Tkinter** - GUI framework
- **Paperscraper** - Preprint data access

## 📞 Support

For questions, issues, or contributions:
- Create an issue in the repository
- Review log files for error details
- Check the Tutorial tab in the GUI for comprehensive guidance
- Review the documentation and troubleshooting sections
- Contact me at marcellino.rau@gmail.com for any questions or info!

---
