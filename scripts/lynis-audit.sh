#!/usr/bin/env bash
#
# Lynis Audit Script for OMEN
# Runs security audits before and after hardening to measure improvements
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
AUDIT_DIR="/var/log/omen/audits"
LYNIS_DIR="/opt/lynis"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to install Lynis
install_lynis() {
    print_info "Checking for Lynis installation..."
    
    if command -v lynis &> /dev/null; then
        print_success "Lynis is already installed"
        lynis --version
        return 0
    fi
    
    print_warning "Lynis not found. Installing..."
    
    # Try package manager first
    if command -v apt-get &> /dev/null; then
        print_info "Installing via apt..."
        apt-get update -qq
        apt-get install -y lynis
    elif command -v yum &> /dev/null; then
        print_info "Installing via yum..."
        yum install -y lynis
    elif command -v dnf &> /dev/null; then
        print_info "Installing via dnf..."
        dnf install -y lynis
    else
        # Install from GitHub
        print_info "Installing from GitHub..."
        
        # Install git if needed
        if ! command -v git &> /dev/null; then
            print_error "git is required but not installed. Please install git first."
            exit 1
        fi
        
        # Clone Lynis
        if [[ -d "$LYNIS_DIR" ]]; then
            print_info "Updating existing Lynis installation..."
            cd "$LYNIS_DIR"
            git pull
        else
            print_info "Cloning Lynis repository..."
            git clone https://github.com/CISOfy/lynis.git "$LYNIS_DIR"
        fi
        
        # Create symlink
        ln -sf "$LYNIS_DIR/lynis" /usr/local/bin/lynis
    fi
    
    if command -v lynis &> /dev/null; then
        print_success "Lynis installed successfully"
        lynis --version
    else
        print_error "Failed to install Lynis"
        exit 1
    fi
}

# Function to run Lynis audit
run_audit() {
    local stage="$1"  # "before" or "after"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local report_file="${AUDIT_DIR}/lynis_${stage}_${timestamp}.log"
    local data_file="${AUDIT_DIR}/lynis_${stage}_${timestamp}.dat"
    
    print_info "Running Lynis audit (${stage} hardening)..."
    print_info "This may take several minutes..."
    
    # Create audit directory
    mkdir -p "$AUDIT_DIR"
    
    # Run Lynis audit
    lynis audit system \
        --no-colors \
        --quick \
        --report-file "$report_file" \
        2>&1 | tee "${AUDIT_DIR}/lynis_${stage}_${timestamp}_output.txt"
    
    # Copy the data file
    if [[ -f /var/log/lynis.log ]]; then
        cp /var/log/lynis.log "$data_file"
    fi
    
    # Extract key metrics
    extract_metrics "$report_file" "$stage" "$timestamp"
    
    print_success "Audit completed: $report_file"
    
    # Create a symlink to latest
    ln -sf "$(basename "$report_file")" "${AUDIT_DIR}/lynis_${stage}_latest.log"
    
    echo "$report_file"
}

# Function to extract key metrics from audit
extract_metrics() {
    local report_file="$1"
    local stage="$2"
    local timestamp="$3"
    local metrics_file="${AUDIT_DIR}/lynis_${stage}_${timestamp}_metrics.txt"
    
    print_info "Extracting metrics..."
    
    # Check if report file exists
    if [[ ! -f "$report_file" ]]; then
        # Try alternate location
        if [[ -f /var/log/lynis-report.dat ]]; then
            report_file="/var/log/lynis-report.dat"
        else
            print_warning "Report file not found, checking system log..."
            report_file="/var/log/lynis.log"
        fi
    fi
    
    if [[ ! -f "$report_file" ]]; then
        print_warning "Could not find Lynis report file"
        return 1
    fi
    
    cat > "$metrics_file" << EOF
================================================================================
LYNIS AUDIT METRICS - ${stage^^} HARDENING
================================================================================
Timestamp: $timestamp
Date: $(date)

EOF
    
    # Extract hardening index
    if grep -q "hardening_index=" "$report_file"; then
        local hardening_index=$(grep "hardening_index=" "$report_file" | cut -d= -f2)
        echo "Hardening Index: $hardening_index" >> "$metrics_file"
    fi
    
    # Extract test results
    echo "" >> "$metrics_file"
    echo "Test Results:" >> "$metrics_file"
    echo "-------------" >> "$metrics_file"
    
    local tests_performed=$(grep -c "Performing test ID" "$report_file" 2>/dev/null || echo "N/A")
    local warnings=$(grep -c "\[ WARNING \]" "$report_file" 2>/dev/null || echo "0")
    local suggestions=$(grep -c "Suggestion" "$report_file" 2>/dev/null || echo "0")
    
    echo "  Tests Performed: $tests_performed" >> "$metrics_file"
    echo "  Warnings: $warnings" >> "$metrics_file"
    echo "  Suggestions: $suggestions" >> "$metrics_file"
    
    # Extract category summaries if available
    if grep -q "Hardening index" "$report_file"; then
        echo "" >> "$metrics_file"
        echo "Category Scores:" >> "$metrics_file"
        echo "----------------" >> "$metrics_file"
        grep -A 20 "Hardening index" "$report_file" | grep -E "^\s*-" >> "$metrics_file" 2>/dev/null || true
    fi
    
    # Extract key findings
    echo "" >> "$metrics_file"
    echo "Key Findings:" >> "$metrics_file"
    echo "-------------" >> "$metrics_file"
    grep -E "\[ WARNING \]|\[ SUGGESTION \]" "$report_file" | head -20 >> "$metrics_file" 2>/dev/null || echo "  No major issues found" >> "$metrics_file"
    
    echo "" >> "$metrics_file"
    echo "Full report: $report_file" >> "$metrics_file"
    echo "================================================================================" >> "$metrics_file"
    
    print_success "Metrics saved: $metrics_file"
    
    # Display summary
    cat "$metrics_file"
}

# Function to compare before and after audits
compare_audits() {
    print_info "Comparing audit results..."
    
    local before_latest="${AUDIT_DIR}/lynis_before_latest.log"
    local after_latest="${AUDIT_DIR}/lynis_after_latest.log"
    
    if [[ ! -f "$before_latest" ]]; then
        print_error "Before audit not found. Run with 'before' first."
        exit 1
    fi
    
    if [[ ! -f "$after_latest" ]]; then
        print_error "After audit not found. Run with 'after' first."
        exit 1
    fi
    
    # Resolve symlinks
    before_latest=$(readlink -f "$before_latest")
    after_latest=$(readlink -f "$after_latest")
    
    local comparison_file="${AUDIT_DIR}/lynis_comparison_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$comparison_file" << EOF
================================================================================
LYNIS AUDIT COMPARISON - BEFORE vs AFTER HARDENING
================================================================================
Generated: $(date)
Before: $(basename "$before_latest")
After:  $(basename "$after_latest")

EOF
    
    # Compare hardening indices
    echo "HARDENING INDEX COMPARISON:" >> "$comparison_file"
    echo "===========================" >> "$comparison_file"
    
    local before_index=$(grep "hardening_index=" "$before_latest" | cut -d= -f2 | head -1 || echo "N/A")
    local after_index=$(grep "hardening_index=" "$after_latest" | cut -d= -f2 | head -1 || echo "N/A")
    
    echo "Before: $before_index" >> "$comparison_file"
    echo "After:  $after_index" >> "$comparison_file"
    
    if [[ "$before_index" != "N/A" ]] && [[ "$after_index" != "N/A" ]]; then
        local improvement=$((after_index - before_index))
        echo "Improvement: +$improvement points" >> "$comparison_file"
    fi
    
    echo "" >> "$comparison_file"
    
    # Compare warnings
    echo "WARNINGS COMPARISON:" >> "$comparison_file"
    echo "====================" >> "$comparison_file"
    
    local before_warnings=$(grep -c "\[ WARNING \]" "$before_latest" 2>/dev/null || echo "0")
    local after_warnings=$(grep -c "\[ WARNING \]" "$after_latest" 2>/dev/null || echo "0")
    local warnings_fixed=$((before_warnings - after_warnings))
    
    echo "Before: $before_warnings warnings" >> "$comparison_file"
    echo "After:  $after_warnings warnings" >> "$comparison_file"
    echo "Fixed:  $warnings_fixed warnings" >> "$comparison_file"
    
    echo "" >> "$comparison_file"
    
    # Compare suggestions
    echo "SUGGESTIONS COMPARISON:" >> "$comparison_file"
    echo "=======================" >> "$comparison_file"
    
    local before_suggestions=$(grep -c "Suggestion" "$before_latest" 2>/dev/null || echo "0")
    local after_suggestions=$(grep -c "Suggestion" "$after_latest" 2>/dev/null || echo "0")
    local suggestions_addressed=$((before_suggestions - after_suggestions))
    
    echo "Before: $before_suggestions suggestions" >> "$comparison_file"
    echo "After:  $after_suggestions suggestions" >> "$comparison_file"
    echo "Addressed: $suggestions_addressed suggestions" >> "$comparison_file"
    
    echo "" >> "$comparison_file"
    echo "================================================================================" >> "$comparison_file"
    
    print_success "Comparison saved: $comparison_file"
    
    # Display comparison
    cat "$comparison_file"
    
    # Generate summary with colors
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    HARDENING SUMMARY                           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Hardening Index:  ${YELLOW}$before_index${NC} → ${GREEN}$after_index${NC}"
    
    if [[ $warnings_fixed -gt 0 ]]; then
        echo -e "  Warnings Fixed:   ${GREEN}$warnings_fixed${NC}"
    else
        echo -e "  Warnings Fixed:   ${YELLOW}$warnings_fixed${NC}"
    fi
    
    if [[ $suggestions_addressed -gt 0 ]]; then
        echo -e "  Suggestions Done: ${GREEN}$suggestions_addressed${NC}"
    else
        echo -e "  Suggestions Done: ${YELLOW}$suggestions_addressed${NC}"
    fi
    
    echo ""
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    before      Run audit before hardening
    after       Run audit after hardening
    compare     Compare before and after audits
    install     Install/update Lynis
    help        Show this help message

Examples:
    # Run before hardening
    sudo $0 before

    # Run after hardening
    sudo $0 after

    # Compare results
    sudo $0 compare

Audit reports are saved to: $AUDIT_DIR
EOF
}

# Main script logic
main() {
    check_root
    
    local command="${1:-help}"
    
    case "$command" in
        before)
            install_lynis
            run_audit "before"
            print_info "Now run your hardening scripts, then run: sudo $0 after"
            ;;
        after)
            install_lynis
            run_audit "after"
            print_info "To see comparison, run: sudo $0 compare"
            ;;
        compare)
            compare_audits
            ;;
        install)
            install_lynis
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

