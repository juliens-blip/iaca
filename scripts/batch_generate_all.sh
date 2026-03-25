#!/bin/bash

##############################################################################
# Batch Generation Orchestrator
#
# Objective: Launch generation batches for all priority subjects sequentially
# Features:
#   - Processes subjects in priority order from generation-plan.md
#   - Logs each batch result (OK/ERROR counts)
#   - Handles rate-limit errors with 30min retry
#   - Displays final summary
#
# Usage:
#   bash scripts/batch_generate_all.sh          # Default: limit 10
#   bash scripts/batch_generate_all.sh 15       # Custom limit: 15 docs per batch
#   bash scripts/batch_generate_all.sh 15 2     # Custom limit + custom retry wait (min)
#
# Environment:
#   - Run AFTER 8:05 AM (Claude quota reset)
#   - Ensure backend is running on :8000
#   - Logs saved to: tasks/pdf-pipeline-refonte/batch-*.log
#
##############################################################################

set -o pipefail

# Configuration
LIMIT_PER_BATCH="${1:-10}"           # Default 10 docs per batch
RETRY_WAIT_MIN="${2:-30}"            # Default 30 min wait on rate-limit
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/tasks/pdf-pipeline-refonte"
MASTER_LOG="${LOG_DIR}/batch-all-run.log"
SUMMARY_LOG="${LOG_DIR}/batch-all-summary.txt"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
BATCH_NUM=0
TOTAL_DOCS_OK=0
TOTAL_DOCS_ERROR=0
FAILED_BATCHES=()

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Priority subjects in order (from generation-plan.md)
declare -a PRIORITY_SUBJECTS=(
    "Licence 2 - Semestre 3"
    "Droit public"
    "Licence 2 - Semestre 4"
    "Licence 3 - Semestre 5"
    "Licence 3 - Semestre 6"
    "Questions contemporaines"
    "Questions sociales"
    "M1 Politique economique"
    "M1 Management et egalites"
    "Economie"
    "Espagnol"
    "Documents divers"
    "Livres et manuels"
)

##############################################################################
# Utility Functions
##############################################################################

log() {
    local level="$1"
    shift
    local msg="$@"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    local log_line="[$timestamp] [$level] $msg"

    echo "$log_line" | tee -a "$MASTER_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@" | tee -a "$MASTER_LOG"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $@" | tee -a "$MASTER_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $@" | tee -a "$MASTER_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" | tee -a "$MASTER_LOG"
}

##############################################################################
# Parse batch log and extract counts
##############################################################################

parse_batch_result() {
    local batch_log="$1"
    local ok_count=0
    local error_count=0

    if [ ! -f "$batch_log" ]; then
        echo "0 0"
        return
    fi

    # Count "OK — fiche_id=" lines
    ok_count=$(grep -c "OK — fiche_id=" "$batch_log" || echo 0)

    # Count "ERROR [fiche]" lines
    error_count=$(grep -c "ERROR.*\[fiche\]" "$batch_log" || echo 0)

    echo "$ok_count $error_count"
}

##############################################################################
# Run a single batch
##############################################################################

run_batch() {
    local matiere="$1"
    local batch_num="$2"
    local attempt="$3"

    BATCH_NUM=$((BATCH_NUM + 1))

    # Generate safe log filename
    local safe_name=$(echo "$matiere" | tr '[:upper:] -/' '[:lower:]___' | tr -d '[:space:]')
    local batch_log="${LOG_DIR}/batch-${safe_name}-${batch_num}.log"

    log_info "═══════════════════════════════════════════════════════════"
    log_info "Batch #$BATCH_NUM | Matière: $matiere | Limit: $LIMIT_PER_BATCH docs"
    if [ "$attempt" -gt 1 ]; then
        log_warn "RETRY ATTEMPT #$attempt"
    fi
    log_info "Log: $batch_log"
    log_info "═══════════════════════════════════════════════════════════"

    # Run the generation script
    local start_time=$(date +%s)

    python3 "$SCRIPT_DIR/reextract_and_generate.py" \
        --matiere "$matiere" \
        --limit "$LIMIT_PER_BATCH" \
        --skip-extract \
        --skip-flashcards \
        2>&1 | tee "$batch_log"

    local exit_code=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Parse results
    read ok_count error_count < <(parse_batch_result "$batch_log")

    log_info "Batch completed in ${duration}s"
    log_info "Results: OK=$ok_count, ERROR=$error_count"

    # Check for rate-limit errors
    local rate_limit_count=$(grep -c "You've hit your limit" "$batch_log" || echo 0)

    if [ "$rate_limit_count" -gt 0 ]; then
        log_warn "Rate-limit errors detected ($rate_limit_count occurrences)"
        return 429  # Signal rate-limit error
    fi

    # Update totals
    TOTAL_DOCS_OK=$((TOTAL_DOCS_OK + ok_count))
    TOTAL_DOCS_ERROR=$((TOTAL_DOCS_ERROR + error_count))

    if [ "$exit_code" -ne 0 ] || [ "$error_count" -gt 0 ]; then
        log_error "Batch FAILED (exit=$exit_code, errors=$error_count)"
        FAILED_BATCHES+=("$matiere")
        return 1
    else
        log_success "Batch PASSED ($ok_count docs generated)"
        return 0
    fi
}

##############################################################################
# Main Loop
##############################################################################

main() {
    log_info "╔════════════════════════════════════════════════════════════╗"
    log_info "║       BATCH GENERATION ORCHESTRATOR                        ║"
    log_info "╚════════════════════════════════════════════════════════════╝"
    log_info ""
    log_info "Configuration:"
    log_info "  Limit per batch: $LIMIT_PER_BATCH docs"
    log_info "  Retry wait: $RETRY_WAIT_MIN min on rate-limit"
    log_info "  Log directory: $LOG_DIR"
    log_info "  Master log: $MASTER_LOG"
    log_info ""
    log_info "Processing ${#PRIORITY_SUBJECTS[@]} subjects..."
    log_info ""

    local consecutive_errors=0

    for matiere in "${PRIORITY_SUBJECTS[@]}"; do
        local attempt=1
        local retry=true

        while [ "$retry" = true ]; do
            run_batch "$matiere" "$BATCH_NUM" "$attempt"
            local result=$?

            if [ "$result" -eq 429 ]; then
                # Rate-limit error
                consecutive_errors=$((consecutive_errors + 1))

                if [ "$consecutive_errors" -ge 3 ]; then
                    log_error "❌ 3 consecutive rate-limit errors detected!"
                    log_warn "Waiting $RETRY_WAIT_MIN minutes before retry..."

                    # Sleep with countdown
                    local sleep_secs=$((RETRY_WAIT_MIN * 60))
                    for ((i = sleep_secs; i > 0; i--)); do
                        printf "\r⏳ Time remaining: %02d:%02d" $((i/60)) $((i%60))
                        sleep 1
                    done
                    echo ""

                    log_info "⏰ Resuming after timeout..."
                    consecutive_errors=0
                    attempt=$((attempt + 1))
                    # Continue retry loop
                else
                    log_warn "Rate-limit ($consecutive_errors/3), continuing with next batch..."
                    retry=false
                fi
            elif [ "$result" -eq 0 ]; then
                # Success
                consecutive_errors=0
                retry=false
            else
                # Other error
                consecutive_errors=$((consecutive_errors + 1))
                if [ "$consecutive_errors" -lt 3 ]; then
                    log_warn "Batch error ($consecutive_errors/3 consecutive), continuing..."
                    retry=false
                else
                    log_error "3 consecutive errors, waiting and retrying..."
                    sleep $((RETRY_WAIT_MIN * 60))
                    attempt=$((attempt + 1))
                    consecutive_errors=0
                fi
            fi
        done

        log_info ""
    done

    # Final summary
    print_summary
}

##############################################################################
# Print Summary
##############################################################################

print_summary() {
    log_info "╔════════════════════════════════════════════════════════════╗"
    log_info "║                     EXECUTION SUMMARY                      ║"
    log_info "╚════════════════════════════════════════════════════════════╝"
    log_info ""

    local total_attempted=$BATCH_NUM
    local success_rate=0

    if [ "$total_attempted" -gt 0 ]; then
        success_rate=$(( (TOTAL_DOCS_OK * 100) / (TOTAL_DOCS_OK + TOTAL_DOCS_ERROR + 1) ))
    fi

    log_info "Total Batches: $total_attempted"
    log_info "Documents Generated: $TOTAL_DOCS_OK"
    log_info "Documents Failed: $TOTAL_DOCS_ERROR"
    log_info "Success Rate: ${success_rate}%"
    log_info ""

    if [ "${#FAILED_BATCHES[@]}" -gt 0 ]; then
        log_error "Failed Batches (${#FAILED_BATCHES[@]}):"
        for failed in "${FAILED_BATCHES[@]}"; do
            log_error "  - $failed"
        done
        log_info ""
    fi

    log_info "Detailed Results:"
    log_info "  ✓ OK:    $TOTAL_DOCS_OK"
    log_info "  ✗ ERROR: $TOTAL_DOCS_ERROR"
    log_info ""

    log_info "Next steps:"
    log_info "  1. Review log files in: $LOG_DIR"
    log_info "  2. Check for patterns in failures"
    log_info "  3. If rate-limited, wait for quota reset at 8am next day"
    log_info "  4. Rerun failed batches with: bash scripts/batch_generate_all.sh $LIMIT_PER_BATCH"
    log_info ""

    # Save summary to file
    {
        echo "═══════════════════════════════════════════════════════════"
        echo "Batch Generation Summary — $(date)"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "Total Batches: $total_attempted"
        echo "Documents OK: $TOTAL_DOCS_OK"
        echo "Documents ERROR: $TOTAL_DOCS_ERROR"
        echo "Success Rate: ${success_rate}%"
        echo ""
        echo "Log directory: $LOG_DIR"
        echo "Master log: $MASTER_LOG"
    } | tee "$SUMMARY_LOG"

    log_success "Summary saved to: $SUMMARY_LOG"
}

##############################################################################
# Startup Checks
##############################################################################

startup_checks() {
    log_info "Running startup checks..."

    # Check if backend is running
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_warn "⚠️  Backend not responding on :8000"
        log_warn "   Make sure to start: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
        log_warn "   Continuing anyway (script will fail if API needed)..."
    else
        log_success "Backend is running ✓"
    fi

    # Check if reextract_and_generate.py exists
    if [ ! -f "$SCRIPT_DIR/reextract_and_generate.py" ]; then
        log_error "Script not found: $SCRIPT_DIR/reextract_and_generate.py"
        return 1
    fi
    log_success "Generation script found ✓"

    # Check if log directory is writable
    if [ ! -w "$LOG_DIR" ]; then
        log_error "Log directory not writable: $LOG_DIR"
        return 1
    fi
    log_success "Log directory is writable ✓"

    log_info "Startup checks passed ✓"
    log_info ""
}

##############################################################################
# Entry Point
##############################################################################

# Initialize master log
{
    echo "═══════════════════════════════════════════════════════════"
    echo "Batch Generation Orchestrator"
    echo "Started: $(date)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
} > "$MASTER_LOG"

# Run startup checks
startup_checks || exit 1

# Run main loop
main

# Final status
echo ""
if [ "$TOTAL_DOCS_OK" -ge 10 ]; then
    log_success "✓ Generation completed successfully!"
    exit 0
else
    log_error "✗ Generation completed with issues (only $TOTAL_DOCS_OK docs OK)"
    exit 1
fi
