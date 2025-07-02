import os
import re
import json
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta


class JobSearch:
    """Enhanced job search and filtering functionality"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        # Load keywords from environment
        keywords_str = os.getenv('KEYWORDS', 'PHP')
        self.keywords = [keyword.strip() for keyword in keywords_str.split(',')]
        
        # Track seen jobs to avoid duplicates (session-based)
        self.seen_jobs: Set[str] = set()
        
        # File to track jobs that have been sent via email (persistent)
        self.sent_jobs_file = 'sent_jobs.json'
        self.sent_jobs: Set[str] = self._load_sent_jobs()
    
    def search_seek_jobs(self, jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search through Seek job data for keyword matches"""
        matches = []
        
        if self.verbose:
            print(f"📊 VERBOSE: Starting Seek job search through {len(jobs_data)} jobs")
        
        for i, job in enumerate(jobs_data, 1):
            job_title = job.get('title', 'No title')
            job_company = job.get('companyName', 'No company')
            job_id = self._get_seek_job_id(job)
            
            if self.verbose:
                print(f"📊 VERBOSE: [{i}/{len(jobs_data)}] Checking Seek job: '{job_title}' at {job_company}")
            
            if self._is_seek_job_match(job):
                if job_id not in self.seen_jobs and job_id not in self.sent_jobs:
                    self.seen_jobs.add(job_id)
                    # Add job scoring based on guide recommendations
                    scored_job = self._score_job_match(job, 'seek')
                    matches.append(scored_job)
                    if self.verbose:
                        print(f"   ✅ MATCH FOUND: '{job_title}' - Score: {scored_job.get('match_score', 0)} - added to results")
                else:
                    if self.verbose:
                        reason = "already seen this session" if job_id in self.seen_jobs else "already sent via email"
                        print(f"   🔄 DUPLICATE: '{job_title}' - {reason}, skipping")
            else:
                if self.verbose:
                    print(f"   ❌ NO MATCH: '{job_title}' - no keywords found")
        
        # Sort by match score (highest first) as suggested in guide
        matches.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        if self.verbose:
            print(f"📊 VERBOSE: Seek search complete - {len(matches)} matches found")
        return matches
    
    def search_linkedin_jobs(self, jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search through LinkedIn job data for keyword matches"""
        matches = []
        
        if self.verbose:
            print(f"📊 VERBOSE: Starting LinkedIn job search through {len(jobs_data)} jobs")
        
        for i, job in enumerate(jobs_data, 1):
            job_title = job.get('title', 'No title')
            job_company = job.get('company', 'No company')
            job_id = self._get_linkedin_job_id(job)
            
            if self.verbose:
                print(f"📊 VERBOSE: [{i}/{len(jobs_data)}] Checking LinkedIn job: '{job_title}' at {job_company}")
            
            if self._is_linkedin_job_match(job):
                if job_id not in self.seen_jobs and job_id not in self.sent_jobs:
                    self.seen_jobs.add(job_id)
                    # Add job scoring based on guide recommendations
                    scored_job = self._score_job_match(job, 'linkedin')
                    matches.append(scored_job)
                    if self.verbose:
                        print(f"   ✅ MATCH FOUND: '{job_title}' - Score: {scored_job.get('match_score', 0)} - added to results")
                else:
                    if self.verbose:
                        reason = "already seen this session" if job_id in self.seen_jobs else "already sent via email"
                        print(f"   🔄 DUPLICATE: '{job_title}' - {reason}, skipping")
            else:
                if self.verbose:
                    print(f"   ❌ NO MATCH: '{job_title}' - no keywords found")
        
        # Sort by match score (highest first) as suggested in guide
        matches.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        if self.verbose:
            print(f"📊 VERBOSE: LinkedIn search complete - {len(matches)} matches found")
        return matches
    
    def _is_seek_job_match(self, job: Dict[str, Any]) -> bool:
        """Check if a Seek job matches any of our keywords"""
        try:
            job_title = job.get('title', '')
            if self.verbose:
                print(f"   📊 VERBOSE: Checking keywords {self.keywords} in Seek job '{job_title}'")
            
            # Search in job title first
            job_title_lower = job_title.lower()
            for keyword in self.keywords:
                if keyword.lower() in job_title_lower:
                    if self.verbose:
                        print(f"   📊 VERBOSE: ✅ Found keyword '{keyword}' in title: '{job_title}'")
                    return True
            
            # Search in content sections
            content_sections = job.get('content', {}).get('sections', [])
            if self.verbose:
                print(f"   📊 VERBOSE: Checking {len(content_sections)} content sections")
            
            for i, section in enumerate(content_sections):
                section_text = str(section).lower()
                section_preview = section_text[:100] + "..." if len(section_text) > 100 else section_text
                
                # Check if any keyword is found in the section
                for keyword in self.keywords:
                    if keyword.lower() in section_text:
                        if self.verbose:
                            print(f"   📊 VERBOSE: ✅ Found keyword '{keyword}' in section {i}: '{section_preview}'")
                        return True
            
            if self.verbose:
                print(f"   📊 VERBOSE: ❌ No keywords found in title or {len(content_sections)} sections")
            
        except Exception as e:
            print(f"❌ Error processing Seek job: {str(e)}")
        
        return False
    
    def _is_linkedin_job_match(self, job: Dict[str, Any]) -> bool:
        """Check if a LinkedIn job matches any of our keywords"""
        try:
            job_title = job.get('title', '')
            company = job.get('company', '')
            description = job.get('description', '')
            
            if self.verbose:
                print(f"   📊 VERBOSE: Checking keywords {self.keywords} in LinkedIn job '{job_title}' at {company}")
            
            # Search in job title first
            job_title_lower = job_title.lower()
            for keyword in self.keywords:
                if keyword.lower() in job_title_lower:
                    if self.verbose:
                        print(f"   📊 VERBOSE: ✅ Found keyword '{keyword}' in title: '{job_title}'")
                    return True
            
            # Search in company name
            company_lower = company.lower()
            for keyword in self.keywords:
                if keyword.lower() in company_lower:
                    if self.verbose:
                        print(f"   📊 VERBOSE: ✅ Found keyword '{keyword}' in company: '{company}'")
                    return True
            
            # Search in description
            description_lower = description.lower()
            description_preview = description_lower[:200] + "..." if len(description_lower) > 200 else description_lower
            
            for keyword in self.keywords:
                if keyword.lower() in description_lower:
                    if self.verbose:
                        print(f"   📊 VERBOSE: ✅ Found keyword '{keyword}' in description: '{description_preview}'")
                    return True
            
            if self.verbose:
                print(f"   📊 VERBOSE: ❌ No keywords found in title, company, or description")
            
        except Exception as e:
            print(f"❌ Error processing LinkedIn job: {str(e)}")
        
        return False
    
    def _get_seek_job_id(self, job: Dict[str, Any]) -> str:
        """Extract unique identifier for Seek job"""
        return job.get('jobLink', f"seek_{hash(str(job))}")
    
    def _get_linkedin_job_id(self, job: Dict[str, Any]) -> str:
        """Extract unique identifier for LinkedIn job"""
        return job.get('jobUrl', f"linkedin_{hash(str(job))}")
    
    def filter_jobs_by_age(self, jobs_data: List[Dict[str, Any]], max_age_days: int, platform: str) -> List[Dict[str, Any]]:
        """Filter jobs by age (if date information is available)"""
        if max_age_days <= 0:
            return jobs_data
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        filtered_jobs = []
        
        for job in jobs_data:
            job_date = self._extract_job_date(job, platform)
            
            if job_date is None:
                # If we can't determine the date, include the job
                filtered_jobs.append(job)
            elif job_date >= cutoff_date:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _extract_job_date(self, job: Dict[str, Any], platform: str) -> datetime:
        """Try to extract job posting date"""
        try:
            if platform == 'seek':
                # Look for date fields in Seek data
                date_str = job.get('postedDate') or job.get('datePosted')
                if date_str:
                    return self._parse_date_string(date_str)
            
            elif platform == 'linkedin':
                # Look for date fields in LinkedIn data
                date_str = job.get('postedTime') or job.get('publishedAt')
                if date_str:
                    return self._parse_date_string(date_str)
        
        except Exception:
            pass
        
        return None
    
    def _parse_date_string(self, date_str: str) -> datetime:
        """Parse various date string formats"""
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If no format matches, return None
        return None
    
    def search_all_jobs(self, scraped_data: Dict[str, List[Dict[str, Any]]], max_age_days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Search all scraped job data and return matches"""
        matches = {
            'seek': [],
            'linkedin': []
        }
        
        # Process Seek jobs
        if scraped_data.get('seek'):
            print(f"🔍 Searching {len(scraped_data['seek'])} Seek jobs for keywords: {', '.join(self.keywords)}")
            
            # Filter by age first
            age_filtered_seek = self.filter_jobs_by_age(scraped_data['seek'], max_age_days, 'seek')
            print(f"📅 {len(age_filtered_seek)} Seek jobs after age filtering")
            
            # Search for keyword matches
            seek_matches = self.search_seek_jobs(age_filtered_seek)
            matches['seek'] = seek_matches
            
            print(f"✅ Found {len(seek_matches)} matching Seek jobs")
        
        # Process LinkedIn jobs
        if scraped_data.get('linkedin'):
            print(f"🔍 Searching {len(scraped_data['linkedin'])} LinkedIn jobs for keywords: {', '.join(self.keywords)}")
            
            # Filter by age first
            age_filtered_linkedin = self.filter_jobs_by_age(scraped_data['linkedin'], max_age_days, 'linkedin')
            print(f"📅 {len(age_filtered_linkedin)} LinkedIn jobs after age filtering")
            
            # Search for keyword matches
            linkedin_matches = self.search_linkedin_jobs(age_filtered_linkedin)
            matches['linkedin'] = linkedin_matches
            
            print(f"✅ Found {len(linkedin_matches)} matching LinkedIn jobs")
        
        total_matches = len(matches['seek']) + len(matches['linkedin'])
        print(f"🎯 Total matches found: {total_matches}")
        
        return matches
    
    def reset_seen_jobs(self):
        """Reset the seen jobs tracking (useful for fresh searches)"""
        self.seen_jobs.clear()
    
    def get_search_summary(self, matches: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate a summary string of search results"""
        seek_count = len(matches.get('seek', []))
        linkedin_count = len(matches.get('linkedin', []))
        total = seek_count + linkedin_count
        
        return f"Search Results: {total} total matches ({seek_count} Seek, {linkedin_count} LinkedIn) for keywords: {', '.join(self.keywords)}"
    
    def _score_job_match(self, job: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Score jobs based on keyword frequency and relevance (from guide)"""
        score = 0
        
        if platform == 'seek':
            # Score based on title
            title = job.get('title', '').lower()
            for keyword in self.keywords:
                count = title.count(keyword.lower())
                score += count * len(keyword) * 3  # Title matches weighted higher
            
            # Score based on content sections
            content_sections = job.get('content', {}).get('sections', [])
            for section in content_sections:
                section_text = str(section).lower()
                for keyword in self.keywords:
                    count = section_text.count(keyword.lower())
                    score += count * len(keyword)
        
        elif platform == 'linkedin':
            # Score based on title
            title = job.get('title', '').lower()
            for keyword in self.keywords:
                count = title.count(keyword.lower())
                score += count * len(keyword) * 3  # Title matches weighted higher
            
            # Score based on company name
            company = job.get('company', '').lower()
            for keyword in self.keywords:
                count = company.count(keyword.lower())
                score += count * len(keyword) * 2  # Company matches weighted medium
            
            # Score based on description
            description = job.get('description', '').lower()
            for keyword in self.keywords:
                count = description.count(keyword.lower())
                score += count * len(keyword)  # Description matches weighted normal
        
        # Add score to job data
        job_copy = job.copy()
        job_copy['match_score'] = score
        return job_copy
    
    def _load_sent_jobs(self) -> Set[str]:
        """Load previously sent job IDs from file"""
        try:
            if os.path.exists(self.sent_jobs_file):
                with open(self.sent_jobs_file, 'r') as f:
                    data = json.load(f)
                    sent_jobs = set(data.get('sent_job_ids', []))
                    if self.verbose:
                        print(f"📋 Loaded {len(sent_jobs)} previously sent job IDs from {self.sent_jobs_file}")
                    return sent_jobs
        except Exception as e:
            print(f"⚠️ Warning: Could not load sent jobs file: {e}")
        
        if self.verbose:
            print(f"📋 No existing sent jobs file found, starting fresh")
        return set()
    
    def _save_sent_jobs(self):
        """Save currently sent job IDs to file"""
        try:
            data = {
                'sent_job_ids': list(self.sent_jobs),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.sent_jobs_file, 'w') as f:
                json.dump(data, f, indent=2)
            if self.verbose:
                print(f"💾 Saved {len(self.sent_jobs)} sent job IDs to {self.sent_jobs_file}")
        except Exception as e:
            print(f"❌ Error saving sent jobs file: {e}")
    
    def mark_jobs_as_sent(self, job_matches: Dict[str, List[Dict[str, Any]]]):
        """Mark jobs as sent after email is sent successfully"""
        job_ids_to_add = []
        
        # Extract job IDs from matches
        for platform, jobs in job_matches.items():
            for job in jobs:
                if platform == 'seek':
                    job_id = self._get_seek_job_id(job)
                elif platform == 'linkedin':
                    job_id = self._get_linkedin_job_id(job)
                else:
                    continue
                
                if job_id not in self.sent_jobs:
                    self.sent_jobs.add(job_id)
                    job_ids_to_add.append(job_id)
        
        if job_ids_to_add:
            self._save_sent_jobs()
            if self.verbose:
                print(f"📧 Marked {len(job_ids_to_add)} jobs as sent via email")
    
    def clear_sent_jobs_history(self):
        """Clear the sent jobs history (useful for testing)"""
        self.sent_jobs.clear()
        try:
            if os.path.exists(self.sent_jobs_file):
                os.remove(self.sent_jobs_file)
                print(f"🗑️ Cleared sent jobs history file: {self.sent_jobs_file}")
            else:
                print(f"🗑️ No sent jobs history file to clear")
        except Exception as e:
            print(f"❌ Error clearing sent jobs history: {e}")
    
    def get_sent_jobs_count(self) -> int:
        """Get count of jobs that have been sent via email"""
        return len(self.sent_jobs)