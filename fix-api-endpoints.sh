#!/bin/bash

echo "Fixing API endpoints in frontend files..."

# 하드코딩된 localhost:8000 API 호출을 API_ENDPOINTS로 교체

# Driver standings
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/driver-standings|API_ENDPOINTS.driverStandings|g' {} \;

# Constructor standings  
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/constructor-standings|API_ENDPOINTS.constructorStandings|g' {} \;

# Calendar
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/calendar|API_ENDPOINTS.calendar|g' {} \;

# Race results
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/race-results|API_ENDPOINTS.raceResults|g' {} \;

# Weather
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/weather|API_ENDPOINTS.weather|g' {} \;

# Live timing
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/live-timing|API_ENDPOINTS.liveTiming|g' {} \;

# Statistics
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/statistics|API_ENDPOINTS.statistics|g' {} \;

# Standings progression
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/standings-progression|API_ENDPOINTS.standingsProgression|g' {} \;

# Race weekends
find frontend/src -name "*.tsx" -exec sed -i '' 's|http://localhost:8000/api/v1/race-weekends|API_ENDPOINTS.raceWeekends|g' {} \;

echo "API endpoints fixed. Remember to:"
echo "1. Import API_ENDPOINTS in files that use it"
echo "2. Update function calls that use year parameters"