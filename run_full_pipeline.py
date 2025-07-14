#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Full Pipeline Runner for Coffee Roasters
Iterates through each roaster in roasters_input.csv, runs scraper and product scraper,
and waits for user confirmation before moving to the next.

Usage:
    python run_full_pipeline.py [options]

Options:
    --start-from <name>     Start from a specific roaster name
    --limit <number>        Limit number of roasters to process
    --skip-roaster          Skip roaster scraping, only do products
    --skip-products         Skip product scraping, only do roasters
    --no-enrichment         Disable LLM enrichment for products
    --dry-run              Show what would be done without making changes
    --auto-continue        Don't wait for user confirmation (auto-continue)
    --push-to-supabase     Automatically push results to Supabase after each roaster
"""

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

from loguru import logger


class FullPipelineRunner:
    def __init__(self, args):
        self.args = args
        self.roasters_file = "data/input/roasters_input.csv"
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "roasters").mkdir(exist_ok=True)
        (self.output_dir / "products").mkdir(exist_ok=True)
        
        self.processed_count = 0
        self.successful_count = 0
        self.failed_count = 0

    def load_roasters(self) -> List[Dict[str, str]]:
        """Load roasters from CSV file."""
        roasters = []
        
        with open(self.roasters_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                roasters.append({
                    'name': row['name'].strip(),
                    'website_url': row['website_url'].strip()
                })
        
        return roasters

    def filter_roasters(self, roasters: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filter roasters based on command line arguments."""
        filtered = roasters
        
        # Start from specific roaster
        if self.args.start_from:
            start_index = None
            for i, roaster in enumerate(filtered):
                if roaster['name'].lower() == self.args.start_from.lower():
                    start_index = i
                    break
            
            if start_index is not None:
                filtered = filtered[start_index:]
                logger.info(f"Starting from roaster: {filtered[0]['name']}")
            else:
                logger.warning(f"Roaster '{self.args.start_from}' not found, starting from beginning")
        
        # Apply limit
        if self.args.limit:
            filtered = filtered[:self.args.limit]
            logger.info(f"Limited to {self.args.limit} roasters")
        
        return filtered

    def run_command(self, cmd: List[str], description: str) -> bool:
        """Run a subprocess command and return success status."""
        logger.info(f"Running: {description}")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"✅ {description} completed successfully")
            if result.stdout.strip():
                logger.debug(f"Output: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {description} failed with exit code {e.returncode}")
            if e.stdout.strip():
                logger.error(f"stdout: {e.stdout.strip()}")
            if e.stderr.strip():
                logger.error(f"stderr: {e.stderr.strip()}")
            return False

    def run_roaster_scraper(self, roaster: Dict[str, str]) -> Optional[str]:
        """Run roaster scraper for a single roaster."""
        if self.args.skip_roaster:
            logger.info("Skipping roaster scraping (--skip-roaster)")
            return None
        
        roaster_name = roaster['name']
        website_url = roaster['website_url']
        
        # Create safe filename
        safe_name = roaster_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        roaster_output = self.output_dir / "roasters" / f"{safe_name}_roaster.json"
        
        # Run roaster scraper
        cmd = [
            "python", "run_roaster.py",
            "--single",
            "--input", f"{roaster_name},{website_url}",
            "--output", str(roaster_output)
        ]
        
        success = self.run_command(cmd, f"Roaster scraper for {roaster_name}")
        
        if success and roaster_output.exists():
            return str(roaster_output)
        else:
            logger.error(f"Roaster scraper failed for {roaster_name}")
            return None

    def run_product_scraper(self, roaster: Dict[str, str], roaster_file: Optional[str] = None) -> Optional[str]:
        """Run product scraper for a roaster."""
        if self.args.skip_products:
            logger.info("Skipping product scraping (--skip-products)")
            return None
        
        roaster_name = roaster['name']
        website_url = roaster['website_url']
        
        # Create safe filename
        safe_name = roaster_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        products_output = self.output_dir / "products" / f"{safe_name}_products.json"
        
        # Build command
        cmd = ["python", "run_product_scraper.py", "batch"]
        
        if roaster_file and Path(roaster_file).exists():
            # Use roaster file if available
            cmd.extend(["--roasters", roaster_file])
        else:
            # Use roaster link directly
            cmd.extend(["--roaster-link", website_url])
        
        cmd.extend(["--output", str(products_output)])
        
        if self.args.no_enrichment:
            cmd.append("--no-enrichment")
        
        success = self.run_command(cmd, f"Product scraper for {roaster_name}")
        
        if success and products_output.exists():
            return str(products_output)
        else:
            logger.error(f"Product scraper failed for {roaster_name}")
            return None

    def push_to_supabase(self, roaster_file: Optional[str], products_file: Optional[str]) -> bool:
        """Push results to Supabase."""
        if not self.args.push_to_supabase:
            return True
        
        if not roaster_file and not products_file:
            logger.warning("No files to push to Supabase")
            return True
        
        cmd = ["python", "push_to_supabase.py"]
        
        if roaster_file and products_file:
            cmd.extend(["--type", "both", "--roasters-file", roaster_file, "--products-file", products_file])
        elif roaster_file:
            cmd.extend(["--type", "roasters", "--roasters-file", roaster_file])
        elif products_file:
            cmd.extend(["--type", "products", "--products-file", products_file])
        
        if self.args.dry_run:
            cmd.append("--dry-run")
        
        return self.run_command(cmd, "Push to Supabase")

    def wait_for_confirmation(self, roaster: Dict[str, str]) -> bool:
        """Wait for user confirmation to continue."""
        if self.args.auto_continue:
            return True
        
        roaster_name = roaster['name']
        
        print("\n" + "=" * 60)
        print(f"COMPLETED: {roaster_name}")
        print("=" * 60)
        
        while True:
            response = input("\nContinue to next roaster? (y/n/s to skip/quit): ").lower().strip()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', 'quit', 'q']:
                logger.info("User requested to stop")
                return False
            elif response in ['s', 'skip']:
                logger.info(f"Skipping {roaster_name}")
                return True
            else:
                print("Please enter 'y' (yes), 'n' (no/quit), or 's' (skip)")

    def process_roaster(self, roaster: Dict[str, str]) -> bool:
        """Process a single roaster through the full pipeline."""
        roaster_name = roaster['name']
        website_url = roaster['website_url']
        
        self.processed_count += 1
        
        print(f"\n{'='*80}")
        print(f"PROCESSING ROASTER {self.processed_count}: {roaster_name}")
        print(f"Website: {website_url}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Step 1: Run roaster scraper
            roaster_file = self.run_roaster_scraper(roaster)
            
            # Step 2: Run product scraper
            products_file = self.run_product_scraper(roaster, roaster_file)
            
            # Step 3: Push to Supabase (if requested)
            if self.args.push_to_supabase:
                self.push_to_supabase(roaster_file, products_file)
            
            # Step 4: Show results
            elapsed_time = time.time() - start_time
            print(f"\n✅ Completed {roaster_name} in {elapsed_time:.1f} seconds")
            
            if roaster_file:
                print(f"   Roaster data: {roaster_file}")
            if products_file:
                print(f"   Products data: {products_file}")
            
            self.successful_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing {roaster_name}: {e}")
            self.failed_count += 1
            return False

    def run(self):
        """Run the full pipeline."""
        logger.info("Starting Full Pipeline Runner")
        
        # Load and filter roasters
        roasters = self.load_roasters()
        logger.info(f"Loaded {len(roasters)} roasters from {self.roasters_file}")
        
        filtered_roasters = self.filter_roasters(roasters)
        logger.info(f"Processing {len(filtered_roasters)} roasters")
        
        if self.args.dry_run:
            logger.info("DRY RUN MODE - No actual scraping will be performed")
        
        # Process each roaster
        for roaster in filtered_roasters:
            success = self.process_roaster(roaster)
            
            if not success:
                logger.error(f"Failed to process {roaster['name']}")
            
            # Wait for user confirmation
            if not self.wait_for_confirmation(roaster):
                break
        
        # Print final summary
        self.print_summary()

    def print_summary(self):
        """Print final summary of the pipeline run."""
        print("\n" + "=" * 80)
        print("FULL PIPELINE SUMMARY")
        print("=" * 80)
        print(f"Total roasters processed: {self.processed_count}")
        print(f"Successful: {self.successful_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Success rate: {(self.successful_count/self.processed_count*100):.1f}%" if self.processed_count > 0 else "N/A")
        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Full Pipeline Runner for Coffee Roasters")
    
    parser.add_argument("--start-from", help="Start from a specific roaster name")
    parser.add_argument("--limit", type=int, help="Limit number of roasters to process")
    parser.add_argument("--skip-roaster", action="store_true", help="Skip roaster scraping, only do products")
    parser.add_argument("--skip-products", action="store_true", help="Skip product scraping, only do roasters")
    parser.add_argument("--no-enrichment", action="store_true", help="Disable LLM enrichment for products")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--auto-continue", action="store_true", help="Don't wait for user confirmation (auto-continue)")
    parser.add_argument("--push-to-supabase", action="store_true", help="Automatically push results to Supabase after each roaster")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.skip_roaster and args.skip_products:
        logger.error("Cannot skip both roaster and product scraping")
        return 1
    
    # Run the pipeline
    runner = FullPipelineRunner(args)
    runner.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())