#!/bin/bash

# Bold Frontend Design - Dependency Check Script
#
# Verifies that required animation libraries are installed
# Returns installation commands if dependencies are missing

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Bold Frontend Design - Dependency Check${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Check if package.json exists
if [ ! -f "package.json" ]; then
  echo -e "${RED}Error: package.json not found${NC}"
  echo -e "${YELLOW}Please run this script from your Next.js/React project root${NC}"
  exit 1
fi

# Required dependencies
REQUIRED_DEPS=(
  "@react-three/fiber"
  "@react-three/drei"
  "@react-three/postprocessing"
  "framer-motion"
  "three"
)

MISSING_DEPS=()
INSTALLED_DEPS=()

# Check each dependency
for dep in "${REQUIRED_DEPS[@]}"; do
  if grep -q "\"$dep\"" package.json; then
    INSTALLED_DEPS+=("$dep")
    echo -e "${GREEN}✓${NC} $dep"
  else
    MISSING_DEPS+=("$dep")
    echo -e "${RED}✗${NC} $dep ${YELLOW}(missing)${NC}"
  fi
done

echo ""

# Report results
if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
  echo -e "${GREEN}======================================${NC}"
  echo -e "${GREEN}All dependencies installed!${NC}"
  echo -e "${GREEN}======================================${NC}\n"
  exit 0
else
  echo -e "${YELLOW}======================================${NC}"
  echo -e "${YELLOW}Missing dependencies: ${#MISSING_DEPS[@]}${NC}"
  echo -e "${YELLOW}======================================${NC}\n"

  echo -e "${BLUE}Install missing dependencies with:${NC}\n"
  echo -e "npm install ${MISSING_DEPS[@]}"
  echo ""
  echo -e "${YELLOW}Or individually:${NC}"
  for dep in "${MISSING_DEPS[@]}"; do
    echo -e "  npm install $dep"
  done
  echo ""

  exit 1
fi
