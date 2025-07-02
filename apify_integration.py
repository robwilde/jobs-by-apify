import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from apify_client import ApifyClient


class ApifyJobScraper:
    """Handles Apify API integration for job scraping"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.client = ApifyClient(os.getenv('APIFY_TOKEN'))
        self.user_id = os.getenv('APIFY_USER_ID')
        
        # Actor IDs
        self.seek_actor_id = 'websift~seek-job-scraper'
        self.linkedin_actor_id = 'bebity~linkedin-jobs-scraper'
    
    def create_seek_input(self, job_title: str, max_results: int = 100, max_age_days: int = 7) -> Dict[str, Any]:
        """Create input configuration for Seek job scraper"""
        # Load base configuration from existing input.json
        base_input_path = '/var/home/mrwilde/Projects/MrWilde/Apps/swe-jobs/jobs-by-apify/jobs-by-apify/actors/SeekJobScraper/input.json'
        
        with open(base_input_path, 'r') as f:
            base_input = json.load(f)
        
        # Get Seek parameters from environment
        seek_salary_min = int(os.getenv('SEEK_SALARY_MIN', '150000'))
        seek_salary_max = int(os.getenv('SEEK_SALARY_MAX', '1000000'))
        seek_work_arrangements = os.getenv('SEEK_WORK_ARRANGEMENTS', 'remote').split(',')
        
        # Update with our parameters
        base_input.update({
            'searchTerm': job_title,
            'suburbOrCity': 'Australia',
            'workArrangements': [arr.strip() for arr in seek_work_arrangements],
            'maxResults': max_results,
            'dateRange': max_age_days,
            'salaryMin': seek_salary_min,
            'salaryMax': seek_salary_max
        })
        
        return base_input
    
    def create_linkedin_input(self, job_title: str, max_results: int = 100, max_age_days: int = 7) -> Dict[str, Any]:
        """Create input configuration for LinkedIn job scraper"""
        # Convert days to LinkedIn's time format
        published_at_map = {
            1: 'r86400',    # 24 hours
            7: 'r604800',   # 1 week  
            30: 'r2592000'  # 1 month
        }
        
        # Find the closest match for max_age_days
        published_at = 'r604800'  # Default to 1 week
        if max_age_days <= 1:
            published_at = 'r86400'
        elif max_age_days <= 7:
            published_at = 'r604800'
        else:
            published_at = 'r2592000'
        
        # Build LinkedIn search parameters from environment
        linkedin_config = {
            'keywords': [job_title],  # Use keywords array as per guide
            'location': os.getenv('LOCATION', 'Australia and New Zealand'),
            'maxResults': min(max_results, 1000),  # Use maxResults instead of rows
            'proxy': {
                'useApifyProxy': True,
                'apifyProxyGroups': ['RESIDENTIAL']
            }
        }
        
        # Add optional work type filter (2=Remote, 1=On-site, 3=Hybrid)
        work_type = os.getenv('LINKEDIN_WORK_TYPE')
        if work_type:
            linkedin_config['workType'] = work_type
        
        # Add optional experience level filter (1=Internship, 2=Entry, 3=Associate, 4=Mid-Senior, 5=Director+)
        experience_level = os.getenv('LINKEDIN_EXPERIENCE_LEVEL')
        if experience_level:
            linkedin_config['experienceLevel'] = experience_level
        
        # Add job type filter (fulltime, parttime, contract, temporary, internship)
        job_type = os.getenv('LINKEDIN_JOB_TYPE')
        if job_type:
            linkedin_config['jobType'] = job_type
        
        # Add date posted filter (day, week, month, anytime) - use this instead of publishedAt
        date_posted = os.getenv('LINKEDIN_DATE_POSTED')
        if date_posted:
            linkedin_config['datePosted'] = date_posted
        else:
            # Keep the old publishedAt as fallback
            linkedin_config['publishedAt'] = published_at
            
        return linkedin_config
    
    def run_seek_scraper(self, job_title: str, max_results: int = 100, max_age_days: int = 7) -> List[Dict[str, Any]]:
        """Run Seek job scraper and return results"""
        print(f"🔍 Running Seek scraper for: {job_title}")
        print("   ⏳ This may take 1-3 minutes to complete...")
        
        input_data = self.create_seek_input(job_title, max_results, max_age_days)
        if self.verbose:
            print(f"📊 VERBOSE: Seek input data: {json.dumps(input_data, indent=2)}")
        
        try:
            # Run the actor and wait for completion
            run = self.client.actor(self.seek_actor_id).call(run_input=input_data)
            if self.verbose:
                print(f"📊 VERBOSE: Seek actor run ID: {run.get('id', 'unknown')}")
            
            # Get the results
            dataset_id = run['defaultDatasetId']
            if self.verbose:
                print(f"📊 VERBOSE: Seek dataset ID: {dataset_id}")
            results = list(self.client.dataset(dataset_id).iterate_items())
            
            print(f"✅ Seek scraper completed: {len(results)} jobs found")
            
            # Log sample job titles if we have results
            if results and self.verbose:
                print(f"📊 VERBOSE: Sample Seek job titles for '{job_title}':")
                for i, job in enumerate(results[:5]):  # Show first 5
                    title = job.get('title', 'No title')
                    company = job.get('companyName', 'No company')
                    print(f"   {i+1}. {title} at {company}")
                if len(results) > 5:
                    print(f"   ... and {len(results) - 5} more jobs")
            
            return results
            
        except Exception as e:
            print(f"❌ Error running Seek scraper: {str(e)}")
            return []
    
    def run_linkedin_scraper(self, job_title: str, max_results: int = 100, max_age_days: int = 7) -> List[Dict[str, Any]]:
        """Run LinkedIn job scraper and return results"""
        print(f"🔍 Running LinkedIn scraper for: {job_title}")
        print("   ⏳ This may take 1-3 minutes to complete...")
        
        input_data = self.create_linkedin_input(job_title, max_results, max_age_days)
        if self.verbose:
            print(f"📊 VERBOSE: LinkedIn input data: {json.dumps(input_data, indent=2)}")
        
        try:
            # Run the actor and wait for completion
            run = self.client.actor(self.linkedin_actor_id).call(run_input=input_data)
            if self.verbose:
                print(f"📊 VERBOSE: LinkedIn actor run ID: {run.get('id', 'unknown')}")
            
            # Get the results
            dataset_id = run['defaultDatasetId']
            if self.verbose:
                print(f"📊 VERBOSE: LinkedIn dataset ID: {dataset_id}")
            results = list(self.client.dataset(dataset_id).iterate_items())
            
            print(f"✅ LinkedIn scraper completed: {len(results)} jobs found")
            
            # Log sample job titles if we have results
            if results and self.verbose:
                print(f"📊 VERBOSE: Sample LinkedIn job titles for '{job_title}':")
                for i, job in enumerate(results[:5]):  # Show first 5
                    title = job.get('title', 'No title')
                    company = job.get('company', 'No company')
                    print(f"   {i+1}. {title} at {company}")
                if len(results) > 5:
                    print(f"   ... and {len(results) - 5} more jobs")
            
            return results
            
        except Exception as e:
            print(f"❌ Error running LinkedIn scraper: {str(e)}")
            return []
    
    def scrape_all_job_titles(self, job_titles: List[str], max_results: int = 100, max_age_days: int = 7, verbose: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape jobs from both platforms for all job titles"""
        all_results = {
            'seek': [],
            'linkedin': []
        }
        
        if verbose:
            print(f"\n📊 VERBOSE LOGGING: Starting scrape for {len(job_titles)} job titles")
            print(f"📊 Job titles to search: {job_titles}")
            print(f"📊 Max results per title: {max_results}")
            print(f"📊 Max age days: {max_age_days}")
        
        for i, job_title in enumerate(job_titles, 1):
            print(f"\n🚀 [{i}/{len(job_titles)}] Scraping jobs for: '{job_title}'")
            if verbose:
                print(f"📊 VERBOSE: This is job title #{i} of {len(job_titles)}")
            
            # Run Seek scraper
            seek_results = self.run_seek_scraper(job_title, max_results, max_age_days)
            if verbose:
                print(f"📊 VERBOSE: Seek returned {len(seek_results)} jobs for '{job_title}'")
            all_results['seek'].extend(seek_results)
            
            # Add small delay between requests
            time.sleep(2)
            
            # Run LinkedIn scraper
            linkedin_results = self.run_linkedin_scraper(job_title, max_results, max_age_days)
            if verbose:
                print(f"📊 VERBOSE: LinkedIn returned {len(linkedin_results)} jobs for '{job_title}'")
            all_results['linkedin'].extend(linkedin_results)
            
            if verbose:
                print(f"📊 VERBOSE: Total jobs so far - Seek: {len(all_results['seek'])}, LinkedIn: {len(all_results['linkedin'])}")
            
            # Add delay between job titles
            time.sleep(3)
        
        if verbose:
            print(f"\n📊 VERBOSE SUMMARY: Final scraping results:")
            print(f"📊 Total Seek jobs scraped: {len(all_results['seek'])}")
            print(f"📊 Total LinkedIn jobs scraped: {len(all_results['linkedin'])}")
            print(f"📊 Grand total jobs: {len(all_results['seek']) + len(all_results['linkedin'])}")
        
        return all_results
    
    def save_results_to_file(self, results: Dict[str, List[Dict[str, Any]]], timestamp: str = None):
        """Save scraping results to JSON files"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Save Seek results
        seek_filename = f'dataset_seek-job-scraper_{timestamp}.json'
        seek_filepath = f'/var/home/mrwilde/Projects/MrWilde/Apps/swe-jobs/jobs-by-apify/jobs-by-apify/{seek_filename}'
        
        with open(seek_filepath, 'w') as f:
            json.dump(results['seek'], f, indent=2)
        
        # Save LinkedIn results  
        linkedin_filename = f'dataset_linkedin-jobs-scraper_{timestamp}.json'
        linkedin_filepath = f'/var/home/mrwilde/Projects/MrWilde/Apps/swe-jobs/jobs-by-apify/jobs-by-apify/{linkedin_filename}'
        
        with open(linkedin_filepath, 'w') as f:
            json.dump(results['linkedin'], f, indent=2)
        
        print(f"📁 Results saved:")
        print(f"   Seek: {seek_filename} ({len(results['seek'])} jobs)")
        print(f"   LinkedIn: {linkedin_filename} ({len(results['linkedin'])} jobs)")
        
        return {
            'seek_file': seek_filepath,
            'linkedin_file': linkedin_filepath,
            'timestamp': timestamp
        }