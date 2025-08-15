#!/bin/bash
set -e

# Multi-Agent Code Generation System Deployment Script
# This script sets up the production environment and deploys the application

echo "🚀 Multi-Agent Code Generation System Deployment"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker found"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose found"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your actual configuration values"
        print_warning "Especially set OPENAI_API_KEY and JWT_SECRET_KEY"
    else
        print_success ".env file already exists"
    fi
    
    # Create necessary directories
    mkdir -p logs uploads temp ssl
    print_success "Created necessary directories"
    
    # Set proper permissions
    chmod 755 logs uploads temp
    print_success "Set directory permissions"
}

# Generate SSL certificates (self-signed for development)
generate_ssl() {
    print_status "Checking SSL certificates..."
    
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        print_status "Generating self-signed SSL certificates..."
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        print_success "SSL certificates generated"
    else
        print_success "SSL certificates already exist"
    fi
}

# Pull latest images
pull_images() {
    print_status "Pulling latest Docker images..."
    docker-compose pull
    print_success "Docker images pulled"
}

# Build application
build_application() {
    print_status "Building application..."
    docker-compose build --no-cache
    print_success "Application built"
}

# Database initialization
init_database() {
    print_status "Initializing database..."
    
    # Start only PostgreSQL first
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    until docker-compose exec postgres pg_isready -U postgres; do
        sleep 2
    done
    print_success "PostgreSQL is ready"
    
    # Run database migrations (if you have them)
    # docker-compose exec app alembic upgrade head
}

# Start services
start_services() {
    print_status "Starting all services..."
    docker-compose up -d
    print_success "All services started"
}

# Health check
health_check() {
    print_status "Performing health checks..."
    
    # Wait a bit for services to start
    sleep 10
    
    # Check application health
    if curl -f http://localhost/health &> /dev/null; then
        print_success "Application is healthy"
    else
        print_warning "Application health check failed, checking direct access..."
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "Application is healthy (direct access)"
        else
            print_error "Application health check failed"
            return 1
        fi
    fi
    
    # Check database
    if docker-compose exec postgres pg_isready -U postgres &> /dev/null; then
        print_success "Database is healthy"
    else
        print_error "Database health check failed"
        return 1
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping &> /dev/null; then
        print_success "Redis is healthy"
    else
        print_error "Redis health check failed"
        return 1
    fi
}

# Show status
show_status() {
    print_status "Deployment Status:"
    echo ""
    docker-compose ps
    echo ""
    print_status "Service URLs:"
    echo "🌐 Application: http://localhost (or https://localhost)"
    echo "🌐 Application Direct: http://localhost:8000"
    echo "📊 Grafana: http://localhost:3000 (admin/admin123)"
    echo "📈 Prometheus: http://localhost:9090"
    echo "🗄️  PostgreSQL: localhost:5432"
    echo "🔄 Redis: localhost:6379"
    echo ""
    print_status "Logs:"
    echo "📋 View logs: docker-compose logs -f"
    echo "📋 App logs: docker-compose logs -f app"
    echo ""
}

# Backup function
backup_data() {
    print_status "Creating backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    docker-compose exec postgres pg_dump -U postgres multiagent > "$BACKUP_DIR/database.sql"
    
    # Backup volumes
    docker run --rm -v $(pwd):/backup -v multiagent_postgres_data:/data alpine \
        tar czf /backup/$BACKUP_DIR/postgres_data.tar.gz -C /data .
    
    docker run --rm -v $(pwd):/backup -v multiagent_redis_data:/data alpine \
        tar czf /backup/$BACKUP_DIR/redis_data.tar.gz -C /data .
    
    print_success "Backup created in $BACKUP_DIR"
}

# Main deployment function
deploy() {
    print_status "Starting deployment process..."
    
    check_prerequisites
    setup_environment
    generate_ssl
    pull_images
    build_application
    init_database
    start_services
    
    if health_check; then
        print_success "🎉 Deployment completed successfully!"
        show_status
    else
        print_error "❌ Deployment failed health checks"
        print_status "Checking service logs..."
        docker-compose logs --tail=50
        exit 1
    fi
}

# Command line options
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "update")
        print_status "Updating application..."
        docker-compose pull
        docker-compose build --no-cache
        docker-compose up -d
        health_check && print_success "Update completed" || print_error "Update failed"
        ;;
    "backup")
        backup_data
        ;;
    "restore")
        if [ -z "$2" ]; then
            print_error "Please specify backup directory: ./deploy.sh restore backups/20240101_120000"
            exit 1
        fi
        print_status "Restoring from $2..."
        # Add restore logic here
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose down
        print_success "Services stopped"
        ;;
    "logs")
        docker-compose logs -f "${2:-}"
        ;;
    "status")
        show_status
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and images"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi all
            docker system prune -af
            print_success "Cleanup completed"
        fi
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment (default)"
        echo "  update    - Update application"
        echo "  backup    - Create backup"
        echo "  restore   - Restore from backup"
        echo "  stop      - Stop all services"
        echo "  logs      - View logs"
        echo "  status    - Show service status"
        echo "  clean     - Remove everything"
        echo "  help      - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac