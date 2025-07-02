#!/usr/bin/env python3
"""
Enhanced Job Search Application
Automated job scraping and filtering with email notifications
"""

import os
import sys
import time
import signal
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules
from apify_integration import ApifyJobScraper
from job_search import JobSearch
from email_notifier import EmailNotifier

# Load environment variables
load_dotenv()


class EnhancedJobSearchApp:
    """Main application class for enhanced job searching"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.scraper = ApifyJobScraper(verbose=verbose)
        self.searcher = JobSearch(verbose=verbose)
        self.notifier = EmailNotifier()
        
        # Load configuration from environment
        self.job_titles = self._load_job_titles()
        self.max_results = int(os.getenv('MAX_RESULTS', '100'))
        self.max_age_days = int(os.getenv('MAX_JOB_AGE_DAYS', '7'))
        
        # Scheduling configuration
        self.morning_time = os.getenv('SCHEDULE_MORNING', '09:00')
        self.afternoon_time = os.getenv('SCHEDULE_AFTERNOON', '17:00')
        
        # Track the last run to determine if we should look for newer jobs only
        self.last_run = None
        
    def _load_job_titles(self) -> list:
        """Load job titles from environment variable"""
        job_titles_str = os.getenv('JOB_TITLES', 'Software Engineer')
        return [title.strip() for title in job_titles_str.split(',')]
    
    def run_job_search(self):
        """Execute a complete job search cycle"""
        print(f"\n{'='*60}")
        print(f"🚀 Starting job search at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Determine age filter based on last run
        age_days = self._get_dynamic_age_filter()
        
        print(f"📋 Job titles: {', '.join(self.job_titles)}")
        print(f"🔍 Keywords: {', '.join(self.searcher.keywords)}")
        print(f"📅 Max job age: {age_days} days")
        print(f"📊 Max results per title: {self.max_results}")
        
        try:
            # Step 1: Scrape jobs from Apify
            print(f"\n📡 Step 1: Scraping jobs from Apify...")
            scraped_data = self.scraper.scrape_all_job_titles(
                self.job_titles, 
                self.max_results, 
                age_days,
                verbose=self.verbose
            )
            
            # Step 2: Save scraped data
            print(f"\n💾 Step 2: Saving scraped data...")
            saved_files = self.scraper.save_results_to_file(scraped_data)
            
            # Step 3: Search for matching jobs
            print(f"\n🔍 Step 3: Searching for keyword matches...")
            self.searcher.reset_seen_jobs()  # Fresh search for duplicates
            matches = self.searcher.search_all_jobs(scraped_data, age_days)
            
            # Step 4: Send email notifications if matches found
            total_matches = len(matches.get('seek', [])) + len(matches.get('linkedin', []))
            
            if total_matches > 0:
                print(f"\n📧 Step 4: Sending email notification...")
                if self.notifier.send_notification(matches, self.searcher.keywords):
                    print(f"✅ Email sent successfully!")
                    # Mark jobs as sent to prevent future duplicates
                    self.searcher.mark_jobs_as_sent(matches)
                else:
                    print(f"❌ Failed to send email notification")
            else:
                print(f"\n📧 Step 4: No matches found - skipping email notification")
            
            # Update last run time
            self.last_run = datetime.now()
            
            print(f"\n✅ Job search completed successfully!")
            print(f"📊 Summary: {self.searcher.get_search_summary(matches)}")
            
        except Exception as e:
            print(f"\n❌ Error during job search: {str(e)}")
            print("❌ Job search failed - please check configuration and try again")
    
    def _get_dynamic_age_filter(self) -> int:
        """Determine age filter based on when we last ran"""
        if self.last_run is None:
            # First run - use configured max age
            return self.max_age_days
        
        # Calculate hours since last run
        hours_since_last = (datetime.now() - self.last_run).total_seconds() / 3600
        
        if hours_since_last < 12:
            # Recent run - look for very new jobs only
            return 1
        elif hours_since_last < 24:
            # Run yesterday - look for jobs from last 24 hours
            return 1
        else:
            # Longer time since last run - use configured max age
            return self.max_age_days
    
    def test_configuration(self):
        """Test the application configuration"""
        print("🧪 Testing Enhanced Job Search Configuration...")
        print(f"📋 Job titles: {', '.join(self.job_titles)}")
        print(f"🔍 Keywords: {', '.join(self.searcher.keywords)}")
        print(f"📧 Email: {self.notifier.to_email}")
        print(f"⏰ Schedule: {self.morning_time} and {self.afternoon_time}")
        
        # Test email configuration
        print("\n📧 Testing email configuration...")
        if self.notifier.check_postmark_status():
            print("📧 Sending test email...")
            if self.notifier.send_test_email():
                print("✅ Email test successful!")
            else:
                print("❌ Email test failed - check Postmark configuration")
        else:
            print("❌ Postmark not properly configured - check POSTMARK_API_TOKEN in .env")
        
        print("\n✅ Configuration test completed!")
    
    def run_daemon_mode(self):
        """Run the application in background daemon mode"""
        print(f"🤖 Starting Enhanced Job Search Daemon...")
        print(f"⏰ Scheduled runs: {self.morning_time} and {self.afternoon_time}")
        print(f"📋 Job titles: {', '.join(self.job_titles)}")
        print(f"🔍 Keywords: {', '.join(self.searcher.keywords)}")
        print("Press Ctrl+C to stop")
        
        # Schedule the job searches
        schedule.every().day.at(self.morning_time).do(self.run_job_search)
        schedule.every().day.at(self.afternoon_time).do(self.run_job_search)
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print(f"\n🛑 Received shutdown signal. Exiting gracefully...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Main daemon loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print(f"\n🛑 Daemon mode stopped by user")
        except Exception as e:
            print(f"\n❌ Daemon error: {str(e)}")
    
    def run_once(self):
        """Run job search once and exit"""
        self.run_job_search()
    
    def clear_sent_jobs_history(self):
        """Clear sent jobs history for testing"""
        print("🧹 Clearing sent jobs history...")
        sent_count = self.searcher.get_sent_jobs_count()
        print(f"📊 Currently tracking {sent_count} sent jobs")
        
        self.searcher.clear_sent_jobs_history()
        print("✅ Sent jobs history cleared successfully!")


def main():
    """Main entry point"""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    app = EnhancedJobSearchApp(verbose=verbose)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            app.test_configuration()
        elif command == 'daemon':
            app.run_daemon_mode()
        elif command == 'once' or command == 'run':
            app.run_once()
        elif command == 'clear-history':
            app.clear_sent_jobs_history()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands:")
            print("  test          - Test configuration")
            print("  once          - Run job search once")
            print("  daemon        - Run in background daemon mode")
            print("  clear-history - Clear sent jobs history (for testing)")
            print("  --verbose/-v  - Enable verbose monitoring output")
    else:
        # Default behavior - run once
        app.run_once()


if __name__ == "__main__":
    main()