#!/bin/bash

# Political Bias Detector - Pre-Deployment Verification Script
# This script verifies all components are ready for deployment to 10.122.0.3

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Political Bias Detector - Pre-Deployment Verification ${NC} ║"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((CHECKS_WARNING++))
}

print_section() {
    echo -e "\n${BLUE}━━━ $1 ━━━${NC}"
}

# START CHECKS
print_header

print_section "File Structure Verification"

files_to_check=(
    ".env.production"
    "docker-compose.production.yml"
    "Dockerfile.backend"
    "frontend-nextjs/Dockerfile"
    "nginx/nginx.conf"
    "nginx/conf.d/default.conf"
    "scripts/deploy.sh"
    "DEPLOYMENT.md"
    "QUICK_DEPLOY.md"
    "DEPLOYMENT_CHECKLIST.md"
    "START_HERE.md"
)

for file in "${files_to_check[@]}"; do
    if [ -f "${PROJECT_DIR}/${file}" ]; then
        check_pass "Found: $file"
    else
        check_fail "Missing: $file"
    fi
done

print_section "Configuration Verification"

# Check .env.production has values
if grep -q "AIzaSyAwFjWSAIr7t3K2SAZNEGKr2B_mqLXX8KU" "${PROJECT_DIR}/.env.production"; then
    check_pass "Gemini API key configured"
else
    check_warn "Gemini API key not found in .env.production"
fi

if grep -q "07e8e55d4bf34310ada5a3fd903508c7" "${PROJECT_DIR}/.env.production"; then
    check_pass "NewsAPI key configured"
else
    check_warn "NewsAPI key not found"
fi

if grep -q "b2931e4e23ee011070c3e39b5c61c67df0e59b99" "${PROJECT_DIR}/.env.production"; then
    check_pass "Serper API key configured"
else
    check_warn "Serper API key not found"
fi

if grep -q "production" "${PROJECT_DIR}/.env.production"; then
    check_pass "Environment set to production"
else
    check_fail "Environment not set to production"
fi

print_section "Backend Files Verification"

backend_files=(
    "backend/main.py"
    "backend/config.py"
    "backend/database.py"
    "backend/api/v1/endpoints/search.py"
    "backend/api/v1/endpoints/url_classifier.py"
    "src/backend/bias_classifier.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "${PROJECT_DIR}/${file}" ]; then
        check_pass "Backend: $file exists"
    else
        check_fail "Backend: $file missing"
    fi
done

print_section "Frontend Files Verification"

frontend_files=(
    "frontend-nextjs/app/page.tsx"
    "frontend-nextjs/app/layout.tsx"
    "frontend-nextjs/package.json"
    "frontend-nextjs/tsconfig.json"
)

for file in "${frontend_files[@]}"; do
    if [ -f "${PROJECT_DIR}/${file}" ]; then
        check_pass "Frontend: $file exists"
    else
        check_fail "Frontend: $file missing"
    fi
done

print_section "Docker Configuration Verification"

# Check docker-compose has all services
if grep -q "postgres:" "${PROJECT_DIR}/docker-compose.production.yml"; then
    check_pass "Docker Compose: PostgreSQL service configured"
else
    check_fail "Docker Compose: PostgreSQL service missing"
fi

if grep -q "backend:" "${PROJECT_DIR}/docker-compose.production.yml"; then
    check_pass "Docker Compose: Backend service configured"
else
    check_fail "Docker Compose: Backend service missing"
fi

if grep -q "frontend:" "${PROJECT_DIR}/docker-compose.production.yml"; then
    check_pass "Docker Compose: Frontend service configured"
else
    check_fail "Docker Compose: Frontend service missing"
fi

if grep -q "nginx:" "${PROJECT_DIR}/docker-compose.production.yml"; then
    check_pass "Docker Compose: Nginx service configured"
else
    check_fail "Docker Compose: Nginx service missing"
fi

print_section "Nginx Configuration Verification"

if grep -q "upstream backend" "${PROJECT_DIR}/nginx/nginx.conf"; then
    check_pass "Nginx: Backend upstream configured"
else
    check_fail "Nginx: Backend upstream missing"
fi

if grep -q "proxy_pass http://backend" "${PROJECT_DIR}/nginx/conf.d/default.conf"; then
    check_pass "Nginx: Backend proxy configured"
else
    check_fail "Nginx: Backend proxy missing"
fi

if grep -q "proxy_pass http://frontend" "${PROJECT_DIR}/nginx/conf.d/default.conf"; then
    check_pass "Nginx: Frontend proxy configured"
else
    check_fail "Nginx: Frontend proxy missing"
fi

print_section "Deployment Script Verification"

if [ -x "${PROJECT_DIR}/scripts/deploy.sh" ]; then
    check_pass "Deploy script is executable"
else
    check_warn "Deploy script is not executable (will set on server)"
fi

if grep -q "check_prerequisites" "${PROJECT_DIR}/scripts/deploy.sh"; then
    check_pass "Deploy script: has prerequisite checks"
else
    check_fail "Deploy script: missing prerequisite checks"
fi

if grep -q "docker-compose" "${PROJECT_DIR}/scripts/deploy.sh"; then
    check_pass "Deploy script: uses docker-compose"
else
    check_fail "Deploy script: does not use docker-compose"
fi

print_section "ML Models Verification"

model_files=(
    "models/custom_bias_detector/config.json"
    "models/custom_bias_detector/model.safetensors"
)

for file in "${model_files[@]}"; do
    if [ -f "${PROJECT_DIR}/${file}" ]; then
        check_pass "Models: $file exists"
    else
        check_warn "Models: $file will be downloaded at startup"
    fi
done

print_section "Documentation Verification"

docs_files=(
    "START_HERE.md"
    "DEPLOYMENT_CHECKLIST.md"
    "DEPLOYMENT.md"
    "QUICK_DEPLOY.md"
)

for file in "${docs_files[@]}"; do
    if [ -f "${PROJECT_DIR}/${file}" ]; then
        file_size=$(stat -f%z "${PROJECT_DIR}/${file}" 2>/dev/null | wc -c)
        if [ "$file_size" -gt 1000 ]; then
            check_pass "Documentation: $file ($(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo 'readable size'))"
        else
            check_warn "Documentation: $file exists but may be incomplete"
        fi
    else
        check_fail "Documentation: $file missing"
    fi
done

print_section "Summary"

TOTAL=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))

echo ""
echo -e "${GREEN}✓ Passed:${NC}  $CHECKS_PASSED"
echo -e "${RED}✗ Failed:${NC}  $CHECKS_FAILED"
echo -e "${YELLOW}⚠ Warnings:${NC} $CHECKS_WARNING"
echo -e "━━━━━━━━━━━━━━━━━━"
echo -e "Total:  $TOTAL checks"

echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical checks passed!${NC}"
    echo ""
    echo "Your system is ready for deployment to 10.122.0.3"
    echo ""
    echo "Next steps:"
    echo "  1. Read: START_HERE.md"
    echo "  2. Review: DEPLOYMENT_CHECKLIST.md"
    echo "  3. SSH to server: ssh user@10.122.0.3"
    echo "  4. Follow deployment guide"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Critical issues found!${NC}"
    echo ""
    echo "Please fix the failed checks before deployment."
    echo "Review the files listed above and run:"
    echo "  bash ${SCRIPT_DIR}/verify-deployment.sh"
    echo ""
    exit 1
fi
