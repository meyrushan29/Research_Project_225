# Well360 - Play Store Launch Quick Checklist

## 🚨 CRITICAL - MUST FIX BEFORE SUBMISSION

- [ ] **Change package name** from `com.example.flutter_application_1` to proper domain (e.g., `com.well360.healthanalyzer`)
- [ ] **Create production signing key** (.jks keystore file)
- [ ] **Configure release signing** in build.gradle.kts
- [ ] **Create and host Privacy Policy** (public URL required)
- [ ] **Deploy backend to cloud** with HTTPS
- [ ] **Remove or secure cleartext traffic** setting in AndroidManifest.xml

## 📱 DEVELOPER ACCOUNT

- [ ] Create Google Play Developer Account ($25)
- [ ] Complete identity verification
- [ ] Fill developer profile

## 🔧 APP CONFIGURATION

- [ ] Update applicationId in `android/app/build.gradle.kts`
- [ ] Update namespace in `android/app/build.gradle.kts`
- [ ] Create `android/key.properties` (add to .gitignore)
- [ ] Update app to use production backend URL
- [ ] Add About/Privacy/Terms screens in app

## 🖼️ MARKETING ASSETS

- [ ] App icon 512x512px ✅ (already have ic_launcher)
- [ ] Feature graphic 1024x500px
- [ ] Screenshots (2-8 required):
  - [ ] Home screen
  - [ ] Hydration tracker
  - [ ] Fitness module
  - [ ] AI analysis feature
  - [ ] Charts/trends
  - [ ] Settings
- [ ] Short description (max 80 chars)
- [ ] Full description (max 4000 chars)
- [ ] Promotional video (optional)

## 📋 PLAY CONSOLE

- [ ] Upload AAB file to internal testing
- [ ] Complete Data Safety form
- [ ] Complete Content rating questionnaire
- [ ] Declare target audience
- [ ] Declare ads (yes/no)
- [ ] Add privacy policy URL
- [ ] Set pricing (free/paid)
- [ ] Select distribution countries
- [ ] Provide test credentials (if login required)

## ✅ TESTING

- [ ] Build release AAB: `flutter build appbundle --release`
- [ ] Test release build on real devices
- [ ] **Closed testing with 20+ testers** (MANDATORY)
- [ ] Run for minimum 14 days
- [ ] Fix all critical bugs
- [ ] Verify all permissions work
- [ ] Test backend connectivity
- [ ] Test offline scenarios

## 📜 LEGAL & PRIVACY

- [ ] Privacy Policy (must include):
  - [ ] What data collected (location, camera, health)
  - [ ] How data used
  - [ ] How data stored
  - [ ] User rights (access, delete, export)
  - [ ] Contact information
- [ ] Terms of Service
- [ ] In-app links to privacy policy
- [ ] Medical disclaimer
- [ ] Data deletion functionality
- [ ] Data export functionality

## 🔒 SECURITY

- [ ] HTTPS only for all API calls
- [ ] Secure backend deployment
- [ ] Environment variables for secrets
- [ ] Database encryption
- [ ] API authentication implemented

## 🚀 SUBMIT

- [ ] All above items completed
- [ ] Upload to production track
- [ ] Submit for review
- [ ] Wait 3-7 days for review
- [ ] Respond to any reviewer feedback

---

## Backend Deployment Checklist

- [ ] Choose hosting provider (Railway/Cloud Run/AWS/Render)
- [ ] Set up cloud database (PostgreSQL recommended)
- [ ] Configure environment variables
- [ ] Deploy FastAPI backend
- [ ] Set up SSL/TLS certificate
- [ ] Test all API endpoints
- [ ] Set up monitoring and logging
- [ ] Configure auto-scaling (if available)
- [ ] Set up backup strategy

---

## Post-Launch Checklist

- [ ] Monitor crash reports (Firebase Crashlytics recommended)
- [ ] Respond to user reviews within 24-48 hours
- [ ] Track key metrics (installs, active users, retention)
- [ ] Plan first update (2-4 weeks after launch)
- [ ] Set up analytics (Firebase Analytics/Google Analytics)
- [ ] Monitor backend performance and costs
- [ ] Collect user feedback for improvements

---

**Estimated Timeline:** 6-10 weeks  
**Minimum Cost:** $25 (Play Store) + $5-50/month (backend hosting)  
**Priority:** Fix critical items first, then proceed through checklist sequentially
