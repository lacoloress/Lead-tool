#!/usr/bin/env python3
import os
import json
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import tempfile
import uuid
from apify_client import ApifyClient

app = Flask(__name__)
CORS(app)

class Config:
    # Apify API
    APIFY_API_TOKEN = "apify_api_4SitbnPsNDiHVsPHj1VM2sSqKLZjQc3REiTS"
    
    # Free Actor for LinkedIn scraping
    APIFY_ACTOR_ID = "apify/linkedin-company-scraper"
    
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

class CompanyAnalyzer:
    def analyze_company(self, company_data):
        score = 0
        insights = []
        
        industry = company_data.get("industry", "").lower()
        if any(target in industry for target in ["saas", "software", "technology", "internet"]):
            score += 30
            insights.append(f"Target industry: {industry.title()} (Score: +30)")
        
        size = company_data.get("size", "")
        if size in ["51-200", "201-500", "501-1000"]:
            score += 25
            insights.append(f"Company size: {size} (Score: +25)")
        elif size in ["1001-2000", "2001-5000", "5001-10000", "10000+"]:
            score += 40
            insights.append(f"Enterprise size: {size} (Score: +40)")
        
        revenue = company_data.get("revenue", "")
        if revenue:
            if any(x in revenue.lower() for x in ["m", "million"]):
                score += 20
            elif any(x in revenue.lower() for x in ["b", "billion"]):
                score += 35
        
        if score >= 80:
            tier = "Enterprise"
            category = "High Value"
        elif score >= 60:
            tier = "Scale-up"
            category = "Medium Value"
        elif score >= 40:
            tier = "Startup"
            category = "Startup"
        else:
            tier = "Small"
            category = "Small Business"
        
        return {
            "score": min(score, 100),
            "tier": tier,
            "category": category,
            "insights": insights,
            "qualified": score >= 50
        }

class ApifyLeadsProcessor:
    def __init__(self):
        self.analyzer = CompanyAnalyzer()
        # Initialize Apify client
        self.client = ApifyClient(token=Config.APIFY_API_TOKEN)
    
    def search_leads(self, search_params):
        """Search for leads using Apify LinkedIn Company Scraper"""
        try:
            # Build the actor input for LinkedIn Company Scraper
            actor_input = {
                "startUrls": [
                    {
                        "url": f"https://www.linkedin.com/search/results/companies/?keywords={'+'.join(search_params.get('industries', []))}&location={search_params.get('locations', [''])[0]}&companySize={','.join(search_params.get('company_sizes', []))}&industry={','.join(search_params.get('industries', []))}",
                        "method": "GET"
                    }
                ],
                "maxConcurrency": 5,
                "maxItems": search_params.get("fetch_count", 100),
                "includeEmployeeNames": True,
                "includeEmployeeHeadlines": True,
                "includeEmployeeUrls": True,
                "includeEmployeeEmails": True
            }
            
            print(f"Apify Actor Input: {actor_input}")
            
            # Start the actor run
            run = self.client.actor(Config.APIFY_ACTOR_ID).call(run_input=actor_input)
            
            print(f"Apify Run Started: {run}")
            
            return {
                "success": True,
                "run_id": run["id"],
                "default_dataset_id": run["defaultDatasetId"],
                "message": "Lead search started successfully"
            }
                
        except Exception as e:
            print(f"Apify search error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_run_results(self, run_id):
        """Get results from a completed Apify run"""
        try:
            # Check run status
            run = self.client.run(run_id).get()
            status = run["status"]
            
            print(f"Run Status: {status}")
            
            if status == 'SUCCEEDED':
                # Get dataset items
                dataset_id = run["defaultDatasetId"]
                if dataset_id:
                    # Use the dataset client to get items
                    dataset_client = self.client.dataset(dataset_id)
                    items = list(dataset_client.iterate_items())
                    
                    processed_leads = self.process_linkedin_leads(items)
                    
                    return {
                        "success": True,
                        "leads": processed_leads,
                        "total": len(processed_leads),
                        "status": "completed"
                    }
                else:
                    return {
                        "success": False,
                        "error": "No dataset ID found"
                    }
            elif status in ['RUNNING', 'READY']:
                return {
                    "success": True,
                    "status": status,
                    "message": "Run still in progress"
                }
            else:
                return {
                    "success": False,
                    "status": status,
                    "error": f"Run failed or unknown status: {status}"
                }
                
        except Exception as e:
            print(f"Apify results error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_linkedin_leads(self, leads_data):
        """Process leads from LinkedIn scraper into our format"""
        processed_leads = []
        
        for lead_data in leads_data:
            # Extract company information
            company_data = {
                "industry": lead_data.get("industry", ""),
                "size": lead_data.get("size", ""),
                "revenue": lead_data.get("annualRevenue", ""),
                "founded_year": lead_data.get("foundedYear", "")
            }
            
            analysis = self.analyzer.analyze_company(company_data)
            
            # Process employees if available
            employees = lead_data.get("employees", [])
            
            for employee in employees:
                # Create processed lead
                processed_lead = {
                    "id": str(uuid.uuid4()),
                    "name": employee.get("name", ""),
                    "email": employee.get("email", ""),
                    "company": lead_data.get("name", ""),
                    "position": employee.get("headline", ""),
                    "linkedin_url": employee.get("url", ""),
                    "profile_photo": f"https://ui-avatars.com/api/?name={employee.get('name', '')}&background=random",
                    "company_website": lead_data.get("website", ""),
                    "location": lead_data.get("headquarters", {}).get("location", ""),
                    "phone": "",
                    "analysis": analysis,
                    "contact_info": {
                        "email": employee.get("email", ""),
                        "phone": "",
                        "linkedin": employee.get("url", ""),
                        "company_website": lead_data.get("website", "")
                    },
                    "scraper_source": "apify_linkedin_scraper",
                    "email_verified": bool(employee.get("email", ""))
                }
                
                if processed_lead["name"] and processed_lead["position"]:
                    processed_leads.append(processed_lead)
        
        return processed_leads

processor = ApifyLeadsProcessor()

@app.route("/")
def index():
    return render_template("index_apify.html")

@app.route("/api/search-leads", methods=["POST"])
def search_leads():
    """Search for leads using Apify"""
    search_params = request.json
    
    if not search_params:
        return jsonify({"error": "Search parameters required"})
    
    # Map frontend parameters to Apify parameters
    apify_params = {
        "fetch_count": search_params.get("number_of_leads", 100),
        "file_name": f"leads_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "job_titles": search_params.get("job_titles", []),
        "locations": search_params.get("locations", []),
        "industries": search_params.get("industries", []),
        "company_sizes": search_params.get("company_sizes", []),
        "min_revenue": search_params.get("min_revenue"),
        "max_revenue": search_params.get("max_revenue"),
        "funding_stages": search_params.get("funding_stages", [])
    }
    
    result = processor.search_leads(apify_params)
    
    if result.get("success"):
        return jsonify({
            "success": True,
            "data": result,
            "message": "Lead search started successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Unknown error")
        })

@app.route("/api/check-run-status", methods=["GET"])
def check_run_status():
    """Check the status of an Apify run"""
    run_id = request.args.get("runId")
    
    if not run_id:
        return jsonify({"error": "runId required"})
    
    result = processor.get_run_results(run_id)
    
    if result.get("success"):
        return jsonify({
            "success": True,
            "data": result,
            "message": "Status checked successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Unknown error")
        })

@app.route("/api/upload-csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
        
        file.save(filepath)
        
        try:
            df = pd.read_csv(filepath)
            leads = []
            
            for _, row in df.iterrows():
                lead = {
                    "id": str(uuid.uuid4()),
                    "name": row.get("name", ""),
                    "email": row.get("email", ""),
                    "company": row.get("company", ""),
                    "position": row.get("position", ""),
                    "linkedin_url": row.get("linkedin_url", ""),
                    "profile_photo": row.get("profile_photo", f"https://ui-avatars.com/api/?name={row.get('name', 'Unknown')}&background=random"),
                    "company_website": row.get("company_website", ""),
                    "location": row.get("location", ""),
                    "phone": row.get("phone", ""),
                    "analysis": processor.analyzer.analyze_company({"industry": "CSV Upload"}),
                    "contact_info": {
                        "email": row.get("email", ""),
                        "phone": row.get("phone", ""),
                        "linkedin": row.get("linkedin_url", ""),
                        "company_website": row.get("company_website", "")
                    },
                    "scraper_source": "csv_upload",
                    "email_verified": False
                }
                leads.append(lead)
            
            os.remove(filepath)
            
            return jsonify({
                "success": True,
                "leads": leads,
                "total": len(leads),
                "message": f"Successfully processed {len(leads)} leads"
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
    
    app.run(debug=True, host="0.0.0.0", port=5001)
