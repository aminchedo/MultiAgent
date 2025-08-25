# Operational Runbooks - Agent System Production
## Version 2.0.0 | Maintenance Window: 2023-11-20 01:00-03:00 UTC

---

## 📋 **Quick Reference**

| **Emergency Contact** | **Contact Info** |
|----------------------|------------------|
| **On-Call DevOps** | +1-555-AGENT-HELP |
| **Security Team** | security-team@agents.example.com |
| **Engineering Lead** | eng-lead@agents.example.com |

| **Critical URLs** | **Purpose** |
|------------------|-------------|
| `https://api.agents.example.com/health` | System Health |
| `https://monitoring.agents.example.com` | Monitoring Dashboard |
| `https://status.agents.example.com` | Public Status Page |

---

## 🚀 **1. Deployment Procedures**

### **1.1 Pre-Deployment Checklist**

```bash
# Verify deployment readiness
./scripts/pre-deployment-check.sh

# Check system status
kubectl get pods -n agent-system
kubectl get deployment agent-system -n agent-system

# Verify health endpoints
curl -f https://api.agents.example.com/health
```

**Required Approvals:**
- [ ] Security Team Sign-off
- [ ] Engineering Lead Approval  
- [ ] DevOps Team Ready
- [ ] Maintenance Window Confirmed

### **1.2 Production Deployment Steps**

#### **Step 1: Environment Preparation**
```bash
# Set deployment variables
export BUILD_VERSION="v2.2.0"
export DOCKER_REGISTRY="your-registry.com"
export ENVIRONMENT="production"

# Verify infrastructure
terraform plan -var-file=production.tfvars
```

#### **Step 2: Pre-Deployment Verification**
```bash
# Run pre-deployment job
kubectl apply -f k8s/production/pre-deployment-checks.yaml
kubectl wait --for=condition=complete job/pre-deployment-checks -n agent-system --timeout=300s
```

#### **Step 3: Blue-Green Deployment**
```bash
# Deploy green environment
envsubst < k8s/production/deployment-verification.yaml | kubectl apply -f -

# Wait for green deployment
kubectl rollout status deployment/agent-system -n agent-system --timeout=600s

# Run post-deployment verification
kubectl apply -f k8s/production/post-deployment-verification.yaml
```

#### **Step 4: Traffic Switch**
```bash
# Switch traffic to green
kubectl patch service agent-system-service -n agent-system \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for 10 minutes
./scripts/monitor_deployment.py --duration 600
```

#### **Step 5: Cleanup**
```bash
# Remove old blue deployment after 24h monitoring
kubectl delete deployment agent-system-blue -n agent-system
```

### **1.3 Deployment Rollback**

#### **Emergency Rollback (< 5 minutes)**
```bash
# Immediate rollback
./scripts/rollback_procedures.sh auto-rollback v2.1.5

# Verify rollback
./scripts/rollback_procedures.sh verify-rollback v2.1.5
```

#### **Planned Rollback**
```bash
# Manual rollback with confirmations
./scripts/rollback_procedures.sh manual-rollback v2.1.5
```

---

## 📊 **2. Monitoring & Alerting**

### **2.1 Health Check Procedures**

#### **System Health Verification**
```bash
# Comprehensive health check
curl -s https://api.agents.example.com/health | jq '.'

# Expected Response:
{
  "status": "healthy",
  "timestamp": "2023-11-20T01:30:00Z",
  "version": "2.2.0",
  "uptime": 86400,
  "checks": {
    "database": "healthy",
    "redis": "healthy", 
    "agents": "healthy",
    "external_apis": "healthy"
  }
}
```

#### **SLA Monitoring**
```bash
# Check SLA compliance
curl -s https://api.agents.example.com/metrics/sla | jq '.'

# SLA Targets:
# - Uptime: ≥ 99.95%
# - Response Time: ≤ 500ms
# - Error Rate: ≤ 0.1%
```

### **2.2 Key Metrics to Monitor**

| **Metric** | **Threshold** | **Action Required** |
|------------|---------------|-------------------|
| **Response Time** | > 500ms | Investigate performance |
| **Error Rate** | > 0.1% | Check logs and errors |
| **CPU Usage** | > 80% | Scale up or investigate |
| **Memory Usage** | > 85% | Scale up or check leaks |
| **Disk Usage** | > 90% | Clean up or scale storage |
| **Active Agents** | < 2 | Restart agent services |

### **2.3 Alert Response Procedures**

#### **Critical Alerts**
1. **System Down**
   ```bash
   # Check pod status
   kubectl get pods -n agent-system
   
   # Check recent events
   kubectl get events -n agent-system --sort-by='.lastTimestamp'
   
   # Scale up if needed
   kubectl scale deployment agent-system --replicas=5 -n agent-system
   ```

2. **High Error Rate**
   ```bash
   # Check application logs
   kubectl logs -n agent-system -l app=agent-system --tail=100
   
   # Check error patterns
   kubectl logs -n agent-system -l app=agent-system | grep ERROR
   ```

3. **Database Issues**
   ```bash
   # Check database connectivity
   kubectl exec -it -n agent-system deployment/agent-system -- \
     python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}').close()"
   
   # Check RDS status in AWS Console
   ```

---

## 🔧 **3. Troubleshooting Guide**

### **3.1 Common Issues**

#### **Issue: Pods Failing to Start**
```bash
# Diagnose pod issues
kubectl describe pod <pod-name> -n agent-system
kubectl logs <pod-name> -n agent-system

# Common fixes:
# 1. Resource constraints
kubectl get limitrange -n agent-system
kubectl top pods -n agent-system

# 2. Image pull issues  
kubectl get events -n agent-system | grep "Failed to pull image"

# 3. Configuration issues
kubectl get configmap agent-system-config -n agent-system -o yaml
```

#### **Issue: High Response Times**
```bash
# Check resource usage
kubectl top pods -n agent-system
kubectl top nodes

# Check HPA status
kubectl get hpa -n agent-system

# Scale manually if needed
kubectl scale deployment agent-system --replicas=10 -n agent-system
```

#### **Issue: Agent Coordination Failures**
```bash
# Check agent status
curl -s https://api.agents.example.com/api/v2/agents/status

# Check coordination metrics
curl -s https://api.agents.example.com/api/v2/metrics | jq '.agents'

# Restart coordination service
kubectl rollout restart deployment agent-system -n agent-system
```

### **3.2 Database Troubleshooting**

#### **Connection Issues**
```bash
# Test database connectivity
kubectl run pg-test --rm -i --tty --image=postgres:15 -- \
  psql "${DATABASE_URL}" -c "SELECT version();"

# Check connection pool
kubectl logs -n agent-system -l app=agent-system | grep "database"
```

#### **Performance Issues**
```bash
# Check slow queries (connect to RDS)
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;

# Check connection count
SELECT count(*) FROM pg_stat_activity;
```

### **3.3 Redis Troubleshooting**

#### **Memory Issues**
```bash
# Check Redis memory usage
kubectl exec -it -n agent-system deployment/agent-system -- \
  redis-cli -h ${REDIS_ENDPOINT} INFO memory

# Check key distribution
kubectl exec -it -n agent-system deployment/agent-system -- \
  redis-cli -h ${REDIS_ENDPOINT} --scan --pattern "*" | head -20
```

#### **Connection Issues**
```bash
# Test Redis connectivity
kubectl exec -it -n agent-system deployment/agent-system -- \
  redis-cli -h ${REDIS_ENDPOINT} ping

# Check connection pool
kubectl logs -n agent-system -l app=agent-system | grep "redis"
```

---

## 🚨 **4. Emergency Procedures**

### **4.1 Emergency Response Matrix**

| **Severity** | **Response Time** | **Actions** |
|--------------|------------------|-------------|
| **P0 - Critical** | < 15 minutes | All hands, immediate response |
| **P1 - High** | < 1 hour | Primary on-call response |
| **P2 - Medium** | < 4 hours | Standard response |
| **P3 - Low** | < 24 hours | Queue for next business day |

### **4.2 Service Degradation Response**

#### **Phase 1: Immediate Stabilization (0-15 minutes)**
```bash
# Check system status
./scripts/rollback_procedures.sh health-check

# Scale up if resource constrained
kubectl scale deployment agent-system --replicas=10 -n agent-system

# Check for obvious issues
kubectl get events -n agent-system --sort-by='.lastTimestamp' | tail -20
```

#### **Phase 2: Investigate and Mitigate (15-60 minutes)**
```bash
# Detailed investigation
kubectl describe deployment agent-system -n agent-system
kubectl logs -n agent-system -l app=agent-system --since=1h

# Check external dependencies
curl -f https://api.openai.com/v1/models
```

#### **Phase 3: Long-term Fix (1+ hours)**
```bash
# Apply hotfix or rollback
./scripts/rollback_procedures.sh auto-rollback v2.1.5

# Monitor recovery
./scripts/monitor_recovery.py --duration 3600
```

### **4.3 Complete System Failure**

#### **Emergency Stop**
```bash
# Stop all services (last resort)
./scripts/rollback_procedures.sh emergency-stop
```

#### **Emergency Restart**
```bash
# Restart from known good state
kubectl delete deployment agent-system -n agent-system
kubectl apply -f k8s/production/deployment-verification.yaml

# Monitor restart
kubectl rollout status deployment/agent-system -n agent-system --timeout=600s
```

---

## 🔐 **5. Security Procedures**

### **5.1 Security Incident Response**

#### **Suspected Security Breach**
1. **Immediate Actions**
   ```bash
   # Isolate the system
   kubectl scale deployment agent-system --replicas=0 -n agent-system
   
   # Preserve evidence
   kubectl get pods -n agent-system -o yaml > incident-evidence.yaml
   kubectl logs -n agent-system -l app=agent-system > incident-logs.txt
   ```

2. **Investigation**
   ```bash
   # Check for suspicious activity
   kubectl get events -n agent-system | grep -E "(Failed|Error|Warning)"
   
   # Review access logs
   kubectl logs -n agent-system -l app=agent-system | grep -E "(401|403|admin)"
   ```

3. **Recovery**
   ```bash
   # Deploy fresh environment
   ./scripts/emergency_deploy.sh --clean-slate
   
   # Rotate all secrets
   kubectl delete secret --all -n agent-system
   ./scripts/regenerate_secrets.sh
   ```

### **5.2 Secret Rotation**

#### **Scheduled Secret Rotation**
```bash
# Rotate database credentials
aws secretsmanager rotate-secret --secret-id agent-system/db-credentials

# Rotate API keys
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret="$(openssl rand -base64 32)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Rolling restart to pick up new secrets
kubectl rollout restart deployment agent-system -n agent-system
```

---

## 📈 **6. Capacity Management**

### **6.1 Scaling Procedures**

#### **Manual Scaling**
```bash
# Scale deployment
kubectl scale deployment agent-system --replicas=15 -n agent-system

# Scale database (requires downtime)
aws rds modify-db-instance --db-instance-identifier agent-system-db \
  --db-instance-class db.r5.2xlarge --apply-immediately

# Scale Redis cluster
aws elasticache modify-replication-group --replication-group-id agent-system-redis \
  --node-group-count 3 --apply-immediately
```

#### **Auto-scaling Configuration**
```bash
# Update HPA limits
kubectl patch hpa agent-system-hpa -n agent-system \
  -p '{"spec":{"maxReplicas":50}}'

# Check auto-scaling events
kubectl describe hpa agent-system-hpa -n agent-system
```

### **6.2 Performance Optimization**

#### **Database Optimization**
```sql
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
ORDER BY n_distinct DESC;

-- Analyze table statistics
ANALYZE;
```

#### **Application Optimization**
```bash
# Check memory usage patterns
kubectl top pods -n agent-system --sort-by=memory

# Profile application (if profiling enabled)
curl -s https://api.agents.example.com/debug/pprof/profile > profile.out
```

---

## 📋 **7. Maintenance Procedures**

### **7.1 Scheduled Maintenance**

#### **Pre-Maintenance Checklist**
- [ ] Maintenance window communicated
- [ ] Backup completed
- [ ] Rollback procedure tested
- [ ] Team on standby

#### **Maintenance Execution**
```bash
# Start maintenance mode
kubectl apply -f k8s/maintenance/maintenance-page.yaml

# Perform updates
./scripts/maintenance_update.sh

# Exit maintenance mode
kubectl delete -f k8s/maintenance/maintenance-page.yaml
```

### **7.2 Backup and Recovery**

#### **Database Backup**
```bash
# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier agent-system-db \
  --db-snapshot-identifier agent-system-backup-$(date +%Y%m%d)

# Verify backup
aws rds describe-db-snapshots \
  --db-snapshot-identifier agent-system-backup-$(date +%Y%m%d)
```

#### **Configuration Backup**
```bash
# Backup all Kubernetes resources
kubectl get all,secrets,configmaps,ingress,pv,pvc -n agent-system -o yaml > \
  backup/k8s-backup-$(date +%Y%m%d).yaml

# Backup Terraform state
terraform state pull > backup/terraform-state-$(date +%Y%m%d).json
```

---

## 📞 **8. Communication Procedures**

### **8.1 Incident Communication**

#### **Internal Communication**
```bash
# Slack notification
curl -X POST ${SLACK_WEBHOOK} -H 'Content-type: application/json' \
  --data '{"text":"🚨 Agent System Incident: <details>"}'

# Email notification
echo "Incident details..." | mail -s "Agent System Alert" team@agents.example.com
```

#### **External Communication**
```bash
# Update status page
curl -X POST https://api.statuspage.io/v1/pages/${PAGE_ID}/incidents \
  -H "Authorization: OAuth ${STATUS_PAGE_TOKEN}" \
  -d '{"incident":{"name":"Service Degradation","status":"investigating"}}'
```

### **8.2 Post-Incident Review**

#### **Required Documentation**
- [ ] Timeline of events
- [ ] Root cause analysis
- [ ] Impact assessment
- [ ] Action items for prevention

#### **Review Template**
```markdown
# Post-Incident Review - Agent System

**Date**: 2023-11-20
**Duration**: 45 minutes
**Impact**: 0.05% error rate increase

## Timeline
- 01:15 UTC: Issue detected
- 01:20 UTC: Investigation started
- 01:45 UTC: Resolution applied
- 02:00 UTC: System fully recovered

## Root Cause
[Detailed analysis]

## Action Items
1. [ ] Improve monitoring for X
2. [ ] Update runbook for Y
3. [ ] Implement additional safeguards
```

---

## ✅ **Go/No-Go Decision Criteria**

### **Go Decision Requirements (All Must Pass)**
- [ ] All tests passing (component, integration, security)
- [ ] Health checks returning 200 OK
- [ ] SLA metrics within targets
- [ ] Security scans passed
- [ ] Rollback procedure verified
- [ ] Team ready and on-call
- [ ] Maintenance window confirmed

### **No-Go Criteria (Any One Fails)**
- [ ] Critical test failures
- [ ] Security vulnerabilities found
- [ ] Infrastructure issues
- [ ] Team unavailable
- [ ] External dependencies down

---

**Document Version**: 2.0.0  
**Last Updated**: 2023-11-19  
**Next Review**: 2023-12-19  
**Owner**: DevOps Team  
**Approved By**: Engineering Lead, Security Team