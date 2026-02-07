#!/bin/bash

################################################################################
# GARCAR ENTERPRISE - MASTER DEPLOYMENT ORCHESTRATOR
# One-Command Production Deployment for All Systems
# Author: Garrett Carrol
# Date: February 7, 2026
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
DEPLOY_MODE="${2:-full}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs/deploy_${TIMESTAMP}"

mkdir -p "${LOG_DIR}"

################################################################################
# LOGGING FUNCTIONS
################################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/deploy.log"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/deploy.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/deploy.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/deploy.log"
}

################################################################################
# PRE-FLIGHT CHECKS
################################################################################

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing=()
    
    command -v docker >/dev/null 2>&1 || missing+=("docker")
    command -v kubectl >/dev/null 2>&1 || missing+=("kubectl")
    command -v git >/dev/null 2>&1 || missing+=("git")
    command -v npm >/dev/null 2>&1 || missing+=("npm")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_error "Install missing tools and try again"
        exit 1
    fi
    
    log_success "All dependencies found"
}

check_environment() {
    log_info "Validating environment: ${ENVIRONMENT}"
    
    if [[ ! "${ENVIRONMENT}" =~ ^(dev|staging|production)$ ]]; then
        log_error "Invalid environment: ${ENVIRONMENT}"
        log_error "Must be one of: dev, staging, production"
        exit 1
    fi
    
    # Check for required environment variables
    if [ -f ".env.${ENVIRONMENT}" ]; then
        log_info "Loading environment from .env.${ENVIRONMENT}"
        set -a
        source ".env.${ENVIRONMENT}"
        set +a
    else
        log_warn "No .env.${ENVIRONMENT} file found"
    fi
    
    log_success "Environment validated"
}

################################################################################
# SYSTEM 1: TREE OF LIFE CORE (THIS REPO)
################################################################################

deploy_tree_of_life() {
    log_info "========================================"
    log_info "DEPLOYING: Tree of Life Core"
    log_info "========================================"
    
    log_info "Building Docker containers..."
    docker-compose build 2>&1 | tee "${LOG_DIR}/tree-of-life-build.log"
    
    log_info "Starting services..."
    docker-compose up -d 2>&1 | tee "${LOG_DIR}/tree-of-life-up.log"
    
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    if docker-compose ps | grep -q "Up"; then
        log_success "Tree of Life Core deployed successfully"
    else
        log_error "Tree of Life Core deployment failed"
        docker-compose logs | tee "${LOG_DIR}/tree-of-life-error.log"
        return 1
    fi
}

################################################################################
# SYSTEM 2: ENTERPRISE AI DEPLOYMENT
################################################################################

deploy_enterprise_ai() {
    log_info "========================================"
    log_info "DEPLOYING: Enterprise AI Grid"
    log_info "========================================"
    
    # Check if repo exists, clone if not
    if [ ! -d "../enterprise-ai-deployment" ]; then
        log_info "Cloning enterprise-ai-deployment..."
        git clone https://github.com/Garrettc123/enterprise-ai-deployment.git ../enterprise-ai-deployment
    fi
    
    cd ../enterprise-ai-deployment
    
    log_info "Initializing Terraform..."
    terraform init 2>&1 | tee "${LOG_DIR}/terraform-init.log"
    
    log_info "Planning infrastructure..."
    terraform plan -out=tfplan 2>&1 | tee "${LOG_DIR}/terraform-plan.log"
    
    if [ "${ENVIRONMENT}" = "production" ]; then
        log_warn "Production deployment requires manual approval"
        read -p "Apply Terraform plan? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            terraform apply tfplan 2>&1 | tee "${LOG_DIR}/terraform-apply.log"
            log_success "Enterprise AI infrastructure deployed"
        else
            log_warn "Terraform apply skipped"
        fi
    else
        terraform apply -auto-approve 2>&1 | tee "${LOG_DIR}/terraform-apply.log"
        log_success "Enterprise AI infrastructure deployed"
    fi
    
    cd -
}

################################################################################
# SYSTEM 3: NWU PROTOCOL (BLOCKCHAIN)
################################################################################

deploy_nwu_protocol() {
    log_info "========================================"
    log_info "DEPLOYING: NWU Protocol"
    log_info "========================================"
    
    # Find NWU protocol repos
    local nwu_repos=()
    for repo in ../*/; do
        if [[ "$(basename $repo)" =~ nwu ]]; then
            nwu_repos+=("$repo")
        fi
    done
    
    if [ ${#nwu_repos[@]} -eq 0 ]; then
        log_warn "No NWU protocol repositories found"
        return 0
    fi
    
    for repo in "${nwu_repos[@]}"; do
        log_info "Deploying $(basename $repo)..."
        cd "$repo"
        
        if [ -f "package.json" ]; then
            npm install 2>&1 | tee "${LOG_DIR}/nwu-npm-install.log"
            
            # Deploy to testnet first if not production
            if [ "${ENVIRONMENT}" != "production" ]; then
                log_info "Deploying to Sepolia testnet..."
                npx hardhat run scripts/deploy.js --network sepolia 2>&1 | tee "${LOG_DIR}/nwu-deploy-sepolia.log"
                log_success "NWU Protocol deployed to testnet"
            else
                log_warn "Production blockchain deployment requires manual execution"
                log_warn "Run: npx hardhat run scripts/deploy.js --network mainnet"
            fi
        fi
        
        cd -
    done
}

################################################################################
# SYSTEM 4: KUBERNETES SERVICES
################################################################################

deploy_kubernetes_services() {
    log_info "========================================"
    log_info "DEPLOYING: Kubernetes Services"
    log_info "========================================"
    
    # Check if kubectl is configured
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_warn "kubectl not configured or cluster not accessible"
        log_warn "Skipping Kubernetes deployment"
        return 0
    fi
    
    log_info "Current cluster: $(kubectl config current-context)"
    
    # Deploy from tree-of-life k8s manifests if they exist
    if [ -d "k8s" ]; then
        log_info "Applying Kubernetes manifests..."
        kubectl apply -f k8s/ 2>&1 | tee "${LOG_DIR}/k8s-apply.log"
    fi
    
    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod --all --timeout=300s 2>&1 | tee "${LOG_DIR}/k8s-wait.log" || true
    
    log_success "Kubernetes services deployed"
}

################################################################################
# SYSTEM 5: DOCKER COMPOSE SERVICES
################################################################################

deploy_additional_services() {
    log_info "========================================"
    log_info "DEPLOYING: Additional Services"
    log_info "========================================"
    
    # Find and deploy other docker-compose services
    for dir in ../*/; do
        if [ -f "${dir}docker-compose.yml" ] && [ "$(basename $dir)" != "tree-of-life-core" ]; then
            log_info "Found service: $(basename $dir)"
            cd "$dir"
            
            log_info "Building $(basename $dir)..."
            docker-compose build 2>&1 | tee "${LOG_DIR}/$(basename $dir)-build.log"
            
            log_info "Starting $(basename $dir)..."
            docker-compose up -d 2>&1 | tee "${LOG_DIR}/$(basename $dir)-up.log"
            
            cd -
        fi
    done
}

################################################################################
# HEALTH CHECKS
################################################################################

run_health_checks() {
    log_info "========================================"
    log_info "RUNNING HEALTH CHECKS"
    log_info "========================================"
    
    local failed=0
    
    # Check Docker services
    log_info "Checking Docker services..."
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker services running"
    else
        log_error "Some Docker services not running"
        failed=$((failed + 1))
    fi
    
    # Check Kubernetes if available
    if kubectl cluster-info >/dev/null 2>&1; then
        log_info "Checking Kubernetes pods..."
        local unhealthy=$(kubectl get pods --all-namespaces | grep -v "Running\|Completed" | wc -l)
        if [ "$unhealthy" -le 1 ]; then  # 1 because of header
            log_success "All Kubernetes pods healthy"
        else
            log_error "Some Kubernetes pods unhealthy"
            kubectl get pods --all-namespaces | grep -v "Running\|Completed" | tee "${LOG_DIR}/unhealthy-pods.log"
            failed=$((failed + 1))
        fi
    fi
    
    if [ $failed -eq 0 ]; then
        log_success "All health checks passed"
        return 0
    else
        log_error "${failed} health check(s) failed"
        return 1
    fi
}

################################################################################
# DEPLOYMENT STATUS SUMMARY
################################################################################

print_status_summary() {
    log_info "========================================"
    log_info "DEPLOYMENT STATUS SUMMARY"
    log_info "========================================"
    
    echo ""
    echo "Environment: ${ENVIRONMENT}"
    echo "Timestamp: ${TIMESTAMP}"
    echo "Logs: ${LOG_DIR}"
    echo ""
    
    # Docker services
    echo "Docker Services:"
    docker-compose ps
    echo ""
    
    # Kubernetes services
    if kubectl cluster-info >/dev/null 2>&1; then
        echo "Kubernetes Pods:"
        kubectl get pods --all-namespaces
        echo ""
        
        echo "Kubernetes Services:"
        kubectl get svc --all-namespaces
        echo ""
    fi
    
    # Access URLs
    echo "Access URLs:"
    echo "- Tree of Life Core: http://localhost:8000"
    echo "- Dashboard: http://localhost:3000"
    echo ""
}

################################################################################
# MAIN DEPLOYMENT FLOW
################################################################################

main() {
    log_info "========================================"
    log_info "GARCAR ENTERPRISE DEPLOYMENT"
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Mode: ${DEPLOY_MODE}"
    log_info "========================================"
    
    # Pre-flight
    check_dependencies
    check_environment
    
    # Core deployments
    deploy_tree_of_life
    
    if [ "${DEPLOY_MODE}" = "full" ]; then
        deploy_enterprise_ai
        deploy_nwu_protocol
        deploy_kubernetes_services
        deploy_additional_services
    fi
    
    # Validation
    run_health_checks
    
    # Summary
    print_status_summary
    
    log_success "========================================"
    log_success "DEPLOYMENT COMPLETE!"
    log_success "========================================"
    
    log_info "Next steps:"
    log_info "1. Review logs in ${LOG_DIR}"
    log_info "2. Access services at URLs above"
    log_info "3. Run: ./scripts/validate-deployment.sh"
    log_info "4. Monitor: docker-compose logs -f"
}

# Run main deployment
main "$@"
