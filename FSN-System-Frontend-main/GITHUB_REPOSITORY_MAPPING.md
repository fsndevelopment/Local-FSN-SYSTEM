# FSN System - GitHub Repository Mapping

## Repository Structure and Local Path Mappings

### Backend Repository
- **GitHub Repository**: https://github.com/fsndevelopment/FSN-System-Backend
- **Local Path**: `/Users/janvorlicek/Desktop/FSN SYSTEM/BACKEND`
- **Contents**: All backend API code, services, models, routes, and related files

### Frontend Repository
- **GitHub Repository**: https://github.com/fsndevelopment/FSN-System-Frontend
- **Local Path**: `/Users/janvorlicek/Desktop/FSN SYSTEM/FRONTEND`
- **Contents**: All frontend React/Next.js code, components, pages, and UI files

### License Repository
- **GitHub Repository**: https://github.com/fsndevelopment/FSN-System-License
- **Local Path**: `/Users/janvorlicek/Desktop/FSN SYSTEM/LICENSE`
- **Contents**: All licensing system code, database files, and license management files

## Critical Rules

⚠️ **NEVER PUSH FILES TO THE WRONG REPOSITORY**

- Only push files from `/BACKEND/` to the Backend repository
- Only push files from `/FRONTEND/` to the Frontend repository  
- Only push files from `/LICENSE/` to the License repository
- Always verify the correct local path before pushing any changes
- Double-check repository URLs before any git operations

## Directory Structure Verification

Before any git operations, verify you're in the correct directory:

```bash
# For Backend
cd "/Users/janvorlicek/Desktop/FSN SYSTEM/BACKEND"
git remote -v  # Should show FSN-System-Backend

# For Frontend  
cd "/Users/janvorlicek/Desktop/FSN SYSTEM/FRONTEND"
git remote -v  # Should show FSN-System-Frontend

# For License
cd "/Users/janvorlicek/Desktop/FSN SYSTEM/LICENSE"
git remote -v  # Should show FSN-System-License
```

## Last Updated
Created: $(date)
