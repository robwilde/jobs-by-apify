# Jobs by Apify - Automated Job Search System

A **production-ready** Python application that automatically scrapes job postings from Seek.com.au and LinkedIn, filters them by keywords, and sends email notifications for relevant matches.

## ✨ Features

- 🔍 **Multi-Platform Scraping**: Integrates with Seek.com.au and LinkedIn job boards via Apify API
- 🎯 **Smart Filtering**: Keyword-based job matching with configurable search criteria
- 📧 **Email Notifications**: Professional HTML email alerts via Postmark transactional email
- 🔄 **Automated Scheduling**: Daemon mode with configurable run times (default: 9 AM & 5 PM)
- 🚫 **Duplicate Prevention**: Intelligent deduplication to avoid repeat notifications
- 📊 **Age Filtering**: Configurable job age limits to focus on recent postings
- 🔧 **Environment Configuration**: Flexible setup via environment variables

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Apify account with API token
- Postmark account for email notifications

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobs-by-apify
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install apify-client schedule python-dotenv postmarker
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   # Apify API Configuration
   APIFY_USER_ID=your_user_id
   APIFY_TOKEN=your_api_token

   # Job Search Parameters
   JOB_TITLES="Software Engineer,Senior PHP Developer,Laravel Developer"
   KEYWORDS=PHP,Laravel,Symfony
   LOCATION="Australia and New Zealand"
   MAX_RESULTS=100
   MAX_JOB_AGE_DAYS=7

   # Platform-Specific Settings
   LINKEDIN_WORK_TYPE=2              # 1=On-site, 2=Remote, 3=Hybrid
   LINKEDIN_EXPERIENCE_LEVEL=4       # 1=Internship, 2=Entry, 3=Associate, 4=Mid-Senior, 5=Director+
   SEEK_SALARY_MIN=150000
   SEEK_SALARY_MAX=1000000
   SEEK_WORK_ARRANGEMENTS=remote

   # Email Configuration
   EMAIL_PROVIDER=postmark
   EMAIL_ADDRESS=your-email@domain.com
   POSTMARK_API_TOKEN=your_postmark_server_token
   FROM_EMAIL=noreply@yourdomain.com

   # Scheduling
   SCHEDULE_MORNING=09:00
   SCHEDULE_AFTERNOON=17:00
   TIMEZONE=Australia/Sydney
   ```

### Usage

#### Run Once
Execute a single job search and notification cycle:
```bash
python enhanced_job_search.py once
```

#### Test Configuration
Verify your setup and send a test email:
```bash
python enhanced_job_search.py test
```

#### Daemon Mode
Run continuously with scheduled searches:
```bash
python enhanced_job_search.py daemon
```

#### Verbose Output
Add detailed logging to any command:
```bash
python enhanced_job_search.py once --verbose
python enhanced_job_search.py test -v
```

## 🏗️ Architecture

### Core Components

- **`enhanced_job_search.py`**: Main orchestrator with scheduling and CLI interface
- **`apify_integration.py`**: Handles Apify API interactions and job scraping
- **`job_search.py`**: Keyword filtering engine with deduplication logic
- **`email_notifier.py`**: HTML email notifications via Postmark

### Data Flow

1. **Scraping**: Fetch jobs from Seek and LinkedIn using Apify actors
2. **Filtering**: Search job content for configured keywords
3. **Deduplication**: Remove duplicate postings using URL-based tracking
4. **Age Filtering**: Apply date-based filtering for recent jobs
5. **Notification**: Send HTML email alerts for new matches

### File Structure

```
jobs-by-apify/
├── enhanced_job_search.py    # Main application
├── apify_integration.py      # Apify API client
├── job_search.py            # Filtering logic
├── email_notifier.py        # Email notifications
├── actors/                  # Apify actor configurations
│   ├── SeekJobScraper/
│   └── LinkedInJobScraper/
├── docs/                    # Documentation
├── CLAUDE.md               # Development instructions
└── README.md               # This file
```

## ⚙️ Configuration

### Job Search Parameters

- **JOB_TITLES**: Comma-separated list of job titles to search for
- **KEYWORDS**: Comma-separated keywords to filter job descriptions
- **LOCATION**: Geographic search scope
- **MAX_RESULTS**: Maximum number of jobs to scrape per search
- **MAX_JOB_AGE_DAYS**: Filter jobs older than specified days

### Platform-Specific Settings

#### LinkedIn
- **LINKEDIN_WORK_TYPE**: Work arrangement preference (1=On-site, 2=Remote, 3=Hybrid)
- **LINKEDIN_EXPERIENCE_LEVEL**: Experience level (1=Internship through 5=Director+)

#### Seek
- **SEEK_SALARY_MIN/MAX**: Salary range filtering
- **SEEK_WORK_ARRANGEMENTS**: Work arrangement preferences (remote, onsite, hybrid)

### Email Configuration

The application uses Postmark for reliable email delivery:
- **EMAIL_PROVIDER**: Set to `postmark`
- **POSTMARK_API_TOKEN**: Your Postmark server API token
- **FROM_EMAIL**: Sender email address
- **EMAIL_ADDRESS**: Recipient email address

## 🔧 Development

### Legacy Support

The application maintains backward compatibility with the original `search_jobs.py` script:
```bash
python search_jobs.py
```

### Testing

Verify your configuration and test email delivery:
```bash
python enhanced_job_search.py test --verbose
```

### Debugging

Use verbose mode to see detailed operation logs:
```bash
python enhanced_job_search.py once --verbose
```

## 📊 Data Management

### Job Deduplication

- **Session-based**: Prevents duplicate processing within a single run
- **Persistent**: Tracks sent notifications in `sent_jobs.json`
- **URL-based**: Uses job URLs as unique identifiers

### Data Storage

- **Historical Data**: Timestamped JSON files for each scraping session
- **Sent Jobs**: Persistent tracking of notified positions
- **Actor Configurations**: Reusable Apify actor input configurations

## 🛠️ Apify Integration

### Supported Actors

- **Seek**: `websift~seek-job-scraper`
- **LinkedIn**: `bebity~linkedin-jobs-scraper`

### Actor Configuration

Actor inputs are stored in `actors/` directory and can be customized for specific search requirements.

## 📧 Email Notifications

### Features

- **HTML Formatting**: Professional email templates with job details
- **Plain Text Fallback**: Ensures compatibility across email clients
- **Transactional Delivery**: Uses Postmark for reliable delivery
- **Job Details**: Includes title, company, location, and direct links

### Sample Email Content

- Job match summary with keyword highlights
- Direct links to job postings
- Company and location information
- Posting date and relevance details

## 🔄 Scheduling

### Daemon Mode

The application runs continuously with scheduled job searches:
- **Default Schedule**: 9:00 AM and 5:00 PM
- **Configurable Times**: Set via environment variables
- **Timezone Support**: Respects configured timezone
- **Graceful Shutdown**: Handles interruption signals properly

### Dynamic Age Filtering

Recent runs automatically adjust age filtering to focus on newly posted jobs, reducing duplicate notifications.

## 🚀 Production Deployment

### Status: Production Ready ✅

The application has been tested and verified for production use:
- All core functionality implemented
- Email notifications operational
- Scheduling system functional
- Configuration validation passing

### Deployment Considerations

- Set up environment variables securely
- Configure Postmark API credentials
- Test email delivery before production use
- Monitor log output for troubleshooting
- Consider process management (systemd, supervisor, etc.)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📞 Support

For issues and questions, please refer to the documentation or create an issue in the repository.