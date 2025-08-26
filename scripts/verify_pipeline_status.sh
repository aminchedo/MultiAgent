#!/bin/bash

echo "=== VERIFYING GITHUB ACTIONS PIPELINE STATUS ==="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_checks=0

check_result() {
    ((total_checks++))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((success_count++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        if [ ! -z "$3" ]; then
            echo -e "   ${YELLOW}Details: $3${NC}"
        fi
    fi
}

echo -e "\n🔒 SECURITY AUDIT VERIFICATION:"

# 1. Check npm audit status
echo "Checking npm security vulnerabilities..."
cd /workspace
npm audit --audit-level high > /dev/null 2>&1
check_result $? "NPM security audit clean" "All high/critical vulnerabilities resolved"

# 2. Frontend Tests
echo -e "\n🎨 FRONTEND TESTS VERIFICATION:"

# Test npm test script
npm test > /dev/null 2>&1
check_result $? "Frontend test script passes" "npm test returns success"

# Test frontend build
npm run build > build.log 2>&1
build_result=$?
check_result $build_result "Frontend build successful" "Next.js build completes without errors"

if [ $build_result -eq 0 ]; then
    echo "   Build output: $(tail -3 build.log | grep 'Compiled successfully')"
fi

# 3. Backend Tests
echo -e "\n🔧 BACKEND TESTS VERIFICATION:"

# Set up environment
export PATH=$PATH:/home/ubuntu/.local/bin
export PYTHONPATH="/workspace:$PYTHONPATH"

# Test backend import
python3 -c "from backend.simple_backend import app; print('Backend import successful')" > /dev/null 2>&1
check_result $? "Backend imports successfully" "FastAPI app can be imported without errors"

# Test backend tests
python3 -m pytest tests/test_simple_backend.py -v > backend_test.log 2>&1
backend_test_result=$?
check_result $backend_test_result "Backend tests pass" "All pytest tests complete successfully"

if [ $backend_test_result -eq 0 ]; then
    passed_tests=$(grep "passed" backend_test.log | tail -1)
    echo "   Test results: $passed_tests"
fi

# 4. API Integration Test
echo -e "\n🌐 API INTEGRATION VERIFICATION:"

# Start backend for testing
python3 backend/simple_backend.py > api_test.log 2>&1 &
BACKEND_PID=$!
sleep 5

# Test health endpoint
curl -f -s http://localhost:8000/health > /dev/null 2>&1
check_result $? "Backend health endpoint responds" "API server accessible"

# Test vibe-coding endpoint
response=$(curl -s -X POST http://localhost:8000/api/vibe-coding \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test pipeline verification"}')

if echo "$response" | grep -q "job_id"; then
    check_result 0 "Vibe-coding API endpoint functional" "API accepts requests and returns job IDs"
else
    check_result 1 "Vibe-coding API endpoint functional" "API endpoint not responding correctly"
fi

# Clean up
kill $BACKEND_PID 2>/dev/null

# 5. Overall Pipeline Status
echo -e "\n📊 PIPELINE STATUS SUMMARY:"
echo -e "   Total Checks: $total_checks"
echo -e "   Successful: $success_count"
echo -e "   Failed: $((total_checks - success_count))"

if [ $success_count -eq $total_checks ]; then
    echo -e "\n${GREEN}🎉 ALL PIPELINE CHECKS PASSED${NC}"
    echo -e "${GREEN}✅ Security: CLEAN (no vulnerabilities)${NC}"
    echo -e "${GREEN}✅ Frontend Tests: PASSING${NC}"
    echo -e "${GREEN}✅ Backend Tests: PASSING${NC}"
    echo -e "${GREEN}✅ API Integration: WORKING${NC}"
    echo -e "${GREEN}✅ GitHub Actions Pipeline: READY FOR GREEN STATUS${NC}"
    echo -e "\n${GREEN}🚀 DEPLOYMENT PIPELINE IS OPERATIONAL${NC}"
    exit 0
elif [ $success_count -ge $((total_checks * 3 / 4)) ]; then
    echo -e "\n${YELLOW}⚠️  MOST CHECKS PASSED - MINOR ISSUES REMAIN${NC}"
    echo -e "${YELLOW}🔧 Address remaining issues before deployment${NC}"
    exit 1
else
    echo -e "\n${RED}❌ CRITICAL PIPELINE ISSUES FOUND${NC}"
    echo -e "${RED}🚨 Pipeline not ready - requires fixes${NC}"
    exit 2
fi