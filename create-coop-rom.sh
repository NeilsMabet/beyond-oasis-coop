#!/usr/bin/env bash
# Linux BPS patcher launcher. Python 3 is the only required dependency.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if (( $# > 2 )); then
    printf 'Usage: bash %s [original-ROM [output-ROM]]\n' "$0" >&2
    exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
    printf 'Python 3 is required. Install python3 using your distribution package manager.\n' >&2
    exit 1
fi
rom="${1:-}"
output="${2:-$script_dir/generated/Beyond Oasis Coop.bin}"
if [[ -z "$rom" ]]; then
    if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v zenity >/dev/null 2>&1; then
        rom="$(zenity --file-selection --title='Select original Beyond Oasis (U) ROM')" || exit 0
    elif [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v kdialog >/dev/null 2>&1; then
        rom="$(kdialog --getopenfilename "$HOME" 'Mega Drive ROM (*.bin *.gen *.md)' --title 'Select original Beyond Oasis (U) ROM')" || exit 0
    else
        printf 'Path to original Beyond Oasis (U) ROM (without quotes): '
        if ! IFS= read -r rom; then
            printf '\nNo ROM selected. Run this script in a terminal or pass a ROM path.\n' >&2
            exit 1
        fi
    fi
fi
if [[ -z "$rom" ]]; then
    printf 'No ROM selected.\n'
    exit 0
fi
exec python3 "$script_dir/src/apply_patch.py" --rom="$rom" --output="$output"
