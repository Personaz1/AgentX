#!/bin/bash

# NeuroRAT Repository Initializer
# Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
# License: MIT

# Color settings
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██████╗  █████╗ ████████╗"
echo "████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝"
echo "██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██████╔╝███████║   ██║   "
echo "██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██╗██╔══██║   ██║   "
echo "██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║  ██║   ██║   "
echo "╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
echo -e "${NC}"
echo -e "${YELLOW}Repository Initializer${NC}"
echo -e "${YELLOW}Author: Mr. Thomas Anderson${NC}"
echo -e "${YELLOW}License: MIT${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed. Please install Git first.${NC}"
    exit 1
fi

# Function for error handling
handle_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Initialize git repository if it doesn't exist
echo -e "${BLUE}Initializing git repository...${NC}"
if [ ! -d ".git" ]; then
    git init || handle_error "Failed to initialize git repository."
    echo -e "${GREEN}Git repository initialized.${NC}"
else
    echo -e "${YELLOW}Git repository already exists.${NC}"
fi

# Add agent_protocol as submodule
echo -e "${BLUE}Adding agent_protocol as a submodule...${NC}"
if [ ! -d "agent_protocol/.git" ]; then
    git submodule add https://github.com/AI-Engineer-Foundation/agent-protocol.git agent_protocol || handle_error "Failed to add agent_protocol submodule."
    echo -e "${GREEN}agent_protocol submodule added.${NC}"
else
    echo -e "${YELLOW}agent_protocol submodule already exists.${NC}"
fi

# Initialize and update submodules
echo -e "${BLUE}Initializing and updating submodules...${NC}"
git submodule init || handle_error "Failed to initialize submodules."
git submodule update || handle_error "Failed to update submodules."
echo -e "${GREEN}Submodules initialized and updated.${NC}"

# Add initial files to git
echo -e "${BLUE}Adding files to git...${NC}"
git add . || handle_error "Failed to add files to git."
echo -e "${GREEN}Files added to git.${NC}"

# Initial commit
echo -e "${BLUE}Making initial commit...${NC}"
git commit -m "Initial commit of NeuroRAT project" || handle_error "Failed to make initial commit."
echo -e "${GREEN}Initial commit made.${NC}"

# Instructions for GitHub
echo ""
echo -e "${YELLOW}Repository initialized successfully!${NC}"
echo ""
echo -e "${BLUE}To push this repository to GitHub:${NC}"
echo "  1. Create a new repository on GitHub (https://github.com/new)"
echo "  2. Run the following commands:"
echo ""
echo "     git remote add origin https://github.com/Personaz1/neurorat.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo -e "${YELLOW}Remember to use responsibly and ethically.${NC}" 