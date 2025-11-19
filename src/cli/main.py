"""
Command-Line Interface for AHGA Research Processor
Supports distributed deployment with machine profiles
"""
import click
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config_loader import (
    load_execution_config,
    display_configuration,
    get_machine_profile,
    list_available_profiles,
    validate_profile
)


# Global options
@click.group()
@click.option('--profile', '-p', default='auto', 
              help='Machine profile (m3, mystery, auto, or none)')
@click.option('--verbose', '-v', is_flag=True, 
              help='Verbose output')
@click.option('--quiet', '-q', is_flag=True, 
              help='Quiet mode')
@click.pass_context
def cli(ctx, profile, verbose, quiet):
    """AHGA Research Processor - AI-powered hypothesis generation system"""
    ctx.ensure_object(dict)
    ctx.obj['profile'] = profile
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    # Load configuration with profile
    config = load_execution_config(profile=profile)
    ctx.obj['config'] = config


#############################################################################
# Config Commands
#############################################################################

@cli.group()
def config():
    """Configuration management"""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Display current configuration"""
    display_configuration()


@config.command('list-profiles')
def config_list_profiles():
    """List available machine profiles"""
    profiles = list_available_profiles()
    
    if not profiles:
        click.echo("No machine profiles found in deploy/ directory")
        return
    
    click.echo("\nAvailable machine profiles:")
    for profile in profiles:
        click.echo(f"  - {profile}")
    
    current = get_machine_profile()
    if current:
        click.echo(f"\nCurrent profile: {current}")
    else:
        click.echo("\nNo profile currently active")


@config.command('validate')
@click.argument('profile_name', required=False)
@click.pass_context
def config_validate(ctx, profile_name):
    """Validate a machine profile"""
    if not profile_name:
        profile_name = ctx.obj['profile']
    
    if validate_profile(profile_name):
        click.secho(f"✅ Profile '{profile_name}' is valid", fg='green')
    else:
        click.secho(f"❌ Profile '{profile_name}' is invalid", fg='red')
        sys.exit(1)


@config.command('test-connectivity')
@click.pass_context
def config_test_connectivity(ctx):
    """Test connectivity to distributed services"""
    import requests
    from src.core.config_loader import get_chromadb_config, get_llm_config
    
    config = ctx.obj['config']
    click.echo("\n" + "="*60)
    click.echo("Connectivity Tests")
    click.echo("="*60 + "\n")
    
    # Test ChromaDB
    chromadb_config = get_chromadb_config()
    if config.is_distributed or config.execution_mode == "chromadb_server":
        host = chromadb_config.get('host', 'localhost')
        port = chromadb_config.get('port', 8000)
        
        click.echo(f"Testing ChromaDB at {host}:{port}...")
        try:
            response = requests.get(f"http://{host}:{port}/api/v1/heartbeat", timeout=5)
            if response.status_code == 200:
                click.secho(f"✅ ChromaDB is responding", fg='green')
            else:
                click.secho(f"❌ ChromaDB returned status {response.status_code}", fg='red')
        except Exception as e:
            click.secho(f"❌ Cannot connect to ChromaDB: {e}", fg='red')
    else:
        click.echo("ChromaDB: Local mode (no network test needed)")
    
    # Test LLM server
    llm_config = get_llm_config()
    if llm_config.get('provider') == 'local':
        api_base = llm_config.get('api_base', 'http://localhost:11434')
        
        click.echo(f"\nTesting LLM server at {api_base}...")
        try:
            response = requests.get(f"{api_base}/v1/models", timeout=5)
            if response.status_code == 200:
                click.secho(f"✅ LLM server is responding", fg='green')
                models = response.json()
                if 'data' in models:
                    click.echo(f"   Available models: {len(models['data'])}")
            else:
                click.secho(f"❌ LLM server returned status {response.status_code}", fg='red')
        except Exception as e:
            click.secho(f"❌ Cannot connect to LLM server: {e}", fg='red')
    else:
        click.echo("\nLLM: Using Google Gemini API (cloud-based)")
    
    click.echo("\n" + "="*60 + "\n")


#############################################################################
# Scrape Commands (Placeholder - extend as needed)
#############################################################################

@cli.group()
def scrape():
    """Data scraping commands"""
    pass


@scrape.command('full')
@click.option('--pubmed-keywords', help='PubMed search keywords')
@click.option('--max-results', default=100, help='Maximum results per source')
@click.pass_context
def scrape_full(ctx, pubmed_keywords, max_results):
    """Scrape all data sources"""
    click.echo(f"Starting full scrape (profile: {ctx.obj['profile']})")
    click.echo(f"Keywords: {pubmed_keywords}")
    click.echo(f"Max results: {max_results}")
    click.echo("\nNote: Full implementation requires integration with existing scrapers")


@scrape.command('journals')
@click.option('--keywords', help='Search keywords')
@click.pass_context
def scrape_journals(ctx, keywords):
    """Scrape journal articles only"""
    click.echo(f"Scraping journals (profile: {ctx.obj['profile']})")
    click.echo(f"Keywords: {keywords}")


@scrape.command('preprints')
@click.pass_context
def scrape_preprints(ctx):
    """Scrape preprints only"""
    click.echo(f"Scraping preprints (profile: {ctx.obj['profile']})")


#############################################################################
# Embeddings Commands (Placeholder)
#############################################################################

@cli.group()
def embeddings():
    """Embedding generation and management"""
    pass


@embeddings.command('generate')
@click.pass_context
def embeddings_generate(ctx):
    """Generate embeddings from scraped data"""
    click.echo(f"Generating embeddings (profile: {ctx.obj['profile']})")


@embeddings.command('load')
@click.pass_context
def embeddings_load(ctx):
    """Load embeddings into ChromaDB"""
    click.echo(f"Loading embeddings to ChromaDB (profile: {ctx.obj['profile']})")


#############################################################################
# Database Commands (Placeholder)
#############################################################################

@cli.group()
def db():
    """Database management commands"""
    pass


@db.command('show')
@click.option('--by-source', is_flag=True, help='Show breakdown by source')
@click.pass_context
def db_show(ctx, by_source):
    """Show database statistics"""
    click.echo(f"Database statistics (profile: {ctx.obj['profile']})")
    if by_source:
        click.echo("Breakdown by source...")


@db.command('clear')
@click.confirmation_option(prompt='Are you sure you want to clear the database?')
@click.pass_context
def db_clear(ctx):
    """Clear database"""
    click.echo(f"Clearing database (profile: {ctx.obj['profile']})")


@db.command('status')
@click.pass_context
def db_status(ctx):
    """Show data source status"""
    click.echo(f"Data source status (profile: {ctx.obj['profile']})")


#############################################################################
# Hypothesis Commands (Placeholder)
#############################################################################

@cli.group()
def hypothesis():
    """Hypothesis generation commands"""
    pass


@hypothesis.command('generate')
@click.option('--topic', help='Research topic')
@click.pass_context
def hypothesis_generate(ctx, topic):
    """Generate research hypotheses"""
    click.echo(f"Generating hypotheses (profile: {ctx.obj['profile']})")
    if topic:
        click.echo(f"Topic: {topic}")


@hypothesis.command('test')
@click.option('--query', default='mitochondrial function', help='Test query')
@click.pass_context
def hypothesis_test(ctx, query):
    """Test hypothesis generation"""
    click.echo(f"Test run (profile: {ctx.obj['profile']})")
    click.echo(f"Query: {query}")


#############################################################################
# Service Management Commands
#############################################################################

@cli.group()
def service():
    """Service management commands"""
    pass


@service.command('start')
@click.argument('service_name', type=click.Choice(['vllm', 'chromadb', 'all']))
@click.pass_context
def service_start(ctx, service_name):
    """Start services"""
    profile = ctx.obj['profile']
    
    if service_name == 'vllm' or service_name == 'all':
        if profile == 'm3':
            click.echo("Starting vLLM service...")
            click.echo("  sudo systemctl start vllm")
            click.echo("  OR: ./deploy/m3/start_services.sh")
        else:
            click.secho("⚠️  vLLM service is for M3 machine only", fg='yellow')
    
    if service_name == 'chromadb' or service_name == 'all':
        if profile == 'mystery':
            click.echo("Starting ChromaDB service...")
            click.echo("  sudo systemctl start chromadb")
            click.echo("  OR: ./deploy/mystery/start_services.sh")
        else:
            click.secho("⚠️  ChromaDB service is for Mystery machine only", fg='yellow')


@service.command('stop')
@click.argument('service_name', type=click.Choice(['vllm', 'chromadb', 'all']))
@click.pass_context
def service_stop(ctx, service_name):
    """Stop services"""
    click.echo(f"Stopping {service_name} service...")
    if service_name == 'vllm' or service_name == 'all':
        click.echo("  sudo systemctl stop vllm")
    if service_name == 'chromadb' or service_name == 'all':
        click.echo("  sudo systemctl stop chromadb")


@service.command('status')
@click.argument('service_name', type=click.Choice(['vllm', 'chromadb', 'all']))
@click.pass_context
def service_status(ctx, service_name):
    """Check service status"""
    click.echo(f"Checking {service_name} status...")
    if service_name == 'vllm' or service_name == 'all':
        click.echo("  sudo systemctl status vllm")
    if service_name == 'chromadb' or service_name == 'all':
        click.echo("  sudo systemctl status chromadb")


#############################################################################
# Main Entry Point
#############################################################################

if __name__ == '__main__':
    cli()

