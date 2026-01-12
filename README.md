# Lead Tool

B2B Lead Generation Tool for finding and qualifying business leads via LinkedIn data.

## User Stories

### US1: Search for Leads via LinkedIn

**As a** sales/marketing professional
**I want to** search for potential leads based on specific criteria
**So that** I can build a targeted prospect list for outreach

#### Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Fill Search    │────▶│  Start Scraper  │────▶│  Poll Status    │────▶│  View Results   │
│  Form           │     │  Job            │     │  Until Done     │     │  Grid           │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Input Parameters

| Parameter         | Type       | Values/Format                       | Required             |
| ----------------- | ---------- | ----------------------------------- | -------------------- |
| `job_titles`      | `string[]` | e.g., `["Founder", "CEO", "CTO"]`   | No\*                 |
| `locations`       | `string[]` | e.g., `["United States", "Canada"]` | No\*                 |
| `industries`      | `string[]` | See Industry Options below          | No\*                 |
| `company_sizes`   | `string[]` | See Company Size Options below      | No                   |
| `funding_stages`  | `string[]` | See Funding Stage Options below     | No                   |
| `number_of_leads` | `number`   | `50`, `100`, `500`, `1000`, `5000`  | Yes (default: `100`) |

\*At least one of `job_titles`, `locations`, or `industries` is required

#### Industry Options

```
information_technology, computer_software, internet, marketing_advertising,
management_consulting, financial_services, consumer_services, healthcare,
health_wellness_fitness, real_estate, restaurants, retail, education,
entertainment, media_production, design, professional_training,
transportation, manufacturing, biotechnology, pharmaceuticals,
medical_devices, e_learning, research, higher_education,
government, nonprofit, legal_services, accounting,
architecture_planning, construction, engineering, automotive,
telecommunications, insurance, hospitality, events_services
```

#### Company Size Options

| Value        | Description          |
| ------------ | -------------------- |
| `1-10`       | 1-10 employees       |
| `11-50`      | 11-50 employees      |
| `51-200`     | 51-200 employees     |
| `201-500`    | 201-500 employees    |
| `501-1000`   | 501-1000 employees   |
| `1001-5000`  | 1001-5000 employees  |
| `5001-10000` | 5001-10000 employees |
| `10001+`     | 10001+ employees     |

#### Funding Stage Options

```
seed, angel, series_a, series_b, series_c, series_d,
series_e, series_f, venture, private_equity
```

---

### US2: Upload Existing Leads from CSV

**As a** sales/marketing professional
**I want to** upload my existing lead list from a CSV file
**So that** I can analyze and score them using the tool's scoring algorithm

#### Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Select CSV     │────▶│  Parse & Score  │────▶│  View Results   │
│  File           │     │  Each Lead      │     │  Grid           │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Input: CSV Columns

| Column            | Required | Description           |
| ----------------- | -------- | --------------------- |
| `name`            | Yes      | Full name of the lead |
| `email`           | No       | Email address         |
| `company`         | No       | Company name          |
| `position`        | No       | Job title             |
| `linkedin_url`    | No       | LinkedIn profile URL  |
| `company_website` | No       | Company website URL   |
| `location`        | No       | Geographic location   |
| `phone`           | No       | Phone number          |

---

### US3: Export Leads to CSV

**As a** sales/marketing professional
**I want to** export my lead results to a CSV file
**So that** I can use them in my CRM or outreach tools

#### Flow

```
┌─────────────────┐     ┌─────────────────┐
│  Click Export   │────▶│  Download CSV   │
│  Button         │     │  File           │
└─────────────────┘     └─────────────────┘
```

#### Output: CSV Columns

| Column            | Description                                          |
| ----------------- | ---------------------------------------------------- |
| `name`            | Lead's full name                                     |
| `email`           | Email address                                        |
| `company`         | Company name                                         |
| `position`        | Job title                                            |
| `linkedin_url`    | LinkedIn profile URL                                 |
| `company_website` | Company website URL                                  |
| `location`        | Geographic location                                  |
| `phone`           | Phone number                                         |
| `score`           | Calculated score (0-100)                             |
| `tier`            | Enterprise, Scale-up, Startup, or Small              |
| `category`        | High Value, Medium Value, Startup, or Small Business |

---

### US4: View Lead Details

**As a** sales/marketing professional
**I want to** click on a lead card to see detailed information
**So that** I can evaluate if they're worth pursuing

#### Flow

```
┌─────────────────┐     ┌─────────────────┐
│  Click Lead     │────▶│  View Detail    │
│  Card           │     │  Panel          │
└─────────────────┘     └─────────────────┘
```

#### Detail View Content

- Profile photo, name, position, company, location
- Company analysis score (0-100) with color coding
- Tier classification
- Email verification status
- Scoring insights (reasons for score)
- Full contact information

---

## Data Models

### Lead

```typescript
interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;
  position: string;
  linkedin_url: string;
  company_website: string;
  location: string;
  phone: string;
  analysis: Analysis;
  source: "search" | "csv_upload";
  email_verified: boolean;
  created_at: string;
}
```

### Analysis

```typescript
interface Analysis {
  score: number; // 0-100
  tier: string; // "Enterprise" | "Scale-up" | "Startup" | "Small"
  category: string; // "High Value" | "Medium Value" | "Startup" | "Small Business"
  insights: string[]; // Reasons for score
  qualified: boolean; // score >= 50
}
```

### API Response (Standard)

```typescript
interface ApiResponse<T> {
  status: boolean;
  data: T | null;
  timestamp: string; // ISO 8601 format
  error?: {
    msg: string;
    code: string;
  };
}
```

#### Error Codes

| Code               | Description                         |
| ------------------ | ----------------------------------- |
| `VALIDATION_ERROR` | Invalid or missing input parameters |
| `SCRAPER_ERROR`    | External scraper service failure    |
| `FILE_ERROR`       | File upload/parse failure           |
| `NOT_FOUND`        | Resource not found                  |
| `INTERNAL_ERROR`   | Unexpected server error             |

---

## Company Scoring Algorithm

### Scoring Criteria

| Criterion        | Condition                            | Points |
| ---------------- | ------------------------------------ | ------ |
| **Industry**     | SaaS, Software, Technology, Internet | +30    |
| **Company Size** | 51-1000 employees                    | +25    |
| **Company Size** | 1001+ employees                      | +40    |
| **Revenue**      | Millions                             | +20    |
| **Revenue**      | Billions                             | +35    |

### Tier Classification

| Score Range | Tier       | Category       |
| ----------- | ---------- | -------------- |
| >= 80       | Enterprise | High Value     |
| >= 60       | Scale-up   | Medium Value   |
| >= 40       | Startup    | Startup        |
| < 40        | Small      | Small Business |

### Qualification Threshold

- **Qualified**: score >= 50
- **Not Qualified**: score < 50

---

## API Endpoints

### POST `/api/leads/search`

Start a new lead search.

**Request:**

```json
{
  "job_titles": ["CEO", "CTO"],
  "locations": ["United States"],
  "industries": ["computer_software"],
  "company_sizes": ["51-200", "201-500"],
  "funding_stages": ["series_a", "series_b"],
  "number_of_leads": 100
}
```

**Response:**

```json
{
  "status": true,
  "data": {
    "run_id": "abc123"
  },
  "timestamp": "2025-01-12T10:30:00Z"
}
```

**Error Response:**

```json
{
  "status": false,
  "data": null,
  "timestamp": "2025-01-12T10:30:00Z",
  "error": {
    "msg": "At least one search criterion required",
    "code": "VALIDATION_ERROR"
  }
}
```

---

### GET `/api/leads/search/{run_id}/status`

Check the status of a search job.

**Response (in progress):**

```json
{
  "status": true,
  "data": {
    "run_status": "running",
    "progress": 45
  },
  "timestamp": "2025-01-12T10:31:00Z"
}
```

**Response (completed):**

```json
{
  "status": true,
  "data": {
    "run_status": "completed",
    "leads": [...],
    "total": 42
  },
  "timestamp": "2025-01-12T10:35:00Z"
}
```

---

### POST `/api/leads/upload`

Upload a CSV file with existing leads.

**Request:** `multipart/form-data` with `file` field

**Response:**

```json
{
  "status": true,
  "data": {
    "leads": [...],
    "total": 25
  },
  "timestamp": "2025-01-12T10:30:00Z"
}
```

**Error Response:**

```json
{
  "status": false,
  "data": null,
  "timestamp": "2025-01-12T10:30:00Z",
  "error": {
    "msg": "Invalid CSV format: missing 'name' column",
    "code": "FILE_ERROR"
  }
}
```

---

### GET `/api/leads/export`

Export current leads as CSV file.

**Response:** CSV file download

---

## Configuration

### Environment Variables

```
APIFY_API_TOKEN=<token>
DATA_DIR=./data
```

### File Storage

```
data/
├── leads.csv           # Persisted leads database
└── exports/            # Generated export files
```
