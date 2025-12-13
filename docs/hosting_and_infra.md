# 📄 Hosting & Infrastructure Documentation

## 1. Overview
Our organizational project is currently hosted and managed using **Render** services under a single account. The infrastructure combines:
- **Render Web Services** for application hosting
- **Render Redis** for caching and session management
- **Supabase** for database and authentication

This document outlines the hosting plan, resource limits, and key considerations.

---

## 2. Hosting Platform: Render
- **Service Type:** Render Web Services  
- **Current Plan:** Free/Starter (under personal account)  
- **Deployment:** Automatic from GitHub repository (continuous deployment enabled)  
- **Region:** Default Render region (US-based)  
- **Limits:**
  - **CPU & Memory:** 512 MB RAM, 0.5 CPU (starter tier)  
  - **Bandwidth:** Shared, limited under free tier  
  - **Custom Domains:** Supported (requires DNS setup)  
  - **SSL:** Auto-provisioned via Let’s Encrypt  
  - **Scaling:** Manual; autoscaling not available on free tier  

---

## 3. Caching Layer: Render Redis
- **Service Type:** Managed Redis instance  
- **Current Plan:** Free tier  
- **Limits:**
  - **Memory:** 25 MB max  
  - **Connections:** Limited concurrent connections (approx. 30–50)  
  - **Persistence:** No persistence enabled on free tier (volatile storage)  
  - **Use Cases:** Session storage, caching, lightweight pub/sub  

---

## 4. Database: Supabase
- **Service Type:** Managed PostgreSQL + Storage  
- **Current Plan:** Free tier  
- **Limits:**
  - **Database Size:** 500 MB  
  - **Row Limit:** ~500,000 rows  
  - **API Requests:** 50,000 requests/month  
  - **Auth Users:** 50,000 users  
  - **Storage:** 1 GB file storage  
  - **Realtime:** Limited concurrent connections  

---

## 5. Current Constraints
- All services are running on **free tiers**, which impose strict limits on memory, storage, and concurrent connections.  
- **No guaranteed uptime or SLA** — suitable for development and testing, but not production-critical workloads.  
- **Scaling limitations**: Manual upgrades required to move beyond free tier limits.  
