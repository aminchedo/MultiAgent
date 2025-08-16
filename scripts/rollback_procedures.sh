#!/bin/bash
# Production Rollback Procedures - Agent System
# Version: 2.0.0
# Emergency Contact: +1-555-AGENT-HELP

set -euo pipefail

# Configuration
NAMESPACE="agent-system"
ROLLBACK_TIMEOUT="300"
HEALTH_CHECK_RETRIES="10"
HEALTH_CHECK_INTERVAL="30"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTION]

Production Rollback Procedures for Agent System

OPTIONS:
    auto-rollback <previous-version>    Automated rollback to previous version
    manual-rollback <previous-version>  Manual rollback with confirmation steps
    verify-rollback <version>           Verify rollback completion
    emergency-stop                      Emergency stop all services
    health-check                        Check system health
    list-versions                       List available rollback versions
    help                               Show this help message

EXAMPLES:
    $0 auto-rollback v2.1.5
    $0 manual-rollback v2.1.5
    $0 verify-rollback v2.1.5
    $0 emergency-stop

EMERGENCY CONTACTS:
    DevOps Team: devops-team@agents.example.com
    On-Call: +1-555-AGENT-HELP
EOF
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl access
    if ! kubectl auth can-i '*' '*' --namespace=${NAMESPACE} >/dev/null 2>&1; then
        error "Insufficient kubectl permissions for namespace ${NAMESPACE}"
        exit 1
    fi
    
    # Check namespace exists
    if ! kubectl get namespace ${NAMESPACE} >/dev/null 2>&1; then
        error "Namespace ${NAMESPACE} does not exist"
        exit 1
    fi
    
    # Check current deployment status
    if ! kubectl get deployment agent-system -n ${NAMESPACE} >/dev/null 2>&1; then
        error "Agent system deployment not found in namespace ${NAMESPACE}"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Function to backup current state
backup_current_state() {
    local backup_dir="/tmp/agent-system-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${backup_dir}"
    
    log "Backing up current state to ${backup_dir}..."
    
    # Backup deployment
    kubectl get deployment agent-system -n ${NAMESPACE} -o yaml > "${backup_dir}/deployment.yaml"
    
    # Backup configmap
    kubectl get configmap agent-system-config -n ${NAMESPACE} -o yaml > "${backup_dir}/configmap.yaml" 2>/dev/null || true
    
    # Backup secrets
    kubectl get secrets -n ${NAMESPACE} -o yaml > "${backup_dir}/secrets.yaml"
    
    # Backup ingress
    kubectl get ingress agent-system-ingress -n ${NAMESPACE} -o yaml > "${backup_dir}/ingress.yaml" 2>/dev/null || true
    
    # Backup HPA
    kubectl get hpa agent-system-hpa -n ${NAMESPACE} -o yaml > "${backup_dir}/hpa.yaml" 2>/dev/null || true
    
    echo "${backup_dir}" > /tmp/last-backup-location
    success "Current state backed up to ${backup_dir}"
}

# Function to get current version
get_current_version() {
    kubectl get deployment agent-system -n ${NAMESPACE} -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "unknown"
}

# Function to list available versions
list_available_versions() {
    log "Available rollback versions:"
    
    # Get from deployment history
    kubectl rollout history deployment/agent-system -n ${NAMESPACE}
    
    # Get from image tags (if available)
    log "Recent image versions:"
    kubectl get deployment agent-system -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].image}'
}

# Function to perform health check
perform_health_check() {
    local endpoint=${1:-"https://api.agents.example.com"}
    local retries=${2:-${HEALTH_CHECK_RETRIES}}
    
    log "Performing health check on ${endpoint}..."
    
    for i in $(seq 1 ${retries}); do
        log "Health check attempt ${i}/${retries}..."
        
        # Basic health endpoint
        if curl -sf "${endpoint}/health" >/dev/null 2>&1; then
            # Check API functionality
            if curl -sf "${endpoint}/api/v2/agents/status" >/dev/null 2>&1; then
                # Check metrics endpoint
                if curl -sf "${endpoint}/metrics" >/dev/null 2>&1; then
                    success "Health check passed on attempt ${i}"
                    return 0
                fi
            fi
        fi
        
        if [ ${i} -lt ${retries} ]; then
            warning "Health check failed, retrying in ${HEALTH_CHECK_INTERVAL} seconds..."
            sleep ${HEALTH_CHECK_INTERVAL}
        fi
    done
    
    error "Health check failed after ${retries} attempts"
    return 1
}

# Function to check system metrics
check_system_metrics() {
    log "Checking system metrics..."
    
    # Check pod status
    local ready_pods=$(kubectl get pods -n ${NAMESPACE} -l app=agent-system --field-selector=status.phase=Running -o name | wc -l)
    local total_pods=$(kubectl get pods -n ${NAMESPACE} -l app=agent-system -o name | wc -l)
    
    log "Pod status: ${ready_pods}/${total_pods} running"
    
    # Check resource usage
    kubectl top pods -n ${NAMESPACE} -l app=agent-system --no-headers 2>/dev/null || log "Resource metrics unavailable"
    
    # Check recent events
    log "Recent events:"
    kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp' | tail -10
}

# Function to automated rollback
auto_rollback() {
    local target_version="$1"
    
    log "Starting automated rollback to version ${target_version}..."
    
    # Backup current state
    backup_current_state
    
    # Get current version
    local current_version=$(get_current_version)
    log "Current version: ${current_version}"
    log "Target version: ${target_version}"
    
    # Confirm rollback
    read -p "Proceed with automated rollback? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        warning "Rollback cancelled by user"
        exit 0
    fi
    
    # Record rollback start
    log "Recording rollback initiation..."
    kubectl annotate deployment agent-system -n ${NAMESPACE} \
        rollback.timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        rollback.from-version="${current_version}" \
        rollback.to-version="${target_version}" \
        rollback.initiated-by="$(whoami)" || true
    
    # Perform rollback
    if [[ "${target_version}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # Rollback to specific version
        log "Rolling back to specific version ${target_version}..."
        kubectl set image deployment/agent-system agent-system="${DOCKER_REGISTRY:-registry.example.com}/agent-system:${target_version}" -n ${NAMESPACE}
    else
        # Rollback using revision number
        log "Rolling back using revision ${target_version}..."
        kubectl rollout undo deployment/agent-system -n ${NAMESPACE} --to-revision="${target_version}"
    fi
    
    # Wait for rollback to complete
    log "Waiting for rollback to complete (timeout: ${ROLLBACK_TIMEOUT}s)..."
    if kubectl rollout status deployment/agent-system -n ${NAMESPACE} --timeout=${ROLLBACK_TIMEOUT}s; then
        success "Rollback deployment completed"
    else
        error "Rollback deployment timed out"
        return 1
    fi
    
    # Verify rollback
    sleep 30  # Allow time for pods to fully start
    if perform_health_check; then
        success "Automated rollback to ${target_version} completed successfully"
        
        # Record successful rollback
        kubectl annotate deployment agent-system -n ${NAMESPACE} \
            rollback.completed="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            rollback.status="success" || true
        
        # Send notification
        send_notification "SUCCESS" "Automated rollback to ${target_version} completed successfully"
    else
        error "Rollback completed but health checks failed"
        kubectl annotate deployment agent-system -n ${NAMESPACE} \
            rollback.status="failed-health-check" || true
        
        send_notification "FAILURE" "Rollback to ${target_version} completed but health checks failed"
        return 1
    fi
}

# Function for manual rollback with detailed steps
manual_rollback() {
    local target_version="$1"
    
    log "Starting manual rollback procedure to version ${target_version}..."
    
    # Step 1: Backup
    echo
    log "STEP 1: Backup current state"
    backup_current_state
    read -p "Press Enter to continue to Step 2..."
    
    # Step 2: Health check before rollback
    echo
    log "STEP 2: Pre-rollback health check"
    check_system_metrics
    perform_health_check || warning "Pre-rollback health check failed"
    read -p "Press Enter to continue to Step 3..."
    
    # Step 3: Scale down to reduce impact
    echo
    log "STEP 3: Scale down deployment"
    kubectl scale deployment agent-system --replicas=1 -n ${NAMESPACE}
    kubectl rollout status deployment/agent-system -n ${NAMESPACE} --timeout=60s
    read -p "Press Enter to continue to Step 4..."
    
    # Step 4: Perform rollback
    echo
    log "STEP 4: Execute rollback"
    if [[ "${target_version}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        kubectl set image deployment/agent-system agent-system="${DOCKER_REGISTRY:-registry.example.com}/agent-system:${target_version}" -n ${NAMESPACE}
    else
        kubectl rollout undo deployment/agent-system -n ${NAMESPACE} --to-revision="${target_version}"
    fi
    
    kubectl rollout status deployment/agent-system -n ${NAMESPACE} --timeout=${ROLLBACK_TIMEOUT}s
    read -p "Press Enter to continue to Step 5..."
    
    # Step 5: Scale back up
    echo
    log "STEP 5: Scale back up"
    kubectl scale deployment agent-system --replicas=3 -n ${NAMESPACE}
    kubectl rollout status deployment/agent-system -n ${NAMESPACE} --timeout=180s
    read -p "Press Enter to continue to Step 6..."
    
    # Step 6: Verify rollback
    echo
    log "STEP 6: Verify rollback"
    sleep 30
    if perform_health_check; then
        success "Manual rollback verification passed"
        send_notification "SUCCESS" "Manual rollback to ${target_version} completed successfully"
    else
        error "Manual rollback verification failed"
        send_notification "FAILURE" "Manual rollback to ${target_version} failed verification"
        
        echo
        warning "Rollback verification failed. Options:"
        echo "1. Investigate and fix issues"
        echo "2. Roll forward to a newer version"
        echo "3. Emergency stop services"
        read -p "Choose option (1/2/3): " option
        
        case $option in
            1) log "Please investigate issues manually" ;;
            2) log "Please deploy a newer version" ;;
            3) emergency_stop ;;
            *) warning "Invalid option selected" ;;
        esac
        
        return 1
    fi
}

# Function to verify rollback completion
verify_rollback() {
    local expected_version="$1"
    
    log "Verifying rollback to version ${expected_version}..."
    
    # Check deployment version
    local current_version=$(get_current_version)
    
    if [[ "${current_version}" == "${expected_version}" ]]; then
        success "Version verification passed: ${current_version}"
    else
        error "Version mismatch: expected ${expected_version}, got ${current_version}"
        return 1
    fi
    
    # Check pod readiness
    local ready_pods=$(kubectl get deployment agent-system -n ${NAMESPACE} -o jsonpath='{.status.readyReplicas}')
    local desired_pods=$(kubectl get deployment agent-system -n ${NAMESPACE} -o jsonpath='{.spec.replicas}')
    
    if [[ "${ready_pods}" == "${desired_pods}" ]]; then
        success "Pod readiness verification passed: ${ready_pods}/${desired_pods}"
    else
        error "Pod readiness verification failed: ${ready_pods}/${desired_pods}"
        return 1
    fi
    
    # Health check
    if perform_health_check; then
        success "Health check verification passed"
    else
        error "Health check verification failed"
        return 1
    fi
    
    # Check metrics
    check_system_metrics
    
    success "Rollback verification completed successfully"
}

# Function for emergency stop
emergency_stop() {
    log "EMERGENCY STOP INITIATED"
    
    warning "This will stop all agent system services immediately!"
    read -p "Type 'EMERGENCY' to confirm: " confirm
    
    if [[ "$confirm" != "EMERGENCY" ]]; then
        warning "Emergency stop cancelled"
        exit 0
    fi
    
    log "Scaling deployment to 0 replicas..."
    kubectl scale deployment agent-system --replicas=0 -n ${NAMESPACE}
    
    log "Waiting for pods to terminate..."
    kubectl wait --for=delete pod -l app=agent-system -n ${NAMESPACE} --timeout=60s || true
    
    success "Emergency stop completed - all services stopped"
    send_notification "EMERGENCY" "Emergency stop executed - all agent system services stopped"
    
    log "To restore services, scale deployment back up:"
    log "kubectl scale deployment agent-system --replicas=3 -n ${NAMESPACE}"
}

# Function to send notifications
send_notification() {
    local status="$1"
    local message="$2"
    
    # Log notification
    log "NOTIFICATION [${status}]: ${message}"
    
    # Send to monitoring system (webhook example)
    if [[ -n "${WEBHOOK_URL:-}" ]]; then
        curl -X POST "${WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{
                \"status\": \"${status}\",
                \"message\": \"${message}\",
                \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
                \"system\": \"agent-system\",
                \"environment\": \"production\"
            }" >/dev/null 2>&1 || true
    fi
    
    # Send email alert (if configured)
    if command -v mail >/dev/null 2>&1 && [[ -n "${ALERT_EMAIL:-}" ]]; then
        echo "${message}" | mail -s "Agent System Rollback Alert [${status}]" "${ALERT_EMAIL}" || true
    fi
}

# Function to generate rollback report
generate_rollback_report() {
    local rollback_type="$1"
    local target_version="$2"
    local report_file="/tmp/rollback-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "${report_file}" << EOF
# Agent System Rollback Report

**Date**: $(date)
**Type**: ${rollback_type}
**Target Version**: ${target_version}
**Executed By**: $(whoami)

## Pre-Rollback Status
- Current Version: $(get_current_version)
- Pod Status: $(kubectl get pods -n ${NAMESPACE} -l app=agent-system --no-headers | wc -l) pods

## Rollback Execution
- Backup Location: $(cat /tmp/last-backup-location 2>/dev/null || echo "N/A")
- Rollback Method: ${rollback_type}
- Target Version: ${target_version}

## Post-Rollback Status
- New Version: $(get_current_version)
- Health Check: $(perform_health_check >/dev/null 2>&1 && echo "PASS" || echo "FAIL")
- System Status: $(kubectl get deployment agent-system -n ${NAMESPACE} -o jsonpath='{.status.conditions[0].type}')

## System Metrics
\`\`\`
$(check_system_metrics 2>&1)
\`\`\`

## Next Steps
- Monitor system for 24 hours
- Verify all functionality
- Update documentation

---
Generated by: $0
EOF
    
    log "Rollback report generated: ${report_file}"
    echo "${report_file}"
}

# Main execution logic
main() {
    case "${1:-help}" in
        auto-rollback)
            if [[ $# -ne 2 ]]; then
                error "Usage: $0 auto-rollback <version>"
                exit 1
            fi
            check_prerequisites
            auto_rollback "$2"
            generate_rollback_report "automated" "$2"
            ;;
        manual-rollback)
            if [[ $# -ne 2 ]]; then
                error "Usage: $0 manual-rollback <version>"
                exit 1
            fi
            check_prerequisites
            manual_rollback "$2"
            generate_rollback_report "manual" "$2"
            ;;
        verify-rollback)
            if [[ $# -ne 2 ]]; then
                error "Usage: $0 verify-rollback <version>"
                exit 1
            fi
            check_prerequisites
            verify_rollback "$2"
            ;;
        emergency-stop)
            check_prerequisites
            emergency_stop
            ;;
        health-check)
            check_prerequisites
            perform_health_check
            check_system_metrics
            ;;
        list-versions)
            check_prerequisites
            list_available_versions
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"