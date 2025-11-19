#!/usr/bin/env python3
"""
AI Research Processor - Main Menu
AI-Powered Scientific Hypothesis Generator for Biomedical Research
"""

import os
import sys
import json
import subprocess
import logging
import traceback
import io
from contextlib import redirect_stdout, redirect_stderr

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.scrapers.pubmed_scraper_json import main as process_pubmed
from src.scrapers.process_xrvix_dumps_json import main as process_xrvix
from src.scrapers.semantic_scholar_scraper import SemanticScholarScraper
from src.core.chromadb_manager import ChromaDBManager
from src.core.processing_config import print_config_info, get_config, DB_BATCH_SIZE

def parse_unified_keywords(keywords_str):
    """
    Parse keywords from user input or config file into a unified format.
    Returns a list of cleaned keywords that both PubMed and Semantic Scholar can use.
    """
    if not keywords_str or not keywords_str.strip():
        # Fall back to config file if no input
        try:
            with open("config/search_keywords_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            keywords_str = config.get("pubmed_keywords", "")
        except Exception:
            keywords_str = ""
    
    if not keywords_str or not keywords_str.strip():
        # Final fallback to default keywords
        return ["biomedical research", "disease mechanisms", "molecular biology", "therapeutic targets"]
    
    # Parse comma-separated keywords and clean them
    keywords = [term.strip() for term in keywords_str.split(',') if term.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword.lower() not in seen:
            seen.add(keyword.lower())
            unique_keywords.append(keyword)
    
    return unique_keywords

# Configure comprehensive logging
def setup_debug_logging():
    """Setup comprehensive debug logging for terminal interface."""
    # Create logs directory if it doesn't exist
    os.makedirs("data/logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/terminal_debug.log', mode='a'),
            logging.StreamHandler(sys.stdout)  # Also output to console
        ]
    )
    
    # Set specific loggers to DEBUG level
    loggers_to_debug = [
        'pubmed_scraper_json',
        'process_xrvix_dumps_json', 
        'semantic_scholar_scraper',
        'chromadb_manager',
        'xrvix_downloader',
        'paperscraper',
        'requests',
        'urllib3'
    ]
    
    for logger_name in loggers_to_debug:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
    
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_debug_logging()

def show_menu():
    """Display the main menu with the specified structure."""
    print("\n" + "="*60)
    print("🚀 AI RESEARCH PROCESSOR - MAIN MENU")
    print("="*60)
    
    print("\n📚 PAPER SCRAPING & PROCESSING:")
    print("1. Full scraper (preprints + journal articles) - Custom keywords")
    print("2. Journal articles only (pubmed, semantic scholar) - Custom keywords")
    print("3. Preprints only (Biorxiv, Medrxiv) - Automatically downloads and processes")
    print("4. Generate embeddings")
    
    print("\n🗄️ VECTOR DATABASE MANAGEMENT:")
    print("5. Load embeddings")
    print("6. Show current ChromaDB data")
    print("7. Clear ChromaDB data")
    
    print("\n⚙️ SETTINGS & CONFIG:")
    print("8. Show data status")
    print("9. Show configurations")
    
    print("\n🧠 HYPOTHESIS GENERATION:")
    print("10. Generate hypotheses")
    print("11. Test run (Biomedical Research)")
    
    print("\n🔧 DEBUG & LOGGING:")
    print("12. Enable/Disable Full Debug Logging")
    print("13. View Debug Log File")
    print("14. Clear Debug Logs")
    
    print("\n15. Exit")
    print("="*60)

def get_user_choice():
    """Get user choice with proper validation."""
    while True:
        try:
            choice = int(input("\nEnter your choice (1-15): "))
            if 1 <= choice <= 15:
                return choice
            else:
                print("❌ Please enter a number between 1 and 15.")
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

# Global debug logging state
DEBUG_LOGGING_ENABLED = True

def toggle_debug_logging():
    """Toggle full debug logging on/off."""
    global DEBUG_LOGGING_ENABLED
    
    print("\n🔧 Debug Logging Configuration")
    print("="*50)
    print(f"Current status: {'ENABLED' if DEBUG_LOGGING_ENABLED else 'DISABLED'}")
    print()
    print("Full debug logging includes:")
    print("• Detailed API request/response logs")
    print("• Raw error messages and stack traces")
    print("• Network connection details")
    print("• Database operation logs")
    print("• All internal processing steps")
    print()
    
    toggle = input("Toggle debug logging? (y/n): ").strip().lower()
    if toggle == 'y':
        DEBUG_LOGGING_ENABLED = not DEBUG_LOGGING_ENABLED
        print(f"✅ Debug logging {'ENABLED' if DEBUG_LOGGING_ENABLED else 'DISABLED'}")
        
        # Update logging level
        if DEBUG_LOGGING_ENABLED:
            logging.getLogger().setLevel(logging.DEBUG)
            print("🔍 All debug information will be displayed in terminal")
        else:
            logging.getLogger().setLevel(logging.INFO)
            print("ℹ️  Only essential information will be displayed")
    else:
        print("❌ Debug logging configuration unchanged")

def view_debug_log():
    """View the debug log file."""
    log_file = "data/logs/terminal_debug.log"
    
    print("\n📋 Debug Log Viewer")
    print("="*50)
    
    if not os.path.exists(log_file):
        print("❌ No debug log file found")
        print("💡 Run some operations first to generate logs")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("📄 Debug log file is empty")
            return
        
        print(f"📄 Debug log file: {log_file}")
        print(f"📊 Total lines: {len(lines)}")
        print()
        
        # Show last 50 lines by default
        show_lines = input("How many lines to show? (default: 50, 'all' for full log): ").strip()
        
        if show_lines.lower() == 'all':
            lines_to_show = lines
            print("📄 Showing full debug log:")
        else:
            try:
                num_lines = int(show_lines) if show_lines else 50
                lines_to_show = lines[-num_lines:] if num_lines < len(lines) else lines
                print(f"📄 Showing last {len(lines_to_show)} lines:")
            except ValueError:
                lines_to_show = lines[-50:]
                print("📄 Showing last 50 lines:")
        
        print("-" * 80)
        for line in lines_to_show:
            print(line.rstrip())
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error reading debug log: {e}")
        logger.error(f"Error reading debug log: {e}", exc_info=True)

def clear_debug_logs():
    """Clear all debug logs."""
    print("\n🗑️ Clear Debug Logs")
    print("="*50)
    
    log_files = [
        "data/logs/terminal_debug.log",
        "data/logs/paper_processing.log", 
        "data/logs/semantic_scholar_scraping.log"
    ]
    
    existing_files = [f for f in log_files if os.path.exists(f)]
    
    if not existing_files:
        print("📄 No log files found to clear")
        return
    
    print("Found log files:")
    for i, file in enumerate(existing_files, 1):
        size = os.path.getsize(file) / 1024  # Size in KB
        print(f"  {i}. {file} ({size:.1f} KB)")
    
    print()
    confirm = input("Clear all log files? (y/n): ").strip().lower()
    if confirm == 'y':
        cleared_count = 0
        for file in existing_files:
            try:
                with open(file, 'w') as f:
                    f.write("")  # Clear the file
                cleared_count += 1
                print(f"✅ Cleared: {file}")
            except Exception as e:
                print(f"❌ Error clearing {file}: {e}")
        
        print(f"\n🎯 Cleared {cleared_count}/{len(existing_files)} log files")
    else:
        print("❌ Log clearing cancelled")

def get_search_keywords():
    """Get custom search keywords from user."""
    print("\n🔍 Search Keywords Configuration")
    print("="*50)
    print("You can customize the search keywords for PubMed and Semantic Scholar.")
    print()
    
    # Check for previously saved keywords
    saved_pubmed, saved_semantic = load_keywords_config()
    
    if saved_pubmed and saved_semantic:
        print("📁 Previously saved keywords found:")
        print(f"   PubMed: {saved_pubmed}")
        print(f"   Semantic Scholar: {saved_semantic}")
        print()
        
        use_saved = input("Use previously saved keywords? (y/n): ").strip().lower()
        if use_saved == 'y':
            return saved_pubmed, saved_semantic
    
    print("Choose keyword configuration:")
    print("1. Use default keywords (biomedical research)")
    print("2. Enter custom keywords")
    print("3. Cancel")
    
    while True:
        choice = input("Enter choice (1-3): ").strip()
        if choice == '1':
            pubmed_keywords = "protein, disease, biomedical, research, biology"
            semantic_keywords = "protein, disease, biomedical, research, biology"
            print(f"   Using default PubMed: {pubmed_keywords}")
            print(f"   Using default Semantic Scholar: {semantic_keywords}")
            break
        elif choice == '2':
            # Get unified keywords for both PubMed and Semantic Scholar
            print("\n🔍 Search Keywords:")
            print("   Default: protein, disease, biomedical, research, biology")
            print("   Note: Same keywords will be used for both PubMed and Semantic Scholar")
            unified_keywords = input("   Enter keywords (comma-separated, or press Enter for default): ").strip()
            
            if not unified_keywords:
                unified_keywords = "protein, disease, biomedical, research, biology"
                print(f"   Using default: {unified_keywords}")
            else:
                print(f"   Using custom: {unified_keywords}")
            
            # Use the same keywords for both sources
            pubmed_keywords = unified_keywords
            semantic_keywords = unified_keywords
            break
        elif choice == '3':
            print("❌ Search cancelled.")
            return None, None
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    print()
    
    # Confirm keywords
    print("📋 Search Configuration Summary:")
    print(f"   Keywords (used for both PubMed and Semantic Scholar): {pubmed_keywords}")
    print()
    
    confirm = input("Proceed with these keywords? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Search cancelled.")
        return None, None
    
    # Save keywords to configuration file for future use
    save_keywords_config(pubmed_keywords, semantic_keywords)
    
    return pubmed_keywords, semantic_keywords

def save_keywords_config(pubmed_keywords, semantic_keywords):
    """Save keywords configuration to file."""
    config = {
        "pubmed_keywords": pubmed_keywords,
        "semantic_keywords": semantic_keywords,
        "last_updated": json.dumps({"timestamp": __import__("datetime").datetime.now().isoformat()})
    }
    
    try:
        with open("config/search_keywords_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        print("💾 Keywords saved to search_keywords_config.json")
    except Exception as e:
        print(f"⚠️  Could not save keywords config: {e}")

def load_keywords_config():
    """Load keywords configuration from file."""
    try:
        if os.path.exists("config/search_keywords_config.json"):
            with open("config/search_keywords_config.json", 'r') as f:
                config = json.load(f)
            return config.get("pubmed_keywords"), config.get("semantic_keywords")
    except Exception as e:
        print(f"⚠️  Could not load keywords config: {e}")
    
    return None, None

def get_pubmed_max_results():
    """Get maximum number of PubMed results from user."""
    print("   Specify the maximum number of PubMed papers to retrieve:")
    print("   • Enter a positive number (e.g., 1000, 5000) for a specific limit")
    print("   • Enter -1 for unlimited results (use with caution)")
    print("   • Press Enter for default (5000)")
    
    while True:
        try:
            user_input = input("   Maximum PubMed results (default: 5000): ").strip()
            
            # If user presses Enter, use default
            if not user_input:
                max_results = 5000
                print(f"   ✅ Using default: {max_results} papers")
                break
            
            # Parse user input
            max_results = int(user_input)
            
            if max_results == -1:
                print("   ⚠️  Unlimited results selected - this may take a very long time!")
                confirm = input("   Are you sure? (y/n): ").strip().lower()
                if confirm == 'y':
                    max_results = 50000  # Set a very high limit instead of truly unlimited
                    print(f"   ✅ Unlimited results mode: {max_results} papers maximum")
                    break
                else:
                    print("   ❌ Unlimited results cancelled, please enter a number")
                    continue
            
            elif max_results <= 0:
                print("   ❌ Please enter a positive number or -1 for unlimited")
                continue
            
            elif max_results > 50000:
                print(f"   ⚠️  {max_results} is a very large number - this may take hours!")
                print(f"   Estimated time: {max_results // 1000} - {max_results // 500} minutes")
                confirm = input("   Are you sure? (y/n): ").strip().lower()
                if confirm == 'y':
                    print(f"   ✅ Maximum results set to: {max_results}")
                    break
                else:
                    print("   ❌ Please enter a smaller number")
                    continue
            
            else:
                print(f"   ✅ Maximum results set to: {max_results}")
                break
                
        except ValueError:
            print("   ❌ Please enter a valid number")
            continue
        except KeyboardInterrupt:
            print("\n👋 Search cancelled by user")
            return None
    
    return max_results

def run_full_scraper():
    """Run full scraper for preprints + journal articles."""
    print("\n🚀 Starting Full Scraper (Preprints + Journal Articles)")
    print("="*60)
    
    # Get custom keywords from user
    pubmed_keywords, semantic_keywords = get_search_keywords()
    if pubmed_keywords is None or semantic_keywords is None:
        return
    
    success_count = 0
    total_sources = 3  # PubMed + xrvix + Semantic Scholar
    
    # Step 1: Process PubMed (journal articles)
    print("\n📚 Step 1/3: Processing PubMed (Journal Articles)...")
    try:
        # Ask user for max results for PubMed
        print(f"   Using keywords: {pubmed_keywords}")
        print("   🔢 PubMed Results Configuration:")
        max_results = get_pubmed_max_results()
        if max_results is None:
            print("❌ PubMed processing cancelled by user")
            return
        
        process_pubmed(max_results=max_results)
        print("✅ PubMed processing completed successfully!")
        success_count += 1
    except Exception as e:
        print(f"❌ PubMed processing failed: {e}")
    
    # Step 2: Process xrvix (preprints)
    print("\n📄 Step 2/3: Processing xrvix (Preprints)...")
    try:
        # Check if dump files exist and download if needed
        dump_dir = "data/scraped_data/paperscraper_dumps"
        server_dumps_dir = os.path.join(dump_dir, "server_dumps")
        
        # Check both old and new directory structures
        biorxiv_dumps = []
        medrxiv_dumps = []
        
        if os.path.exists(server_dumps_dir):
            biorxiv_dumps = [f for f in os.listdir(server_dumps_dir) if 'biorxiv' in f.lower()]
            medrxiv_dumps = [f for f in os.listdir(server_dumps_dir) if 'medrxiv' in f.lower()]
        elif os.path.exists(dump_dir):
            biorxiv_dumps = [f for f in os.listdir(dump_dir) if f.startswith('biorxiv')]
            medrxiv_dumps = [f for f in os.listdir(dump_dir) if f.startswith('medrxiv')]
        
        if not biorxiv_dumps and not medrxiv_dumps:
            print("   ❌ No preprint dumps found!")
            print("   💡 Downloading latest preprint dumps automatically...")
            
            # Automatically download dumps
            from src.scrapers.xrvix_downloader import XRXivDownloader
            downloader = XRXivDownloader()
            success = downloader.download_all_dumps()
            
            if not success:
                print("   ❌ Failed to download preprint dumps!")
                print("   💡 Skipping preprint processing")
                raise Exception("Failed to download preprint dumps")
            
            print("   ✅ Preprint dumps downloaded successfully!")
        
        # xrvix processing doesn't use custom keywords (it processes existing dumps)
        process_xrvix()
        print("✅ xrvix processing completed successfully!")
        success_count += 1
    except Exception as e:
        print(f"❌ xrvix processing failed: {e}")
    
    # Step 3: Process Semantic Scholar
    print("\n🔬 Step 3/3: Processing Semantic Scholar...")
    try:
        semantic_scraper = SemanticScholarScraper()
        # Set custom keywords for Semantic Scholar scraper
        semantic_scraper.search_keywords = [keyword.strip() for keyword in semantic_keywords.split(',')]
        print(f"   Using keywords: {semantic_keywords}")
        semantic_scraper.run_complete_scraping()
        print("✅ Semantic Scholar processing completed successfully!")
        success_count += 1
    except Exception as e:
        print(f"❌ Semantic Scholar processing failed: {e}")
    
    # Summary
    print(f"\n🎉 Full scraper completed!")
    print(f"✅ Successfully processed: {success_count}/{total_sources} sources")
    
    if success_count == total_sources:
        print("🎯 All sources processed successfully!")
    elif success_count > 0:
        print("⚠️  Some sources failed, but others succeeded.")
    else:
        print("❌ All sources failed. Check error messages above.")

def run_journal_articles_only():
    """Run scraper for journal articles only (PubMed + Semantic Scholar)."""
    print("\n📚 Starting Journal Articles Scraper (PubMed + Semantic Scholar)")
    print("="*60)
    
    # Get custom keywords from user
    pubmed_keywords, semantic_keywords = get_search_keywords()
    if pubmed_keywords is None or semantic_keywords is None:
        return
    
    success_count = 0
    total_sources = 2  # PubMed + Semantic Scholar
    
    # Step 1: Process PubMed
    print("\n📚 Step 1/2: Processing PubMed...")
    try:
        print(f"   Using keywords: {pubmed_keywords}")
        print("   🔍 Searching until no more unique papers found for each keyword")
        
        process_pubmed()
        print("✅ PubMed processing completed successfully!")
        success_count += 1
    except Exception as e:
        print(f"❌ PubMed processing failed: {e}")
    
    # Step 2: Process Semantic Scholar
    print("\n🔬 Step 2/2: Processing Semantic Scholar...")
    try:
        semantic_scraper = SemanticScholarScraper()
        # Use unified keyword parsing to ensure consistency with PubMed
        search_keywords = parse_unified_keywords(semantic_keywords)
        semantic_scraper.search_keywords = search_keywords
        print(f"   Using keywords: {', '.join(search_keywords)}")
        semantic_scraper.run_complete_scraping()
        print("✅ Semantic Scholar processing completed successfully!")
        success_count += 1
    except Exception as e:
        print(f"❌ Semantic Scholar processing failed: {e}")
    
    # Summary
    print(f"\n🎉 Journal articles scraper completed!")
    print(f"✅ Successfully processed: {success_count}/{total_sources} sources")

def run_preprints_only():
    """Run scraper for preprints only (Biorxiv, Medrxiv)."""
    print("\n📄 Starting Preprints Scraper (Biorxiv, Medrxiv)")
    print("="*60)
    
    print("ℹ️  Note: Preprint processing uses existing dump files.")
    print("   Custom keywords are not applicable for this option.")
    print("   The system will process all available preprint data.")
    print()
    
    try:
        # Check if dump files exist
        dump_dir = "data/scraped_data/paperscraper_dumps"
        server_dumps_dir = os.path.join(dump_dir, "server_dumps")
        
        # Check for dump files in the correct location
        biorxiv_dumps = []
        medrxiv_dumps = []
        
        if os.path.exists(server_dumps_dir):
            biorxiv_dumps = [f for f in os.listdir(server_dumps_dir) if f.startswith('biorxiv') and f.endswith('.jsonl')]
            medrxiv_dumps = [f for f in os.listdir(server_dumps_dir) if f.startswith('medrxiv') and f.endswith('.jsonl')]
        
        if not biorxiv_dumps and not medrxiv_dumps:
            print("❌ No preprint dumps found!")
            print("💡 Downloading latest preprint dumps automatically...")
            print()
            
            # Automatically download dumps
            from src.scrapers.xrvix_downloader import XRXivDownloader
            downloader = XRXivDownloader()
            success = downloader.download_all_dumps()
            
            if not success:
                print("❌ Failed to download preprint dumps!")
                print("💡 Please check your internet connection and try again")
                return
            
            print("✅ Preprint dumps downloaded successfully!")
            print("🔄 Now processing the downloaded dumps...")
            print()
        else:
            print(f"✅ Found {len(biorxiv_dumps)} Biorxiv dumps and {len(medrxiv_dumps)} Medrxiv dumps")
            print("🔄 Processing existing dumps...")
            print()
        
        confirm = input("Proceed with preprint processing? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Preprint processing cancelled.")
            return
        
        process_xrvix()
        print("✅ Preprints processing completed successfully!")
    except Exception as e:
        print(f"❌ Preprints processing failed: {e}")
        print("💡 Make sure you have an internet connection for downloading dumps")

def cleanup_autosave_files(pubmed_dir):
    """Clean up autosave files after embedding generation is complete."""
    try:
        import glob
        
        # Find all autosave files
        autosave_pattern = os.path.join(pubmed_dir, "pubmed_autosave_*.jsonl")
        autosave_files = glob.glob(autosave_pattern)
        
        if autosave_files:
            print(f"\n🧹 Found {len(autosave_files)} autosave files:")
            for autosave_file in autosave_files:
                file_size = os.path.getsize(autosave_file)
                print(f"   - {os.path.basename(autosave_file)} ({file_size:,} bytes)")
            
            print("💡 Note: Autosave files are intermediate files created during scraping.")
            print("   They're automatically cleaned up since the final data is preserved.")
            
            # Automatically clean up autosave files (they're just intermediate files)
            print("🧹 Automatically cleaning up autosave files...")
            
            cleaned_count = 0
            for autosave_file in autosave_files:
                try:
                    os.remove(autosave_file)
                    cleaned_count += 1
                    print(f"   ✅ Deleted: {os.path.basename(autosave_file)}")
                except Exception as e:
                    print(f"   ⚠️  Could not delete {os.path.basename(autosave_file)}: {e}")
            
            print(f"🧹 Cleaned up {cleaned_count} autosave files")
        else:
            print("🧹 No autosave files found to clean up")
            
    except Exception as e:
        print(f"⚠️  Error during autosave cleanup: {e}")

def generate_embeddings():
    """Generate embeddings for processed data using unified EmbeddingsClient."""
    from src.core.embeddings_client import EmbeddingsClient
    from src.core.config_loader import load_execution_config
    
    print("\n🔄 Starting Embedding Generation...")
    print("="*60)
    
    try:
        # Display configuration
        config = load_execution_config()
        embeddings_config = config.get_embeddings_config()
        print(f"\n📊 Embeddings Configuration:")
        print(f"   Provider: {embeddings_config.get('provider', 'google')}")
        print(f"   Model: {embeddings_config.get('model_name', 'text-embedding-004')}")
        
        # Initialize embeddings client
        try:
            embeddings_client = EmbeddingsClient()
            print("✅ Embeddings client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize embeddings client: {e}")
            print("💡 Check your configuration in config/LLM_config.json or config/keys.json")
            return
        
        # Check if we have PubMed data to process
        pubmed_files = []
        pubmed_dir = "data/scraped_data/pubmed"
        if os.path.exists(pubmed_dir):
            pubmed_files = [f for f in os.listdir(pubmed_dir) if f.endswith('.jsonl')]
        
        if not pubmed_files:
            print("❌ No PubMed data files found")
            print("💡 Run PubMed scraping (option 1) first to generate data")
            return
        
        print(f"\n📚 Found {len(pubmed_files)} PubMed data files:")
        for file in pubmed_files:
            file_path = os.path.join(pubmed_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"   - {file} ({file_size:,} bytes)")
        
        # Ask user which file to process
        print("\n📋 Available PubMed files:")
        for i, file in enumerate(pubmed_files, 1):
            print(f"   {i}. {file}")
        
        try:
            choice = input(f"\nSelect file to process (1-{len(pubmed_files)}) or 'all' for all files: ").strip()
            
            if choice.lower() == 'all':
                selected_files = pubmed_files
            else:
                file_index = int(choice) - 1
                if 0 <= file_index < len(pubmed_files):
                    selected_files = [pubmed_files[file_index]]
                else:
                    print("❌ Invalid selection")
                    return
        except ValueError:
            print("❌ Invalid input")
            return
        
        print(f"\n🚀 Processing {len(selected_files)} file(s)...")
        
        # Import and run the PubMed embedding generation
        import sys
        sys.path.append('src/scrapers')
        from pubmed_scraper_json import process_existing_pubmed_data
        
        # Run the embedding generation for each selected file
        for file in selected_files:
            print(f"\n📄 Processing {file}...")
            file_path = os.path.join(pubmed_dir, file)
            
            # Process the existing data file
            success = process_existing_pubmed_data(file_path, google_api_key)
            
            if success:
                print(f"✅ Successfully processed {file}")
            else:
                print(f"❌ Failed to process {file}")
        
        print("\n✅ Embedding generation completed!")
        
        # Clean up autosave files
        cleanup_autosave_files(pubmed_dir)
        
        print("💡 You can now load embeddings into ChromaDB (option 5)")
        
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        import traceback
        traceback.print_exc()

def load_embeddings():
    """Load embeddings into ChromaDB."""
    print("\n🗄️ Loading embeddings into ChromaDB...")
    print("="*60)
    
    try:
        # Initialize ChromaDB manager
        manager = ChromaDBManager()
        
        # Create collection
        if not manager.create_collection():
            print("❌ Failed to create ChromaDB collection")
            return False
        
        # Check if collection already has data
        stats = manager.get_collection_stats()
        if stats.get('total_documents', 0) > 0:
            print(f"📚 ChromaDB already has {stats.get('total_documents', 0)} documents!")
            print("💡 ChromaDB uses persistent storage - data is already saved locally.")
            
            # Ask user if they want to reload anyway
            reload_choice = input("\nDo you want to reload the data anyway? (y/n): ").strip().lower()
            if reload_choice != 'y':
                print("✅ Using existing ChromaDB data.")
                return True
        
        total_loaded = 0
        
        # Load PubMed embeddings from batch files
        pubmed_batch_dir = "data/embeddings/pubmed"
        pubmed_single_file = "data/embeddings/xrvix_embeddings/pubmed_embeddings.json"
        
        # First try to load from batch files (newer format)
        if os.path.exists(pubmed_batch_dir):
            batch_files = [f for f in os.listdir(pubmed_batch_dir) if f.startswith("batch_") and f.endswith(".json")]
            if batch_files:
                print(f"🔄 Loading PubMed embeddings from {len(batch_files)} batch files...")
                if manager.add_embeddings_from_directory(pubmed_batch_dir, sources=["pubmed"], db_batch_size=DB_BATCH_SIZE):
                    stats = manager.get_collection_stats()
                    total_docs = stats.get('total_documents', 0)
                    print(f"✅ Loaded PubMed embeddings from batch files (total documents: {total_docs})")
                    total_loaded = total_docs
                else:
                    print("❌ Failed to load PubMed embeddings from batch files")
        
        # Fallback to single file (legacy format)
        elif os.path.exists(pubmed_single_file):
            print("🔄 Loading PubMed embeddings from single file...")
            pubmed_data = manager.load_embeddings_from_json(pubmed_single_file)
            if pubmed_data:
                if manager.add_embeddings_to_collection(pubmed_data, "pubmed"):
                    total_loaded += len(pubmed_data.get('embeddings', []))
                    print(f"✅ Loaded {len(pubmed_data.get('embeddings', []))} PubMed embeddings")
        
        # Load all embeddings from xrvix directory (auto-detects all sources)
        xrvix_path = "data/embeddings/xrvix_embeddings"
        if os.path.exists(xrvix_path):
            print("🔄 Loading all embeddings from xrvix directory (auto-detecting sources)...")
            if manager.add_embeddings_from_directory(xrvix_path, db_batch_size=DB_BATCH_SIZE):
                stats = manager.get_collection_stats()
                total_docs = stats.get('total_documents', 0)
                print(f"✅ Loaded all embeddings (total documents: {total_docs})")
                total_loaded = total_docs
        
        if total_loaded == 0:
            print("⚠️  No data was loaded. Make sure you have processed some data first.")
            return False
        
        # Display final statistics
        stats = manager.get_collection_stats()
        print(f"\n📊 Vector Database Statistics:")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Collection name: {stats.get('collection_name', 'N/A')}")
        
        print(f"\n✅ Successfully loaded {total_loaded} embeddings into vector database!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading data into vector database: {e}")
        return False

def show_chromadb_data():
    """Show current ChromaDB data."""
    print("\n🗄️ Current ChromaDB Data:")
    print("="*60)
    
    try:
        manager = ChromaDBManager()
        collections = manager.list_collections()
        
        if not collections:
            print("❌ No collections found in ChromaDB")
            print("💡 Run option 5 to load data into ChromaDB")
            return
        
        print(f"✅ ChromaDB is available with {len(collections)} collection(s)")
        
        # Check each collection
        for collection_name in collections:
            print(f"\n📚 Collection: {collection_name}")
            
            if not manager.switch_collection(collection_name):
                print("   ❌ Failed to access collection")
                continue
            
            # Get statistics
            stats = manager.get_collection_stats()
            total_docs = stats.get('total_documents', 0)
            print(f"   📊 Total documents: {total_docs}")
            
            if total_docs == 0:
                print("   ⚠️  Collection is empty")
            else:
                print("   ✅ Collection has data - ready for searching!")
                
                # Show source breakdown
                batch_stats = manager.get_batch_statistics()
                if batch_stats and batch_stats.get('sources'):
                    print("   📦 Source breakdown:")
                    for source, source_stats in batch_stats['sources'].items():
                        print(f"      {source}: {source_stats['total_documents']} documents")
        
        print(f"\n💡 ChromaDB uses persistent storage - data is saved locally")
        
    except Exception as e:
        print(f"❌ Error checking ChromaDB status: {e}")

def clear_chromadb_data():
    """Clear ChromaDB data."""
    print("\n🗑️ Clearing ChromaDB Data:")
    print("="*60)
    
    try:
        manager = ChromaDBManager()
        
        # Initialize collection first to ensure it's accessible
        if manager.create_collection():
            if manager.clear_collection():
                print("✅ ChromaDB collection cleared successfully!")
            else:
                print("❌ Failed to clear ChromaDB collection")
        else:
            print("❌ Failed to initialize ChromaDB collection")
            
    except Exception as e:
        print(f"❌ Error clearing ChromaDB: {e}")

def show_data_status():
    """Show the status of available data."""
    print("\n📊 Data Status Overview:")
    print("=" * 50)
    
    # Check PubMed data
    print("\n📚 PubMed Data (Journal Articles):")
    pubmed_path = "data/embeddings/xrvix_embeddings/pubmed_embeddings.json"
    if os.path.exists(pubmed_path):
        try:
            with open(pubmed_path, 'r') as f:
                pubmed_data = json.load(f)
                pubmed_count = len(pubmed_data.get('embeddings', []))
                size = os.path.getsize(pubmed_path) / 1024
                print(f"   ✅ Available: {pubmed_count} papers ({size:.1f} KB)")
        except Exception as e:
            print(f"   ⚠️  Available but error reading: {e}")
    else:
        print("   ❌ Not available")
    
    # Check Biorxiv data
    print("\n📄 Biorxiv Data (Preprints):")
    biorxiv_path = "data/embeddings/xrvix_embeddings/biorxiv"
    if os.path.exists(biorxiv_path):
        try:
            batch_files = [f for f in os.listdir(biorxiv_path) if f.startswith("batch_") and f.endswith(".json")]
            print(f"   ✅ Available: {len(batch_files)} batch files")
            if batch_files:
                # Try to get total count from first batch
                first_batch = os.path.join(biorxiv_path, batch_files[0])
                with open(first_batch, 'r') as f:
                    batch_data = json.load(f)
                    sample_count = len(batch_data.get('embeddings', []))
                    estimated_total = sample_count * len(batch_files)
                    print(f"   📊 Estimated papers: ~{estimated_total}")
        except Exception as e:
            print(f"   ⚠️  Available but error reading: {e}")
    else:
        print("   ❌ Not available")
    
    # Check Medrxiv data
    print("\n📄 Medrxiv Data (Preprints):")
    medrxiv_path = "data/embeddings/xrvix_embeddings/medrxiv"
    if os.path.exists(medrxiv_path):
        try:
            batch_files = [f for f in os.listdir(medrxiv_path) if f.startswith("batch_") and f.endswith(".json")]
            print(f"   ✅ Available: {len(batch_files)} batch files")
            if batch_files:
                # Try to get total count from first batch
                first_batch = os.path.join(medrxiv_path, batch_files[0])
                with open(first_batch, 'r') as f:
                    batch_data = json.load(f)
                    sample_count = len(batch_data.get('embeddings', []))
                    estimated_total = sample_count * len(batch_files)
                    print(f"   📊 Estimated papers: ~{estimated_total}")
        except Exception as e:
            print(f"   ⚠️  Available but error reading: {e}")
    else:
        print("   ❌ Not available")
    
    # Check Semantic Scholar API data
    print("\n🔬 Semantic Scholar API Data:")
    semantic_path = "data/embeddings/semantic_scholar"
    if os.path.exists(semantic_path):
        try:
            paper_files = [f for f in os.listdir(semantic_path) if f.endswith('.json') and f != 'metadata.json']
            metadata_file = os.path.join(semantic_path, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    semantic_data = json.load(f)
                    semantic_count = semantic_data.get('total_papers', 0)
                    print(f"   ✅ Available: {semantic_count} papers")
            else:
                print(f"   ✅ Available: {len(paper_files)} individual paper files")
        except Exception as e:
            print(f"   ⚠️  Available but error reading: {e}")
    else:
        print("   ❌ Not available")
    
    # Check ChromaDB
    print("\n🗄️ ChromaDB Vector Database:")
    if os.path.exists("data/vector_db/chroma_db"):
        try:
            manager = ChromaDBManager()
            collections = manager.list_collections()
            if collections:
                stats = manager.get_collection_stats()
                total_docs = stats.get('total_documents', 0)
                print(f"   ✅ Available: {total_docs} documents")
            else:
                print("   ⚠️  Available but empty")
        except Exception as e:
            print(f"   ⚠️  Available but error accessing: {e}")
    else:
        print("   ❌ Not available")
    
    print("\n💡 Recommendations:")
    print("   • Use options 1-3 to collect missing data sources")
    print("   • Use option 5 to load data into ChromaDB")
    print("   • Use option 10 to generate hypotheses")

def show_configurations():
    """Show current configurations."""
    print("\n⚙️ Current Configurations:")
    print("="*60)
    print_config_info()

def generate_hypotheses():
    """Launch the hypothesis generation system."""
    print("\n🧠 Starting Hypothesis Generation System...")
    print("="*60)
    
    try:
        # Check if ChromaDB has data
        manager = ChromaDBManager()
        collections = manager.list_collections()
        
        if not collections:
            print("❌ No ChromaDB collections found")
            print("💡 Run option 5 to load data into ChromaDB first")
            return
        
        # Ensure collection is properly initialized
        if not manager.create_collection():
            print("❌ Failed to initialize ChromaDB collection")
            return
        
        stats = manager.get_collection_stats()
        if stats.get('total_documents', 0) == 0:
            print("❌ ChromaDB is empty")
            print("💡 Run option 5 to load data into ChromaDB first")
            return
        
        print(f"✅ ChromaDB has {stats.get('total_documents', 0)} documents")
        print("🚀 Launching Enhanced RAG System...")
        
        # Launch the enhanced RAG system
        subprocess.run([sys.executable, "src/ai/enhanced_rag_with_chromadb.py"])
        
    except Exception as e:
        print(f"❌ Failed to launch hypothesis generation system: {e}")

def test_run_research():
    """Run a test with configured research focus."""
    print("\n🧪 Test Run: Biomedical Research")
    print("="*60)
    
    try:
        # Check if ChromaDB has data
        manager = ChromaDBManager()
        collections = manager.list_collections()
        
        if not collections:
            print("❌ No ChromaDB collections found")
            print("💡 Run option 5 to load data into ChromaDB first")
            return
        
        # Ensure collection is properly initialized
        if not manager.create_collection():
            print("❌ Failed to initialize ChromaDB collection")
            return
        
        stats = manager.get_collection_stats()
        if stats.get('total_documents', 0) == 0:
            print("❌ ChromaDB is empty")
            print("💡 Run option 5 to load data into ChromaDB first")
            return
        
        print(f"✅ ChromaDB has {stats.get('total_documents', 0)} documents")
        print("🧪 Running test query: 'protein function and disease'")
        
        # Launch the enhanced RAG system with a test query
        print("🚀 Launching Enhanced RAG System for test run...")
        subprocess.run([sys.executable, "src/ai/enhanced_rag_with_chromadb.py"])
        
    except Exception as e:
        print(f"❌ Failed to run test: {e}")

def execute_with_debug_logging(func, *args, **kwargs):
    """Execute a function with comprehensive debug logging and error handling."""
    global DEBUG_LOGGING_ENABLED
    
    logger.info(f"Starting execution: {func.__name__}")
    logger.debug(f"Function: {func.__name__}, Args: {args}, Kwargs: {kwargs}")
    
    try:
        # Capture stdout and stderr for detailed logging
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            result = func(*args, **kwargs)
        
        # Log captured output
        stdout_content = stdout_capture.getvalue()
        stderr_content = stderr_capture.getvalue()
        
        if stdout_content:
            logger.debug(f"STDOUT from {func.__name__}:\n{stdout_content}")
        if stderr_content:
            logger.debug(f"STDERR from {func.__name__}:\n{stderr_content}")
        
        logger.info(f"Successfully completed: {func.__name__}")
        return result
        
    except Exception as e:
        # Log the full error with stack trace
        logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
        
        # Display raw error information
        print(f"\n🔍 RAW ERROR DETAILS:")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"\nFull Stack Trace:")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        
        # Also log to file
        logger.error(f"Full stack trace for {func.__name__}:", exc_info=True)
        
        return None

def main():
    """Main function with the new menu structure."""
    print("🚀 Welcome to AI Research Processor!")
    print("💡 AI-Powered Scientific Hypothesis Generator for Biomedical Research")
    print("📚 This system helps generate novel research hypotheses from scientific literature")
    print(f"🔧 Debug Logging: {'ENABLED' if DEBUG_LOGGING_ENABLED else 'DISABLED'}")
    
    while True:
        try:
            show_menu()
            choice = get_user_choice()
            
            logger.info(f"User selected option: {choice}")
            
            if choice == 1:
                execute_with_debug_logging(run_full_scraper)
                
            elif choice == 2:
                execute_with_debug_logging(run_journal_articles_only)
                
            elif choice == 3:
                execute_with_debug_logging(run_preprints_only)
                
            elif choice == 4:
                execute_with_debug_logging(generate_embeddings)
                
            elif choice == 5:
                execute_with_debug_logging(load_embeddings)
                
            elif choice == 6:
                execute_with_debug_logging(show_chromadb_data)
                
            elif choice == 7:
                execute_with_debug_logging(clear_chromadb_data)
                
            elif choice == 8:
                execute_with_debug_logging(show_data_status)
                
            elif choice == 9:
                execute_with_debug_logging(show_configurations)
                
            elif choice == 10:
                execute_with_debug_logging(generate_hypotheses)
                
            elif choice == 11:
                execute_with_debug_logging(test_run_research)
                
            elif choice == 12:
                toggle_debug_logging()
                
            elif choice == 13:
                view_debug_log()
                
            elif choice == 14:
                clear_debug_logs()
                
            elif choice == 15:
                print("\n👋 Goodbye! Thank you for using AI Research Processor!")
                logger.info("User exited the application")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                logger.warning(f"Invalid choice entered: {choice}")
            
            if choice not in [12, 13, 14, 15]:  # Don't pause for debug/logging options
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Application interrupted by user")
            logger.info("Application interrupted by user (Ctrl+C)")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in main loop: {e}")
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            print("\n🔍 RAW ERROR DETAILS:")
            print("="*60)
            traceback.print_exc()
            print("="*60)
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
